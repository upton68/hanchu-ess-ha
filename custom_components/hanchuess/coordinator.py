"""DataUpdateCoordinator for Hanchuess."""
import asyncio
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import ConfigEntryAuthFailed
from .api import HanchuessApiClient, ReauthRequired
from .battery import battery_dev_ids, station_battery_values
from .const import (
    DOMAIN,
    CONF_REALTIME_INTERVAL,
    CONF_STATISTICS_INTERVAL,
    CONF_BATTERY_INTERVAL,
    CONF_SCHEDULE_INTERVAL,
    DEFAULT_SCHEDULE_INTERVAL,
    MIN_SCHEDULE_INTERVAL,
    SCHEDULE_KEYS,
    DEFAULT_REALTIME_INTERVAL,
    DEFAULT_STATISTICS_INTERVAL,
    DEFAULT_BATTERY_INTERVAL,
    DEFAULT_BATTERY_ONLY_INTERVAL,
    MODE_BATTERY_ONLY,
)

_LOGGER = logging.getLogger(__name__)


def _raise_auth_failed(client: HanchuessApiClient, msg: str):
    """Raise ConfigEntryAuthFailed once, UpdateFailed for the rest."""
    if not client._reauth_triggered:
        client._reauth_triggered = True
        raise ConfigEntryAuthFailed(msg)
    raise UpdateFailed(msg)


async def _try_refresh(client, update_cb, force=False):
    """Try to refresh token. Returns True if refreshed, raises on reauth needed."""
    try:
        new_token = await client.async_refresh_token(force=force)
    except ReauthRequired:
        _raise_auth_failed(client, "Token refresh returned 90076, reauth required")
    if new_token:
        update_cb(new_token)
        return True
    return False


class HanchuessRealtimeCoordinator(DataUpdateCoordinator):
    """Realtime data coordinator (60s)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_realtime",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_REALTIME_INTERVAL, DEFAULT_REALTIME_INTERVAL
                )
            ),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict:
        inverter_serial_number = self.entry.data["sn"]
        language = self.hass.config.language or "en"

        # Proactive refresh at 25 days
        if self.client.should_refresh_token():
            await _try_refresh(self.client, self._update_entry_token)

        data = await self.client.async_get_device_status(
            inverter_serial_number, language
        )

        # Reactive refresh on 401
        if data and data.get("_token_expired"):
            refreshed = await _try_refresh(self.client, self._update_entry_token, force=True)
            if refreshed:
                data = await self.client.async_get_device_status(
                    inverter_serial_number, language
                )

        if data and data.get("_token_expired"):
            _raise_auth_failed(self.client, "Token expired and refresh failed")

        if not data:
            raise UpdateFailed("Failed to get device status")
        return data

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )


class HanchuessStatisticsCoordinator(DataUpdateCoordinator):
    """Statistics data coordinator (5min)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_statistics",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_STATISTICS_INTERVAL, DEFAULT_STATISTICS_INTERVAL
                )
            ),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict:
        inverter_serial_number = self.entry.data["sn"]
        language = self.hass.config.language or "en"

        data = await self.client.async_get_device_statistics(
            inverter_serial_number, language
        )

        if data and data.get("_token_expired"):
            refreshed = await _try_refresh(self.client, self._update_entry_token, force=True)
            if refreshed:
                data = await self.client.async_get_device_statistics(
                    inverter_serial_number, language
                )

        if data and data.get("_token_expired"):
            _raise_auth_failed(self.client, "Token expired and refresh failed")

        if not data:
            raise UpdateFailed("Failed to get device statistics")
        return data

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )


