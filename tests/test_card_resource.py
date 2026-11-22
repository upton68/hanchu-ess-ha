"""Tests for the Lovelace card resource auto-registration (issue #41).

Home Assistant's storage-mode ResourceStorageCollection is loaded lazily. On
older HA versions, async_create_item() did not load it first, so if the
integration ran before anything else had touched the collection, it saw an
empty list and saved a one-item list over .storage/lovelace_resources —
wiping every other dashboard resource. _LazyResources below reproduces that
older behaviour so the test fails if the load step is ever removed.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("homeassistant")

from custom_components.hanchuess import (
    CARD_FILES,
    CARD_URL,
    CARD_URLS,
    OCTOPUS_CARD_FILE,
    WEATHER_CARD_FILE,
    _async_register_card_resource,
)

ALL_CARD_URLS = [CARD_URLS[card_file] for card_file in CARD_FILES]

OTHER_RESOURCES = [
    {"id": "a", "type": "module", "url": "/hacsfiles/apexcharts-card/apexcharts-card.js"},
    {"id": "b", "type": "module", "url": "/hacsfiles/power-flow-card-plus/power-flow-card-plus.js"},
]


class _LazyResources:
    """Mimics a not-yet-loaded ResourceStorageCollection (pre-fix HA behaviour)."""

    def __init__(self, stored):
        self.stored = [dict(r) for r in stored]  # what's on disk
        self.data = []  # in-memory items
        self.loaded = False

    async def async_load(self):
        self.data = [dict(r) for r in self.stored]

    async def async_get_info(self):
        if not self.loaded:
            await self.async_load()
            self.loaded = True
        return {"resources": len(self.data)}

    def async_items(self):
        return self.data

    async def async_create_item(self, data):
        # Deliberately does NOT load first, as on older HA.
        item = {"id": "new", "type": data["res_type"], "url": data["url"]}
        self.data.append(item)
        self.stored = [dict(r) for r in self.data]  # save in-memory list to disk
        return item

    async def async_update_item(self, item_id, updates):
        for item in self.data:
            if item["id"] == item_id:
                item["type"] = updates["res_type"]
                item["url"] = updates["url"]
        self.stored = [dict(r) for r in self.data]
        return item


def _make_hass(resources, mode="storage"):
    return SimpleNamespace(
        data={"lovelace": SimpleNamespace(resource_mode=mode, resources=resources)}
    )


async def test_unloaded_collection_keeps_existing_resources():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources))

    urls = [r["url"] for r in resources.stored]
    assert urls == [r["url"] for r in OTHER_RESOURCES] + ALL_CARD_URLS


async def test_card_already_registered_is_not_duplicated():
    stored = OTHER_RESOURCES + [{"id": "c", "type": "module", "url": CARD_URL}]
    resources = _LazyResources(stored)

    await _async_register_card_resource(_make_hass(resources))

    urls = [r["url"] for r in resources.stored]
    assert urls.count(CARD_URL) == 1
    assert urls == [r["url"] for r in OTHER_RESOURCES] + ALL_CARD_URLS


async def test_yaml_mode_is_left_alone():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources, mode="yaml"))

    assert resources.stored == OTHER_RESOURCES
    assert resources.loaded is False


async def test_no_lovelace_data_is_a_no_op():
    await _async_register_card_resource(SimpleNamespace(data={}))


# --- HA 2026.11: card moved off /hacsfiles -------------------------------------


@pytest.mark.parametrize(
    "old_url",
    [
        "/hacsfiles/hanchuess/hanchuess-energy-card.js",
        "/local/community/hanchuess/hanchuess-energy-card.js",
        "/hanchuess_card/hanchuess-energy-card.js?v=0.0.1",
    ],
)
async def test_old_card_url_is_updated_in_place(old_url):
    """An existing entry pointing at an old URL is repointed, not duplicated."""
    stored = OTHER_RESOURCES + [{"id": "c", "type": "module", "url": old_url}]
    resources = _LazyResources(stored)

    await _async_register_card_resource(_make_hass(resources))

    urls = [r["url"] for r in resources.stored]
    assert urls == [r["url"] for r in OTHER_RESOURCES] + ALL_CARD_URLS


async def test_card_url_is_not_under_hacsfiles():
    assert not CARD_URL.startswith("/hacsfiles/")
    assert CARD_URL.startswith("/hanchuess_card/hanchuess-energy-card.js?v=")


# --- Weather Optimize and Octopus cards (issue #74) ------------------------------


async def test_strategy_cards_are_registered_without_touching_other_resources():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources))

    assert resources.stored[:2] == OTHER_RESOURCES
    urls = [r["url"] for r in resources.stored]
    for card_file in (WEATHER_CARD_FILE, OCTOPUS_CARD_FILE):
        assert urls.count(CARD_URLS[card_file]) == 1
    assert all(r["type"] == "module" for r in resources.stored[2:])


async def test_registration_is_idempotent():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources))
    first = [dict(r) for r in resources.stored]
    await _async_register_card_resource(_make_hass(resources))

    assert resources.stored == first
    assert len(resources.stored) == len(OTHER_RESOURCES) + len(CARD_FILES)


@pytest.mark.parametrize("card_file", [WEATHER_CARD_FILE, OCTOPUS_CARD_FILE])
async def test_old_strategy_card_version_is_updated_in_place(card_file):
    old_url = f"/hanchuess_card/{card_file}?v=0.0.1"
    stored = OTHER_RESOURCES + [{"id": "c", "type": "module", "url": old_url}]
    resources = _LazyResources(stored)

    await _async_register_card_resource(_make_hass(resources))

    urls = [r["url"] for r in resources.stored]
    assert old_url not in urls
    assert urls.count(CARD_URLS[card_file]) == 1
    assert len(urls) == len(OTHER_RESOURCES) + len(CARD_FILES)


def test_strategy_card_urls_are_versioned_and_served_with_the_energy_card():
    for card_file in (WEATHER_CARD_FILE, OCTOPUS_CARD_FILE):
        assert CARD_URLS[card_file].startswith(f"/hanchuess_card/{card_file}?v=")
        assert CARD_URLS[card_file].split("?v=")[1] == CARD_URL.split("?v=")[1]


def test_card_files_ship_with_the_integration():
    import os

    import custom_components.hanchuess as integration

    www = os.path.join(os.path.dirname(integration.__file__), "www")
    for card_file in (*CARD_FILES, "hanchuess-strategy-common.js"):
        assert os.path.isfile(os.path.join(www, card_file)), card_file
