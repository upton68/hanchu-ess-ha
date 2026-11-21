"""Weather Optimize and Octopus (Electricity Price Strategy) records.

The Hanchu cloud keeps these two strategies as records of their own, read and
written through dedicated endpoints rather than iotGet/iotSet. Every save
creates a new record, and a read returns the latest one.

This module has no Home Assistant dependencies so the merge rules can be
tested on their own. The rules (issue #72):

* A save always starts from the record read just before it, never from a
  cached copy, and only the staged fields are changed.
* Everything else is sent back exactly as it was read: unknown fields, every
  ``weathers[]`` and ``octopuses[]`` entry, the slot counts in Price mode and
  the prices in Point mode. Nothing is forced, including the enable flags.
* Values are written in the format the cloud used for that field (a string
  stays a string, a number stays a number).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

WEATHER = "weather"
OCTOPUS = "octopus"
KINDS = (WEATHER, OCTOPUS)

# Shared by both records and shown as one setting in the app.
PRIORITY_KEY = "weatherOctopusRepeatSelect"
PRIORITY_OPTIONS = {"Octopus": "1", "Weather Optimize": "2"}

# Staged keys for list entries: "soc:<band key>" and "slots:<timeStr>".
SOC_PREFIX = "soc:"
SLOTS_PREFIX = "slots:"


@dataclass(frozen=True)
class WeatherBand:
    """One weather condition in ``weathers[]`` (matched on code and cloud)."""

    key: str
    code: str
    cloud: str
    label: str


WEATHER_BANDS: tuple[WeatherBand, ...] = (
    WeatherBand("sunny", "100", "", "Sunny"),
    WeatherBand("few_clouds", "101", "11-25", "Few Clouds"),
    WeatherBand("partly_cloudy", "101", "26-50", "Partly Cloudy"),
    WeatherBand("mostly_cloudy", "101", "51-85", "Mostly Cloudy"),
    WeatherBand("heavy_clouds", "101", "86-100", "Heavy Clouds"),
    WeatherBand("light_rain", "305", "", "Light Rain"),
    WeatherBand("moderate_rain", "306", "", "Moderate Rain"),
    WeatherBand("heavy_rain", "307", "", "Heavy Rain"),
    WeatherBand("heavy_snow", "400", "", "Heavy Snow"),
    WeatherBand("haze_dust", "500", "", "Haze/Dust"),
    WeatherBand("other_weather", "1000", "", "Other Weather"),
)
WEATHER_BANDS_BY_KEY = {band.key: band for band in WEATHER_BANDS}

# The two Octopus Point-settings windows. Both are charge windows; ``num`` is
# the number of half-hour slots to charge in that window.
OCTOPUS_WINDOWS = ("00:00-08:00", "12:00-19:00")
OCTOPUS_SLOTS_MAX = 10
OCTOPUS_PRICE_MAX = 50
OCTOPUS_TYPES = {"Price settings": "1", "Point settings": "2"}

# Fields the server adds or needs that are not settings.
_NON_SETTING_FIELDS = ("id", "confirm", "sn")


def soc_key(band_key: str) -> str:
    return f"{SOC_PREFIX}{band_key}"


def slots_key(window: str) -> str:
    return f"{SLOTS_PREFIX}{window}"


def strategy_record(result: Any) -> dict | None:
    """The record from a read response, {} if none saved yet, None on failure."""
    if not isinstance(result, dict) or result.get("_token_expired"):
        return None
    if not (result.get("success") or result.get("code") == 200):
        return None
    data = result.get("data")
    if data is None:
        return {}
    return data if isinstance(data, dict) else None


def save_succeeded(result: Any) -> bool:
    return isinstance(result, dict) and bool(
        result.get("success") or result.get("code") == 200
    )


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------

def _to_str(value: Any) -> str:
    if isinstance(value, float):
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _like(existing: Any, value: Any) -> Any:
    """``value`` in the same format the cloud used for ``existing``."""
    if isinstance(existing, bool):
        return value
    if isinstance(existing, int):
        number = float(value)
        return int(number) if number.is_integer() else round(number, 2)
    if isinstance(existing, float):
        return round(float(value), 2)
    # Strings, and fields the record doesn't have yet (the cloud uses strings).
    return _to_str(value)


def _same_code(a: Any, b: str) -> bool:
    return str(a).strip() == b


def _same_cloud(a: Any, b: str) -> bool:
    return str(a or "").strip() == b


def find_weather_entry(record: dict | None, band: WeatherBand) -> dict | None:
    for item in (record or {}).get("weathers") or []:
        if (
            isinstance(item, dict)
            and _same_code(item.get("code"), band.code)
            and _same_cloud(item.get("cloud"), band.cloud)
        ):
            return item
    return None


def find_octopus_window(record: dict | None, window: str) -> dict | None:
    for item in (record or {}).get("octopuses") or []:
        if isinstance(item, dict) and str(item.get("timeStr", "")).strip() == window:
            return item
    return None


def record_value(record: dict | None, key: str) -> Any:
    """Read a field, a band's SOC (``soc:``) or a window's slots (``slots:``)."""
    if record is None:
        return None
    if key.startswith(SOC_PREFIX):
        band = WEATHER_BANDS_BY_KEY.get(key[len(SOC_PREFIX):])
        item = find_weather_entry(record, band) if band else None
        return item.get("soc") if item else None
    if key.startswith(SLOTS_PREFIX):
        item = find_octopus_window(record, key[len(SLOTS_PREFIX):])
        return item.get("num") if item else None
    return record.get(key)


# ---------------------------------------------------------------------------
# Merging staged changes into the latest record
# ---------------------------------------------------------------------------

def _list_code_like(items: list) -> Any:
    """A sample code from the list, so a new entry uses the same type."""
    for item in items:
        if isinstance(item, dict) and "code" in item:
            return item["code"]
    return "0"


def _merge_soc(payload: dict, band_key: str, value: Any) -> None:
    band = WEATHER_BANDS_BY_KEY.get(band_key)
    if band is None:
        return
    weathers = payload.get("weathers")
    if not isinstance(weathers, list):
        weathers = []
        payload["weathers"] = weathers
    item = find_weather_entry(payload, band)
    if item is not None:
        item["soc"] = _like(item.get("soc", ""), int(round(float(value))))
        return
    sample = _list_code_like(weathers)
    weathers.append({
        "code": _like(sample, band.code),
        "cloud": band.cloud,
        "soc": _to_str(int(round(float(value)))),
    })


def _merge_slots(payload: dict, window: str, value: Any) -> None:
    octopuses = payload.get("octopuses")
    if not isinstance(octopuses, list):
        octopuses = []
        payload["octopuses"] = octopuses
    item = find_octopus_window(payload, window)
    num = int(round(float(value)))
    if item is not None:
        item["num"] = _like(item.get("num"), num) if "num" in item else num
        return
    octopuses.append({"timeStr": window, "num": num})


def merge_record(record: dict | None, staged: dict, sn: str) -> dict:
    """The payload to save: ``record`` with ``staged`` applied.

    ``record`` must be the latest one read from the cloud. It is not changed.
    """
    payload = copy.deepcopy(record or {})
    for key, value in staged.items():
        if key.startswith(SOC_PREFIX):
            _merge_soc(payload, key[len(SOC_PREFIX):], value)
        elif key.startswith(SLOTS_PREFIX):
            _merge_slots(payload, key[len(SLOTS_PREFIX):], value)
        else:
            payload[key] = _like(payload.get(key), value)
    payload["sn"] = sn
    payload["confirm"] = "0"
    return payload


def _settings_only(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in _NON_SETTING_FIELDS}


def changes_applied(record: dict | None, staged: dict, sn: str) -> bool:
    """Whether ``record`` already holds every staged value.

    Used after a save whose response was lost or unclear, to tell whether the
    new record was created before giving up.
    """
    if record is None:
        return False
    merged = merge_record(record, staged, sn)
    return _settings_only(merged) == _settings_only(record)


# ---------------------------------------------------------------------------
# Decoding for entities
# ---------------------------------------------------------------------------

def decode_flag(raw: Any) -> bool | None:
    if raw is None or raw == "":
        return None
    return str(raw).strip() in ("1", "true", "True")


def decode_number(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def decode_hhmm(raw: Any) -> tuple[int, int] | None:
    """"HH:MM" to (hour, minute); 24:00 is read as 00:00."""
    if not isinstance(raw, str) or ":" not in raw:
        return None
    try:
        hour_text, minute_text = raw.strip().split(":", 1)
        hour, minute = int(hour_text), int(minute_text[:2])
    except ValueError:
        return None
    if hour == 24 and minute == 0:
        hour = 0
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return None
    return hour, minute


def encode_hhmm(hour: int, minute: int) -> str:
    return f"{hour:02d}:{minute:02d}"


def decode_option(raw: Any, options: dict[str, str]) -> str | None:
    if raw is None:
        return None
    code = str(raw).strip()
    for label, value in options.items():
        if value == code:
            return label
    return None
