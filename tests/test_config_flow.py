"""Config-flow tests using the Home Assistant test harness.

These require `pytest-homeassistant-custom-component` (which provides the `hass`
fixture and custom-integration loading). The module skips if it is not installed.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip on any platform without the HA test harness (e.g. Windows, where Home
# Assistant core cannot be imported). Guard the specific submodule we need so a
# partial/namespace remnant can't defeat the skip.
pytest.importorskip("pytest_homeassistant_custom_component.common")

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.hanchuess as hanchuess
from custom_components.hanchuess.const import DOMAIN, WEB_CONSOLE_URL

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

CLIENT_PATH = "custom_components.hanchuess.config_flow.HanchuessApiClient"


@pytest.fixture(autouse=True)
def _bypass_card_dependencies(hass):
    """Skip dependency setup when the integration is loaded for the flow.

    The integration depends on frontend/http/websocket_api only to register the
    bundled Lovelace card; none are needed to exercise the config flow, and the
    HA test harness cannot set up `frontend`. Marking them as already loaded
    makes integration loading skip dependency setup.
    """
    for dep in ("http", "websocket_api", "frontend"):
        hass.config.components.add(dep)


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
    instance.async_get_device_status = AsyncMock(
        return_value={"stationId": "ST2503268043IE"}
    )
    instance.async_get_station_detail = AsyncMock(
        return_value={
            "code": 200,
            "data": {
                "bmsList": [
                    {"sn": "B007EN5811054"},
                    {"sn": "B002MU4810030"},
                ]
            },
        }
    )
    return patcher, instance


async def test_user_flow_creates_entry(hass: HomeAssistant):
    hass.config.language = "fr"
    patcher, instance = _patched_client(
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
        assert result3["data"]["stationId"] == "ST2503268043IE"
        assert result3["data"]["battery_serials"] == [
            "B007EN5811054",
            "B002MU4810030",
        ]
        instance.async_get_device_status.assert_awaited_once_with("SN1", "fr")
        instance.async_get_station_detail.assert_awaited_once_with("ST2503268043IE", "fr")
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


async def test_select_device_battery_lookup_failed_shows_console_hint(
    hass: HomeAssistant,
):
    """An empty station detail (account never used on the web console) shows
    battery_lookup_failed with the console URL placeholder filled in."""
    patcher, instance = _patched_client(
        token="tok", devices=[{"sn": "SN1", "devType": "2"}]
    )
    instance.async_get_station_detail = AsyncMock(return_value={})
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"account": "a", "password": "p"}
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"devices": ["SN1"]}
        )
        assert result3["type"] == FlowResultType.FORM
        assert result3["step_id"] == "select_device"
        assert result3["errors"] == {"base": "battery_lookup_failed"}
        assert result3["description_placeholders"] == {
            "console_url": WEB_CONSOLE_URL
        }
    finally:
        patcher.stop()


async def test_select_device_aborts_if_already_configured(hass: HomeAssistant):
    """A device that becomes configured between rendering and submitting the
    select_device form aborts instead of creating a duplicate entry.

    A second device (SN2) must stay available so the "no available devices"
    guard (config_flow.py's `if not available`) doesn't fire first and mask
    the unique-id abort this test targets.
    """
    patcher, _ = _patched_client(
        token="tok",
        devices=[{"sn": "SN1", "devType": "2"}, {"sn": "SN2", "devType": "2"}],
    )
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"account": "a", "password": "p"}
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "select_device"

        # Simulate SN1 becoming configured by another flow in the meantime.
        existing = MockConfigEntry(
            domain=DOMAIN, data={"sn": "SN1", "token": "tok"}, unique_id="SN1"
        )
        existing.add_to_hass(hass)

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"devices": ["SN1"]}
        )
        assert result3["type"] == FlowResultType.ABORT
        assert result3["reason"] == "already_configured"
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


async def test_import_flow_preserves_station_id(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "import"},
        data={
            "sn": "SN1",
            "dev_type": "2",
            "token": "tok",
            "stationId": "ST2503268043IE",
            "battery_serials": ["B007EN5811054", "B002MU4810030"],
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["stationId"] == "ST2503268043IE"
    assert result["data"]["battery_serials"] == [
        "B007EN5811054",
        "B002MU4810030",
    ]


async def test_options_flow_sets_options(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"sn": "SN1", "token": "tok"}, unique_id="SN1"
    )
    entry.add_to_hass(hass)

    # OptionsFlowWithReload schedules an entry reload on success; stub it so the
    # test does not perform real integration setup.
    with patch.object(hass.config_entries, "async_schedule_reload", MagicMock()):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "realtime_interval": 120,
                "statistics_interval": 600,
                "battery_interval": 900,
                "fast_charge_duration": 45,
            },
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        "realtime_interval": 120,
        "statistics_interval": 600,
        "battery_interval": 900,
        "fast_charge_duration": 45,
    }


async def test_options_flow_rejects_out_of_range(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"sn": "SN1", "token": "tok"}, unique_id="SN1"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    # realtime_interval below the configured minimum (30) is rejected by the
    # voluptuous Range validator before the entry is updated.
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "realtime_interval": 10,
                "statistics_interval": 600,
                "fast_charge_duration": 45,
            },
        )

    assert entry.options == {}


async def test_setup_entry_refreshes_battery_serials(hass: HomeAssistant):
    hass.config.language = "fr"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "sn": "SN1",
            "token": "tok",
            "stationId": "ST2503268043IE",
            "battery_serials": ["B1"],
        },
        unique_id="SN1",
    )
    entry.add_to_hass(hass)

    client = MagicMock()
    client.async_get_station_detail = AsyncMock(
        return_value={
            "success": True,
            "data": {"bmsList": [{"sn": "B1"}, {"sn": "B2"}]},
        }
    )
    client.async_get_device_status = AsyncMock(return_value={"devStatus": 1})
    client.async_get_device_statistics = AsyncMock(return_value={"load": 1})
    client.async_get_menu = AsyncMock(return_value={"code": 200, "data": {}})
    client.async_iot_get = AsyncMock(return_value={})
    client.async_get_battery_data = AsyncMock(
        side_effect=lambda serial, language="en": {
            "success": True,
            "data": {"sn": serial, "language": language},
        }
    )
    client.should_refresh_token.return_value = False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["_client"] = client

    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
        result = await hanchuess.async_setup_entry(hass, entry)

    assert result is True
    assert entry.data["battery_serials"] == ["B1", "B2"]
    client.async_get_station_detail.assert_awaited_once_with("ST2503268043IE", "fr")
    client.async_get_battery_data.assert_any_await("B1", "fr")


async def test_setup_entry_backfills_station_id(hass: HomeAssistant):
    hass.config.language = "fr"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "sn": "SN1",
            "token": "tok",
            "battery_serials": ["B1"],
        },
        unique_id="SN1",
    )
    entry.add_to_hass(hass)

    client = MagicMock()
    client.async_get_device_status = AsyncMock(return_value={"stationId": "ST2503268043IE"})
    client.async_get_station_detail = AsyncMock(
        return_value={"success": True, "data": {"bmsList": [{"sn": "B1"}, {"sn": "B2"}]}}
    )
    client.async_get_device_statistics = AsyncMock(return_value={"load": 1})
    client.async_get_menu = AsyncMock(return_value={"code": 200, "data": {}})
    client.async_iot_get = AsyncMock(return_value={})
    client.async_get_battery_data = AsyncMock(
        side_effect=lambda serial, language="en": {
            "success": True,
            "data": {"sn": serial, "language": language},
        }
    )
    client.should_refresh_token.return_value = False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["_client"] = client

    with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
        result = await hanchuess.async_setup_entry(hass, entry)

    assert result is True
    assert entry.data["stationId"] == "ST2503268043IE"
    assert entry.data["battery_serials"] == ["B1", "B2"]
    client.async_get_device_status.assert_awaited_once_with("SN1", "fr")
    client.async_get_station_detail.assert_awaited_once_with("ST2503268043IE", "fr")
    client.async_get_battery_data.assert_any_await("B1", "fr")
