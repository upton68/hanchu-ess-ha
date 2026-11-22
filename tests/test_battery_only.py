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
    # Battery energy coordinator shares the battery coordinator's devId map.
    assert data.energy is not None
    assert data.energy.dev_ids is data.battery.dev_ids
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


# --- beta.2: devId lookup, station fallback, polling, precision ------------------

from custom_components.hanchuess.battery import (  # noqa: E402
    battery_dev_ids,
    station_battery_values,
)
from custom_components.hanchuess.coordinator import HanchuessBatteryCoordinator  # noqa: E402

DETAIL_OK = {"code": 200, "success": True, "data": {"sn": "x", "vPack": "53.24", "socPack": "88.1"}}
EMPTY = {"code": 200, "success": True, "data": {}}
FAILED = {"code": 100, "success": False, "msg": "device not found"}


def test_battery_dev_ids_and_station_values():
    detail = _station([], [
        {**_bms("B1"), "devId": "B1"},
        {**_bms("B2"), "devId": "D2", "sohPack": 100},
    ])
    assert battery_dev_ids(detail) == {"B1": "B1", "B2": "D2"}
    values = station_battery_values(detail)
    assert values["B2"] == {"socPack": 88.1, "sohPack": 100, "devModel": "3", "onlineStatus": "1"}
    summary = station_summary(detail)
    assert [b["dev_id_differs"] for b in summary["batteries"]] == [False, True]


def _coordinator(hass, client, mode="battery_only", serials=("B1", "B2"), options=None):
    data = {"token": "t", "stationId": "ST1", "battery_serials": list(serials)}
    if mode:
        data["mode"] = mode
    else:
        data["sn"] = "SN1"
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options or {})
    entry.add_to_hass(hass)
    return HanchuessBatteryCoordinator(hass, entry, client)


# HV stack (#78): queryBatteryDataDivisions has no per-module data.
HV_NOT_FOUND = {"code": 100, "msg": "90060 Not Found Data!", "success": False}

# rack/queryRackDataDivisions for a Home-ESS-HV-5.12K stack (from #78, trimmed).
RACK_OK = {"code": 200, "success": True, "data": {
    "rackTotalV": "475.3", "rackTotalA": "-4.8", "rackCapFull": 100.0,
    "rackCapRemain": 70.0, "rackSoc": 70.1, "rackSoh": "100.0", "rackCapacity": "46.1",
    "maxCellV": "3.303", "minCellV": "3.295", "maxCellVDiff": "0.008",
    "packAvgT": "19.2", "rackSoftVer": "HOME-ESS-HV-5.12_BCU_2.55",
    "onlineStatus": "1", "dataTimeTs": 1795379366161, "rackPwr": "-2281.4",
    "todayCharge": "19.90", "todayDischarge": "8.80", "packNum": 9,
    "pack1V": "52.741", "packList": [{"packSn": "P1"}],
}}


def _poll_client(station, by_id, rack_by_id=None):
    client = MagicMock()
    client.async_get_station_detail = AsyncMock(return_value=station)
    client.async_get_battery_data = AsyncMock(side_effect=lambda dev_id, lang="en": by_id.get(dev_id, EMPTY))
    client.async_get_rack_data = AsyncMock(
        side_effect=lambda sn, lang="en": (rack_by_id or {}).get(sn, HV_NOT_FOUND)
    )
    return client


async def test_battery_queried_by_dev_id(hass: HomeAssistant):
    station = _station([], [{**_bms("B1"), "devId": "B1"}, {**_bms("B2"), "devId": "D2"}])
    client = _poll_client(station, {"B1": DETAIL_OK, "D2": DETAIL_OK})
    coordinator = _coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert data["B2"]["vPack"] == "53.24"
    queried = [c.args[0] for c in client.async_get_battery_data.await_args_list]
    assert "D2" in queried and "B2" not in queried
    assert coordinator.battery_status["B2"] == {
        "queried_by": "devId", "dev_id_differs": True, "ok": True, "source": "detail", "error": None}


async def test_battery_falls_back_to_sn_when_dev_id_empty(hass: HomeAssistant):
    station = _station([], [{**_bms("B1"), "devId": "B1"}, {**_bms("B2"), "devId": "D2"}])
    client = _poll_client(station, {"B1": DETAIL_OK, "D2": EMPTY, "B2": DETAIL_OK})
    coordinator = _coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert data["B2"]["vPack"] == "53.24"
    assert coordinator.battery_status["B2"]["queried_by"] == "sn"


