"""Tests for the `hanchuess/iot_get` and `hanchuess/iot_set` WebSocket handlers.

Exercises the underlying async handler functions directly (via `__wrapped__`,
since `websocket_api.async_response` normally schedules them as a background
task rather than returning an awaitable), following the MagicMock/AsyncMock
style used in tests/test_device_control_service.py — no live `hass` instance
required.
"""
from __future__ import annotations

import inspect

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("homeassistant")

from custom_components.hanchuess import ws_iot_get, ws_iot_set
from custom_components.hanchuess.staging import SettingsStagingBuffer

# async_response (and require_admin on iot_set) wrap the handler; unwrap
# follows __wrapped__, preserved by functools.wraps, to the coroutine function.
_ws_iot_get = inspect.unwrap(ws_iot_get)
_ws_iot_set = inspect.unwrap(ws_iot_set)


def _make_entry(sn="SN1", staging=None):
    entry = MagicMock()
    entry.data = {"sn": sn}
    entry.runtime_data.control_registry = {}
    entry.runtime_data.staging = staging if staging is not None else SettingsStagingBuffer()
    return entry


def _make_msg(**overrides):
    msg = {"id": 1, "sn": "SN1", "dev_type": "2"}
    msg.update(overrides)
    return msg


# ---------------------------------------------------------------------------
# ws_iot_get (Load)
# ---------------------------------------------------------------------------

async def test_ws_iot_get_syncs_control_entities_on_success():
    coordinator = MagicMock()
    coordinator.client.async_iot_get = AsyncMock(
        return_value={"CHG_PWR_LMT": "2000", "WORK_MODE_CMB": "1"}
    )
    entry = _make_entry()
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ), patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        await _ws_iot_get(
            MagicMock(), connection, _make_msg(keys=["CHG_PWR_LMT", "WORK_MODE_CMB"])
        )

    mock_apply.assert_called_once_with(
        entry, {"CHG_PWR_LMT": "2000", "WORK_MODE_CMB": "1"}
    )
    connection.send_result.assert_called_once_with(
        1, {"CHG_PWR_LMT": "2000", "WORK_MODE_CMB": "1"}
    )


async def test_ws_iot_get_no_entry_skips_sync_without_raising():
    coordinator = MagicMock()
    coordinator.client.async_iot_get = AsyncMock(return_value={"CHG_PWR_LMT": "2000"})
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=None,
    ):
        await _ws_iot_get(MagicMock(), connection, _make_msg(keys=["CHG_PWR_LMT"]))

    connection.send_result.assert_called_once_with(1, {"CHG_PWR_LMT": "2000"})


async def test_ws_iot_get_device_not_found():
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=None,
    ), patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        await _ws_iot_get(MagicMock(), connection, _make_msg(sn="NOPE", keys=["CHG_PWR_LMT"]))

    connection.send_error.assert_called_once()
    mock_apply.assert_not_called()
    connection.send_result.assert_not_called()


# ---------------------------------------------------------------------------
# ws_iot_set (Set)
# ---------------------------------------------------------------------------

async def test_ws_iot_set_syncs_control_entities_on_success():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )
    staging = SettingsStagingBuffer()
    staging.stage("CHG_PWR_LMT", 1500)
    staging.stage("WORK_MODE_CMB", "2")
    entry = _make_entry(staging=staging)
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ), patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        await _ws_iot_set(
            MagicMock(), connection, _make_msg(value={"CHG_PWR_LMT": 2000})
        )

    mock_apply.assert_called_once_with(entry, {"CHG_PWR_LMT": 2000})
    # Overwritten key discarded; unrelated staged key survives.
    assert staging.pending == {"WORK_MODE_CMB": "2"}
    connection.send_result.assert_called_once_with(1, {})


async def test_ws_iot_set_no_entry_skips_sync_without_raising():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=None,
    ):
        await _ws_iot_set(
            MagicMock(), connection, _make_msg(value={"CHG_PWR_LMT": 2000})
        )

    connection.send_result.assert_called_once_with(1, {})


async def test_ws_iot_set_failure_does_not_sync_entities():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": False, "msg": "Device error"}
    )
    entry = _make_entry()
    connection = MagicMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ) as mock_find_entry, patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        await _ws_iot_set(
            MagicMock(), connection, _make_msg(value={"CHG_PWR_LMT": 2000})
        )

    connection.send_error.assert_called_once_with(1, "control_failed", "Device error")
    mock_find_entry.assert_not_called()
    mock_apply.assert_not_called()