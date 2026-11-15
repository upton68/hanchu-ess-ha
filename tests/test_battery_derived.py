"""Tests for Battery Power, Remaining Energy and Last Data Update (2.7.0)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components.sensor import SensorDeviceClass  # noqa: E402
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower  # noqa: E402

from custom_components.hanchuess import sensor as sensor_mod  # noqa: E402
from custom_components.hanchuess.battery import station_battery_values  # noqa: E402
from custom_components.hanchuess.sensor import (  # noqa: E402
    DERIVED_BATTERY_SENSORS,
    BatteryDerivedSensor,
    battery_power_w,
    last_data_update,
    remaining_energy_kwh,
)

BATTERY = {
    "vPack": "53.24", "iPack": "-12.50", "socPack": "88.1",
    "designCapacity": 9.40, "dataTimeTs": 1794571858310,
}


@pytest.mark.parametrize(
    "data,expected",
    [
        (BATTERY, -665.5),                        # discharging -> negative
        ({"vPack": "51.27", "iPack": "34.37"}, 1762.1),  # charging -> positive
        ({"vPack": "53.2", "iPack": "0.00"}, 0.0),
        ({"vPack": "53.2"}, None),
        ({"vPack": "bad", "iPack": "1"}, None),
        ({}, None),
    ],
)
def test_battery_power(data, expected):
    assert battery_power_w(data) == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        (BATTERY, 8.281),
        ({"socPack": "10.25", "designCapacity": "3.2"}, 0.328),
        ({"socPack": "50"}, None),
        ({}, None),
    ],
)
def test_remaining_energy(data, expected):
    assert remaining_energy_kwh(data) == expected


def test_last_data_update():
    assert last_data_update(BATTERY) == datetime.fromtimestamp(
        1794571858.310, tz=timezone.utc
    )
    # Station-list fallback uses latestDataTimeTs.
    assert last_data_update({"latestDataTimeTs": 1793292243391}) == datetime.fromtimestamp(
        1793292243.391, tz=timezone.utc
    )
    assert last_data_update({}) is None
    assert last_data_update({"dataTimeTs": 0}) is None


def test_station_values_carry_upload_time():
    detail = {"data": {"bmsList": [{"sn": "B1", "socPack": 9.3, "latestDataTimeTs": 1793292243391}]}}
    assert station_battery_values(detail)["B1"]["latestDataTimeTs"] == 1793292243391


def _sensor(key, data=BATTERY):
    coordinator = MagicMock()
    coordinator.data = {"B1": data}
    entry = SimpleNamespace(data={}, runtime_data=SimpleNamespace(inverter_device_id="d"))
    return BatteryDerivedSensor(coordinator, entry, "B1", key, DERIVED_BATTERY_SENSORS[key])


def test_battery_power_sensor():
    sensor = _sensor("battery_power")
    assert sensor.native_value == -665.5
    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.unique_id == "B1_battery_power"
    assert sensor.entity_registry_enabled_default is True


def test_remaining_energy_sensor():
    sensor = _sensor("battery_remaining_energy")
    assert sensor.native_value == 8.281
    assert sensor.device_class == SensorDeviceClass.ENERGY_STORAGE
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR


def test_last_data_update_sensor_is_diagnostic_and_disabled():
    sensor = _sensor("battery_last_data_update")
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.entity_registry_enabled_default is False
    assert sensor.native_value.year == 2026


def test_derived_sensor_handles_missing_battery():
    coordinator = MagicMock()
    coordinator.data = {}
    entry = SimpleNamespace(data={}, runtime_data=SimpleNamespace(inverter_device_id="d"))
    sensor = BatteryDerivedSensor(
        coordinator, entry, "B1", "battery_power", DERIVED_BATTERY_SENSORS["battery_power"]
    )
    assert sensor.native_value is None


async def test_setup_adds_derived_sensors_for_each_battery():
    battery = MagicMock()
    battery.data = {"B1": BATTERY, "B2": {}}
    entry = SimpleNamespace(
        data={"mode": "battery_only", "battery_serials": ["B1", "B2"]},
        runtime_data=SimpleNamespace(
            realtime=None, statistics=None, battery=battery, inverter_device_id="dev1"
        ),
    )
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    derived = {(e._battery_serial, e._sensor_key) for e in added if isinstance(e, BatteryDerivedSensor)}
    assert derived == {(sn, key) for sn in ("B1", "B2") for key in DERIVED_BATTERY_SENSORS}


def test_translations():
    base = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"
    en = json.loads((base / "en.json").read_text(encoding="utf-8"))["entity"]["sensor"]
    zh = json.loads((base / "zh-Hans.json").read_text(encoding="utf-8"))["entity"]["sensor"]
    for key in DERIVED_BATTERY_SENSORS:
        assert key in en and key in zh
    assert en["battery_full_capacity"]["name"] == "Full Charge Capacity"
