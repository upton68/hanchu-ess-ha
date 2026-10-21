"""Button platform for Hanchuess — Read Settings and Write Settings."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .models import inverter_model_name
from .const import DOMAIN
from . import HanchuessConfigEntry

_LOGGER = logging.getLogger(__name__)

# All control keys managed by the staging buffer.
# Matches the startup iotGet call in __init__.py async_setup_entry.
ALL_CONTROL_KEYS: list[str] = [
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


def apply_iot_values(entry, values: dict) -> None:
    """Push raw iotGet values into registered control entities.

    Iterates the control_registry on entry.runtime_data, calls each entity's
    apply_value(raw) for every key present in ``values``, then requests an HA
    state write.  Used by the Read Settings button after a successful iotGet.
    """
    registry: dict = entry.runtime_data.control_registry
    for key, raw in values.items():
        entity = registry.get(key)
        if entity is None:
            continue
        try:
            entity.apply_value(raw)
            entity.async_write_ha_state()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "[HANCHUESS] apply_iot_values: error applying %s=%s: %s", key, raw, err
            )


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Read Settings and Write Settings button entities."""
    async_add_entities([
        HanchuessReadSettingsButton(hass, entry),
        HanchuessWriteSettingsButton(hass, entry),
    ])


# ---------------------------------------------------------------------------
# Read Settings button
# ---------------------------------------------------------------------------

class HanchuessReadSettingsButton(ButtonEntity):
    """Reads all control-entity values from the device via iotGet."""

    _attr_has_entity_name = True
    _attr_name = "Read Settings"
    _attr_icon = "mdi:download"

    def __init__(self, hass: HomeAssistant, entry: HanchuessConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_read_settings"

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    async def async_press(self) -> None:
        """Fetch all control settings from the device and refresh entity states."""
        inverter_serial_number = self._entry.data["sn"]
        client = self._entry.runtime_data.realtime.client
        _LOGGER.info("[HANCHUESS] Read Settings pressed for %s", inverter_serial_number)
        try:
            values = await client.async_iot_get(
                inverter_serial_number, "2", ALL_CONTROL_KEYS
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("[HANCHUESS] Read Settings failed: %s", err)
            return
        if not values:
            _LOGGER.warning("[HANCHUESS] Read Settings returned empty response")
            return
        apply_iot_values(self._entry, values)
        self._entry.runtime_data.staging.clear()
        _LOGGER.info("[HANCHUESS] Read Settings applied %d values and cleared staging", len(values))


# ---------------------------------------------------------------------------
# Write Settings button
# ---------------------------------------------------------------------------

class HanchuessWriteSettingsButton(ButtonEntity):
    """Flushes all staged control-entity changes to the device via a single iotSet."""

    _attr_has_entity_name = True
    _attr_name = "Write Settings"
    _attr_icon = "mdi:upload"

    def __init__(self, hass: HomeAssistant, entry: HanchuessConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_write_settings"

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    async def async_press(self) -> None:
        """Flush all staged settings to the device."""
        # Import here to avoid circular import at module level
        from . import async_flush_staged
        await async_flush_staged(self._hass, self._entry)
