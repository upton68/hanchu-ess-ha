"""Tests for the ``hanchuess/strategy_entities`` WebSocket command (issue #74).

The Weather Optimize and Octopus cards find their entities through this
command, by unique id, so renamed entities and older installs' entity ids
are found.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("homeassistant")

from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.hanchuess import ws_strategy_entities  # noqa: E402
from custom_components.hanchuess.const import DOMAIN, MODE_BATTERY_ONLY  # noqa: E402
from custom_components.hanchuess.strategy_entity import card_entity_keys  # noqa: E402

SN = "SN1"


def _entry(hass, sn=SN, **data):
    entry = MockConfigEntry(domain=DOMAIN, data={"sn": sn, "token": "t", **data})
    entry.add_to_hass(hass)
    return entry


def _register(hass, entry, key, *, sn=SN, object_id=None, disabled=False):
    platform, suffix = card_entity_keys()[key]
    return er.async_get(hass).async_get_or_create(
        platform,
        DOMAIN,
        f"{sn}_{suffix}",
        suggested_object_id=object_id or f"hanchuess_{sn.lower()}_{suffix}",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.INTEGRATION if disabled else None,
    )


def _call(hass, sn=SN):
    connection = MagicMock()
    ws_strategy_entities(hass, connection, {"id": 7, "type": "hanchuess/strategy_entities", "sn": sn})
    return connection


def _result(connection):
    connection.send_error.assert_not_called()
    connection.send_result.assert_called_once()
    msg_id, payload = connection.send_result.call_args.args
    assert msg_id == 7
    return payload["entities"]


def test_keys_cover_every_strategy_entity_and_pending_changes():
    keys = card_entity_keys()
    assert keys["weather_optimize"] == ("switch", "weather_optimize")
    assert keys["octopus_charge_slots_0000_0800"] == ("number", "octopus_charge_slots_0000_0800")
    assert keys["save_octopus_strategy"] == ("button", "save_octopus_strategy")
    assert keys["pending_changes"] == ("sensor", "pending_settings_changes")
    assert len([k for k in keys if k.startswith("weather_soc_")]) == 11


async def test_returns_entity_ids_by_unique_id(hass: HomeAssistant):
    entry = _entry(hass)
    for key in card_entity_keys():
        _register(hass, entry, key)

    entities = _result(_call(hass))

    assert set(entities) == set(card_entity_keys())
    assert entities["weather_optimize"] == {
        "entity_id": f"switch.hanchuess_{SN.lower()}_weather_optimize",
        "disabled": False,
    }
    assert entities["pending_changes"]["entity_id"] == (
        f"sensor.hanchuess_{SN.lower()}_pending_settings_changes"
    )


async def test_renamed_and_pre_rename_entity_ids_are_found(hass: HomeAssistant):
    entry = _entry(hass)
    # Older installs keep the entity ids from before the switches were renamed.
    _register(hass, entry, "octopus_charge", object_id="hanchuess_sn1_octopus_charge")
    _register(hass, entry, "octopus_discharge", object_id="hanchuess_sn1_octopus_discharge")
    # And a user can rename any of them.
    registry = er.async_get(hass)
    weather = _register(hass, entry, "weather_optimize")
    registry.async_update_entity(weather.entity_id, new_entity_id="switch.my_weather_switch")
    save = _register(hass, entry, "save_octopus_strategy")
    registry.async_update_entity(save.entity_id, new_entity_id="button.save_octopus")

    entities = _result(_call(hass))

    assert entities["octopus_charge"]["entity_id"] == "switch.hanchuess_sn1_octopus_charge"
    assert entities["octopus_discharge"]["entity_id"] == "switch.hanchuess_sn1_octopus_discharge"
    assert entities["weather_optimize"]["entity_id"] == "switch.my_weather_switch"
    assert entities["save_octopus_strategy"]["entity_id"] == "button.save_octopus"


async def test_disabled_state_is_reported(hass: HomeAssistant):
    entry = _entry(hass)
    _register(hass, entry, "weather_optimize", disabled=True)
    _register(hass, entry, "save_weather_optimize", disabled=True)
    _register(hass, entry, "weather_soc_sunny")
    user_disabled = _register(hass, entry, "strategy_priority")
    er.async_get(hass).async_update_entity(
        user_disabled.entity_id, disabled_by=er.RegistryEntryDisabler.USER
    )

    entities = _result(_call(hass))

    assert entities["weather_optimize"]["disabled"] is True
    assert entities["save_weather_optimize"]["disabled"] is True
    assert entities["strategy_priority"]["disabled"] is True
    assert entities["weather_soc_sunny"]["disabled"] is False


async def test_entities_not_in_registry_are_left_out(hass: HomeAssistant):
    entry = _entry(hass)
    _register(hass, entry, "octopus_strategy")

    entities = _result(_call(hass))

    assert set(entities) == {"octopus_strategy"}


async def test_only_the_requested_inverters_entities(hass: HomeAssistant):
    entry1 = _entry(hass)
    entry2 = _entry(hass, sn="SN2")
    _register(hass, entry1, "octopus_strategy")
    _register(hass, entry2, "octopus_strategy", sn="SN2")

    entities = _result(_call(hass, sn="SN2"))

    assert entities == {
        "octopus_strategy": {
            "entity_id": "switch.hanchuess_sn2_octopus_strategy",
            "disabled": False,
        }
    }


async def test_unknown_sn_is_not_found(hass: HomeAssistant):
    _entry(hass)

    connection = _call(hass, sn="NOPE")

    connection.send_result.assert_not_called()
    connection.send_error.assert_called_once()
    assert connection.send_error.call_args.args[:2] == (7, "not_found")


async def test_battery_only_station_is_not_found(hass: HomeAssistant):
    _entry(hass, mode=MODE_BATTERY_ONLY)

    connection = _call(hass)

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args.args[:2] == (7, "not_found")