class HanchuessBatteryCoordinator(DataUpdateCoordinator):
    """Battery data coordinator.

    Each battery is read with queryBatteryDataDivisions, by its devId from the
    station list where known (falling back to its sn). For a battery-only
    station the station list is also read on every poll, so a battery whose
    detail data is missing still reports SOC/SOH, and the last outcome per
    battery is kept for diagnostics.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        self.battery_only = entry.data.get("mode") == MODE_BATTERY_ONLY
        default = DEFAULT_BATTERY_ONLY_INTERVAL if self.battery_only else DEFAULT_BATTERY_INTERVAL
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_battery",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_BATTERY_INTERVAL, default)
            ),
        )
        self.entry = entry
        self.client = client
        self.dev_ids: dict[str, str] = {}
        # serial -> {"ok", "source", "queried_by", "dev_id_differs", "error"}
        self.battery_status: dict[str, dict] = {}
        self.station_detail: dict | None = None

    @staticmethod
    def _has_detail(result: dict | None) -> bool:
        if not result or result.get("_token_expired"):
            return False
        return bool(result.get("success", True)) and bool(result.get("data"))

    @staticmethod
    def _error(result: dict | None) -> str | None:
        if not result:
            return "no response"
        if result.get("success") is False or result.get("code") not in (None, 200):
            return f"code={result.get('code')} msg={result.get('msg')}"
        if not result.get("data"):
            return "empty data"
        return None

    async def _async_update_data(self) -> dict:
        battery_serials = self.entry.data.get("battery_serials", [])
        if not battery_serials:
            return {}
        language = self.hass.config.language or "en"

        station_values: dict[str, dict] = {}
        if self.battery_only and self.entry.data.get("stationId"):
            detail = await self.client.async_get_station_detail(
                self.entry.data["stationId"], language
            )
            if detail and detail.get("success", True) and detail.get("data"):
                self.station_detail = detail
                self.dev_ids.update(battery_dev_ids(detail))
                station_values = station_battery_values(detail)

        async def _fetch(serial: str):
            dev_id = self.dev_ids.get(serial) or serial
            result = await self.client.async_get_battery_data(dev_id, language)
            queried_by = "devId" if dev_id != serial else "sn"
            if not self._has_detail(result) and dev_id != serial and not (
                result and result.get("_token_expired")
            ):
                retry = await self.client.async_get_battery_data(serial, language)
                if self._has_detail(retry):
                    return serial, retry, "sn"
            return serial, result, queried_by

        results = await asyncio.gather(*(_fetch(serial) for serial in battery_serials))
        data = {}
        token_expired = False
        for serial, result, queried_by in results:
            if result and result.get("_token_expired"):
                token_expired = True
                continue
            status = {
                "queried_by": queried_by,
                "dev_id_differs": self.dev_ids.get(serial, serial) != serial,
            }
            if self._has_detail(result):
                data[serial] = result.get("data") or {}
                status.update(ok=True, source="detail", error=None)
            elif station_values.get(serial):
                data[serial] = dict(station_values[serial])
                status.update(ok=True, source="station", error=self._error(result))
            else:
                status.update(ok=False, source=None, error=self._error(result))
            if not status["ok"] or status["source"] != "detail":
                _LOGGER.debug(
                    "[HANCHUESS] Battery detail unavailable (%s): %s",
                    status["queried_by"], status["error"],
                )
            self.battery_status[serial] = status

        if token_expired:
            refreshed = await _try_refresh(self.client, self._update_entry_token, force=True)
            if refreshed:
                return await self._async_update_data()
            _raise_auth_failed(self.client, "Token expired and refresh failed")

        if not data:
            raise UpdateFailed("Failed to get battery data")
        return data

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )


class HanchuessScheduleCoordinator(DataUpdateCoordinator):
    """Polls the inverter's work mode, slots and SOC limits (default 5 min).

    Feeds the Inverter Status sensor only. The values are kept in this
    coordinator rather than written to the control entities, so a poll never
    overwrites settings the user has staged but not yet written. Auth problems
    are left to the realtime coordinator; a failed poll keeps the last values.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        interval = max(
            int(entry.options.get(CONF_SCHEDULE_INTERVAL, DEFAULT_SCHEDULE_INTERVAL)),
            MIN_SCHEDULE_INTERVAL,
        )
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_schedule",
            config_entry=entry,
            update_interval=timedelta(seconds=interval),
        )
        self.entry = entry
        self.client = client
        self.last_read = None  # when values were last read from the inverter

    def seed(self, values: dict) -> None:
        """Use values already read from the inverter (e.g. at startup)."""
        seeded = {k: v for k, v in values.items() if k in SCHEDULE_KEYS}
        if seeded:
            self.last_read = dt_util.utcnow()
            self.async_set_updated_data(seeded)

    async def _async_update_data(self) -> dict:
        values = await self.client.async_iot_get(
            self.entry.data["sn"], "2", SCHEDULE_KEYS
        )
        if values:
            self.last_read = dt_util.utcnow()
            return {**(self.data or {}), **values}
        if self.data:
            _LOGGER.debug("[HANCHUESS] Schedule poll returned nothing, keeping last values")
            return self.data
        raise UpdateFailed("Failed to read inverter schedule")

    def note_written(self, values: dict) -> None:
        """Merge settings this integration has just written successfully."""
        written = {k: v for k, v in values.items() if k in SCHEDULE_KEYS}
        if written:
            self.async_set_updated_data({**(self.data or {}), **written})
