"""Integration tests for HanchuessApiClient against real Hanchu cloud endpoints.

Requires environment variables:
  HANCHUESS_ACCOUNT   — Hanchu app email
  HANCHUESS_PASSWORD  — Hanchu app password

Device-specific tests also require:
  HANCHUESS_SN        — inverter serial number (tests skip if not set)
  HANCHUESS_DEV_TYPE  — device type, defaults to "2"

Write-path tests (device_control, fast_charge_discharge) require:
  HANCHUESS_ALLOW_WRITE=1  (not set by default to avoid unintended device changes)
"""
import os

import pytest
import pytest_asyncio

ACCOUNT = os.environ.get("HANCHUESS_ACCOUNT")
PASSWORD = os.environ.get("HANCHUESS_PASSWORD")

if not ACCOUNT or not PASSWORD:
    pytest.skip(
        "HANCHUESS_ACCOUNT and HANCHUESS_PASSWORD must be set to run integration tests",
        allow_module_level=True,
    )

from custom_components.hanchuess.api import HanchuessApiClient
from custom_components.hanchuess.const import BASE_URL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def client():
    """Return a logged-in HanchuessApiClient, shared for the entire module."""
    c = HanchuessApiClient(BASE_URL)
    token = await c.async_login(ACCOUNT, PASSWORD)
    assert token, (
        f"Login to {BASE_URL} failed for account {ACCOUNT!r}. "
        "Check the [HANCHUESS] log lines above for the server response or connection error."
    )
    return c


@pytest.fixture(scope="module")
def sn():
    value = os.environ.get("HANCHUESS_SN")
    if not value:
        pytest.skip("HANCHUESS_SN not set — skipping device-specific test")
    return value


@pytest.fixture(scope="module")
def dev_type():
    return os.environ.get("HANCHUESS_DEV_TYPE", "2")


@pytest.fixture(scope="module")
def allow_write():
    if not os.environ.get("HANCHUESS_ALLOW_WRITE"):
        pytest.skip("HANCHUESS_ALLOW_WRITE not set — skipping write-path test")


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

async def test_login_returns_token(client):
    assert isinstance(client.token, str)
    assert len(client.token) > 0


async def test_should_refresh_token_false_on_fresh_login(client):
    """A freshly issued token should not be flagged for refresh."""
    assert client.should_refresh_token() is False


async def test_refresh_token(client):
    """Refreshing a valid token should return a non-empty string."""
    new_token = await client.async_refresh_token(force=True)
    assert isinstance(new_token, str)
    assert len(new_token) > 0


# ---------------------------------------------------------------------------
# Device list
# ---------------------------------------------------------------------------

async def test_get_devices(client):
    devices = await client.async_get_devices()
    assert isinstance(devices, list)


# ---------------------------------------------------------------------------
# Device-specific read tests (require HANCHUESS_SN)
# ---------------------------------------------------------------------------

async def test_get_device_status(client, sn):
    data = await client.async_get_device_status(sn)
    assert isinstance(data, dict)
    assert "_token_expired" not in data


async def test_get_device_statistics(client, sn):
    data = await client.async_get_device_statistics(sn)
    assert isinstance(data, dict)
    assert "_token_expired" not in data


async def test_get_menu(client, sn):
    data = await client.async_get_menu(sn)
    assert isinstance(data, dict)
    assert "data" in data


async def test_iot_get(client, sn, dev_type):
    keys = [
        "WORK_MODE_CMB",
        "CHG_PWR_LMT",
        "DSCHG_PWR_LMT",
        "CHG_BAT_SOC_LMT",
        "DSCHG_BAT_SOC_LMT",
    ]
    data = await client.async_iot_get(sn, dev_type, keys)
    assert isinstance(data, dict)
    # At least one of the known keys should be present
    assert any(k in data for k in keys), f"None of {keys} found in iotGet response: {data}"


# ---------------------------------------------------------------------------
# Write-path tests (require HANCHUESS_SN + HANCHUESS_ALLOW_WRITE=1)
# ---------------------------------------------------------------------------

async def test_device_control_no_op(client, sn, dev_type, allow_write):
    """Read current work mode then write the same value back — net effect is zero."""
    current = await client.async_iot_get(sn, dev_type, ["WORK_MODE_CMB"])
    work_mode = current.get("WORK_MODE_CMB")
    assert work_mode is not None, "Could not read WORK_MODE_CMB for no-op write"

    result = await client.async_device_control(sn, dev_type, {"WORK_MODE_CMB": work_mode})
    assert result.get("success"), f"device_control failed: {result.get('msg')}"


async def test_fast_charge_stop_is_noop(client, sn, allow_write):
    """Sending stop-fast-charge (act=-2) is safe even when fast charge isn't running."""
    result = await client.async_fast_charge_discharge(sn, act=-2, duration=0)
    assert result.get("success"), f"fast_charge_discharge stop failed: {result.get('msg')}"
