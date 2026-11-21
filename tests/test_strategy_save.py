"""Strategy coordinator, save sequence and entities (#72).

Uses a fake cloud in which every save creates a new record with the next id,
and a read returns the latest one, as the Hanchu cloud does.
"""
from __future__ import annotations

import copy
from datetime import time as dt_time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component.common")

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hanchuess.api import ReauthRequired
from custom_components.hanchuess.const import DOMAIN
from custom_components.hanchuess.coordinator import HanchuessStrategyCoordinator
from custom_components.hanchuess.sensor import HanchuessSettingsPendingSensor
from custom_components.hanchuess.staging import SettingsStagingBuffer
from custom_components.hanchuess.strategy import (
    OCTOPUS,
    PRIORITY_KEY,
    WEATHER,
    slots_key,
    soc_key,
)
from custom_components.hanchuess.strategy_entity import (
    HanchuessStrategyNumber,
    HanchuessStrategySaveButton,
    HanchuessStrategySelect,
    HanchuessStrategySwitch,
    HanchuessStrategyText,
    HanchuessStrategyTime,
    NUMBERS,
    SELECTS,
    SWITCHES,
    TEXTS,
    TIMES,
    strategy_numbers,
)

SN = "SN1"
NOTIFY = "custom_components.hanchuess.coordinator.persistent_notification"


class FakeCloud:
    def __init__(self):
        self.next_id = 27483
        self.records = {
            WEATHER: {
                "id": 27482, "sn": SN, "weatherOpen": "1",
                "weatherChargeTimeStart": "23:30", "weatherChargeTimeEnd": "05:30",
                PRIORITY_KEY: "2",
                "weathers": [
                    {"code": "100", "cloud": "", "soc": "40"},
                    {"code": "777", "cloud": "", "soc": "10"},
                ],
            },
            OCTOPUS: {
                "id": 27400, "sn": SN, "octopusOpen": "0", "octopusType": "1",
                "octopusPriceEnable": "1", "octopusDischargeEnable": "0",
                "octopusPrice": "12.5", "octopusDischargePrice": "30",
                PRIORITY_KEY: "2", "postalCode": "AB1 2CD",
                "octopuses": [
                    {"timeStr": "00:00-08:00", "num": "4"},
                    {"timeStr": "12:00-19:00", "num": "2"},
                ],
            },
        }
        self.saves: list[tuple[str, dict]] = []
        self.calls: list[str] = []
        self.save_result = {"code": 200, "success": True}
        self.apply_failed_save = False

    async def get(self, kind, sn, language="en"):
        self.calls.append(f"read:{kind}")
        return {"code": 200, "success": True, "data": copy.deepcopy(self.records[kind])}

    async def save(self, kind, record, language="en"):
        self.calls.append(f"save:{kind}")
        self.saves.append((kind, copy.deepcopy(record)))
        if self.save_result.get("code") == 200 or self.apply_failed_save:
            stored = {k: v for k, v in record.items() if k != "confirm"}
            stored["id"] = self.next_id
            self.next_id += 1
            self.records[kind] = stored
        return self.save_result


@pytest.fixture
def cloud():
    return FakeCloud()


@pytest.fixture
def coordinator(hass: HomeAssistant, cloud):
    entry = MockConfigEntry(domain=DOMAIN, data={"sn": SN, "token": "t"}, unique_id=SN)
    entry.add_to_hass(hass)
    client = MagicMock()
    client.async_get_strategy = AsyncMock(side_effect=cloud.get)
    client.async_save_strategy = AsyncMock(side_effect=cloud.save)
    client.async_refresh_token = AsyncMock(return_value="new-token")
    return HanchuessStrategyCoordinator(hass, entry, client)


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------

async def test_poll_reads_both_records(coordinator, cloud):
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.record(WEATHER)["id"] == 27482
    assert coordinator.record(OCTOPUS)["id"] == 27400


async def test_failed_read_keeps_last_record(coordinator, cloud):
    await coordinator.async_refresh()
    coordinator.client.async_get_strategy = AsyncMock(return_value={})
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.record(WEATHER)["id"] == 27482
    assert coordinator.errors[WEATHER] == "request failed"


async def test_first_poll_fails_when_nothing_read(coordinator):
    coordinator.client.async_get_strategy = AsyncMock(return_value={"code": 100})
    await coordinator.async_refresh()
    assert not coordinator.last_update_success


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

