"""Battery-only stations: Hanchu batteries with a third-party inverter (#61)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hanchuess.battery import (
    battery_only_serials,
    has_hanchu_inverter,
    is_hanchu_inverter,
    station_summary,
)

# Shapes taken from the stationInfo captures in #43 and #61.
HANCHU_PCS = {"pcsBrand": "HanChuESS", "pcsBrandCode": "1", "devType": 1, "devStatus": "1"}
LUX_PLACEHOLDER = {"pcsBrand": "", "pcsBrandCode": "11", "devType": 3, "devStatus": "99",
                   "onlineStatus": "99"}


def _bms(sn, adr="1", soc=88.1):
    return {"sn": sn, "dtuSn": "L10ABCDEFGH", "adr": adr, "devModel": "3",
            "onlineStatus": "1", "socPack": soc}


SIX_BATTERIES = [_bms(f"B002AAAA000{i}", adr=str((i % 3) + 1)) for i in range(6)]


def _station(pcs, bms):
    return {"code": 200, "success": True, "data": {
        "ownerName": "someone@example.com", "stationId": "ST25SECRET",
        "coordinates": "1.0,52.0", "pcsList": pcs, "bmsList": bms}}


def test_hanchu_inverter_detected_by_brand_or_code():
    assert is_hanchu_inverter(HANCHU_PCS)
    assert is_hanchu_inverter({"pcsBrand": "hanchuess"})
    assert is_hanchu_inverter({"pcsBrandCode": "1"})
    assert not is_hanchu_inverter(LUX_PLACEHOLDER)
    assert not is_hanchu_inverter({})


def test_placeholder_inverters_count_as_battery_only():
    detail = _station([LUX_PLACEHOLDER, LUX_PLACEHOLDER], SIX_BATTERIES)
    assert not has_hanchu_inverter(detail)
    assert battery_only_serials(detail) == [b["sn"] for b in SIX_BATTERIES]


def test_empty_pcs_list_is_battery_only():
    detail = _station([], SIX_BATTERIES[:4])
    assert len(battery_only_serials(detail)) == 4


def test_station_with_hanchu_inverter_is_not_battery_only():
    detail = _station([HANCHU_PCS], SIX_BATTERIES[:2])
    assert has_hanchu_inverter(detail)
    assert battery_only_serials(detail) == []


def test_no_batteries_or_no_detail():
    assert battery_only_serials(_station([LUX_PLACEHOLDER], [])) == []
    assert battery_only_serials({}) == []
    assert battery_only_serials(None) == []


def test_station_summary_is_redacted():
    summary = station_summary(_station([LUX_PLACEHOLDER], SIX_BATTERIES[:1]))
    text = repr(summary)
    for secret in ("someone@example.com", "ST25SECRET", "52.0", "B002AAAA0000", "L10ABCDEFGH"):
        assert secret not in text
    assert summary["inverters"] == [{
        "hanchu": False, "brand": "", "brand_code": "11", "dev_type": 3,
        "status": "99", "online": "99"}]
    assert summary["batteries"][0]["sn"] == "B002A…"
    assert summary["batteries"][0]["logger"] == "L10AB…"
    assert summary["batteries"][0]["dev_model"] == "3"


# --- Setup -----------------------------------------------------------------------

pytest.importorskip("homeassistant")

from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.exceptions import ConfigEntryNotReady  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

import custom_components.hanchuess as hanchuess  # noqa: E402
from custom_components.hanchuess.const import DOMAIN  # noqa: E402


def _battery_entry(serials=None):
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="station_ST1",
        data={
            "mode": "battery_only",
            "token": "tok",
            "stationId": "ST1",
            "stationName": "Home",
            "battery_serials": serials if serials is not None else ["B1"],
        },
    )


def _client(detail):
    client = MagicMock()
    client.token = "tok"
    client.async_get_station_detail = AsyncMock(return_value=detail)
    client.async_get_battery_data = AsyncMock(
        return_value={"success": True, "data": {"sn": "B1", "socPack": "88", "vPack": "53.2"}}
    )
    return client


async def test_setup_battery_only_entry(hass: HomeAssistant):
    entry = _battery_entry()
    entry.add_to_hass(hass)
    detail = _station([LUX_PLACEHOLDER], [_bms("B1"), _bms("B2", adr="2")])
    client = _client(detail)
    hass.data.setdefault(DOMAIN, {})["_client"] = client
    hass.data[DOMAIN]["_card_registered"] = True

    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()) as forward:
        assert await hanchuess.async_setup_entry(hass, entry) is True

    forward.assert_awaited_once()
    assert forward.await_args.args[1] == ["sensor"]
    data = entry.runtime_data
    assert data.battery_only is True
    assert data.realtime is None and data.statistics is None and data.schedule is None
    assert data.battery is not None
    # Newly listed battery added to the entry.
    assert entry.data["battery_serials"] == ["B1", "B2"]
    # Station device is the batteries' parent.
    from homeassistant.helpers import device_registry as dr
    device = dr.async_get(hass).async_get(data.inverter_device_id)
    assert device.name == "Hanchu Station Home"
    assert (DOMAIN, "station_ST1") in device.identifiers
    assert data.station_summary["batteries"][0]["sn"] == "B1"
    # Only the battery side was called: no inverter endpoints.
    assert not client.async_get_device_status.called
    assert not client.async_iot_get.called


async def test_setup_battery_only_without_batteries_retries(hass: HomeAssistant):
    entry = _battery_entry(serials=[])
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})["_client"] = _client(_station([], []))
    hass.data[DOMAIN]["_card_registered"] = True
    with pytest.raises(ConfigEntryNotReady):
        await hanchuess.async_setup_entry(hass, entry)


async def test_unload_battery_only_entry_unloads_sensor_only(hass: HomeAssistant):
    entry = _battery_entry()
    entry.add_to_hass(hass)
    with patch.object(
        hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)
    ) as unload:
        assert await hanchuess.async_unload_entry(hass, entry) is True
    assert unload.await_args.args[1] == ["sensor"]


async def test_services_ignore_battery_only_entries(hass: HomeAssistant):
    entry = _battery_entry()
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(realtime=None)
    with patch.object(hanchuess, "_iter_entry_runtime_data", return_value=[(entry, entry.runtime_data)]):
        assert hanchuess._find_realtime_coordinator(hass) is None
        assert hanchuess._find_entry(hass) is None


# --- Sensors and diagnostics -------------------------------------------------------

from custom_components.hanchuess import sensor as sensor_mod  # noqa: E402
from custom_components.hanchuess.diagnostics import async_get_config_entry_diagnostics  # noqa: E402


async def test_sensor_setup_battery_only_adds_battery_sensors_only():
    battery = MagicMock()
    battery.data = {"B1": {"socPack": "88", "numBatT": 4}}
    entry = SimpleNamespace(
        data={"mode": "battery_only", "battery_serials": ["B1"]},
        runtime_data=SimpleNamespace(
            realtime=None, statistics=None, battery=battery, inverter_device_id="dev1"
        ),
    )
    added = []
    await sensor_mod.async_setup_entry(MagicMock(), entry, lambda ents: added.extend(ents))
    assert added
    assert all(getattr(e, "_battery_serial", None) == "B1" for e in added)
    info = added[0].device_info
    assert info["via_device_id"] == "dev1"


async def test_diagnostics_include_station_summary(hass: HomeAssistant):
    entry = _battery_entry()
    entry.add_to_hass(hass)
    summary = station_summary(_station([LUX_PLACEHOLDER], SIX_BATTERIES[:1]))
    from custom_components.hanchuess.staging import SettingsStagingBuffer

    entry.runtime_data = hanchuess.HanchuessData(
        realtime=None, statistics=None, battery=None, number_limits={},
        startup_values={}, staging=SettingsStagingBuffer(), control_registry={},
        inverter_device_id="dev1", battery_only=True, station_summary=summary,
    )
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["mode"] == "battery_only"
    assert diag["station_summary"] == summary
    assert diag["entry"]["data"]["token"] == "**REDACTED**"
    assert diag["entry"]["data"]["stationName"] == "**REDACTED**"
    assert diag["entry"]["data"]["mode"] == "battery_only"
