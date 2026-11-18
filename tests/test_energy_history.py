"""Tests for station Monthly / Yearly / Lifetime energy (pcs/historyStaticsChart)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hanchuess import sensor as sensor_mod
from custom_components.hanchuess.const import DOMAIN
from custom_components.hanchuess.coordinator import (
    HISTORY_FIELDS,
    HanchuessHistoryCoordinator,
    _sum_rows,
)
from custom_components.hanchuess.sensor import (
    HISTORY_METRICS,
    HISTORY_PERIODS,
    HistoryEnergySensor,
)


def _row(date, pv, load=0, imp=0, exp=0, chg=0, dschg=0):
    # Shaped like the console response; extra fields are ignored.
    return {"pvDge": pv, "loadEe": load, "gridTdEe": imp, "gridTdFe": exp,
            "batTdChg": chg, "batTdDschg": dschg, "date": date, "profit": "1.0",
            "acTdEe": 0.0, "geTotal": 0.0}


YEAR = [_row("2026-01", 85.8, 1056.14, 1072.27, 72.13, 607.4, 577.6),
        _row("2026-02", 116.18, 827.77, 895.24, 160.75, 514.0, 491.1),
        _row("2026-11", 10.5, 300.0, 310.0, 1.0, 200.0, 190.0)]
ALL = [_row("2025", 80.07, 865.65, 861.65, 59.97, 516.8, 500.7),
       _row("2026", 3981.65, 7669.16, 9892.61, 5840.7, 7744.9, 7380.5)]
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def _client(answers):
    client = MagicMock()
    client._reauth_triggered = False
    calls = []

    async def history(sn, date_str, language="en"):
        calls.append((sn, date_str))
        answer = answers[date_str]
        return answer.pop(0) if isinstance(answer, list) else answer

    client.async_get_station_history = AsyncMock(side_effect=history)
    client.calls = calls
    return client


def _entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="SN1", data={"sn": "SN1", "token": "tok"})
    entry.add_to_hass(hass)
    return entry


def test_sum_rows_ignores_bad_values():
    totals = _sum_rows([_row("a", 1.25), _row("b", "2.5"), {"pvDge": "x"}, {"pvDge": None}])
    assert totals["pv"] == 3.75
    assert set(totals) == set(HISTORY_FIELDS)


async def test_month_year_and_lifetime(hass: HomeAssistant):
    client = _client({"2026": {"code": 200, "data": YEAR}, "0": {"code": 200, "data": ALL}})
    coordinator = HanchuessHistoryCoordinator(hass, _entry(hass), client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        data = await coordinator._async_update_data()
    assert client.calls == [("SN1", "2026"), ("SN1", "0")]
    assert data["month_key"] == "2026-11"
    assert data["month"]["pv"] == 10.5
    assert data["month"]["battery_discharge"] == 190.0
    assert data["year"]["pv"] == round(85.8 + 116.18 + 10.5, 2)
    assert data["year"]["grid_import"] == round(1072.27 + 895.24 + 310.0, 2)
    assert data["lifetime"]["pv"] == round(80.07 + 3981.65, 2)
    assert data["lifetime"]["grid_export"] == round(59.97 + 5840.7, 2)


async def test_month_with_no_row_yet_is_zero(hass: HomeAssistant):
    client = _client({"2026": {"code": 200, "data": YEAR[:2]}, "0": {"code": 200, "data": ALL}})
    coordinator = HanchuessHistoryCoordinator(hass, _entry(hass), client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        data = await coordinator._async_update_data()
    assert data["month"] == {name: 0.0 for name in HISTORY_FIELDS}


async def test_keeps_previous_figures_when_a_call_fails(hass: HomeAssistant):
    client = _client({
        "2026": [{"code": 200, "data": YEAR}, {"code": 100, "success": False}],
        "0": [{"code": 200, "data": ALL}, {"code": 100, "success": False}],
    })
    coordinator = HanchuessHistoryCoordinator(hass, _entry(hass), client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        coordinator.data = await coordinator._async_update_data()
        data = await coordinator._async_update_data()
    assert data["month"]["pv"] == 10.5
    assert data["lifetime"]["pv"] == round(80.07 + 3981.65, 2)
    assert coordinator.errors == {"2026": "code=100 msg=None", "0": "code=100 msg=None"}


async def test_previous_month_not_carried_into_new_month(hass: HomeAssistant):
    client = _client({
        "2026": [{"code": 200, "data": YEAR}, {"code": 100}],
        "0": {"code": 200, "data": ALL},
    })
    coordinator = HanchuessHistoryCoordinator(hass, _entry(hass), client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        coordinator.data = await coordinator._async_update_data()
    december = NOW.replace(month=12, day=1)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=december):
        data = await coordinator._async_update_data()
    assert "month" not in data and "year" not in data  # unknown, not November's
    assert data["lifetime"]["pv"] > 0


async def test_update_failed_with_nothing(hass: HomeAssistant):
    client = _client({"2026": {"code": 100}, "0": {"code": 100}})
    coordinator = HanchuessHistoryCoordinator(hass, _entry(hass), client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_token_refresh_then_auth_failed(hass: HomeAssistant):
    entry = _entry(hass)
    client = _client({"2026": [{"_token_expired": True}, {"code": 200, "data": YEAR}],
                      "0": {"code": 200, "data": ALL}})
    client.async_refresh_token = AsyncMock(return_value="new")
    coordinator = HanchuessHistoryCoordinator(hass, entry, client)
    with patch("custom_components.hanchuess.coordinator.dt_util.now", return_value=NOW):
        data = await coordinator._async_update_data()
    assert data["month"]["pv"] == 10.5
    assert entry.data["token"] == "new"

    client = _client({"2026": {"_token_expired": True}, "0": {}})
    client.async_refresh_token = AsyncMock(return_value=None)
    coordinator = HanchuessHistoryCoordinator(hass, entry, client)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


def _sensor_entry():
    return SimpleNamespace(data={"sn": "SN1"}, runtime_data=SimpleNamespace(inverter_model=None))


def test_sensor_values_and_attributes():
    coordinator = MagicMock()
    coordinator.data = {"month": {"pv": 10.5}, "year": None}
    entry = _sensor_entry()
    with patch.object(sensor_mod, "inverter_model_name", return_value=None):
        month = HistoryEnergySensor(coordinator, entry, "month", "pv")
        assert month.native_value == 10.5
        assert month.unique_id == "SN1_monthly_pv_energy"
        assert month.translation_key == "monthly_pv_energy"
        assert month.state_class == "total_increasing"
        assert month.device_class == "energy"
        assert HistoryEnergySensor(coordinator, entry, "year", "pv").native_value is None
        assert HistoryEnergySensor(coordinator, entry, "lifetime", "load").native_value is None


async def test_api_payload_and_path():
    from custom_components.hanchuess.api import STATION_HISTORY_PATH, HanchuessApiClient
    from custom_components.hanchuess.crypto import _encrypt_payload

    client = HanchuessApiClient.__new__(HanchuessApiClient)
    client._request = AsyncMock(return_value={"code": 200, "data": []})
    await client.async_get_station_history("SN1", "0", "en")
    path, payload = client._request.await_args.args[:2]
    assert path == STATION_HISTORY_PATH == "/gateway/platform/pcs/historyStaticsChart"
    assert payload == _encrypt_payload(
        {"sn": "SN1", "devType": "2", "maxCount": 1440, "dateStr": "0", "masterSum": True}
    )
    assert "timezone" in client._request.await_args.kwargs["extra_headers"]


def test_translations_cover_history_sensors():
    base = Path(__file__).parents[1] / "custom_components" / "hanchuess" / "translations"
    for name in ("en.json", "zh-Hans.json"):
        data = json.loads((base / name).read_text(encoding="utf-8"))
        sensors = data["entity"]["sensor"]
        for prefix in HISTORY_PERIODS.values():
            for metric in HISTORY_METRICS:
                assert f"{prefix}_{metric}_energy" in sensors, (name, prefix, metric)
        assert "history_interval" in data["options"]["step"]["init"]["data"]
