"""Tests for per-string PV sensors from getDeviceStatus pvListVo."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components.sensor import SensorDeviceClass  # noqa: E402
from homeassistant.const import (  # noqa: E402
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)

from custom_components.hanchuess import sensor as sensor_mod  # noqa: E402
from custom_components.hanchuess.sensor import (  # noqa: E402
    _POWER_SCALE,
    _VOLTAGE_SCALE,
    PV_STRING_SENSORS,
    PvStringSensor,
    parse_quantity,
    pv_strings,
)

TRANSLATIONS = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"

# As returned on an AC-coupled HESS-HY-S-5.0K at night (#issue discussion).
NIGHT = {"pvListVo": [
    {"name": "PV1", "power": "0.00kW", "voltage": "0.20V"},
    {"name": "PV2", "power": "0.00kW", "voltage": "0.30V"},
]}
DAY = {"pvListVo": [
    {"name": "PV1", "power": "2.45kW", "voltage": "385.6V"},
    {"name": "PV2", "power": "850W", "voltage": "212.4V"},
    {"name": "PV3", "power": "0.00kW", "voltage": "3.1V"},
]}


@pytest.mark.parametrize(
    "value,scales,expected",
    [
        ("2.45kW", _POWER_SCALE, 2450.0),
        ("850W", _POWER_SCALE, 850.0),
        ("0.00kW", _POWER_SCALE, 0.0),
        (" 1.2 kW ", _POWER_SCALE, 1200.0),
        ("1500", _POWER_SCALE, 1500.0),
        (1500, _POWER_SCALE, 1500.0),
        ("385.6V", _VOLTAGE_SCALE, 385.6),
        ("500mV", _VOLTAGE_SCALE, 0.5),
        ("12kWh", _POWER_SCALE, None),   # unknown unit
        ("--", _POWER_SCALE, None),
        (None, _POWER_SCALE, None),
    ],
)
def test_parse_quantity(value, scales, expected):
    assert parse_quantity(value, scales) == expected


def test_pv_strings_daytime():
    strings = pv_strings(DAY)
    assert list(strings) == ["PV1", "PV2", "PV3"]
    assert strings["PV1"] == {"power": 2450.0, "voltage": 385.6, "current": 6.35}
    assert strings["PV2"] == {"power": 850.0, "voltage": 212.4, "current": 4.0}
    # Below 10 V the current isn't meaningful.
    assert strings["PV3"]["current"] is None


def test_pv_strings_night_and_missing():
    assert pv_strings(NIGHT)["PV1"] == {"power": 0.0, "voltage": 0.2, "current": None}
    assert pv_strings({}) == {}
    assert pv_strings(None) == {}
    assert pv_strings({"pvListVo": [{"power": "1kW"}]}) == {}  # no name


def _sensor(data, name, measure, enabled=True):
    coordinator = MagicMock()
    coordinator.data = data
    entry = SimpleNamespace(data={"sn": "SN1"})
    return PvStringSensor(coordinator, entry, name, measure, enabled)


def test_pv_string_sensors():
    power = _sensor(DAY, "PV2", "power")
    assert power.native_value == 850.0
    assert power.unique_id == "SN1_pv2_power"
    assert power.device_class == SensorDeviceClass.POWER
    assert power.native_unit_of_measurement == UnitOfPower.WATT
    assert power.translation_key == "pv_string_power"
    assert power.translation_placeholders == {"string": "PV2"}

    voltage = _sensor(DAY, "PV1", "voltage")
    assert voltage.native_value == 385.6
    assert voltage.native_unit_of_measurement == UnitOfElectricPotential.VOLT

    current = _sensor(DAY, "PV1", "current")
    assert current.native_value == 6.35
    assert current.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    assert _sensor(DAY, "PV4", "power").native_value is None  # string gone
    assert _sensor(DAY, "PV1", "power", enabled=False).entity_registry_enabled_default is False


async def _setup(realtime_data, with_realtime=False):
    realtime = MagicMock()
    realtime.data = realtime_data
    statistics = MagicMock()
    statistics.data = {}
    entry = SimpleNamespace(
        data={"sn": "SN1", "battery_serials": []},
        runtime_data=SimpleNamespace(
            realtime=realtime, statistics=statistics, battery=None,
            staging=MagicMock(), inverter_model=None, schedule=None,
        ),
    )
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    sensors = [e for e in added if isinstance(e, PvStringSensor)]
    return (sensors, realtime, added) if with_realtime else sensors


async def test_setup_creates_sensors_per_reported_string():
    sensors = await _setup({**DAY, "bypMeterSwitch": 0})
    assert {(s._string_name, s._measure) for s in sensors} == {
        (n, m) for n in ("PV1", "PV2", "PV3") for m in PV_STRING_SENSORS
    }
    assert all(s.entity_registry_enabled_default for s in sensors)


async def test_setup_disables_string_sensors_on_ac_coupled_systems():
    sensors = await _setup({**NIGHT, "bypMeterSwitch": 1})
    assert len(sensors) == 6
    assert not any(s.entity_registry_enabled_default for s in sensors)


async def test_setup_without_pv_list_creates_none():
    assert await _setup({"bypMeterSwitch": 0}) == []


def _no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    duplicates = sorted({k for k in keys if keys.count(k) > 1})
    assert not duplicates, f"duplicate keys: {duplicates}"
    return dict(pairs)


@pytest.mark.parametrize("name", ["en.json", "zh-Hans.json"])
def test_translations_have_no_duplicate_keys_and_cover_pv(name):
    data = json.loads((TRANSLATIONS / name).read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    sensors = data["entity"]["sensor"]
    for measure in PV_STRING_SENSORS:
        assert "{string}" in sensors[f"pv_string_{measure}"]["name"]



async def test_strings_missing_at_startup_are_added_when_they_appear():
    # Overnight the cloud left pvListVo out; HA restarted then.
    sensors, realtime, added = await _setup({"bypMeterSwitch": 0}, with_realtime=True)
    assert sensors == []
    listener = realtime.async_add_listener.call_args.args[0]

    listener()  # still no list: nothing added
    assert not any(isinstance(e, PvStringSensor) for e in added)

    realtime.data = {**DAY, "bypMeterSwitch": 0}
    listener()  # morning: the list is back
    names = {(e._string_name, e._measure) for e in added if isinstance(e, PvStringSensor)}
    assert names == {(n, m) for n in ("PV1", "PV2", "PV3") for m in PV_STRING_SENSORS}
    assert all(e.entity_registry_enabled_default for e in added if isinstance(e, PvStringSensor))

    count = len(added)
    listener()  # same strings again: not added twice
    assert len(added) == count


async def test_strings_present_at_startup_are_not_added_again():
    sensors, realtime, added = await _setup({**DAY, "bypMeterSwitch": 0}, with_realtime=True)
    count = len(added)
    realtime.async_add_listener.call_args.args[0]()
    assert len(added) == count
