"""Unit tests for the diagnostics module (no hass harness required).

The diagnostics entry points only need ``entry.as_dict()``/``entry.data``/
``entry.runtime_data`` and ``async_redact_data`` (available with the bare
``homeassistant`` package), so they can be exercised with light fakes in the
same cross-platform style as ``tests/test_logic.py``. The module skips if the
``homeassistant`` package is unavailable.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("homeassistant")

from custom_components.hanchuess import HanchuessData
from custom_components.hanchuess.const import DOMAIN
from custom_components.hanchuess.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
)

REDACTED = "**REDACTED**"  # async_redact_data's sentinel


class _FakeEntry:
    """Stand-in for a HA ConfigEntry exposing only what diagnostics reads."""

    def __init__(self, entry_id="entry1", data=None):
        self.entry_id = entry_id
        self.data = data or {
            "token": "secret-token",
            "sn": "SN123",
            "account": "user@example.com",
            "stationId": "station-1",
            "battery_serials": ["BAT-1", "BAT-2"],
            "dev_type": "2",
        }
        self.runtime_data = None

    def as_dict(self):
        return {
            "entry_id": self.entry_id,
            "title": "My Device",
            "domain": DOMAIN,
            "data": dict(self.data),
        }


def _make_runtime_data(**overrides):
    """Build a HanchuessData with sensible defaults for fields a test doesn't set."""
    from custom_components.hanchuess.staging import SettingsStagingBuffer
    defaults = {
        "realtime": SimpleNamespace(data={}),
        "statistics": SimpleNamespace(data={}),
        "battery": None,
        "number_limits": {},
        "startup_values": {},
        "staging": SettingsStagingBuffer(),
        "control_registry": {},
        "inverter_device_id": "test_inverter_device_id",
    }
    defaults.update(overrides)
    return HanchuessData(**defaults)


async def test_entry_not_set_up_returns_only_entry_and_resolved():
    entry = _FakeEntry()
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert set(diag) == {"entry", "resolved"}
    assert "device_status" not in diag
    assert "statistics" not in diag


async def test_full_diagnostics_includes_all_sections():
    entry = _FakeEntry()
    entry.runtime_data = _make_runtime_data(
        realtime=SimpleNamespace(data={"batSoc": 55, "loadPwr": 800}),
        statistics=SimpleNamespace(data={"loadTdEe": 12.3}),
        battery=SimpleNamespace(data={"BAT-1": {"tBat1": 23.5, "sn": "BAT-1"}}),
        number_limits={"CHG_PWR_LMT": {"min": "0", "max": "5000"}},
        startup_values={"WORK_MODE_CMB": "1"},
    )
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert set(diag) == {
        "entry",
        "resolved",
        "device_status",
        "statistics",
        "battery",
        "number_limits",
        "startup_values",
    }
    assert diag["device_status"] == {"batSoc": 55, "loadPwr": 800}
    assert diag["statistics"] == {"loadTdEe": 12.3}
    assert diag["battery"]["coordinator_present"] is True
    assert diag["battery"]["configured_serial_count"] == 2
    assert diag["battery"]["payload_count"] == 1
    assert diag["battery"]["payload"]["battery_1"]["tBat1"] == 23.5
    assert diag["battery"]["payload"]["battery_1"]["sn"] == REDACTED
    assert diag["startup_values"] == {"WORK_MODE_CMB": "1"}


async def test_sensitive_keys_redacted_in_entry():
    entry = _FakeEntry()
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    entry_data = diag["entry"]["data"]
    assert entry_data["token"] == REDACTED
    assert entry_data["sn"] == REDACTED
    assert entry_data["account"] == REDACTED
    assert entry_data["stationId"] == REDACTED
    assert entry_data["battery_serials"] == REDACTED
    # title is in TO_REDACT, dev_type is not.
    assert diag["entry"]["title"] == REDACTED
    assert entry_data["dev_type"] == "2"


async def test_resolved_block_preserves_dev_type_redacts_sn():
    entry = _FakeEntry()
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["resolved"]["dev_type"] == "2"
    assert diag["resolved"]["sn"] == REDACTED


async def test_redaction_reaches_nested_coordinator_data():
    entry = _FakeEntry()
    entry.runtime_data = _make_runtime_data(
        realtime=SimpleNamespace(data={"sn": "SN123", "token": "leak", "batSoc": 55}),
    )
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["device_status"]["sn"] == REDACTED
    assert diag["device_status"]["token"] == REDACTED
    assert diag["device_status"]["batSoc"] == 55


async def test_number_limits_passed_through_unredacted():
    # number_limits is surfaced verbatim (not wrapped in async_redact_data), so
    # even a key that looks sensitive but is not in TO_REDACT stays intact.
    limits = {"CHG_PWR_LMT": {"min": "0", "max": "5000"}, "sn": "kept"}
    entry = _FakeEntry()
    entry.runtime_data = _make_runtime_data(number_limits=limits)
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["number_limits"] == limits


async def test_none_coordinator_data_becomes_empty_dict():
    entry = _FakeEntry()
    entry.runtime_data = _make_runtime_data(
        realtime=SimpleNamespace(data=None),
        statistics=SimpleNamespace(data=None),
    )
    hass = MagicMock()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["device_status"] == {}
    assert diag["statistics"] == {}


async def test_device_diagnostics_delegates_to_entry_diagnostics():
    entry = _FakeEntry()
    entry.runtime_data = _make_runtime_data(
        realtime=SimpleNamespace(data={"batSoc": 55}),
    )
    hass = MagicMock()
    device = MagicMock()

    entry_diag = await async_get_config_entry_diagnostics(hass, entry)
    device_diag = await async_get_device_diagnostics(hass, entry, device)

    assert device_diag == entry_diag
