"""DataUpdateCoordinator for Hanchuess."""
import asyncio
from datetime import date, timedelta as _td
import logging
from datetime import timedelta
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import ConfigEntryAuthFailed
from .api import HanchuessApiClient, ReauthRequired
from .battery import battery_dev_ids, station_battery_values
from .energy import BatteryEnergyState, add_samples
from .staging import SettingsStagingBuffer
from .strategy import (
    KINDS as STRATEGY_KINDS,
    OCTOPUS,
    PRIORITY_KEY,
    WEATHER,
    changes_applied,
    merge_record,
    save_succeeded,
    strategy_record,
)
from .const import (
    DOMAIN,
    CONF_REALTIME_INTERVAL,
    CONF_STATISTICS_INTERVAL,
    CONF_BATTERY_INTERVAL,
    CONF_ENERGY_INTERVAL,
    CONF_HISTORY_INTERVAL,
    DEFAULT_HISTORY_INTERVAL,
    DEFAULT_ENERGY_INTERVAL,
    ENERGY_MAX_CATCHUP_DAYS,
    CONF_SCHEDULE_INTERVAL,
    DEFAULT_SCHEDULE_INTERVAL,
    MIN_SCHEDULE_INTERVAL,
    SCHEDULE_KEYS,
    STRATEGY_INTERVAL,
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


MINUTE_CHART_PAGE = 1440


def _minute_samples(result: dict) -> list:
    """The sample list from a powerMinuteChart response."""
    data = result.get("data")
    if isinstance(data, dict):
        data = data.get("list") or data.get("records") or data.get("data")
    return data if isinstance(data, list) else []


class _TokenExpired(Exception):
    """The cloud rejected the token during an energy fetch."""


def energy_store_key(entry_id: str) -> str:
    return f"{DOMAIN}.battery_energy.{entry_id}"


class HanchuessBatteryEnergyCoordinator(DataUpdateCoordinator):
    """Per-battery charge/discharge energy (default every 5 minutes).

    Reads each battery's minute samples (powerMinuteChart), asking only for
    samples newer than the last one counted, and keeps Today and Total figures
    per battery. Totals and the last sample time are saved, so a restart picks
    up where it left off (catching up at most a few days). Days follow the
    local time zone.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: HanchuessApiClient,
        dev_ids: dict[str, str] | None = None,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_battery_energy",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_ENERGY_INTERVAL, DEFAULT_ENERGY_INTERVAL)
            ),
        )
        self.entry = entry
        self.client = client
        # Shared with the battery coordinator: sn -> devId from the station.
        self.dev_ids = dev_ids if dev_ids is not None else {}
        self.states: dict[str, BatteryEnergyState] = {}
        self.errors: dict[str, str | None] = {}
        self._query_by: dict[str, str] = {}  # sn -> id that returned samples
        # Whether the cloud accepts a range starting mid-day (None = not known yet).
        self._incremental: bool | None = None
        self._store = Store(hass, 1, energy_store_key(entry.entry_id))
        self._loaded = False

    def _snapshot(self) -> dict:
        return {serial: state.as_dict() for serial, state in self.states.items()}

    async def _async_load(self) -> None:
        stored = await self._store.async_load() or {}
        for serial, data in stored.items():
            self.states[serial] = BatteryEnergyState.from_dict(data)
        self._loaded = True

    @staticmethod
    def _day_bounds(day: date) -> tuple[int, int]:
        start = dt_util.start_of_local_day(day)
        end = dt_util.start_of_local_day(day + _td(days=1))
        return int(start.timestamp() * 1000), int(end.timestamp() * 1000) - 1

    async def _chart(self, candidate: str, start_ms: int, end_ms: int, language: str) -> dict:
        result = await self.client.async_get_battery_minute_chart(
            candidate, start_ms, end_ms, language
        )
        if result.get("_token_expired"):
            raise _TokenExpired
        return result

    @staticmethod
    def _failed(result: dict) -> bool:
        return result.get("success") is False or result.get("code") not in (None, 200)

    async def _fetch_day(self, serial: str, state: BatteryEnergyState,
                         day_start: int, day_end: int, language: str) -> bool:
        """Count the samples of one local day newer than the last one counted.

        The cloud expects the range to end at the end of the day, as the web
        console sends it. The start is moved on to the last sample counted so
        only new samples come back; if the cloud refuses that, the whole day
        is asked for instead (already-counted samples are skipped).
        """
        incremental = (
            state.last_ts is not None
            and state.last_ts >= day_start
            and self._incremental is not False
        )
        start_ms = state.last_ts + 1 if incremental else day_start
        if start_ms > day_end:
            return True
        dev_id = self.dev_ids.get(serial) or serial
        candidates = [self._query_by[serial]] if serial in self._query_by else [dev_id]
        if serial not in candidates:
            candidates.append(serial)
        for candidate in candidates:
            result = await self._chart(candidate, start_ms, day_end, language)
            if self._failed(result) and incremental:
                retry = await self._chart(candidate, day_start, day_end, language)
                if not self._failed(retry):
                    _LOGGER.debug(
                        "[HANCHUESS] Minute chart refused a mid-day start; "
                        "fetching whole days from now on"
                    )
                    self._incremental = False
                    incremental = False
                    result = retry
            if self._failed(result):
                self.errors[serial] = (
                    f"code={result.get('code')} "
                    f"msg={result.get('msg') or result.get('message')}"
                )
                continue
            samples = _minute_samples(result)
            if not samples and candidate != candidates[-1]:
                continue  # maybe registered under the other ID
            if samples:
                self._query_by[serial] = candidate
                if incremental:
                    self._incremental = True
            add_samples(state, samples)
            # A full page may mean more samples in the range: fetch the rest.
            pages = 1
            while len(samples) >= MINUTE_CHART_PAGE and pages < 3 and state.last_ts:
                result = await self._chart(candidate, state.last_ts + 1, day_end, language)
                if self._failed(result):
                    break
                samples = _minute_samples(result)
                add_samples(state, samples)
                pages += 1
            self.errors[serial] = None
            return True
        if not self.errors.get(serial):
            self.errors[serial] = "no response"
        return False

    async def _update_battery(self, serial: str, language: str) -> bool:
        today = dt_util.now().date()
        state = self.states.setdefault(serial, BatteryEnergyState())
        if state.day is None:
            state.start_day(today.isoformat())
        day = date.fromisoformat(state.day)
        if (today - day).days > ENERGY_MAX_CATCHUP_DAYS:
            # Too long ago to catch up: restart counting from today.
            state.start_day(today.isoformat())
            state.last_ts = None
            state.last_power = None
            day = today
        while day < today:
            start, end = self._day_bounds(day)
            if not await self._fetch_day(serial, state, start, end, language):
                return False  # retry the same day next poll
            day += _td(days=1)
            state.start_day(day.isoformat())
        start, end = self._day_bounds(today)
        return await self._fetch_day(serial, state, start, end, language)

    async def _async_update_data(self) -> dict:
        if not self._loaded:
            await self._async_load()
        serials = self.entry.data.get("battery_serials", [])
        language = self.hass.config.language or "en"
        for attempt in range(2):
            try:
                results = [await self._update_battery(serial, language) for serial in serials]
                break
            except _TokenExpired:
                if attempt == 0 and await _try_refresh(
                    self.client, self._update_entry_token, force=True
                ):
                    continue
                _raise_auth_failed(self.client, "Token expired and refresh failed")
        self._store.async_delay_save(self._snapshot, 10)
        if serials and not any(results) and not any(
            self.states.get(serial) and self.states[serial].last_ts for serial in serials
        ):
            raise UpdateFailed("Failed to read battery minute data")
        return self._snapshot()

    async def async_save_now(self) -> None:
        """Write the totals straight away (on unload, so a reload starts from them)."""
        if self._loaded:
            await self._store.async_save(self._snapshot())

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )


# Station energy history fields (console Statistics), kWh.
HISTORY_FIELDS = {
    "pv": "pvDge",
    "load": "loadEe",
    "grid_import": "gridTdEe",
    "grid_export": "gridTdFe",
    "battery_charge": "batTdChg",
    "battery_discharge": "batTdDschg",
}


def _history_rows(result: dict) -> list | None:
    """Rows of a historyStaticsChart response, or None if it failed."""
    if result.get("success") is False or result.get("code") not in (None, 200):
        return None
    data = result.get("data")
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else None


def _sum_rows(rows: list) -> dict:
    totals = {}
    for name, field in HISTORY_FIELDS.items():
        total = 0.0
        for row in rows:
            try:
                total += float(row.get(field) or 0)
            except (TypeError, ValueError):
                continue
        totals[name] = round(total, 2)
    return totals


class HanchuessHistoryCoordinator(DataUpdateCoordinator):
    """Station energy for this month, this year and in total (default hourly).

    Uses the web console's Statistics chart (pcs/historyStaticsChart): the
    year view gives one row per month, the all-years view one row per year.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_history",
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_HISTORY_INTERVAL, DEFAULT_HISTORY_INTERVAL)
            ),
        )
        self.entry = entry
        self.client = client
        self.errors: dict[str, str | None] = {}

    async def _fetch(self, date_str: str, language: str) -> list | None:
        result = await self.client.async_get_station_history(
            self.entry.data["sn"], date_str, language
        )
        if result.get("_token_expired"):
            raise _TokenExpired
        rows = _history_rows(result)
        self.errors[date_str] = None if rows is not None else (
            f"code={result.get('code')} msg={result.get('msg') or result.get('message')}"
        )
        return rows

    async def _async_update_data(self) -> dict:
        now = dt_util.now()
        year_key = str(now.year)
        month_key = f"{now.year}-{now.month:02d}"
        language = self.hass.config.language or "en"
        for attempt in range(2):
            try:
                year_rows = await self._fetch(year_key, language)
                all_rows = await self._fetch("0", language)
                break
            except _TokenExpired:
                if attempt == 0 and await _try_refresh(
                    self.client, self._update_entry_token, force=True
                ):
                    continue
                _raise_auth_failed(self.client, "Token expired and refresh failed")
        previous = self.data or {}
        data = {"month_key": month_key, "year_key": year_key}
        if year_rows is not None:
            data["month"] = _sum_rows([r for r in year_rows if r.get("date") == month_key])
            data["year"] = _sum_rows(year_rows)
        elif previous.get("month_key") == month_key:
            data["month"], data["year"] = previous.get("month"), previous.get("year")
        if all_rows is not None:
            data["lifetime"] = _sum_rows(all_rows)
        else:
            data["lifetime"] = previous.get("lifetime")
        if year_rows is None and all_rows is None and not previous:
            raise UpdateFailed("Failed to read station energy history")
        return data

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )


