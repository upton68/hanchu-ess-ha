"""Tests for per-battery Charge/Discharge Today and Total (powerMinuteChart)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hanchuess.energy import (
    MAX_GAP_MS,
    BatteryEnergyState,
    add_samples,
    sample_power,
    segment_energy,
)

MINUTE = 60_000


def _s(ts, v, i):
    return {"dataTimeTs": ts, "vPack": str(v), "iPack": str(i)}


# --- pure calculation -------------------------------------------------------


def test_sample_power():
    assert sample_power(_s(1000, 50, 10)) == (1000, 500.0)
    assert sample_power(_s(1000, 50, -10)) == (1000, -500.0)
    assert sample_power({"dataTimeTs": 1, "vPack": "x", "iPack": "1"}) is None
    assert sample_power({"vPack": "50", "iPack": "1"}) is None


def test_segment_energy_same_sign():
    # 1000 W for one hour = 1 kWh charge.
    assert segment_energy(1000, 1000, 1) == (1.0, 0.0)
    charge, discharge = segment_energy(-2000, -1000, 1)
    assert charge == 0.0 and discharge == pytest.approx(1.5)
    assert segment_energy(1000, 1000, 0) == (0.0, 0.0)


def test_segment_energy_splits_at_sign_change():
    # +1000 W to -1000 W over 1 h: half the time each side, 0.25 kWh each.
    charge, discharge = segment_energy(1000, -1000, 1)
    assert charge == pytest.approx(0.25)
    assert discharge == pytest.approx(0.25)
    # Not netted off to zero.
    assert charge + discharge > 0


def test_add_samples_counts_charge_and_discharge():
    state = BatteryEnergyState(day="2026-11-16")
    samples = [_s(i * MINUTE, 50, 60) for i in range(61)]  # 3000 W for 60 min
    assert add_samples(state, samples) == 61
    assert state.charge_today == pytest.approx(3.0)
    assert state.charge_total == pytest.approx(3.0)
    assert state.discharge_today == 0.0
    more = [_s((61 + i) * MINUTE, 50, -24) for i in range(60)]  # -1200 W
    add_samples(state, more)
    assert state.discharge_today > 1.1  # ~1.18 after the crossing minute


def test_add_samples_ignores_duplicates_and_unsorted():
    state = BatteryEnergyState(day="d")
    samples = [_s(2 * MINUTE, 50, 20), _s(0, 50, 20), _s(MINUTE, 50, 20)]
    add_samples(state, samples)
    first = state.charge_total
    assert add_samples(state, samples) == 0  # same samples again
    assert state.charge_total == first
    assert state.last_ts == 2 * MINUTE


def test_add_samples_skips_gaps():
    state = BatteryEnergyState(day="d")
    add_samples(state, [_s(0, 50, 20), _s(MINUTE, 50, 20)])
    before = state.charge_total
    add_samples(state, [_s(MINUTE + MAX_GAP_MS + 1, 50, 20)])
    assert state.charge_total == before  # gap not guessed
    add_samples(state, [_s(2 * MINUTE + MAX_GAP_MS + 1, 50, 20)])
    assert state.charge_total > before  # counting resumes after the gap


def test_start_day_keeps_totals_and_round_trip():
    state = BatteryEnergyState(day="a", charge_today=1, discharge_today=2,
                               charge_total=10, discharge_total=20, last_ts=5, last_power=1.0)
    restored = BatteryEnergyState.from_dict(json.loads(json.dumps(state.as_dict())))
    assert restored == state
    restored.start_day("b")
    assert (restored.charge_today, restored.discharge_today) == (0.0, 0.0)
    assert (restored.charge_total, restored.discharge_total) == (10, 20)
    assert restored.day == "b"


def test_from_dict_tolerates_missing():
    assert BatteryEnergyState.from_dict(None) == BatteryEnergyState()
    assert BatteryEnergyState.from_dict({"charge_total": 3}).charge_total == 3


# --- coordinator ------------------------------------------------------------

pytest.importorskip("homeassistant")

from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.exceptions import ConfigEntryAuthFailed  # noqa: E402
from homeassistant.helpers.update_coordinator import UpdateFailed  # noqa: E402
from homeassistant.util import dt as dt_util  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.hanchuess.const import DOMAIN  # noqa: E402
from custom_components.hanchuess.coordinator import (  # noqa: E402
    HanchuessBatteryEnergyCoordinator,
    energy_store_key,
)


def _entry(hass, serials=("B1",)):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="SN1",
        data={"sn": "SN1", "token": "tok", "battery_serials": list(serials)},
    )
    entry.add_to_hass(hass)
    return entry


def _end_of_day_ms(start_ms: int) -> int:
    day = dt_util.as_local(dt_util.utc_from_timestamp(start_ms / 1000)).date()
    return _ms(dt_util.start_of_local_day(day + timedelta(days=1))) - 1


def _chart_client(series_by_id, whole_days_only=False):
    """Fake client answering powerMinuteChart from {id: [samples]} by range.

    Like the real cloud, it refuses (code 100) a range that doesn't end at
    the end of the start's local day. With whole_days_only it also refuses a
    start that isn't midnight.
    """
    client = MagicMock()
    client.token = "tok"
    client._reauth_triggered = False
    calls = []

    async def chart(dev_id, start, end, language="en"):
        calls.append((dev_id, start, end))
        if end != _end_of_day_ms(start):
            return {"code": 100, "success": False}
        if whole_days_only and end - start != 86_400_000 - 1:
            return {"code": 100, "success": False}
        if dev_id not in series_by_id:
            return {"code": 200, "success": True, "data": []}
        rows = [s for s in series_by_id[dev_id] if start <= s["dataTimeTs"] <= end]
        return {"code": 200, "success": True, "data": rows}

    client.async_get_battery_minute_chart = AsyncMock(side_effect=chart)
    client.calls = calls
    return client


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _today_series(minutes, power_a=20.0, start_offset=0):
    start = dt_util.start_of_local_day()
    return [_s(_ms(start) + (start_offset + i) * MINUTE, 50, power_a) for i in range(minutes)]


async def _coord(hass, client, entry, dev_ids=None):
    coordinator = HanchuessBatteryEnergyCoordinator(hass, entry, client, dev_ids or {})
    return coordinator


async def test_coordinator_counts_today_and_fetches_incrementally(hass: HomeAssistant):
    entry = _entry(hass)
    series = _today_series(61)  # 1000 W for 60 min from midnight
    client = _chart_client({"B1": series})
    now = dt_util.start_of_local_day() + timedelta(hours=2)
    coordinator = await _coord(hass, client, entry)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=now):
        data = await coordinator._async_update_data()
        assert data["B1"]["charge_today"] == pytest.approx(1.0)
        assert data["B1"]["day"] == now.date().isoformat()
        last = data["B1"]["last_ts"]
        await coordinator._async_update_data()
    # Second poll asks only for samples after the last one counted, and
    # every request ends at the end of the day, as the web console sends it.
    assert client.calls[-1][1] == last + 1
    assert all(end == _end_of_day_ms(start) for _, start, end in client.calls)
    assert coordinator.states["B1"].charge_total == pytest.approx(1.0)


async def test_coordinator_uses_dev_id_then_falls_back_to_sn(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({"B1": _today_series(11)})  # only answers under the sn
    now = dt_util.start_of_local_day() + timedelta(hours=1)
    coordinator = await _coord(hass, client, entry, dev_ids={"B1": "D1"})
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=now):
        await coordinator._async_update_data()
        assert [c[0] for c in client.calls] == ["D1", "B1"]
        await coordinator._async_update_data()
    # Remembers which ID worked.
    assert client.calls[-1][0] == "B1"


async def test_coordinator_day_rollover_catches_up_yesterday(hass: HomeAssistant):
    entry = _entry(hass)
    today_start = dt_util.start_of_local_day()
    yesterday_start = dt_util.start_of_local_day(today_start.date() - timedelta(days=1))
    # Yesterday 23:00-23:59 charging at 1000 W, today 00:00-00:30 discharging.
    late = [_s(_ms(yesterday_start) + (23 * 60 + i) * MINUTE, 50, 20) for i in range(60)]
    early = [_s(_ms(today_start) + i * MINUTE, 50, -20) for i in range(31)]
    client = _chart_client({"B1": late + early})
    coordinator = await _coord(hass, client, entry)
    # Saved state from yesterday at 23:00.
    coordinator._loaded = True
    coordinator.states["B1"] = BatteryEnergyState(
        day=yesterday_start.date().isoformat(), charge_today=5.0, charge_total=50.0,
        last_ts=_ms(yesterday_start) + 23 * 60 * MINUTE - MINUTE, last_power=1000.0,
    )
    now = today_start + timedelta(minutes=45)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=now):
        data = await coordinator._async_update_data()
    state = data["B1"]
    assert state["day"] == now.date().isoformat()
    assert state["charge_today"] == pytest.approx(0.0, abs=0.01)  # only the crossing minute
    assert state["discharge_today"] == pytest.approx(0.5, abs=0.01)
    assert state["charge_total"] == pytest.approx(51.0, abs=0.01)  # yesterday's last hour added


async def test_coordinator_restarts_after_long_outage(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({"B1": _today_series(11)})
    coordinator = await _coord(hass, client, entry)
    coordinator._loaded = True
    old = (dt_util.now() - timedelta(days=10)).date().isoformat()
    coordinator.states["B1"] = BatteryEnergyState(day=old, charge_total=7.0, last_ts=1, last_power=5.0)
    now = dt_util.start_of_local_day() + timedelta(hours=1)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=now):
        data = await coordinator._async_update_data()
    assert len(client.calls) == 1  # no day-by-day catch-up
    assert data["B1"]["day"] == now.date().isoformat()
    assert data["B1"]["charge_total"] == pytest.approx(7.0 + 10 * 1000 / 60 / 1000)


async def test_coordinator_refreshes_token_once(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({"B1": _today_series(5)})
    answers = [{"_token_expired": True}]
    original = client.async_get_battery_minute_chart.side_effect

    async def chart(*args):
        return answers.pop(0) if answers else await original(*args)

    client.async_get_battery_minute_chart.side_effect = chart
    client.async_refresh_token = AsyncMock(return_value="new")
    coordinator = await _coord(hass, client, entry)
    await coordinator._async_update_data()
    client.async_refresh_token.assert_awaited_once()
    assert entry.data["token"] == "new"


async def test_coordinator_auth_failed_when_refresh_fails(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({})
    client.async_get_battery_minute_chart = AsyncMock(return_value={"_token_expired": True})
    client.async_refresh_token = AsyncMock(return_value=None)
    coordinator = await _coord(hass, client, entry)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_update_failed_with_no_data(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({})
    client.async_get_battery_minute_chart = AsyncMock(return_value={"code": 500, "msg": "x"})
    coordinator = await _coord(hass, client, entry)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert coordinator.errors["B1"] == "code=500 msg=x"


async def test_coordinator_persists_and_reloads(hass: HomeAssistant, hass_storage):
    entry = _entry(hass)
    hass_storage[energy_store_key(entry.entry_id)] = {
        "version": 1, "key": energy_store_key(entry.entry_id),
        "data": {"B1": {"day": dt_util.now().date().isoformat(), "charge_total": 12.5,
                         "discharge_total": 3.0, "last_ts": None}},
    }
    client = _chart_client({"B1": _today_series(3)})
    coordinator = await _coord(hass, client, entry)
    data = await coordinator._async_update_data()
    assert data["B1"]["charge_total"] >= 12.5
    assert data["B1"]["discharge_total"] == 3.0


# --- sensors ----------------------------------------------------------------

from custom_components.hanchuess import sensor as sensor_mod  # noqa: E402
from custom_components.hanchuess.sensor import (  # noqa: E402
    BATTERY_ENERGY_SENSORS,
    BatteryEnergySensor,
    BatteryStateSensor,
)


def _sensor_entry(energy):
    battery = MagicMock()
    battery.data = {"B1": {"stateBat": "1"}}
    return SimpleNamespace(
        data={"mode": "battery_only", "battery_serials": ["B1"]},
        runtime_data=SimpleNamespace(
            realtime=None, statistics=None, battery=battery, energy=energy,
            inverter_device_id="dev1",
        ),
    )


def test_energy_sensor_values():
    energy = MagicMock()
    today = dt_util.now().date().isoformat()
    energy.data = {"B1": {"day": today, "charge_today": 1.23456, "discharge_today": 0.5,
                          "charge_total": 10.0, "discharge_total": 9.0, "last_ts": 1}}
    entry = _sensor_entry(energy)
    values = {
        key: BatteryEnergySensor(energy, entry, "B1", key).native_value
        for key in BATTERY_ENERGY_SENSORS
    }
    assert values == {
        "battery_charge_today": 1.235, "battery_discharge_today": 0.5,
        "battery_charge_total": 10.0, "battery_discharge_total": 9.0,
    }
    sensor = BatteryEnergySensor(energy, entry, "B1", "battery_charge_total")
    assert sensor.unique_id == "B1_battery_charge_total"
    assert sensor.state_class == "total_increasing"
    assert sensor.device_class == "energy"


def test_energy_sensor_unknown_until_first_sample_and_zero_on_new_day():
    energy = MagicMock()
    energy.data = {"B1": {"day": "2000-01-01", "charge_today": 4.0, "charge_total": 9.0,
                          "last_ts": None}}
    entry = _sensor_entry(energy)
    assert BatteryEnergySensor(energy, entry, "B1", "battery_charge_total").native_value is None
    energy.data["B1"]["last_ts"] = 1
    assert BatteryEnergySensor(energy, entry, "B1", "battery_charge_today").native_value == 0.0
    assert BatteryEnergySensor(energy, entry, "B1", "battery_charge_total").native_value == 9.0


@pytest.mark.parametrize("data,expected", [
    ({"stateBat": "0"}, "idle"), ({"stateBat": 1}, "charging"),
    ({"stateBat": "2"}, "discharging"), ({"stateBat": "9"}, None),
    # No stateBat: fall back to the current's direction.
    ({"iPack": "12.5"}, "charging"), ({"iPack": "-3"}, "discharging"),
    ({"iPack": "0.00"}, "idle"), ({"stateBat": "x"}, None), ({}, None),
])
def test_battery_state_sensor(data, expected):
    entry = _sensor_entry(None)
    battery = entry.runtime_data.battery
    battery.data = {"B1": data}
    sensor = BatteryStateSensor(battery, entry, "B1")
    assert sensor.native_value == expected
    assert sensor.options == ["idle", "charging", "discharging"]


async def test_setup_adds_energy_and_state_sensors():
    entry = _sensor_entry(MagicMock(data={}))
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    keys = {e._sensor_key for e in added if isinstance(e, BatteryEnergySensor)}
    assert keys == set(BATTERY_ENERGY_SENSORS)
    assert any(isinstance(e, BatteryStateSensor) for e in added)


async def test_setup_without_energy_coordinator_skips_energy_sensors():
    entry = _sensor_entry(None)
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    assert not any(isinstance(e, BatteryEnergySensor) for e in added)


def test_translations_present_in_both_languages():
    base = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"
    for name in ("en.json", "zh-Hans.json"):
        data = json.loads((base / name).read_text(encoding="utf-8"))
        sensors = data["entity"]["sensor"]
        for key in [*BATTERY_ENERGY_SENSORS, "battery_state"]:
            assert key in sensors, (name, key)
        assert set(sensors["battery_state"]["state"]) == {"idle", "charging", "discharging"}
        assert "energy_interval" in data["options"]["step"]["init"]["data"]


# --- api --------------------------------------------------------------------


async def test_api_minute_chart_payload_and_401():
    from custom_components.hanchuess.api import HanchuessApiClient
    from custom_components.hanchuess.crypto import _encrypt_payload

    client = HanchuessApiClient.__new__(HanchuessApiClient)
    client._request = AsyncMock(return_value={"code": 200, "data": []})
    await client.async_get_battery_minute_chart("D1", 1, 2, "en")
    path, payload = client._request.await_args.args[:2]
    assert path == "/gateway/platform/bmsInfo/powerMinuteChart"
    assert payload == _encrypt_payload({"sn": "D1", "devType": "1", "maxCount": 1440,
                                        "dataTimeTsStart": 1, "dataTimeTsEnd": 2})
    client._request = AsyncMock(return_value={"code": 401})
    assert await client.async_get_battery_minute_chart("D1", 1, 2) == {"_token_expired": True}
    client._request = AsyncMock(return_value=None)
    assert await client.async_get_battery_minute_chart("D1", 1, 2) == {}


async def test_save_now_writes_store(hass: HomeAssistant, hass_storage):
    entry = _entry(hass)
    coordinator = await _coord(hass, _chart_client({"B1": _today_series(3)}), entry)
    await coordinator.async_save_now()  # nothing loaded yet: no write
    assert energy_store_key(entry.entry_id) not in hass_storage
    await coordinator._async_update_data()
    await coordinator.async_save_now()
    saved = hass_storage[energy_store_key(entry.entry_id)]["data"]
    assert saved["B1"]["last_ts"] is not None


async def test_api_battery_data_marks_401():
    from custom_components.hanchuess.api import HanchuessApiClient

    client = HanchuessApiClient.__new__(HanchuessApiClient)
    client._request = AsyncMock(return_value={"code": 401, "msg": "expired"})
    assert await client.async_get_battery_data("D1") == {"_token_expired": True}



async def test_coordinator_falls_back_to_whole_days(hass: HomeAssistant):
    entry = _entry(hass)
    client = _chart_client({"B1": _today_series(31)}, whole_days_only=True)
    coordinator = await _coord(hass, client, entry)
    now = dt_util.start_of_local_day() + timedelta(hours=1)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=now):
        first = await coordinator._async_update_data()
        total = first["B1"]["charge_total"]
        await coordinator._async_update_data()  # mid-day start refused -> whole day
        await coordinator._async_update_data()  # goes straight to whole day
    assert coordinator._incremental is False
    assert coordinator.states["B1"].charge_total == pytest.approx(total)  # no double count
    assert coordinator.errors["B1"] is None
    assert len(client.calls) == 4  # 1 + (refused + retry) + 1
