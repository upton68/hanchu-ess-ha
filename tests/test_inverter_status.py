"""Tests for the Inverter Status sensor: status logic, schedule coordinator, sensor."""
from __future__ import annotations

from datetime import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.hanchuess.status import (
    CHARGING,
    DISCHARGING,
    FAST_CHARGING,
    FAST_DISCHARGING,
    IDLE,
    SCHEDULED_CHARGE,
    SCHEDULED_DISCHARGE,
    STATUS_OPTIONS,
    compute_inverter_status,
    slot_active,
)

H = 3600


def _s(hh, mm=0):
    return hh * H + mm * 60


# --- slot_active ----------------------------------------------------------------


@pytest.mark.parametrize(
    "start,end,now,expected",
    [
        (_s(2), _s(5), _s(3), True),
        (_s(2), _s(5), _s(5), False),  # end is exclusive
        (_s(2), _s(5), _s(1, 59), False),
        (_s(23, 30), _s(5, 30), _s(0, 10), True),  # crosses midnight
        (_s(23, 30), _s(5, 30), _s(23, 45), True),
        (_s(23, 30), _s(5, 30), _s(12), False),
        (0, _s(5, 30), _s(1), True),  # starts at midnight: active, not "off"
        (_s(23, 30), 0, _s(23, 45), True),  # ends at midnight: active
        (_s(23, 30), 0, _s(1), False),
        (0, 0, _s(1), False),  # both 00:00 = switched off
        (_s(3), _s(3), _s(3), False),
        ("7200", "18000.0", _s(3), True),  # iotGet returns strings
        (None, _s(5), _s(3), False),
        ("bad", _s(5), _s(3), False),
    ],
)
def test_slot_active(start, end, now, expected):
    assert slot_active(start, end, now) is expected


# --- compute_inverter_status ----------------------------------------------------

USER_DEFINED = {"WORK_MODE_CMB": "3", "DTU_AC_CHG_SOC_LMT": "100", "DSCHG_BAT_SOC_LMT": "10"}


def _rt(**kw):
    data = {"batSoc": 0.5, "deviceStatusOfTestFastChg": 0}
    data.update(kw)
    return data


def test_no_realtime_data_returns_none():
    assert compute_inverter_status(None, USER_DEFINED, time(3), 500) is None
    assert compute_inverter_status({}, USER_DEFINED, time(3), 500) is None


@pytest.mark.parametrize("fast,expected", [(1, FAST_CHARGING), (2, FAST_DISCHARGING), ("1", FAST_CHARGING)])
def test_fast_charge_wins_over_everything(fast, expected):
    schedule = {**USER_DEFINED, "TCT_START_1": _s(2), "TCT_END_1": _s(5)}
    status = compute_inverter_status(
        _rt(deviceStatusOfTestFastChg=fast), schedule, time(3), -3000
    )
    assert status == expected


def test_scheduled_charge_inside_charge_slot():
    schedule = {**USER_DEFINED, "TCT_START_2": _s(23, 30), "TCT_END_2": _s(5, 30)}
    assert compute_inverter_status(_rt(), schedule, time(0, 30), 3000) == SCHEDULED_CHARGE


def test_scheduled_charge_ends_at_grid_charge_maximum():
    schedule = {**USER_DEFINED, "DTU_AC_CHG_SOC_LMT": "80", "TCT_START_1": _s(2), "TCT_END_1": _s(5)}
    # SOC 80% has reached the limit: no longer scheduled; battery idle.
    assert compute_inverter_status(_rt(batSoc=0.8), schedule, time(3), 0) == IDLE
    assert compute_inverter_status(_rt(batSoc=0.79), schedule, time(3), 0) == SCHEDULED_CHARGE


def test_scheduled_discharge_and_minimum_soc():
    schedule = {**USER_DEFINED, "TDT_START_1": _s(16), "TDT_END_1": _s(19)}
    assert compute_inverter_status(_rt(batSoc=0.5), schedule, time(17), -2500) == SCHEDULED_DISCHARGE
    # At the minimum discharge SOC the schedule can't discharge any further.
    assert compute_inverter_status(_rt(batSoc=0.1), schedule, time(17), 0) == IDLE


def test_charge_slot_checked_before_discharge_slot():
    schedule = {
        **USER_DEFINED,
        "TCT_START_1": _s(2), "TCT_END_1": _s(5),
        "TDT_START_1": _s(2), "TDT_END_1": _s(5),
    }
    assert compute_inverter_status(_rt(), schedule, time(3), 0) == SCHEDULED_CHARGE


def test_not_user_defined_ignores_slots():
    schedule = {**USER_DEFINED, "WORK_MODE_CMB": "1", "TCT_START_1": _s(2), "TCT_END_1": _s(5)}
    assert compute_inverter_status(_rt(), schedule, time(3), 1200) == CHARGING


def test_falls_back_to_realtime_work_mode_when_schedule_missing():
    # No schedule data at all: nothing can be "scheduled".
    assert compute_inverter_status(_rt(workModeCmb=3), None, time(3), -800) == DISCHARGING