def _describe_failure(result) -> str:
    if not isinstance(result, dict) or not result:
        return "request failed"
    if result.get("_token_expired"):
        return "token expired"
    return f"code={result.get('code')} msg={result.get('msg') or result.get('message')}"


class HanchuessStrategyCoordinator(DataUpdateCoordinator):
    """Weather Optimize and Octopus strategy records (issue #72), every 5 min.

    Data is {"weather": record | None, "octopus": record | None}; a failed read
    keeps the last record. All the entities are disabled by default, and a
    coordinator only polls while it has listeners, so nothing is read unless
    someone enables one. Auth problems are left to the realtime coordinator,
    as for the schedule poll.

    Each strategy has its own staging buffer, separate from the inverter's
    iotSet buffer. async_save() reads the latest record, merges the staged
    changes into it, saves it once and reads it back.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HanchuessApiClient):
        super().__init__(
            hass,
            _LOGGER,
            name="hanchuess_strategy",
            config_entry=entry,
            update_interval=timedelta(seconds=STRATEGY_INTERVAL),
        )
        self.entry = entry
        self.client = client
        self.staging = {kind: SettingsStagingBuffer() for kind in STRATEGY_KINDS}
        self.errors: dict[str, str | None] = {}
        self._lock = asyncio.Lock()
        self._first_read = None

    @property
    def _sn(self) -> str:
        return self.entry.data["sn"]

    def _language(self) -> str:
        return self.hass.config.language or "en"

    def record(self, kind: str) -> dict | None:
        return (self.data or {}).get(kind)

    def async_ensure_loaded(self) -> None:
        """Start one background read if nothing has been read yet.

        Called by each entity as it is added, so enabling an entity shows
        values straight away instead of after the first poll interval.
        """
        if self.data is not None or self._first_read is not None:
            return
        self._first_read = self.entry.async_create_background_task(
            self.hass, self.async_refresh(), "hanchuess strategy first read"
        )

    async def _async_update_data(self) -> dict:
        async with self._lock:
            previous = self.data or {}
            data = {}
            for kind in STRATEGY_KINDS:
                result = await self.client.async_get_strategy(
                    kind, self._sn, self._language()
                )
                record = strategy_record(result)
                self.errors[kind] = None if record is not None else _describe_failure(result)
                data[kind] = record if record is not None else previous.get(kind)
            if not previous and all(data[kind] is None for kind in STRATEGY_KINDS):
                raise UpdateFailed(
                    "Failed to read the Weather Optimize and Octopus settings"
                )
            return data

    async def _call(self, request):
        """Run ``request``; on a 401, refresh the token and run it once more.

        A 401 means the cloud did nothing, so repeating a save is safe here.
        A rejected refresh is not escalated: the realtime coordinator raises
        the reauth prompt on its next poll.
        """
        result = await request()
        if not (isinstance(result, dict) and result.get("_token_expired")):
            return result
        try:
            token = await self.client.async_refresh_token(force=True)
        except ReauthRequired:
            return result
        if not token:
            return result
        self._update_entry_token(token)
        return await request()

    async def _read_latest(self, kind: str) -> dict | None:
        language = self._language()
        result = await self._call(
            lambda: self.client.async_get_strategy(kind, self._sn, language)
        )
        record = strategy_record(result)
        self.errors[kind] = None if record is not None else _describe_failure(result)
        return record

    def _set_record(self, kind: str, record: dict) -> None:
        self.async_set_updated_data({**(self.data or {}), kind: record})

    async def _save_one(self, kind: str, staged: dict) -> tuple[bool, str | None]:
        latest = await self._read_latest(kind)
        if latest is None:
            return False, f"Could not read the current settings ({self.errors.get(kind)})"
        payload = merge_record(latest, staged, self._sn)
        language = self._language()
        _LOGGER.info(
            "[HANCHUESS] Saving %s strategy for %s: %s",
            kind, self._sn, sorted(staged),
        )
        result = await self._call(
            lambda: self.client.async_save_strategy(kind, payload, language)
        )
        after = await self._read_latest(kind)
        if after is not None:
            self._set_record(kind, after)
        if save_succeeded(result):
            return True, None
        # The save is never repeated (each one creates a record), but the
        # response may have been lost after the record was created.
        if (
            after is not None
            and after.get("id") != latest.get("id")
            and changes_applied(after, staged, self._sn)
        ):
            _LOGGER.info("[HANCHUESS] %s save had no clear reply but was applied", kind)
            return True, None
        msg = result.get("msg") if isinstance(result, dict) else None
        return False, msg or _describe_failure(result)

    def _discard_saved(self, kind: str, saved: dict) -> None:
        """Unstage what was saved, unless it was changed again meanwhile."""
        buffer = self.staging[kind]
        buffer.discard(
            [key for key, value in saved.items()
             if key in buffer.pending and buffer.pending[key] == value]
        )

    async def async_save(self, kind: str) -> bool:
        """Save the staged changes for one strategy.

        A staged Strategy priority is saved to both records, since the app
        shows it as one setting. The other strategy's own staged changes stay
        staged until its Save is pressed.
        """
        async with self._lock:
            staged = self.staging[kind].snapshot()
            if not staged:
                _LOGGER.debug("[HANCHUESS] %s save: nothing staged", kind)
                return True
            ok, error = await self._save_one(kind, staged)
            failed = kind
            saved = []
            if ok:
                saved.append(kind)
                self._discard_saved(kind, staged)
                if PRIORITY_KEY in staged:
                    other = OCTOPUS if kind == WEATHER else WEATHER
                    priority = {PRIORITY_KEY: staged[PRIORITY_KEY]}
                    ok, error = await self._save_one(other, priority)
                    if ok:
                        saved.append(other)
                        self._discard_saved(other, priority)
                    else:
                        failed = other
        for saved_kind in saved:
            persistent_notification.async_dismiss(
                self.hass, self._notification_id(saved_kind)
            )
        if ok:
            return True
        self._notify_failure(failed, error)
        return False

    def _notification_id(self, kind: str) -> str:
        return f"hanchuess_{kind}_save_failed_{self._sn}"

    def _notify_failure(self, kind: str, error: str | None) -> None:
        name = "Weather Optimize" if kind == WEATHER else "Octopus strategy"
        pending = sorted(self.staging[kind].pending)
        _LOGGER.error("[HANCHUESS] %s save failed for %s: %s", name, self._sn, error)
        try:
            persistent_notification.async_create(
                self.hass,
                (
                    f"Could not save the {name} settings for inverter **{self._sn}**.\n\n"
                    f"Pending: `{', '.join(pending)}`\n\n"
                    f"Error: {error or 'Unknown error'}\n\n"
                    "The changes are still staged. Press **Save** again to retry."
                ),
                title=f"Hanchuess — {name} not saved",
                notification_id=self._notification_id(kind),
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("[HANCHUESS] Could not create persistent notification: %s", err)

    def _update_entry_token(self, token: str):
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "token": token}
            )
