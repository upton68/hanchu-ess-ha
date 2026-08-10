"""Config flow for Hanchuess."""
import logging
import time
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.core import callback
from .const import (
    DOMAIN,
    BASE_URL,
    CONF_REALTIME_INTERVAL,
    CONF_STATISTICS_INTERVAL,
    CONF_BATTERY_INTERVAL,
    CONF_FAST_CHARGE_DURATION,
    DEFAULT_REALTIME_INTERVAL,
    DEFAULT_STATISTICS_INTERVAL,
    DEFAULT_BATTERY_INTERVAL,
    DEFAULT_FAST_CHARGE_DURATION,
)
from .battery import extract_battery_serials
from .api import HanchuessApiClient

_LOGGER = logging.getLogger(__name__)


class HanchuessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._token = None
        self._devices = []
        self._client = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HanchuessOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Step 1: Login."""
        # Check if already logged in — use shared client directly
        existing = self.hass.data.get(DOMAIN, {})
        shared_client = existing.get("_client")
        if shared_client and shared_client.token:
            self._token = shared_client.token
            self._client = shared_client
            self._devices = await shared_client.async_get_devices()
            if self._devices:
                return await self.async_step_select_device()

        errors = {}
        if user_input is not None:
            client = HanchuessApiClient(self.hass, BASE_URL)
            token = await client.async_login(
                user_input["account"], user_input["password"]
            )
            if token:
                self._token = client.token
                self._client = client
                self._devices = await client.async_get_devices()
                if self._devices:
                    return await self.async_step_select_device()
                errors["base"] = "no_devices"
            else:
                errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("account"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )

    async def async_step_select_device(self, user_input=None):
        """Step 2: Select devices (multi-select)."""
        errors = {}
        # Filter inverters and exclude already configured
        configured_ids = set()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            configured_ids.add(entry.data.get("sn"))

        available = {
            d["sn"]: d["sn"]
            for d in self._devices
            if d.get("devType") == "2" and d["sn"] not in configured_ids
        }

        if not available:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            selected = user_input.get("devices", [])
            if not selected:
                errors["base"] = "no_devices"
            else:
                # Create entry for the first device
                inverter_serial_number = selected[0]
                await self.async_set_unique_id(inverter_serial_number)
                self._abort_if_unique_id_configured()

                client = self._client or HanchuessApiClient(self.hass, BASE_URL, token=self._token)
                self._client = client

                language = self.hass.config.language or "en"
                device_status = await client.async_get_device_status(
                    inverter_serial_number, language
                )
                station_id = device_status.get("stationId")
                if not station_id:
                    errors["base"] = "station_lookup_failed"
                    return self.async_show_form(
                        step_id="select_device",
                        data_schema=vol.Schema({
                            vol.Required("devices"): cv.multi_select(available),
                        }),
                        errors=errors,
                    )

                station_detail = await client.async_get_station_detail(station_id, language)
                if not station_detail:
                    errors["base"] = "battery_lookup_failed"
                    return self.async_show_form(
                        step_id="select_device",
                        data_schema=vol.Schema({
                            vol.Required("devices"): cv.multi_select(available),
                        }),
                        errors=errors,
                    )
                battery_serials = extract_battery_serials(station_detail)

                # Find devType
                dev_type = "2"
                for d in self._devices:
                    if d["sn"] == inverter_serial_number:
                        dev_type = d.get("devType", "2")
                        break

                # Build pending devices with devType
                pending = []
                for pending_inverter_serial_number in selected[1:]:
                    p_type = "2"
                    for d in self._devices:
                        if d["sn"] == pending_inverter_serial_number:
                            p_type = d.get("devType", "2")
                            break
                    pending.append({"sn": pending_inverter_serial_number, "devType": p_type})

                return self.async_create_entry(
                    title=f"Hanchuess {inverter_serial_number}",
                    data={
                        "sn": inverter_serial_number,
                        "dev_type": dev_type,
                        "token": self._token,
                        "stationId": station_id,
                        "battery_serials": battery_serials,
                        "pending_devices": pending,
                    },
                )

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required("devices"): cv.multi_select(available),
            }),
            errors=errors,
        )

    async def async_step_import(self, data: dict):
        """Handle creation of additional devices from pending list."""
        inverter_serial_number = data["sn"]
        await self.async_set_unique_id(inverter_serial_number)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Hanchuess {inverter_serial_number}",
            data={
                "sn": inverter_serial_number,
                "dev_type": data.get("dev_type", "2"),
                "token": data["token"],
                "stationId": data.get("stationId"),
                "battery_serials": data.get("battery_serials", []),
                "pending_devices": [],
            },
        )

    async def async_step_reauth(self, entry_data: dict):
        """Handle reauth triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Re-authenticate with user credentials."""
        errors = {}
        if user_input is not None:
            client = HanchuessApiClient(self.hass, BASE_URL)
            token = await client.async_login(
                user_input["account"], user_input["password"]
            )
            if token:
                # Update token for ALL entries and shared client
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    self.hass.config_entries.async_update_entry(
                        entry, data={**entry.data, "token": token}
                    )
                # Update shared client
                domain_data = self.hass.data.get(DOMAIN, {})
                if "_client" in domain_data:
                    domain_data["_client"]._token = token
                    domain_data["_client"]._token_time = time.time()
                    domain_data["_client"]._reauth_triggered = False
                # Schedule reload for all entries (non-blocking)
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(entry.entry_id)
                    )
                return self.async_abort(reason="reauth_successful")
            errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({
                vol.Required("account"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )


class HanchuessOptionsFlow(OptionsFlowWithReload):
    """Options flow: poll intervals and fast-charge duration."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data_schema = vol.Schema({
            vol.Required(
                CONF_REALTIME_INTERVAL,
                default=options.get(CONF_REALTIME_INTERVAL, DEFAULT_REALTIME_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
            vol.Required(
                CONF_STATISTICS_INTERVAL,
                default=options.get(CONF_STATISTICS_INTERVAL, DEFAULT_STATISTICS_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
            vol.Required(
                CONF_BATTERY_INTERVAL,
                default=options.get(CONF_BATTERY_INTERVAL, DEFAULT_BATTERY_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
            vol.Required(
                CONF_FAST_CHARGE_DURATION,
                default=options.get(CONF_FAST_CHARGE_DURATION, DEFAULT_FAST_CHARGE_DURATION),
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=240)),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
