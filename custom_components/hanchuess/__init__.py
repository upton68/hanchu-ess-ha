"""Hanchuess Home Assistant integration."""
import logging
import os
import asyncio
from dataclasses import dataclass
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.components import websocket_api
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, PLATFORMS, BASE_URL
from .api import HanchuessApiClient
from .battery import merge_battery_serials
from .coordinator import (
    HanchuessRealtimeCoordinator,
    HanchuessStatisticsCoordinator,
    HanchuessBatteryCoordinator,
)
from .staging import SettingsStagingBuffer

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_DEVICE_CONTROL = "device_control"
SERVICE_SCHEMA = vol.Schema({
    vol.Required("sn"): cv.string,
    vol.Required("dev_type"): cv.string,
    vol.Required("value"): dict,
})

CARD_URL = "/hacsfiles/hanchuess/hanchuess-energy-card.js"


@dataclass
class HanchuessData:
    """Data stored on a config entry's runtime_data for the lifetime of its setup."""

    realtime: HanchuessRealtimeCoordinator
    statistics: HanchuessStatisticsCoordinator
    battery: HanchuessBatteryCoordinator | None
    number_limits: dict
    startup_values: dict
    staging: SettingsStagingBuffer
    control_registry: dict  # control_key -> entity, populated by async_added_to_hass


type HanchuessConfigEntry = ConfigEntry[HanchuessData]