def test_missing_soc_limits_still_report_scheduled():
    schedule = {"WORK_MODE_CMB": "3", "TCT_START_1": _s(2), "TCT_END_1": _s(5)}
    assert compute_inverter_status(_rt(), schedule, time(3), 0) == SCHEDULED_CHARGE


@pytest.mark.parametrize(
    "power,expected",
    [(1500, CHARGING), (-1500, DISCHARGING), (15, IDLE), (-15, IDLE), (0, IDLE), (None, IDLE)],
)
def test_battery_power_with_deadband(power, expected):
    assert compute_inverter_status(_rt(), {"WORK_MODE_CMB": "1"}, time(12), power) == expected


def test_status_options_are_the_translation_keys():
    import json
    from pathlib import Path

    base = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"
    for name in ("en.json", "zh-Hans.json"):
        states = json.loads((base / name).read_text(encoding="utf-8"))["entity"]["sensor"][
            "inverter_status"
        ]["state"]
        assert sorted(states) == sorted(STATUS_OPTIONS)


# --- Schedule coordinator -------------------------------------------------------

pytest.importorskip("homeassistant")

from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.hanchuess.const import DOMAIN  # noqa: E402
from custom_components.hanchuess.coordinator import HanchuessScheduleCoordinator  # noqa: E402
from homeassistant.helpers.update_coordinator import UpdateFailed  # noqa: E402


def _coordinator(hass, options=None, values=None):
    entry = MockConfigEntry(domain=DOMAIN, data={"sn": "SN1"}, options=options or {})
    entry.add_to_hass(hass)
    client = MagicMock()
    client.async_iot_get = AsyncMock(return_value=values or {})
    return HanchuessScheduleCoordinator(hass, entry, client), client


async def test_schedule_interval_default_and_minimum(hass):
    coordinator, _ = _coordinator(hass)
    assert coordinator.update_interval.total_seconds() == 300
    coordinator, _ = _coordinator(hass, options={"schedule_interval": 120})
    assert coordinator.update_interval.total_seconds() == 120
    coordinator, _ = _coordinator(hass, options={"schedule_interval": 10})
    assert coordinator.update_interval.total_seconds() == 60


async def test_schedule_poll_reads_inverter_values(hass):
    coordinator, client = _coordinator(hass, values={"WORK_MODE_CMB": "3", "TCT_START_1": "7200"})
    data = await coordinator._async_update_data()
    assert data == {"WORK_MODE_CMB": "3", "TCT_START_1": "7200"}
    assert coordinator.last_read is not None
    keys = client.async_iot_get.call_args.args[2]
    assert "TCT_START_1" in keys and "DSCHG_BAT_SOC_LMT" in keys


async def test_schedule_poll_failure_keeps_last_values(hass):
    coordinator, client = _coordinator(hass)
    coordinator.data = {"WORK_MODE_CMB": "3"}
    assert await coordinator._async_update_data() == {"WORK_MODE_CMB": "3"}


async def test_schedule_poll_failure_without_data_raises(hass):
    coordinator, _ = _coordinator(hass)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_seed_and_note_written(hass):
    coordinator, _ = _coordinator(hass)
    coordinator.seed({"WORK_MODE_CMB": "3", "CHG_PWR_LMT": "4000", "TCT_START_1": "0"})
    assert coordinator.data == {"WORK_MODE_CMB": "3", "TCT_START_1": "0"}
    assert coordinator.last_read is not None

    read_at = coordinator.last_read
    coordinator.note_written({"TCT_START_1": "7200", "CHG_PWR_LMT": "3000"})
    assert coordinator.data == {"WORK_MODE_CMB": "3", "TCT_START_1": "7200"}
    assert coordinator.last_read == read_at  # a write isn't a read


# --- Sensor -----------------------------------------------------------------------

from custom_components.hanchuess.sensor import InverterStatusSensor  # noqa: E402


def test_sensor_combines_realtime_and_schedule(monkeypatch):
    schedule = SimpleNamespace(
        data={**USER_DEFINED, "TCT_START_1": _s(2), "TCT_END_1": _s(5)}, last_read=None
    )
    entry = SimpleNamespace(data={"sn": "SN1"}, runtime_data=SimpleNamespace(schedule=schedule))
    realtime = MagicMock()
    realtime.data = _rt(batP=3.2, batPUnit="kW")
    sensor = InverterStatusSensor(realtime, entry)

    from datetime import datetime

    monkeypatch.setattr(
        "custom_components.hanchuess.sensor.dt_util.now", lambda: datetime(2026, 11, 10, 3, 0)
    )
    assert sensor.native_value == SCHEDULED_CHARGE
    assert sensor.unique_id == "SN1_inverter_status"
    assert sensor.options == STATUS_OPTIONS

    monkeypatch.setattr(
        "custom_components.hanchuess.sensor.dt_util.now", lambda: datetime(2026, 11, 10, 12, 0)
    )
    assert sensor.native_value == CHARGING  # 3.2 kW scaled to watts, outside the slot
