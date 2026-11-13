"""Tests for battery cell voltage sensors (max/min/difference and per-cell)."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("homeassistant")

from homeassistant.const import UnitOfElectricPotential  # noqa: E402

from custom_components.hanchuess import sensor as sensor_mod  # noqa: E402
from custom_components.hanchuess.sensor import (  # noqa: E402
    CELL_STAT_SENSORS,
    BatteryCellStatSensor,
    BatteryCellVoltageSensor,
    _battery_cell_count,
    _has_cell_data,
    cell_voltage_stat,
)

# A Home-ESS-LV-9.4K (devModel 3) as returned by queryBatteryDataDivisions (#61).
CELLS = {
    f"vBat{i}": v
    for i, v in enumerate(
        ["3.290", "3.311", "3.308", "3.309", "3.309", "3.308", "3.303", "3.308",
         "3.303", "3.305", "3.311", "3.309", "3.294", "3.310", "3.308", "3.315"],
        start=1,
    )
}
BATTERY = {
    "sn": "B1",
    "devModel": "3",
    "numBat": 16,
    "numBatT": 4,
    "maxVoltage": "3.315",
    "minVoltage": "3.290",
    "maxVoltageDifference": "0.025",
    "vPack": "52.9",
    **CELLS,
}


def _coordinator(data):
    coordinator = MagicMock()
    coordinator.data = {"B1": data}
    return coordinator


ENTRY = SimpleNamespace(data={"sn": "SN1"})


# --- helpers ------------------------------------------------------------------


def test_cell_stats_use_reported_fields():
    assert cell_voltage_stat(BATTERY, "max") == 3.315
    assert cell_voltage_stat(BATTERY, "min") == 3.290
    assert cell_voltage_stat(BATTERY, "diff") == 0.025


def test_cell_stats_fall_back_to_cell_voltages():
    data = {"numBat": 16, **CELLS}
    assert cell_voltage_stat(data, "max") == 3.315
    assert cell_voltage_stat(data, "min") == 3.290
    assert cell_voltage_stat(data, "diff") == 0.025


def test_cell_difference_falls_back_to_max_minus_min():
    data = {"maxVoltage": "3.328", "minVoltage": "3.327"}
    assert cell_voltage_stat(data, "diff") == 0.001


def test_cell_stats_without_data_are_none():
    for stat in ("max", "min", "diff"):
        assert cell_voltage_stat({}, stat) is None


@pytest.mark.parametrize(
    "data,expected",
    [
        (BATTERY, 16),
        ({"vBat1": "3.3", "vBat2": "3.3", "vBat3": "3.3"}, 3),  # no numBat
        ({"numBat": "8", "vBat1": "3.3"}, 8),
        ({"numBat": "bad"}, 0),
        ({}, 0),
    ],
)
def test_battery_cell_count(data, expected):
    assert _battery_cell_count(data) == expected


def test_has_cell_data():
    assert _has_cell_data(BATTERY)
    assert _has_cell_data({"maxVoltage": "3.3"})
    assert not _has_cell_data({"vPack": "52.9", "socPack": "88"})
    assert not _has_cell_data({})


# --- entities -------------------------------------------------------------------


def test_cell_voltage_sensor():
    sensor = BatteryCellVoltageSensor(_coordinator(BATTERY), ENTRY, "B1", 13)
    assert sensor.native_value == 3.294
    assert sensor.unique_id == "B1_battery_cell_voltage_13"
    assert sensor.translation_key == "battery_cell_voltage"
    assert sensor.translation_placeholders == {"cell": "13"}
    assert sensor.entity_registry_enabled_default is False
    assert sensor.native_unit_of_measurement == UnitOfElectricPotential.VOLT


@pytest.mark.parametrize(
    "key,expected", [
        ("battery_cell_voltage_max", 3.315),
        ("battery_cell_voltage_min", 3.290),
        ("battery_cell_voltage_difference", 0.025),
    ],
)
def test_cell_stat_sensors(key, expected):
    sensor = BatteryCellStatSensor(
        _coordinator(BATTERY), ENTRY, "B1", key, CELL_STAT_SENSORS[key]
    )
    assert sensor.native_value == expected
    assert sensor.entity_registry_enabled_default is True
    assert sensor.native_unit_of_measurement == UnitOfElectricPotential.VOLT


def test_cell_difference_is_shown_in_millivolts():
    key = "battery_cell_voltage_difference"
    sensor = BatteryCellStatSensor(_coordinator(BATTERY), ENTRY, "B1", key, CELL_STAT_SENSORS[key])
    assert sensor.suggested_unit_of_measurement == UnitOfElectricPotential.MILLIVOLT


# --- setup ----------------------------------------------------------------------


async def _setup_entities(battery_data):
    realtime = MagicMock()
    realtime.data = {}
    statistics = MagicMock()
    statistics.data = {}
    battery = MagicMock()
    battery.data = {"B1": battery_data}
    entry = SimpleNamespace(
        data={"sn": "SN1", "battery_serials": ["B1"]},
        runtime_data=SimpleNamespace(
            realtime=realtime, statistics=statistics, battery=battery,
            staging=MagicMock(), inverter_model=None, schedule=None,
        ),
    )
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    return [e for e in added if getattr(e, "_battery_serial", None) == "B1"]


async def test_setup_adds_cell_sensors_when_data_has_cells():
    entities = await _setup_entities(BATTERY)
    keys = {getattr(e, "_sensor_key", None) for e in entities}
    assert set(CELL_STAT_SENSORS) <= keys
    cells = [e for e in entities if isinstance(e, BatteryCellVoltageSensor)]
    assert len(cells) == 16


async def test_setup_skips_cell_sensors_without_cell_data():
    entities = await _setup_entities({"vPack": "52.9", "socPack": "88"})
    assert not any(
        isinstance(e, (BatteryCellStatSensor, BatteryCellVoltageSensor)) for e in entities
    )


# --- translations ---------------------------------------------------------------


def test_translations_cover_cell_sensors():
    base = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"
    for name in ("en.json", "zh-Hans.json"):
        sensors = json.loads((base / name).read_text(encoding="utf-8"))["entity"]["sensor"]
        for key in (*CELL_STAT_SENSORS, "battery_cell_voltage"):
            assert key in sensors, (name, key)
        assert "{cell}" in sensors["battery_cell_voltage"]["name"]