async def test_save_reads_latest_before_writing(coordinator, cloud):
    await coordinator.async_refresh()
    # The record changes in the app after HA last polled.
    cloud.records[WEATHER] = {**cloud.records[WEATHER], "id": 27490, "weatherChargeTimeEnd": "06:00"}
    coordinator.staging[WEATHER].stage(soc_key("sunny"), 75)
    cloud.calls.clear()

    with patch(NOTIFY):
        assert await coordinator.async_save(WEATHER)

    assert cloud.calls == ["read:weather", "save:weather", "read:weather"]
    kind, payload = cloud.saves[0]
    assert payload["id"] == 27490  # not the cached 27482
    assert payload["weatherChargeTimeEnd"] == "06:00"  # app change kept
    assert payload["confirm"] == "0"
    assert payload["weathers"] == [
        {"code": "100", "cloud": "", "soc": "75"},
        {"code": "777", "cloud": "", "soc": "10"},  # unknown category kept
    ]
    # Re-read after save: entities see the new record straight away.
    assert coordinator.record(WEATHER)["id"] == 27483
    assert coordinator.staging[WEATHER].count == 0


async def test_nothing_staged_saves_nothing(coordinator, cloud):
    assert await coordinator.async_save(OCTOPUS)
    assert cloud.saves == []


async def test_priority_is_saved_to_both_records(coordinator, cloud):
    await coordinator.async_refresh()
    for kind in (WEATHER, OCTOPUS):
        coordinator.staging[kind].stage(PRIORITY_KEY, "1")
    coordinator.staging[OCTOPUS].stage("octopusPrice", 9.5)  # not saved yet
    coordinator.staging[WEATHER].stage("weatherOpen", "0")

    with patch(NOTIFY):
        assert await coordinator.async_save(WEATHER)

    assert [k for k, _ in cloud.saves] == [WEATHER, OCTOPUS]
    weather_payload, octopus_payload = cloud.saves[0][1], cloud.saves[1][1]
    assert weather_payload[PRIORITY_KEY] == "1"
    assert weather_payload["weatherOpen"] == "0"
    assert octopus_payload[PRIORITY_KEY] == "1"
    assert octopus_payload["octopusPrice"] == "12.5"  # other staged change left out
    assert coordinator.staging[WEATHER].pending == {}
    assert coordinator.staging[OCTOPUS].pending == {"octopusPrice": 9.5}
    assert coordinator.record(OCTOPUS)[PRIORITY_KEY] == "1"


async def test_failed_save_keeps_changes_staged_and_notifies(coordinator, cloud):
    await coordinator.async_refresh()
    cloud.save_result = {"code": 100, "success": False, "msg": "Invalid value"}
    coordinator.staging[OCTOPUS].stage("octopusPrice", 60)

    with patch(NOTIFY) as notify:
        assert not await coordinator.async_save(OCTOPUS)

    assert len(cloud.saves) == 1  # never repeated
    assert coordinator.staging[OCTOPUS].pending == {"octopusPrice": 60}
    notify.async_create.assert_called_once()
    assert "Invalid value" in notify.async_create.call_args.args[1]


async def test_save_with_lost_reply_that_was_applied_counts_as_saved(coordinator, cloud):
    await coordinator.async_refresh()
    cloud.save_result = {}  # e.g. timeout after the cloud stored it
    cloud.apply_failed_save = True
    coordinator.staging[OCTOPUS].stage(slots_key("00:00-08:00"), 6)

    with patch(NOTIFY) as notify:
        assert await coordinator.async_save(OCTOPUS)

    assert len(cloud.saves) == 1
    assert coordinator.staging[OCTOPUS].count == 0
    notify.async_create.assert_not_called()


async def test_failed_priority_save_to_other_record_is_reported(coordinator, cloud):
    await coordinator.async_refresh()
    for kind in (WEATHER, OCTOPUS):
        coordinator.staging[kind].stage(PRIORITY_KEY, "1")
    original_save = cloud.save

    async def octopus_fails(kind, record, language="en"):
        if kind == OCTOPUS:
            cloud.saves.append((kind, record))
            return {"code": 100, "msg": "busy"}
        return await original_save(kind, record, language)

    coordinator.client.async_save_strategy = AsyncMock(side_effect=octopus_fails)
    with patch(NOTIFY) as notify:
        assert not await coordinator.async_save(WEATHER)

    assert coordinator.staging[WEATHER].count == 0
    assert coordinator.staging[OCTOPUS].pending == {PRIORITY_KEY: "1"}
    assert "Octopus" in notify.async_create.call_args.kwargs["title"]


