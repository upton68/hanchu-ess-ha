"""Mocked unit tests for HanchuessApiClient.

These run fully offline — no live credentials, no Home Assistant — by mocking the
aiohttp layer with aioresponses. They pin the API client's behaviour and error
contract (see plans/P1-09-api-error-contract.md).
"""
import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.hanchuess.api import HanchuessApiClient, ReauthRequired
from custom_components.hanchuess.const import BASE_URL

LOGIN = f"{BASE_URL}/gateway/identify/auth/token"
REFRESH = f"{BASE_URL}/gateway/identify/auth/token/refresh"
DEVICE_LIST = f"{BASE_URL}/gateway/app/ha/getDeviceList"
STATUS = f"{BASE_URL}/gateway/app/ha/getDeviceStatus"
STATISTICS = f"{BASE_URL}/gateway/app/ha/getDeviceStatistics"
MENU = f"{BASE_URL}/gateway/app/ha/menu"
IOT_GET = f"{BASE_URL}/gateway/app/ha/iotGet"
IOT_SET = f"{BASE_URL}/gateway/app/ha/iotSet"
FAST = f"{BASE_URL}/gateway/app/ha/fastChargeDischarge"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success_sets_token():
    client = HanchuessApiClient(BASE_URL)
    with aioresponses() as m:
        m.post(LOGIN, payload={"success": True, "data": "tok-123"})
        token = await client.async_login("user", "pass")
    assert token == "tok-123"
    assert client.token == "tok-123"


async def test_login_failure_returns_none():
    client = HanchuessApiClient(BASE_URL)
    with aioresponses() as m:
        m.post(LOGIN, payload={"success": False, "msg": "bad creds"})
        token = await client.async_login("user", "wrong")
    assert token is None
    assert client.token is None


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

async def test_refresh_token_success():
    client = HanchuessApiClient(BASE_URL, token="old")
    with aioresponses() as m:
        m.post(REFRESH, payload={"success": True, "data": "new-tok"})
        new = await client.async_refresh_token(force=True)
    assert new == "new-tok"
    assert client.token == "new-tok"


async def test_refresh_token_code_100_raises_reauth():
    client = HanchuessApiClient(BASE_URL, token="old")
    with aioresponses() as m:
        m.post(REFRESH, payload={"success": False, "code": 100, "msg": "expired"})
        with pytest.raises(ReauthRequired):
            await client.async_refresh_token(force=True)


async def test_refresh_token_other_failure_returns_none():
    client = HanchuessApiClient(BASE_URL, token="old")
    with aioresponses() as m:
        m.post(REFRESH, payload={"success": False, "code": 500})
        result = await client.async_refresh_token(force=True)
    assert result is None


def test_should_refresh_token_fresh_is_false():
    client = HanchuessApiClient(BASE_URL, token="t")  # _token_time = now
    assert client.should_refresh_token() is False


def test_should_refresh_token_stale_is_true():
    client = HanchuessApiClient(BASE_URL, token="t")
    client._token_time = 0  # epoch — well past the refresh window
    assert client.should_refresh_token() is True


# ---------------------------------------------------------------------------
# Device list
# ---------------------------------------------------------------------------

async def test_get_devices_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(DEVICE_LIST, payload={"success": True, "data": [{"sn": "SN1"}]})
        devices = await client.async_get_devices()
    assert devices == [{"sn": "SN1"}]


async def test_get_devices_empty_on_unsuccess():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(DEVICE_LIST, payload={"success": False})
        devices = await client.async_get_devices()
    assert devices == []


# ---------------------------------------------------------------------------
# Device status / statistics — success, empty, token-expired
# ---------------------------------------------------------------------------

async def test_get_device_status_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(STATUS, payload={"success": True, "data": {"batSoc": 55}})
        data = await client.async_get_device_status("SN1")
    assert data == {"batSoc": 55}


async def test_get_device_status_empty_on_unsuccess():
    """Current contract: an unsuccessful response is indistinguishable from empty."""
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(STATUS, payload={"success": False})
        data = await client.async_get_device_status("SN1")
    assert data == {}


async def test_get_device_status_401_flags_token_expired():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(STATUS, status=401)
        data = await client.async_get_device_status("SN1")
    assert data == {"_token_expired": True}


async def test_get_device_statistics_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(STATISTICS, payload={"success": True, "data": {"load": 12.3}})
        data = await client.async_get_device_statistics("SN1")
    assert data == {"load": 12.3}


# ---------------------------------------------------------------------------
# Menu / iotGet
# ---------------------------------------------------------------------------

async def test_get_menu_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(MENU, payload={"code": 200, "data": {"energy": {}}})
        data = await client.async_get_menu("SN1")
    assert data.get("code") == 200
    assert "data" in data


async def test_get_menu_non_200_returns_empty():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(MENU, payload={"code": 500})
        data = await client.async_get_menu("SN1")
    assert data == {}


async def test_iot_get_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(IOT_GET, payload={"success": True, "data": {"WORK_MODE_CMB": "1"}})
        data = await client.async_iot_get("SN1", "2", ["WORK_MODE_CMB"])
    assert data == {"WORK_MODE_CMB": "1"}


# ---------------------------------------------------------------------------
# Device control (iotSet)
# ---------------------------------------------------------------------------

async def test_device_control_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(IOT_SET, payload={"success": True, "data": {}})
        result = await client.async_device_control("SN1", "2", {"CHG_PWR_LMT": 3000})
    assert result["success"] is True


async def test_device_control_failure_returns_msg():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(IOT_SET, payload={"success": False, "msg": "rejected"})
        result = await client.async_device_control("SN1", "2", {"CHG_PWR_LMT": 3000})
    assert result == {"success": False, "msg": "rejected"}


async def test_device_control_401_token_expired():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(IOT_SET, status=401)
        result = await client.async_device_control("SN1", "2", {"CHG_PWR_LMT": 3000})
    assert result == {"success": False, "msg": "token_expired"}


# ---------------------------------------------------------------------------
# Fast charge / discharge
# ---------------------------------------------------------------------------

async def test_fast_charge_success():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(FAST, payload={"success": True, "data": {}})
        result = await client.async_fast_charge_discharge("SN1", 2, 3600)
    assert result["success"] is True


async def test_fast_charge_code_100_device_error():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(FAST, payload={"code": 100, "msg": "Device busy"})
        result = await client.async_fast_charge_discharge("SN1", 2, 3600)
    assert result == {"success": False, "msg": "Device busy"}


async def test_fast_charge_401_token_expired():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(FAST, status=401)
        result = await client.async_fast_charge_discharge("SN1", 2, 3600)
    assert result == {"success": False, "msg": "token_expired"}


async def test_fast_charge_request_failed():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(FAST, status=500)  # unexpected status -> _request returns None
        result = await client.async_fast_charge_discharge("SN1", 2, 3600)
    assert result == {"success": False, "msg": "Request failed"}


# ---------------------------------------------------------------------------
# Transport failures (timeout / connection error) collapse to a safe default
# ---------------------------------------------------------------------------

async def test_timeout_returns_empty_device_list():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(DEVICE_LIST, exception=asyncio.TimeoutError())
        devices = await client.async_get_devices()
    assert devices == []


async def test_connection_error_returns_empty_device_list():
    client = HanchuessApiClient(BASE_URL, token="t")
    with aioresponses() as m:
        m.post(DEVICE_LIST, exception=aiohttp.ClientError())
        devices = await client.async_get_devices()
    assert devices == []
