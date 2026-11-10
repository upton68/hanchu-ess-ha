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
    """Battery data coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_battery",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_BATTERY_INTERVAL, DEFAULT_BATTERY_INTERVAL
                )
            ),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict:
        battery_serials = self.entry.data.get("battery_serials", [])
        if not battery_serials:
            return {}
        language = self.hass.config.language or "en"

        async def _fetch(serial: str):
            return serial, await self.client.async_get_battery_data(serial, language)

        results = await asyncio.gather(*(_fetch(serial) for serial in battery_serials))
        data = {}
        token_expired = False
        for serial, result in results:
            if result and result.get("_token_expired"):
                token_expired = True
                continue
            if result:
                data[serial] = result.get("data", {})

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
