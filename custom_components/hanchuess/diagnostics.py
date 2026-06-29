"""Diagnostics support for Hanchuess."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN

TO_REDACT = {"token", "account", "password", "sn", "stationId", "username", "pwd", "unique_id", "title"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag: dict[str, Any] = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "resolved": async_redact_data(
            {"dev_type": entry.data.get("dev_type"), "sn": entry.data.get("sn")},
            TO_REDACT,
        ),
    }

    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not store:
        # Entry not fully set up yet — return what we have so download never fails.
        return diag

    realtime = store.get("realtime")
    statistics = store.get("statistics")

    diag["device_status"] = async_redact_data(
        getattr(realtime, "data", None) or {}, TO_REDACT
    )
    diag["statistics"] = async_redact_data(
        getattr(statistics, "data", None) or {}, TO_REDACT
    )
    diag["number_limits"] = store.get("number_limits", {})
    diag["startup_values"] = async_redact_data(
        store.get("startup_values", {}) or {}, TO_REDACT
    )

    return diag


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device.

    One config entry maps to exactly one physical device (keyed by ``sn``), so the
    device diagnostics are the same as the config-entry diagnostics.
    """
    return await async_get_config_entry_diagnostics(hass, entry)
