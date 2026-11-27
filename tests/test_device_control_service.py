"""Tests for the `hanchuess.device_control` service response.

Exercises `async_device_control_service` directly (the module-level function the
service handler delegates to), following the MagicMock/AsyncMock style used in
tests/test_staged_write.py — no live `hass` instance required.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.core import SupportsResponse

from custom_components.hanchuess import (
    DOMAIN,
    SERVICE_DEVICE_CONTROL,
    async_device_control_service,
    async_setup,
)
from custom_components.hanchuess.staging import SettingsStagingBuffer


def _make_call(sn="SN1", dev_type="2", value=None):
    return SimpleNamespace(data={"sn": sn, "dev_type": dev_type, "value": value or {"WORK_MODE_CMB": "1"}})


def _make_entry(sn="SN1", staging=None):
    entry = MagicMock()
    entry.data = {"sn": sn}
    entry.runtime_data.control_registry = {}
    entry.runtime_data.staging = staging if staging is not None else SettingsStagingBuffer()
    return entry


async def test_device_control_service_success():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=None,
    ):
        result = await async_device_control_service(MagicMock(), _make_call())

    assert result == {"success": True, "message": "OK"}
    coordinator.client.async_device_control.assert_awaited_once_with(
        "SN1", "2", {"WORK_MODE_CMB": "1"}
    )


async def test_device_control_service_syncs_control_entities_on_success():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )
    entry = _make_entry()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ), patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        result = await async_device_control_service(
            MagicMock(), _make_call(value={"CHG_PWR_LMT": 2000})
        )

    assert result == {"success": True, "message": "OK"}
    mock_apply.assert_called_once_with(entry, {"CHG_PWR_LMT": 2000})


async def test_device_control_service_discards_stale_staged_keys_on_success():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )
    staging = SettingsStagingBuffer()
    staging.stage("CHG_PWR_LMT", 1500)
    staging.stage("WORK_MODE_CMB", "2")
    entry = _make_entry(staging=staging)

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ):
        await async_device_control_service(
            MagicMock(), _make_call(value={"CHG_PWR_LMT": 2000})
        )

    # The overwritten key is dropped; the unrelated staged key survives.
    assert staging.pending == {"WORK_MODE_CMB": "2"}


async def test_device_control_service_no_entry_skips_sync_without_raising():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": True, "data": {}}
    )

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=None,
    ):
        result = await async_device_control_service(MagicMock(), _make_call())

    assert result == {"success": True, "message": "OK"}


async def test_device_control_service_failure_does_not_sync_entities():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": False, "msg": "Device error"}
    )
    entry = _make_entry()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ), patch(
        "custom_components.hanchuess._find_entry",
        return_value=entry,
    ) as mock_find_entry, patch(
        "custom_components.hanchuess.button.apply_iot_values"
    ) as mock_apply:
        result = await async_device_control_service(MagicMock(), _make_call())

    assert result == {"success": False, "message": "Device error"}
    mock_find_entry.assert_not_called()
    mock_apply.assert_not_called()


async def test_device_control_service_device_rejects_write():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(
        return_value={"success": False, "msg": "Device error"}
    )

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ):
        result = await async_device_control_service(MagicMock(), _make_call())

    assert result == {"success": False, "message": "Device error"}


async def test_device_control_service_unknown_error_defaults_message():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock(return_value={"success": False})

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=coordinator,
    ):
        result = await async_device_control_service(MagicMock(), _make_call())

    assert result == {"success": False, "message": "Unknown error"}


async def test_device_control_service_device_not_found():
    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=None,
    ):
        result = await async_device_control_service(MagicMock(), _make_call(sn="NOPE"))

    assert result == {"success": False, "message": "Device NOPE not found"}


async def test_device_control_service_not_found_does_not_call_client():
    coordinator = MagicMock()
    coordinator.client.async_device_control = AsyncMock()

    with patch(
        "custom_components.hanchuess._find_realtime_coordinator",
        return_value=None,
    ):
        await async_device_control_service(MagicMock(), _make_call())

    coordinator.client.async_device_control.assert_not_awaited()


async def test_device_control_service_registered_with_optional_response():
    hass = MagicMock()
    hass.data = {}

    await async_setup(hass, {})

    device_control_calls = [
        call_args
        for call_args in hass.services.async_register.call_args_list
        if call_args.args[0] == DOMAIN and call_args.args[1] == SERVICE_DEVICE_CONTROL
    ]
    assert len(device_control_calls) == 1
    # Registered through async_register_admin_service, which passes the
    # schema and supports_response positionally.
    call_args = device_control_calls[0]
    assert SupportsResponse.OPTIONAL in (
        call_args.kwargs.get("supports_response"),
        *call_args.args[4:],
    )
