"""Unit tests for pure entity logic (no live API, no hass instance required).

Importing the platform modules requires the `homeassistant` package, so the whole
module skips if it is unavailable.
"""
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("homeassistant")

from custom_components.hanchuess import time as time_mod
from custom_components.hanchuess.sensor import (
    SENSORS,
    HanchueSensor,
    _parse_energy_menu,
)
from custom_components.hanchuess.time import TIME_SLOTS, HanchuessTimeSlot


class _FakeEntry:
    def __init__(self, sn="SN1"):
        self.data = {"sn": sn}


def _make_sensor(config, value, unit=None):
    """Build a HanchueSensor backed by a fake coordinator carrying one value.

    When ``unit`` is given it is stored under the config's ``unit_key`` so the
    sibling-unit scaling path can be exercised.
    """
    coordinator = MagicMock()
    data = {config["key"]: value}
    if unit is not None and config.get("unit_key"):
        data[config["unit_key"]] = unit
    coordinator.data = data
    return HanchueSensor(coordinator, _FakeEntry(), "test_sensor", config)


# ---------------------------------------------------------------------------
# auto_watt scaling (see plans/P0-06-auto-watt-scaling.md)
#
# Scaling now trusts the API's per-field `<field>Unit` sibling. The magnitude
# heuristic below is only the fallback for readings that arrive without a unit.
# ---------------------------------------------------------------------------

# --- unit-driven path: scale on the explicit `<field>Unit` field --------------

def test_auto_watt_unit_kw_scaled_to_watts():
    s = _make_sensor(SENSORS["battery_power"], 2.01, unit="kW")
    assert s.native_value == 2010.0


def test_auto_watt_unit_w_left_as_watts():
    s = _make_sensor(SENSORS["battery_power"], 623, unit="W")
    assert s.native_value == 623.0


def test_auto_watt_unit_w_small_value_not_misscaled():
    # P0-06 hazard resolved: with an explicit "W" unit, a genuine 8 W reading
    # stays 8 W instead of being scaled to 8000 W.
    s = _make_sensor(SENSORS["battery_power"], 8, unit="W")
    assert s.native_value == 8.0


def test_auto_watt_unit_kw_fractional_value():
    s = _make_sensor(SENSORS["pv_power"], 0.5, unit="kW")
    assert s.native_value == 500.0


def test_auto_watt_unit_lowercase_kw_scaled():
    s = _make_sensor(SENSORS["grid_power"], 2.0, unit="kw")
    assert s.native_value == 2000.0


# --- fallback path: no unit field, legacy magnitude heuristic -----------------

def test_auto_watt_small_value_scaled_to_watts():
    s = _make_sensor({"key": "batP", "auto_watt": True}, 5)
    assert s.native_value == 5000.0


def test_auto_watt_large_value_unchanged():
    s = _make_sensor({"key": "batP", "auto_watt": True}, 1500)
    assert s.native_value == 1500.0


def test_auto_watt_boundary_ten_treated_as_watts():
    # abs(10) < 10 is False, so 10 is treated as already-watts.
    s = _make_sensor({"key": "batP", "auto_watt": True}, 10)
    assert s.native_value == 10.0


def test_auto_watt_negative_small_value_scaled():
    s = _make_sensor({"key": "batP", "auto_watt": True}, -5)
    assert s.native_value == -5000.0


def test_auto_watt_small_value_misscaled_only_without_unit():
    # The misscale is now confined to the fallback path: a small reading that
    # arrives WITHOUT a unit field is still assumed to be kW (8 -> 8000 W).
    # Compare test_auto_watt_unit_w_small_value_not_misscaled.
    s = _make_sensor({"key": "batP", "auto_watt": True}, 8)
    assert s.native_value == 8000.0


def test_load_power_is_raw_watts():
    # load_power reads loadPwr, which has no `<field>Unit` sibling and is always
    # reported in watts, so it is surfaced raw (no auto_watt, no misscale).
    s = _make_sensor(SENSORS["load_power"], 8)
    assert s.native_value == 8


def test_auto_watt_non_numeric_returns_none():
    s = _make_sensor({"key": "batP", "auto_watt": True}, "not-a-number")
    assert s.native_value is None


