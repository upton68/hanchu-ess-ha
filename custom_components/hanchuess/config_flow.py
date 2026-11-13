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
    WEB_CONSOLE_URL,
    MODE_BATTERY_ONLY,
    CONF_REALTIME_INTERVAL,
    CONF_STATISTICS_INTERVAL,
    CONF_BATTERY_INTERVAL,
    CONF_FAST_CHARGE_DURATION,
    DEFAULT_REALTIME_INTERVAL,
    DEFAULT_STATISTICS_INTERVAL,
    DEFAULT_BATTERY_INTERVAL,
    DEFAULT_FAST_CHARGE_DURATION,
    CONF_SCHEDULE_INTERVAL,
    DEFAULT_SCHEDULE_INTERVAL,
    MIN_SCHEDULE_INTERVAL,
    DEFAULT_BATTERY_ONLY_INTERVAL,
    MIN_BATTERY_ONLY_INTERVAL,
)
from .battery import battery_only_serials, extract_battery_serials
from .api import HanchuessApiClient

_LOGGER = logging.getLogger(__name__)


class HanchuessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._token = None
        self._devices = []
        self._client = None
        self._account = None
        self._password = None
        # stationId -> {"name": ..., "battery_serials": [...]}
        self._battery_stations: dict[str, dict] = {}

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
            self._account = shared_client._account
            self._password = shared_client._password
            self._devices = await shared_client.async_get_devices()
            if self._available_inverters():
                return await self.async_step_select_device()
            if await self._discover_battery_stations():
                return await self.async_step_battery_station()

        errors = {}
        if user_input is not None:
            client = HanchuessApiClient(self.hass, BASE_URL)
            token = await client.async_login(
                user_input["account"], user_input["password"]
            )
            if token:
                self._token = client.token
                self._client = client
                self._account = user_input["account"]
                self._password = user_input["password"]
                self._devices = await client.async_get_devices()
                if self._available_inverters():
                    return await self.async_step_select_device()
                # No Hanchu inverter: look for Hanchu batteries on the
                # account's stations (e.g. with a third-party inverter).
                if await self._discover_battery_stations():
                    return await self.async_step_battery_station()
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

    def _configured_ids(self) -> set:
        return {
            e.unique_id for e in self.hass.config_entries.async_entries(DOMAIN)
        } | {
            e.data.get("sn") for e in self.hass.config_entries.async_entries(DOMAIN)
        }

    def _available_inverters(self) -> dict:
        configured = self._configured_ids()
        return {
            d["sn"]: d["sn"]
            for d in self._devices
            if d.get("devType") == "2" and d.get("sn") and d["sn"] not in configured
        }

    async def _discover_battery_stations(self) -> bool:
        """Find stations with Hanchu batteries but no Hanchu inverter."""
        client = self._client
        if client is None:
            return False
        language = self.hass.config.language or "en"
        configured = self._configured_ids()
        self._battery_stations = {}
        for station in await client.async_get_stations(language):
            station_id = station.get("stationId")
            if not station_id or f"station_{station_id}" in configured:
                continue
            detail = await client.async_get_station_detail(station_id, language)
            serials = battery_only_serials(detail)
            if serials:
                self._battery_stations[station_id] = {
                    "name": station.get("stationName") or station_id,
                    "battery_serials": serials,
                }
        return bool(self._battery_stations)

    async def async_step_battery_station(self, user_input=None):
        """Add a station's Hanchu batteries when there's no Hanchu inverter."""
        stations = self._battery_stations
        if user_input is not None:
            station_id = user_input.get("station") or next(iter(stations))
            station = stations[station_id]
            await self.async_set_unique_id(f"station_{station_id}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Hanchu Batteries {station['name']}",
                data={
                    "mode": MODE_BATTERY_ONLY,
                    "token": self._token,
                    **self._credentials(),
                    "stationId": station_id,
                    "stationName": station["name"],
                    "battery_serials": station["battery_serials"],
                },
            )

        if len(stations) == 1:
            station = next(iter(stations.values()))
            return self.async_show_form(
                step_id="battery_station",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "station": station["name"],
                    "count": str(len(station["battery_serials"])),
                },
            )
        options = {
            station_id: f"{s['name']} ({len(s['battery_serials'])} batteries)"
            for station_id, s in stations.items()
        }
        return self.async_show_form(
            step_id="battery_station",
            data_schema=vol.Schema({vol.Required("station"): vol.In(options)}),
            description_placeholders={"station": "", "count": ""},
        )

    def _credentials(self) -> dict:
        """Credentials to store with the entry, so a rejected refresh can re-login."""
        if self._account and self._password:
            return {"account": self._account, "password": self._password}
        return {}

    async def async_step_select_device(self, user_input=None):
        """Step 2: Select devices (multi-select)."""
        errors = {}
        # Filter inverters and exclude already configured
        available = self._available_inverters()

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
                        description_placeholders={"console_url": WEB_CONSOLE_URL},
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
                        **self._credentials(),
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
                **({"account": data["account"], "password": data["password"]}
                   if data.get("account") and data.get("password") else {}),
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
                        entry,
                        data={
                            **entry.data,
                            "token": token,
                            "account": user_input["account"],
                            "password": user_input["password"],
                        },
                    )
                # Update shared client
                domain_data = self.hass.data.get(DOMAIN, {})
                if "_client" in domain_data:
                    domain_data["_client"]._token = token
                    domain_data["_client"]._token_time = time.time()
                    domain_data["_client"]._reauth_triggered = False
                    domain_data["_client"].set_credentials(
                        user_input["account"], user_input["password"]
                    )
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
        if self.config_entry.data.get("mode") == MODE_BATTERY_ONLY:
            # Battery-only stations only have the battery poll.
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({
                    vol.Required(
                        CONF_BATTERY_INTERVAL,
                        default=options.get(
                            CONF_BATTERY_INTERVAL, DEFAULT_BATTERY_ONLY_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_BATTERY_ONLY_INTERVAL, max=86400),
                    ),
                }),
            )

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
            vol.Required(
                CONF_SCHEDULE_INTERVAL,
                default=options.get(CONF_SCHEDULE_INTERVAL, DEFAULT_SCHEDULE_INTERVAL),
            ): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCHEDULE_INTERVAL, max=3600)
            ),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