async def test_missing_detail_falls_back_to_station_soc(hass: HomeAssistant):
    station = _station([], [{**_bms("B1", soc=1.99), "devId": "B1"}, {**_bms("B2", soc=10.25), "devId": "B2"}])
    client = _poll_client(station, {"B1": DETAIL_OK, "B2": FAILED})
    coordinator = _coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert data["B1"]["vPack"] == "53.24"
    assert data["B2"]["socPack"] == 10.25
    assert data["B2"]["devModel"] == "3"
    assert "vPack" not in data["B2"]
    status = coordinator.battery_status["B2"]
    assert status["source"] == "station" and status["ok"] is True
    assert status["error"] == "code=100 msg=device not found"


async def test_normal_mode_does_not_read_station_when_batteries_work(hass: HomeAssistant):
    client = _poll_client({}, {"B1": DETAIL_OK, "B2": DETAIL_OK})
    coordinator = _coordinator(hass, client, mode=None)
    await coordinator._async_update_data()
    client.async_get_station_detail.assert_not_called()


async def test_normal_mode_without_station_values_leaves_battery_out(hass: HomeAssistant):
    client = _poll_client({}, {"B1": DETAIL_OK, "B2": EMPTY})
    coordinator = _coordinator(hass, client, mode=None)
    data = await coordinator._async_update_data()
    assert "B2" not in data
    assert coordinator.battery_status["B2"] == {
        "queried_by": "sn", "dev_id_differs": False, "ok": False, "source": None, "error": "empty data"}




async def test_normal_mode_hv_stack_falls_back_to_station_values(hass: HomeAssistant):
    station = _station([HANCHU_PCS], [{**_bms("B1", soc=76.5), "devId": "B1"}])
    client = _poll_client(station, {"B1": HV_NOT_FOUND})
    coordinator = _coordinator(hass, client, mode=None, serials=("B1",))
    data = await coordinator._async_update_data()  # no UpdateFailed: SOC is there
    assert data["B1"]["socPack"] == 76.5
    assert "vPack" not in data["B1"]
    client.async_get_station_detail.assert_awaited_once()
    status = coordinator.battery_status["B1"]
    assert status["source"] == "station" and status["ok"] is True
    assert status["error"] == "code=100 msg=90060 Not Found Data!"


async def test_battery_only_polls_every_minute_by_default(hass: HomeAssistant):
    client = _poll_client({}, {})
    assert _coordinator(hass, client).update_interval.total_seconds() == 60
    assert _coordinator(hass, client, mode=None).update_interval.total_seconds() == 600
    assert _coordinator(hass, client, options={"battery_interval": 120}).update_interval.total_seconds() == 120


def test_battery_sensors_have_display_precision():
    from custom_components.hanchuess.sensor import BATTERY_SENSORS, BatterySensor

    coordinator = MagicMock()
    coordinator.data = {"B1": {"vPack": "53.24"}}
    entry = SimpleNamespace(data={}, runtime_data=SimpleNamespace(inverter_device_id="d"))
    voltage = BatterySensor(coordinator, entry, "B1", "battery_voltage", BATTERY_SENSORS["battery_voltage"])
    assert voltage.suggested_display_precision == 2
    assert voltage.native_value == 53.24
    current = BatterySensor(coordinator, entry, "B1", "battery_current", BATTERY_SENSORS["battery_current"])
    assert current.suggested_display_precision == 2


async def test_diagnostics_include_battery_status(hass: HomeAssistant):
    from custom_components.hanchuess.staging import SettingsStagingBuffer

    entry = _battery_entry(serials=["B1", "B2"])
    entry.add_to_hass(hass)
    battery = MagicMock()
    battery.data = {"B1": {"socPack": "1"}}
    battery.battery_status = {"B1": {"ok": True}, "B2": {"ok": False, "error": "empty data"}}
    battery.station_detail = _station([LUX_PLACEHOLDER], [_bms("B1"), _bms("B2")])
    entry.runtime_data = hanchuess.HanchuessData(
        realtime=None, statistics=None, battery=battery, number_limits={},
        startup_values={}, staging=SettingsStagingBuffer(), control_registry={},
        inverter_device_id="dev1", battery_only=True, station_summary=None,
    )
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["battery_status"] == {
        "battery_1": {"ok": True}, "battery_2": {"ok": False, "error": "empty data"}}
    assert len(diag["station_summary"]["batteries"]) == 2
    assert "B1" not in repr(diag["battery_status"])


