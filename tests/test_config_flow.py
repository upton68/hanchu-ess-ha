"""Config-flow tests using the Home Assistant test harness.

These require `pytest-homeassistant-custom-component` (which provides the `hass`
fixture and custom-integration loading). The module skips if it is not installed.
"""
from unittest.mock import AsyncMock, patch

import pytest

# Skip on any platform without the HA test harness (e.g. Windows, where Home
# Assistant core cannot be imported). Guard the specific submodule we need so a
# partial/namespace remnant can't defeat the skip.
pytest.importorskip("pytest_homeassistant_custom_component.common")

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hanchuess.const import DOMAIN

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

CLIENT_PATH = "custom_components.hanchuess.config_flow.HanchuessApiClient"


def _patched_client(token="tok", devices=None):
    """Patch HanchuessApiClient in config_flow with a mock instance."""
    patcher = patch(CLIENT_PATH)
    mock_cls = patcher.start()
    instance = mock_cls.return_value
    instance.token = token
    instance.async_login = AsyncMock(return_value=token)
    instance.async_get_devices = AsyncMock(
        return_value=devices if devices is not None else []
    )
    return patcher, instance


async def test_user_flow_creates_entry(hass: HomeAssistant):
    patcher, _ = _patched_client(
        token="tok", devices=[{"sn": "SN1", "devType": "2"}]
    )
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"account": "a", "password": "p"}
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "select_device"

        # Creating the entry triggers integration setup; stub it so the test does
        # not perform real network/coordinator work.
        with patch(
            "custom_components.hanchuess.async_setup_entry", return_value=True
        ):
            result3 = await hass.config_entries.flow.async_configure(
                result2["flow_id"], {"devices": ["SN1"]}
            )
            await hass.async_block_till_done()
        assert result3["type"] == FlowResultType.CREATE_ENTRY
        assert result3["data"]["sn"] == "SN1"
        assert result3["data"]["dev_type"] == "2"
        assert result3["data"]["token"] == "tok"
    finally:
        patcher.stop()


async def test_user_flow_auth_failed(hass: HomeAssistant):
    patcher, instance = _patched_client()
    instance.async_login = AsyncMock(return_value=None)
    instance.token = None
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"account": "a", "password": "wrong"}
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "auth_failed"}
    finally:
        patcher.stop()


async def test_user_flow_no_devices(hass: HomeAssistant):
    patcher, _ = _patched_client(token="tok", devices=[])
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"account": "a", "password": "p"}
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "no_devices"}
    finally:
        patcher.stop()


async def test_reauth_flow_success(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"sn": "SN1", "token": "old"}, unique_id="SN1"
    )
    entry.add_to_hass(hass)

    patcher, _ = _patched_client(token="new-tok")
    try:
        # Avoid the real entry reload (which would attempt full integration setup).
        with patch.object(
            hass.config_entries, "async_reload", AsyncMock(return_value=True)
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_REAUTH,
                    "entry_id": entry.entry_id,
                },
                data=entry.data,
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth_confirm"

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"account": "a", "password": "p"}
            )
            assert result2["type"] == FlowResultType.ABORT
            assert result2["reason"] == "reauth_successful"

        # Token on the existing entry was updated.
        assert entry.data["token"] == "new-tok"
    finally:
        patcher.stop()
