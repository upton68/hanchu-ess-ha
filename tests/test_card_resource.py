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

from custom_components.hanchuess import CARD_URL, _async_register_card_resource

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


def _make_hass(resources, mode="storage"):
    return SimpleNamespace(
        data={"lovelace": SimpleNamespace(resource_mode=mode, resources=resources)}
    )


async def test_unloaded_collection_keeps_existing_resources():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources))

    urls = [r["url"] for r in resources.stored]
    assert urls == [r["url"] for r in OTHER_RESOURCES] + [CARD_URL]


async def test_card_already_registered_is_not_duplicated():
    stored = OTHER_RESOURCES + [{"id": "c", "type": "module", "url": CARD_URL}]
    resources = _LazyResources(stored)

    await _async_register_card_resource(_make_hass(resources))

    assert [r["url"] for r in resources.stored].count(CARD_URL) == 1
    assert len(resources.stored) == 3


async def test_yaml_mode_is_left_alone():
    resources = _LazyResources(OTHER_RESOURCES)

    await _async_register_card_resource(_make_hass(resources, mode="yaml"))

    assert resources.stored == OTHER_RESOURCES
    assert resources.loaded is False


async def test_no_lovelace_data_is_a_no_op():
    await _async_register_card_resource(SimpleNamespace(data={}))