async def test_normal_setup_seeds_battery_dev_ids(hass: HomeAssistant):
    """Installs with a Hanchu inverter also read batteries by devId."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="SN1",
        data={"sn": "SN1", "token": "tok", "stationId": "ST1", "battery_serials": ["B1", "B2"]},
    )
    entry.add_to_hass(hass)
    station = _station([HANCHU_PCS], [{**_bms("B1"), "devId": "B1"}, {**_bms("B2"), "devId": "D2"}])
    client = MagicMock()
    client.token = "tok"
    client.should_refresh_token.return_value = False
    client.async_get_device_status = AsyncMock(return_value={"devStatus": 1, "stationId": "ST1"})
    client.async_get_device_statistics = AsyncMock(return_value={"load": 1})
    client.async_get_menu = AsyncMock(return_value={"code": 200, "data": {}})
    client.async_iot_get = AsyncMock(return_value={})
    client.async_get_station_detail = AsyncMock(return_value=station)
    client.async_get_battery_data = AsyncMock(
        side_effect=lambda dev_id, lang="en": DETAIL_OK if dev_id in ("B1", "D2") else EMPTY
    )
    hass.data.setdefault(DOMAIN, {})["_client"] = client
    hass.data[DOMAIN]["_card_registered"] = True

    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
        assert await hanchuess.async_setup_entry(hass, entry) is True

    battery = entry.runtime_data.battery
    assert battery.dev_ids == {"B1": "B1", "B2": "D2"}
    assert battery.data["B2"]["vPack"] == "53.24"
    queried = [c.args[0] for c in client.async_get_battery_data.await_args_list]
    assert "D2" in queried and "B2" not in queried
    # Normal installs don't re-read the station list on each battery poll.
    assert client.async_get_station_detail.await_count == 1


async def test_normal_setup_continues_when_battery_detail_is_empty(hass: HomeAssistant):
    """#76: HESS-HY-T battery detail comes back empty; the inverter must still load."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="SN1",
        data={"sn": "SN1", "token": "tok", "stationId": "ST1", "battery_serials": ["B1"]},
    )
    entry.add_to_hass(hass)
    client = MagicMock()
    client.token = "tok"
    client.should_refresh_token.return_value = False
    client.async_get_device_status = AsyncMock(return_value={"devStatus": 1, "stationId": "ST1"})
    client.async_get_device_statistics = AsyncMock(return_value={"load": 1})
    client.async_get_menu = AsyncMock(return_value={"code": 200, "data": {}})
    client.async_iot_get = AsyncMock(return_value={})
    # Setup reads the station once; the battery fallback's read finds nothing
    # (e.g. the station call fails too), so there is no battery data at all.
    client.async_get_station_detail = AsyncMock(
        side_effect=[_station([HANCHU_PCS], [{**_bms("B1"), "devId": "B1"}]), {}]
    )
    client.async_get_battery_data = AsyncMock(return_value=EMPTY)
    hass.data.setdefault(DOMAIN, {})["_client"] = client
    hass.data[DOMAIN]["_card_registered"] = True

    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
        assert await hanchuess.async_setup_entry(hass, entry) is True

    battery = entry.runtime_data.battery
    assert battery is not None
    assert battery.data == {}  # battery sensors can be set up, and show unavailable
    assert battery.last_update_success is False
    assert entry.runtime_data.realtime.last_update_success is True



async def test_hv_stack_reads_rack_data(hass: HomeAssistant):
    station = _station([HANCHU_PCS], [{**_bms("B1", soc=70.0), "devId": "D1"}])
    client = _poll_client(station, {"B1": HV_NOT_FOUND, "D1": HV_NOT_FOUND}, {"D1": RACK_OK})
    coordinator = _coordinator(hass, client, mode=None, serials=("B1",))
    coordinator.dev_ids["B1"] = "D1"
    data = await coordinator._async_update_data()
    b1 = data["B1"]
    assert (b1["vPack"], b1["iPack"], b1["socPack"], b1["sohPack"]) == ("475.3", "-4.8", 70.1, "100.0")
    assert (b1["capFull"], b1["capRemain"], b1["designCapacity"]) == (100.0, 70.0, "46.1")
    assert (b1["maxVoltage"], b1["minVoltage"], b1["maxVoltageDifference"]) == ("3.303", "3.295", "0.008")
    assert b1["todayCharge"] == "19.90" and b1["devModel"] == "3"  # station model kept
    assert "packList" not in b1 and "pack1V" not in b1
    status = coordinator.battery_status["B1"]
    assert status["source"] == "rack" and status["rack_queried_by"] == "devId"
    tried = [c.args[0] for c in client.async_get_rack_data.await_args_list]
    assert tried == ["B1", "D1"]

    # Next poll goes straight to the ID that worked.
    client.async_get_rack_data.reset_mock()
    await coordinator._async_update_data()
    assert [c.args[0] for c in client.async_get_rack_data.await_args_list] == ["D1"]


