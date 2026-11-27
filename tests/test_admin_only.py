"""Raw inverter writes are restricted to administrators (hacs/default#14998).

``hanchuess.device_control`` and the ``hanchuess/iot_set`` WebSocket command
forward caller-chosen key/value pairs straight to the inverter's iotSet, so a
non-admin user must be refused. Automations and scripts (no user on the
context) must keep working, as the Predbat bridge depends on them.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.core import Context, HomeAssistant  # noqa: E402
from homeassistant.exceptions import Unauthorized  # noqa: E402

from custom_components.hanchuess import (  # noqa: E402
    DOMAIN,
    SERVICE_DEVICE_CONTROL,
    async_setup,
    ws_iot_set,
)

DATA = {"sn": "SN1", "dev_type": "2", "value": {"WORK_MODE_CMB": "1"}}


@pytest.fixture
async def setup_hass(hass: HomeAssistant):
    await async_setup(hass, {})
    return hass


@pytest.fixture
def mock_control():
    with patch(
        "custom_components.hanchuess.async_device_control_service",
        AsyncMock(return_value={"success": True, "message": "ok"}),
    ) as control:
        yield control


async def test_device_control_refuses_non_admin_user(setup_hass, hass_read_only_user, mock_control):
    with pytest.raises(Unauthorized):
        await setup_hass.services.async_call(
            DOMAIN, SERVICE_DEVICE_CONTROL, DATA, blocking=True,
            context=Context(user_id=hass_read_only_user.id),
        )
    mock_control.assert_not_awaited()


async def test_device_control_allows_admin_user(setup_hass, hass_admin_user, mock_control):
    await setup_hass.services.async_call(
        DOMAIN, SERVICE_DEVICE_CONTROL, DATA, blocking=True,
        context=Context(user_id=hass_admin_user.id),
    )
    mock_control.assert_awaited_once()


async def test_device_control_allows_automations(setup_hass, mock_control):
    """Automations and scripts call services with no user on the context."""
    result = await setup_hass.services.async_call(
        DOMAIN, SERVICE_DEVICE_CONTROL, DATA, blocking=True, return_response=True,
    )
    mock_control.assert_awaited_once()
    assert result == {"success": True, "message": "ok"}


def test_iot_set_refuses_non_admin(hass: HomeAssistant):
    connection = MagicMock()
    connection.user.is_admin = False
    with pytest.raises(Unauthorized):
        ws_iot_set(hass, connection, {"id": 1, "type": "hanchuess/iot_set", **DATA})