def test_auto_watt_missing_value_returns_none():
    coordinator = MagicMock()
    coordinator.data = {}
    s = HanchueSensor(coordinator, _FakeEntry(), "x", {"key": "batP", "auto_watt": True})
    assert s.native_value is None


def test_scale_factor_applied():
    s = _make_sensor({"key": "batSoc", "scale": 100}, 0.55)
    assert s.native_value == 55.0


# ---------------------------------------------------------------------------
# _parse_energy_menu (see plans/P0-07-parse-energy-menu-indexerror.md)
# ---------------------------------------------------------------------------

def test_parse_energy_menu_empty_returns_defaults():
    assert _parse_energy_menu({}) == {"work_mode_options": [], "fields": []}
    assert _parse_energy_menu({"data": {}}) == {"work_mode_options": [], "fields": []}


def test_parse_energy_menu_extracts_work_mode_options():
    menu = {
        "data": {
            "energy": {
                "items": [
                    [
                        {
                            "itemCode": "WORK_MODE_CMB",
                            "itemType": "3",
                            "itemCodeSignal": "WORK_MODE_CMB",
                            "optVal": '[{"name": "Self Use", "value": "1"},'
                                      ' {"name": "Backup", "value": "2"}]',
                        }
                    ]
                ]
            }
        }
    }
    result = _parse_energy_menu(menu)
    assert result["work_mode_options"] == [
        {"label": "Self Use", "value": "1", "signal": "WORK_MODE_CMB"},
        {"label": "Backup", "value": "2", "signal": "WORK_MODE_CMB"},
    ]


def test_parse_energy_menu_numeric_field_with_step():
    menu = {
        "data": {
            "energy": {
                "items": [
                    [
                        {
                            "itemCode": "CHG_PWR_LMT",
                            "itemType": "1",
                            "itemName": "Charge Power Limit",
                            "minVal": "0",
                            "maxVal": "5000",
                            "defFmt": "0.0",
                        }
                    ]
                ]
            }
        }
    }
    fields = _parse_energy_menu(menu)["fields"]
    assert len(fields) == 1
    field = fields[0]
    assert field["code"] == "CHG_PWR_LMT"
    assert field["min"] == "0"
    assert field["max"] == "5000"
    assert field["step"] == 0.1


def test_parse_energy_menu_bad_work_mode_json_is_tolerated():
    menu = {
        "data": {
            "energy": {
                "items": [
                    [
                        {
                            "itemCode": "WORK_MODE_CMB",
                            "itemType": "3",
                            "itemCodeSignal": "WORK_MODE_CMB",
                            "optVal": "{not-valid-json",
                        }
                    ]
                ]
            }
        }
    }
    # Should not raise; work_mode_options stays empty.
    assert _parse_energy_menu(menu)["work_mode_options"] == []


# ---------------------------------------------------------------------------
# Time-slot seconds-since-midnight encode/decode
# ---------------------------------------------------------------------------

def _make_slot(startup_values, client=None):
    config = TIME_SLOTS["charge_slot_1_start"]  # control_key TCT_START_1
    return HanchuessTimeSlot(
        client or MagicMock(), _FakeEntry(), "charge_slot_1_start", config, startup_values
    )


def test_time_slot_decodes_seconds_to_time():
    slot = _make_slot({"TCT_START_1": 3661})  # 01:01:01 -> 01:01
    assert slot.native_value == dt_time(1, 1)


def test_time_slot_decodes_string_seconds():
    slot = _make_slot({"TCT_START_1": "9000"})  # 02:30
    assert slot.native_value == dt_time(2, 30)


def test_time_slot_invalid_value_falls_back_to_midnight():
    slot = _make_slot({"TCT_START_1": "garbage"})
    assert slot.native_value == dt_time(0, 0)


def test_time_slot_missing_value_defaults_to_midnight():
    slot = _make_slot({})
    assert slot.native_value == dt_time(0, 0)


async def test_time_slot_encodes_time_to_seconds_on_send(monkeypatch):
    monkeypatch.setattr(time_mod, "DEBOUNCE_SECONDS", 0)
    client = MagicMock()
    client.async_device_control = AsyncMock(return_value={"success": True})
    slot = _make_slot({}, client=client)
    slot._pending_value = dt_time(2, 30)  # 9000 seconds

    await slot._send_after_delay()

    client.async_device_control.assert_awaited_once_with(
        "SN1", "2", {"TCT_START_1": 9000}
    )