async def test_lv_battery_not_asked_for_rack_data_again(hass: HomeAssistant):
    station = _station([HANCHU_PCS], [{**_bms("B1"), "devId": "B1"}])
    client = _poll_client(station, {"B1": EMPTY})
    coordinator = _coordinator(hass, client, mode=None, serials=("B1",))
    await coordinator._async_update_data()
    assert client.async_get_rack_data.await_count == 1
    await coordinator._async_update_data()
    assert client.async_get_rack_data.await_count == 1  # remembered: not a stack


def test_hv_rack_power_and_remaining_energy():
    from custom_components.hanchuess.battery import rack_battery_values
    from custom_components.hanchuess.sensor import battery_power_w

    values = rack_battery_values(RACK_OK["data"])
    assert battery_power_w(values) == round(475.3 * -4.8, 1)  # matches rackPwr -2281.4


async def test_api_rack_payload():
    from custom_components.hanchuess.api import HanchuessApiClient
    from custom_components.hanchuess.crypto import _encrypt_payload

    client = HanchuessApiClient.__new__(HanchuessApiClient)
    client._request = AsyncMock(return_value={"code": 200, "data": {}})
    await client.async_get_rack_data("R1", "en")
    path, payload = client._request.await_args.args[:2]
    assert path == "/gateway/platform/rack/queryRackDataDivisions"
    assert payload == _encrypt_payload({"sn": "R1", "type": "1"})


async def test_hv_stack_energy_from_its_own_daily_figures(hass: HomeAssistant):
    from custom_components.hanchuess.coordinator import HanchuessBatteryEnergyCoordinator

    entry = MockConfigEntry(domain=DOMAIN, data={"sn": "SN1", "battery_serials": ["B1"]})
    entry.add_to_hass(hass)
    battery = MagicMock()
    battery.data = {"B1": {"hvStack": True, "todayCharge": "19.90", "todayDischarge": "8.80",
                           "dataTimeTs": 1795379366161}}
    client = MagicMock()
    client.async_get_battery_minute_chart = AsyncMock()
    energy = HanchuessBatteryEnergyCoordinator(hass, entry, client, {}, battery)

    data = await energy._async_update_data()
    assert (data["B1"]["charge_today"], data["B1"]["charge_total"]) == (19.9, 19.9)
    assert (data["B1"]["discharge_today"], data["B1"]["discharge_total"]) == (8.8, 8.8)
    client.async_get_battery_minute_chart.assert_not_called()  # no minute chart for a stack

    battery.data["B1"].update(todayCharge="21.40", todayDischarge="8.80")
    data = await energy._async_update_data()
    assert data["B1"]["charge_total"] == pytest.approx(21.4)  # +1.5
    assert data["B1"]["discharge_total"] == pytest.approx(8.8)  # unchanged

    # Midnight: the cloud resets today's figures; Total keeps counting.
    battery.data["B1"].update(todayCharge="0.30", todayDischarge="0.10")
    data = await energy._async_update_data()
    assert data["B1"]["charge_today"] == 0.3
    assert data["B1"]["charge_total"] == pytest.approx(21.7)
    assert data["B1"]["discharge_total"] == pytest.approx(8.9)


def test_hv_stack_skips_lv_only_sensors():
    from custom_components.hanchuess.battery import rack_battery_values
    from custom_components.hanchuess.sensor import BatterySensor, _battery_entities

    battery = MagicMock()
    battery.data = {"B1": {**rack_battery_values(RACK_OK["data"]), "devModel": "3"}}
    entry = SimpleNamespace(
        data={"battery_serials": ["B1"]},
        runtime_data=SimpleNamespace(inverter_device_id="d", energy=None),
    )
    keys = {e._sensor_key for e in _battery_entities(entry, battery) if isinstance(e, BatterySensor)}
    assert not any(k.startswith("battery_temperature_") and k[-1].isdigit() for k in keys)
    assert "battery_voltage" in keys and "battery_soc_pack" in keys
    configs = {e._config.get("key") for e in _battery_entities(entry, battery) if isinstance(e, BatterySensor)}
    assert "tEnv" not in configs and "tMos" not in configs and "tPack" in configs