def _iter_entry_runtime_data(hass: HomeAssistant):
    """Yield (entry, runtime_data) for every Hanchuess entry that has finished setup."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        data = getattr(entry, "runtime_data", None)
        if data is not None:
            yield entry, data


def _find_realtime_coordinator(hass: HomeAssistant, sn: str | None = None):
    """Return the realtime coordinator for `sn`, or the first configured one if sn is None."""
    for entry, data in _iter_entry_runtime_data(hass):
        if sn is None or entry.data.get("sn") == sn:
            return data.realtime
    return None


def _find_entry(hass: HomeAssistant, sn: str | None = None):
    """Return the config entry for `sn`, or the first one if sn is None."""
    for entry, _data in _iter_entry_runtime_data(hass):
        if sn is None or entry.data.get("sn") == sn:
            return entry
    return None


async def async_flush_staged(hass: HomeAssistant, entry) -> bool:
    """Flush all staged settings for ``entry`` to the device in one iotSet call.

    Returns True on success, False on failure.  On double failure a persistent
    notification is created and the buffer is left intact so the user can retry.
    """
    staging = entry.runtime_data.staging
    snapshot = staging.snapshot()
    if not snapshot:
        _LOGGER.debug("[HANCHUESS] async_flush_staged: nothing staged, skipping")
        return True

    inverter_serial_number = entry.data["sn"]
    client = entry.runtime_data.realtime.client
    _LOGGER.info(
        "[HANCHUESS] Flushing %d staged setting(s) for %s: %s",
        len(snapshot),
        inverter_serial_number,
        list(snapshot.keys()),
    )

    result = await client.async_device_control(inverter_serial_number, "2", snapshot)
    if result.get("success"):
        staging.clear()
        _LOGGER.info("[HANCHUESS] Write Settings succeeded for %s", inverter_serial_number)
        return True

    # First attempt failed — wait 5 s and retry once.
    _LOGGER.warning(
        "[HANCHUESS] Write Settings first attempt failed (%s), retrying in 5 s…",
        result.get("msg"),
    )
    import asyncio as _asyncio
    await _asyncio.sleep(5)
    result = await client.async_device_control(inverter_serial_number, "2", snapshot)
    if result.get("success"):
        staging.clear()
        _LOGGER.info("[HANCHUESS] Write Settings retry succeeded for %s", inverter_serial_number)
        return True

    # Both attempts failed — notify the user and leave the buffer intact.
    _LOGGER.error(
        "[HANCHUESS] Write Settings failed after retry for %s: %s",
        inverter_serial_number,
        result.get("msg"),
    )
    try:
        hass.components.persistent_notification.async_create(
            title="Hanchuess — Write Settings Failed",
            message=(
                f"Could not write settings to inverter **{inverter_serial_number}** after two attempts.\n\n"
                f"Pending keys: `{', '.join(snapshot.keys())}`\n\n"
                f"Error: {result.get('msg', 'Unknown error')}\n\n"
                "The changes are still staged — press **Write Settings** again to retry."
            ),
            notification_id=f"hanchuess_write_failed_{inverter_serial_number}",
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("[HANCHUESS] Could not create persistent notification: %s", err)
    return False


async def async_device_control_service(hass: HomeAssistant, call: ServiceCall) -> dict:
    """Handle the `hanchuess.device_control` service call.

    Returns {"success": bool, "message": str} so automations can inspect the
    outcome via `response_variable`.
    """
    inverter_serial_number = call.data["sn"]
    dev_type = call.data["dev_type"]
    value = call.data["value"]
    _LOGGER.info(
        "[HANCHUESS] service device_control: %s %s",
        inverter_serial_number,
        value,
    )
    coordinator = _find_realtime_coordinator(hass, inverter_serial_number)
    if not coordinator:
        message = f"Device {inverter_serial_number} not found"
        _LOGGER.error("[HANCHUESS] device_control: %s", message)
        return {"success": False, "message": message}

    result = await coordinator.client.async_device_control(
        inverter_serial_number, dev_type, value
    )
    if result.get("success"):
        entry = _find_entry(hass, inverter_serial_number)
        if entry is not None:
            from .button import apply_iot_values

            apply_iot_values(entry, value)
            entry.runtime_data.staging.discard(value.keys())
        else:
            _LOGGER.warning(
                "[HANCHUESS] device_control: no config entry found for %s, "
                "skipping control entity sync",
                inverter_serial_number,
            )
        return {"success": True, "message": "OK"}

    message = result.get("msg", "Unknown error")
    _LOGGER.error("[HANCHUESS] device_control failed: %s", message)
    return {"success": False, "message": message}


async def _async_initial_refresh(coordinator, entry: ConfigEntry) -> None:
    """Run the first coordinator refresh in a state-safe way.

    Home Assistant requires async_config_entry_first_refresh() to be called only
    while the entry is SETUP_IN_PROGRESS. Some test setups call async_setup_entry
    directly with NOT_LOADED entries, so fall back to async_refresh() there.
    """
    if entry.state is ConfigEntryState.SETUP_IN_PROGRESS:
        await coordinator.async_config_entry_first_refresh()
        return

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady(
            f"Initial coordinator refresh failed for {coordinator.name}"
        )


async def _resolve_station_id(
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: HanchuessApiClient,
    device_status: dict | None = None,
) -> str | None:
    """Return the stored station ID, backfilling it from device status if needed.
    resolve_station_id(...) checks entry.data["stationId"]. If it already exists, it returns it immediately.
    If missing, it uses a provided device_status payload (when available) or calls
    client.async_get_device_status(sn, language), pulls stationId from the response,
    writes it back into the config entry (async_update_entry), and returns it (or None if unavailable).
    """
    station_id = entry.data.get("stationId")
    if station_id:
        return station_id

    if device_status is None:
        language = hass.config.language or "en"
        device_status = await client.async_get_device_status(entry.data["sn"], language)
    station_id = device_status.get("stationId") if device_status else None
    if station_id:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "stationId": station_id},
        )
    return station_id


async def _refresh_battery_serials(
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: HanchuessApiClient,
    station_id: str | None,
) -> list[str]:
    """Refresh stored battery serials from the latest station detail.
    refresh_battery_serials(...) starts from stored battery_serials. If there is no station_id, it returns
    existing serials unchanged. Otherwise, it fetches station detail, merges discovered battery serials
    with existing ones via merge_battery_serials, and if the merged list is changed, it updates all Hanchu
    entries that share that same stationId so they all store the same battery_serials. It finally returns
    the merged serial list."""
    existing_serials = entry.data.get("battery_serials", [])
    if not station_id:
        return existing_serials

    language = hass.config.language or "en"
    station_detail = await client.async_get_station_detail(station_id, language)
    merged_serials = merge_battery_serials(existing_serials, station_detail)
    if merged_serials != existing_serials:
        for other_entry in hass.config_entries.async_entries(DOMAIN):
            if other_entry.data.get("stationId") == station_id:
                hass.config_entries.async_update_entry(
                    other_entry,
                    data={**other_entry.data, "battery_serials": merged_serials},
                )
    return merged_serials


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/hacsfiles/hanchuess",
                os.path.join(os.path.dirname(__file__), "www"),
                cache_headers=False,
            )
        ])
    except Exception:
        _LOGGER.warning("[HANCHUESS] Static path registration failed")

    websocket_api.async_register_command(hass, ws_iot_get)
    websocket_api.async_register_command(hass, ws_iot_set)
    websocket_api.async_register_command(hass, ws_fast_charge)
    websocket_api.async_register_command(hass, ws_clear_staging)

    async def handle_device_control(call: ServiceCall):
        return await async_device_control_service(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_DEVICE_CONTROL,
        handle_device_control,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    async def handle_fast_charge(call: ServiceCall):
        inverter_serial_number = call.data.get("sn")

        if not inverter_serial_number:
            coordinator = _find_realtime_coordinator(hass)
            inverter_serial_number = coordinator.entry.data.get("sn") if coordinator else None

        if not inverter_serial_number:
            _LOGGER.error("[HANCHUESS] fast_charge: No inverter serial found")
            return

        act = call.data["act"]
        duration = call.data.get("duration", 0)

        coordinator = _find_realtime_coordinator(hass, inverter_serial_number)
        if not coordinator:
            _LOGGER.error(
                "[HANCHUESS] fast_charge: device %s not found",
                inverter_serial_number,
            )
            return

        result = await coordinator.client.async_fast_charge_discharge(
            inverter_serial_number, act, duration
        )

        if not result.get("success"):
            _LOGGER.error("[HANCHUESS] fast_charge failed: %s", result.get("msg"))

    hass.services.async_register(
        DOMAIN,
        "fast_charge",
        handle_fast_charge,
        schema=vol.Schema({
            vol.Optional("sn"): cv.string,
            vol.Required("act"): vol.All(int, vol.Range(min=-3, max=3)),
            vol.Optional("duration"): vol.All(int, vol.Range(min=0)),
        }),
    )

    async def handle_write_settings(call: ServiceCall):
        """Flush staged settings for the specified (or only) inverter."""
        sn = call.data.get("sn")
        if sn:
            target = _find_entry(hass, sn)
            if not target:
                _LOGGER.error("[HANCHUESS] write_settings: device %s not found", sn)
                return
            await async_flush_staged(hass, target)
            return

        all_entries = list(_iter_entry_runtime_data(hass))
        if len(all_entries) == 1:
            target_entry, _ = all_entries[0]
            await async_flush_staged(hass, target_entry)
        elif len(all_entries) == 0:
            _LOGGER.error("[HANCHUESS] write_settings: no configured inverters found")
        else:
            _LOGGER.error(
                "[HANCHUESS] write_settings: multiple inverters configured — "
                "provide 'sn' to specify which one to flush"
            )

    hass.services.async_register(
        DOMAIN,
        "write_settings",
        handle_write_settings,
        schema=vol.Schema({vol.Optional("sn"): cv.string}),
    )

    return True


@websocket_api.websocket_command({
    vol.Required("type"): "hanchuess/iot_get",
    vol.Required("sn"): str,
    vol.Required("dev_type"): str,
    vol.Required("keys"): [str],
})
@websocket_api.async_response
async def ws_iot_get(hass, connection, msg):
    inverter_serial_number = msg["sn"]
    dev_type = msg["dev_type"]
    keys = msg["keys"]
    coordinator = _find_realtime_coordinator(hass, inverter_serial_number)
    if not coordinator:
        connection.send_error(
            msg["id"], "not_found", f"Device {inverter_serial_number} not found"
        )
        return
    result = await coordinator.client.async_iot_get(inverter_serial_number, dev_type, keys)
    entry = _find_entry(hass, inverter_serial_number)
    if entry is not None:
        from .button import apply_iot_values

        apply_iot_values(entry, result)
    else:
        _LOGGER.warning(
            "[HANCHUESS] ws_iot_get: no config entry found for %s, "
            "skipping control entity sync",
            inverter_serial_number,
        )
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({
    vol.Required("type"): "hanchuess/iot_set",
    vol.Required("sn"): str,
    vol.Required("dev_type"): str,
    vol.Required("value"): dict,
})
@websocket_api.async_response
async def ws_iot_set(hass, connection, msg):
    inverter_serial_number = msg["sn"]
    dev_type = msg["dev_type"]
    value = msg["value"]
    for k, v in value.items():
        if isinstance(v, str):
            try:
                value[k] = int(v)
            except ValueError:
                pass
    coordinator = _find_realtime_coordinator(hass, inverter_serial_number)
    if not coordinator:
        connection.send_error(
            msg["id"], "not_found", f"Device {inverter_serial_number} not found"
        )
        return
    result = await coordinator.client.async_device_control(
        inverter_serial_number, dev_type, value
    )
    if result.get("success"):
        entry = _find_entry(hass, inverter_serial_number)
        if entry is not None:
            from .button import apply_iot_values

            apply_iot_values(entry, value)
            entry.runtime_data.staging.discard(value.keys())
        else:
            _LOGGER.warning(
                "[HANCHUESS] ws_iot_set: no config entry found for %s, "
                "skipping control entity sync",
                inverter_serial_number,
            )
        connection.send_result(msg["id"], result.get("data", {}))
    else:
        connection.send_error(msg["id"], "control_failed", result.get("msg", "Unknown error"))


@websocket_api.websocket_command({
    vol.Required("type"): "hanchuess/fast_charge",
    vol.Required("sn"): str,
    vol.Required("act"): vol.All(int, vol.Range(min=-3, max=3)),
    vol.Required("duration"): vol.All(int, vol.Range(min=0)),
})
@websocket_api.async_response
async def ws_fast_charge(hass, connection, msg):
    inverter_serial_number = msg["sn"]
    coordinator = _find_realtime_coordinator(hass, inverter_serial_number)
    if not coordinator:
        connection.send_error(
            msg["id"], "not_found", f"Device {inverter_serial_number} not found"
        )
        return
    result = await coordinator.client.async_fast_charge_discharge(
        inverter_serial_number, msg["act"], msg["duration"]
    )
    if result.get("success"):
        connection.send_result(msg["id"], result.get("data", {}))
    else:
        connection.send_error(msg["id"], "fast_charge_failed", result.get("msg", "Unknown error"))


@websocket_api.websocket_command({
    vol.Required("type"): "hanchuess/clear_staging",
    vol.Required("sn"): str,
})
@websocket_api.async_response
async def ws_clear_staging(hass, connection, msg):
    """Clear the staging buffer for the given inverter.

    Called by the Lovelace card after a successful Load or Set so that the
    HA Pending Changes sensor reflects the now-clean state.
    """
    inverter_serial_number = msg["sn"]
    entry = _find_entry(hass, inverter_serial_number)
    if entry is None:
        connection.send_error(
            msg["id"], "not_found", f"Device {inverter_serial_number} not found"
        )
        return
    entry.runtime_data.staging.clear()
    _LOGGER.debug("[HANCHUESS] Staging buffer cleared via WS for %s", inverter_serial_number)
    connection.send_result(msg["id"], {})


async def async_setup_entry(hass: HomeAssistant, entry: HanchuessConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    if not hass.data[DOMAIN].get("_card_registered"):
        try:
            lovelace_data = hass.data.get("lovelace")
            if lovelace_data and lovelace_data.resource_mode == "storage":
                resources = lovelace_data.resources
                existing = [r for r in resources.async_items() if "hanchuess-energy-card" in r.get("url", "")]
                if not existing:
                    await resources.async_create_item({
                        "res_type": "module",
                        "url": CARD_URL,
                    })
                    _LOGGER.info("[HANCHUESS] Card resource auto-registered")
            hass.data[DOMAIN]["_card_registered"] = True
        except Exception as err:
            _LOGGER.warning("[HANCHUESS] Card resource auto-register failed: %s", err)

    if "_client" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["_client"] = HanchuessApiClient(
            hass,
            domain=BASE_URL,
            token=entry.data.get("token"),
        )
    client = hass.data[DOMAIN]["_client"]

    coordinator = HanchuessRealtimeCoordinator(hass, entry, client)
    await _async_initial_refresh(coordinator, entry)

    stats_coordinator = HanchuessStatisticsCoordinator(hass, entry, client)
    await _async_initial_refresh(stats_coordinator, entry)

    station_id = await _resolve_station_id(hass, entry, client, coordinator.data)
    battery_serials = await _refresh_battery_serials(hass, entry, client, station_id)

    battery_coordinator = None
    if battery_serials:
        battery_coordinator = HanchuessBatteryCoordinator(hass, entry, client)
        await _async_initial_refresh(battery_coordinator, entry)

    # Fetch menu to get device-specific min/max values for number entities
    language = hass.config.language or "en"
    inverter_serial_number = entry.data["sn"]
    number_limits = {
        "CHG_PWR_LMT": {"min": 0, "max": 5000},
        "DSCHG_PWR_LMT": {"min": 0, "max": 5000},
        "CHG_BAT_SOC_LMT": {"min": 50, "max": 100},
        "DSCHG_BAT_SOC_LMT": {"min": 5, "max": 45},
        "DTU_AC_CHG_SOC_LMT": {"min": 20, "max": 100},
    }
    try:
        menu_data = await client.async_get_menu(inverter_serial_number, language)
        energy = menu_data.get("data", {}).get("energy", {})
        for group in energy.get("items", []):
            for item in group:
                signal = item.get("itemCodeSignal", "")
                if signal in number_limits:
                    try:
                        min_val = float(item.get("minVal", number_limits[signal]["min"]))
                        max_val = float(item.get("maxVal", number_limits[signal]["max"]))
                        if min_val is not None and max_val is not None:
                            number_limits[signal]["min"] = min_val
                            number_limits[signal]["max"] = max_val
                            _LOGGER.info("[HANCHUESS] %s limits: %s-%s", signal, min_val, max_val)
                    except (ValueError, TypeError):
                        pass
    except Exception as err:
        _LOGGER.warning("[HANCHUESS] Could not fetch menu for number limits, using defaults: %s", err)

    # Fetch all current values in one iotGet call — relies on the API
    # client's own internal retry/timeout handling (see api.py)
    startup_values = {}
    try:
        startup_values = await client.async_iot_get(
            inverter_serial_number,
            "2",
            [
                "WORK_MODE_CMB",
                "CHG_PWR_LMT",
                "DSCHG_PWR_LMT",
                "CHG_BAT_SOC_LMT",
                "DSCHG_BAT_SOC_LMT",
                "DTU_AC_CHG_SOC_LMT",
                "TCT_START_1", "TCT_END_1",
                "TCT_START_2", "TCT_END_2",
                "TCT_START_3", "TCT_END_3",
                "TDT_START_1", "TDT_END_1",
                "TDT_START_2", "TDT_END_2",
                "TDT_START_3", "TDT_END_3",
            ]
        )
        _LOGGER.info("[HANCHUESS] Startup values fetched: %s", startup_values)
    except Exception as err:
        _LOGGER.warning("[HANCHUESS] Could not fetch startup values: %s", err)

    entry.runtime_data = HanchuessData(
        realtime=coordinator,
        statistics=stats_coordinator,
        battery=battery_coordinator,
        number_limits=number_limits,
        startup_values=startup_values,
        staging=SettingsStagingBuffer(),
        control_registry={},
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if startup_values:
        from .button import apply_iot_values
        apply_iot_values(entry, startup_values)
        _LOGGER.info(
            "[HANCHUESS] Applied %d startup value(s) to control entities",
            len(startup_values),
        )

    pending = entry.data.get("pending_devices", [])
    if pending:
        for item in pending:
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data={
                    "sn": item["sn"],
                    "dev_type": item.get("devType", "2"),
                    "token": entry.data["token"],
                    "stationId": entry.data.get("stationId"),
                    "battery_serials": entry.data.get("battery_serials", []),
                },
            )
        new_data = {k: v for k, v in entry.data.items() if k != "pending_devices"}
        hass.config_entries.async_update_entry(entry, data=new_data)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: HanchuessConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