async def test_save_refreshes_token_after_401_and_tries_once_more(coordinator, cloud):
    await coordinator.async_refresh()
    coordinator.staging[WEATHER].stage("weatherOpen", "0")
    real_save = coordinator.client.async_save_strategy.side_effect
    responses = [{"_token_expired": True}]

    async def save(kind, record, language="en"):
        if responses:
            return responses.pop()
        return await real_save(kind, record, language)

    coordinator.client.async_save_strategy = AsyncMock(side_effect=save)
    with patch(NOTIFY):
        assert await coordinator.async_save(WEATHER)
    coordinator.client.async_refresh_token.assert_awaited_once_with(force=True)
    assert coordinator.config_entry.data["token"] == "new-token"
    assert len(cloud.saves) == 1


async def test_save_gives_up_when_reauth_needed(coordinator, cloud):
    await coordinator.async_refresh()
    coordinator.staging[WEATHER].stage("weatherOpen", "0")
    coordinator.client.async_get_strategy = AsyncMock(return_value={"_token_expired": True})
    coordinator.client.async_refresh_token = AsyncMock(side_effect=ReauthRequired)
    with patch(NOTIFY):
        assert not await coordinator.async_save(WEATHER)
    assert cloud.saves == []
    assert coordinator.staging[WEATHER].count == 1


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

def _entity(cls, coordinator, specs, key):
    spec = next(s for s in specs if s.key == key)
    entity = cls(coordinator, coordinator.config_entry, spec)
    entity.async_write_ha_state = MagicMock()
    return entity


async def test_entities_are_disabled_by_default_and_show_record(coordinator):
    await coordinator.async_refresh()
    number = _entity(HanchuessStrategyNumber, coordinator, NUMBERS, "weather_soc_sunny")
    assert number.entity_registry_enabled_default is False
    assert number.available
    assert number.native_value == 40
    assert number.unique_id == f"{SN}_weather_soc_sunny"
    price = _entity(HanchuessStrategyNumber, coordinator, NUMBERS, "octopus_charge_price")
    assert price.native_value == 12.5
    assert (price.native_min_value, price.native_max_value, price.native_step) == (0, 50, 0.01)
    slots = _entity(
        HanchuessStrategyNumber, coordinator, NUMBERS, "octopus_charge_slots_1200_1900"
    )
    assert slots.native_value == 2
    assert slots.native_max_value == 10


async def test_entities_unavailable_until_record_read(coordinator):
    switch = _entity(HanchuessStrategySwitch, coordinator, SWITCHES, "weather_optimize")
    assert not switch.available


async def test_staged_value_shown_over_record(coordinator):
    await coordinator.async_refresh()
    switch = _entity(HanchuessStrategySwitch, coordinator, SWITCHES, "octopus_strategy")
    assert switch.is_on is False
    await switch.async_turn_on()
    assert coordinator.staging[OCTOPUS].pending == {"octopusOpen": "1"}
    assert switch.is_on is True
    await coordinator.async_refresh()  # a poll does not undo the staged value
    assert switch.is_on is True


async def test_time_number_text_and_select_stage_cloud_formats(coordinator):
    await coordinator.async_refresh()
    start = _entity(HanchuessStrategyTime, coordinator, TIMES, "weather_charge_start")
    assert start.native_value == dt_time(23, 30)
    await start.async_set_value(dt_time(1, 5))
    price = _entity(HanchuessStrategyNumber, coordinator, NUMBERS, "octopus_discharge_price")
    await price.async_set_native_value(25.456)
    slots = _entity(
        HanchuessStrategyNumber, coordinator, NUMBERS, "octopus_charge_slots_0000_0800"
    )
    await slots.async_set_native_value(7.0)
    text = _entity(HanchuessStrategyText, coordinator, TEXTS, "octopus_postcode")
    assert text.native_value == "AB1 2CD"
    await text.async_set_value(" ZZ9 9ZZ ")
    schema = _entity(HanchuessStrategySelect, coordinator, SELECTS, "octopus_schema_type")
    assert schema.current_option == "Price settings"
    await schema.async_select_option("Point settings")

    assert coordinator.staging[WEATHER].pending == {"weatherChargeTimeStart": "01:05"}
    assert coordinator.staging[OCTOPUS].pending == {
        "octopusDischargePrice": 25.46,
        slots_key("00:00-08:00"): 7,
        "postalCode": "ZZ9 9ZZ",
        "octopusType": "2",
    }


async def test_priority_select_stages_both_strategies(coordinator):
    await coordinator.async_refresh()
    select = _entity(HanchuessStrategySelect, coordinator, SELECTS, "strategy_priority")
    assert select.current_option == "Weather Optimize"
    await select.async_select_option("Octopus")
    assert coordinator.staging[WEATHER].pending == {PRIORITY_KEY: "1"}
    assert coordinator.staging[OCTOPUS].pending == {PRIORITY_KEY: "1"}
    assert select.current_option == "Octopus"
    with pytest.raises(HomeAssistantError):
        await select.async_select_option("Neither")


async def test_save_button_raises_on_failure(coordinator, cloud):
    await coordinator.async_refresh()
    cloud.save_result = {"code": 100, "msg": "no"}
    coordinator.staging[WEATHER].stage("weatherOpen", "0")
    button = HanchuessStrategySaveButton(
        coordinator, coordinator.config_entry, WEATHER, "save_weather_optimize",
        "Save Weather Optimize",
    )
    with patch(NOTIFY), pytest.raises(HomeAssistantError):
        await button.async_press()


async def test_no_entities_without_strategy_coordinator():
    entry = SimpleNamespace(data={"sn": SN}, runtime_data=SimpleNamespace(strategy=None))
    assert strategy_numbers(entry) == []


async def test_entity_counts():
    assert len(NUMBERS) == 15  # 11 weather SOC + 2 slot windows + 2 prices
    assert len(SWITCHES) == 4
    assert len(TIMES) == 2
    assert len(SELECTS) == 2
    assert len(TEXTS) == 1


async def test_pending_sensor_counts_strategy_buffers(coordinator):
    entry = SimpleNamespace(
        data={"sn": SN},
        runtime_data=SimpleNamespace(staging=SettingsStagingBuffer(), strategy=coordinator),
    )
    sensor = HanchuessSettingsPendingSensor(entry)
    sensor.async_write_ha_state = MagicMock()
    await sensor.async_added_to_hass()
    entry.runtime_data.staging.stage("CHG_PWR_LMT", 2000)
    coordinator.staging[OCTOPUS].stage("octopusOpen", "1")
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "inverter_settings": 1, "weather_optimize": 0, "octopus_strategy": 1,
    }
    assert sensor.async_write_ha_state.call_count == 2


async def test_full_setup_registers_strategy_entities_disabled(
    hass: HomeAssistant, cloud, enable_custom_integrations
):
    """Real platform setup: the entities exist, disabled, and nothing is polled."""
    for dep in ("http", "websocket_api", "frontend"):
        hass.config.components.add(dep)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"sn": SN, "token": "tok", "stationId": "ST1", "battery_serials": []},
        unique_id=SN,
    )
    entry.add_to_hass(hass)

    client = MagicMock()
    client.token = "tok"
    client.should_refresh_token.return_value = False
    client.async_get_device_status = AsyncMock(return_value={"devStatus": 1})
    client.async_get_device_statistics = AsyncMock(return_value={"load": 1})
    client.async_get_station_detail = AsyncMock(return_value={"success": True, "data": {"bmsList": []}})
    client.async_get_menu = AsyncMock(return_value={"code": 200, "data": {}})
    client.async_iot_get = AsyncMock(return_value={})
    client.async_get_station_history = AsyncMock(return_value={})
    client.async_get_strategy = AsyncMock(side_effect=cloud.get)
    client.async_save_strategy = AsyncMock(side_effect=cloud.save)
    card = patch("custom_components.hanchuess._async_register_card_resource", AsyncMock())
    client_cls = patch("custom_components.hanchuess.HanchuessApiClient", return_value=client)
    with card, client_cls:
        await _setup_and_check(hass, entry, client)


async def _setup_and_check(hass, entry, client):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    expected = {
        "switch": ["weather_optimize", "octopus_strategy", "octopus_charge", "octopus_discharge"],
        "time": ["weather_charge_start", "weather_charge_end"],
        "select": ["octopus_schema_type", "strategy_priority"],
        "text": ["octopus_postcode"],
        "button": ["save_weather_optimize", "save_octopus_strategy"],
        "number": ["weather_soc_sunny", "weather_soc_other_weather",
                   "octopus_charge_slots_0000_0800", "octopus_charge_slots_1200_1900",
                   "octopus_charge_price", "octopus_discharge_price"],
    }
    for platform, keys in expected.items():
        for key in keys:
            entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{SN}_{key}")
            assert entity_id, f"{platform} {key} missing"
            assert registry.async_get(entity_id).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    # Existing controls are untouched and still enabled.
    work_mode = registry.async_get_entity_id("select", DOMAIN, f"{SN}_work_mode")
    assert registry.async_get(work_mode).disabled_by is None
    # All strategy entities disabled: no strategy reads at all.
    client.async_get_strategy.assert_not_awaited()

    # Enabling one starts a read straight away.
    switch_id = registry.async_get_entity_id("switch", DOMAIN, f"{SN}_weather_optimize")
    registry.async_update_entity(switch_id, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(switch_id).state == "on"
    assert client.async_get_strategy.await_count == 2  # weather + octopus, once

    assert await hass.config_entries.async_unload(entry.entry_id)
