"""Per-battery charge/discharge energy from the cloud's minute samples.

The Hanchu cloud keeps a minute-by-minute series per battery
(bmsInfo/powerMinuteChart): pack voltage, current and a timestamp. Energy is
the area under voltage x current over time. Positive current is charging,
negative is discharging, and the two are counted separately.

This module is pure calculation, with no Home Assistant code, so it can be
tested on its own. The battery energy coordinator fetches only the samples
since the last one counted and feeds them through ``add_samples``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# Samples further apart than this are a gap (e.g. the battery's WiFi logger
# dropped out). The gap is skipped rather than guessed.
MAX_GAP_MS = 5 * 60 * 1000

_MS_PER_HOUR = 3_600_000


@dataclass
class BatteryEnergyState:
    """Running energy totals for one battery."""

    day: str | None = None  # local date (ISO) that the "today" figures belong to
    charge_today: float = 0.0  # kWh
    discharge_today: float = 0.0  # kWh
    charge_total: float = 0.0  # kWh, never resets
    discharge_total: float = 0.0  # kWh, never resets
    last_ts: int | None = None  # ms timestamp of the last sample counted
    last_power: float | None = None  # W at that sample

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "BatteryEnergyState":
        state = cls()
        for field_name in asdict(state):
            if data and field_name in data:
                setattr(state, field_name, data[field_name])
        return state

    def start_day(self, day: str) -> None:
        """Begin a new local day: reset the daily figures, keep the totals."""
        self.day = day
        self.charge_today = 0.0
        self.discharge_today = 0.0


def _number(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sample_power(sample: dict) -> tuple[int, float] | None:
    """(timestamp ms, power W) for one minute sample, or None if unusable."""
    ts = _number(sample.get("dataTimeTs"))
    voltage = _number(sample.get("vPack"))
    current = _number(sample.get("iPack"))
    if ts is None or voltage is None or current is None:
        return None
    return int(ts), voltage * current


def segment_energy(p0: float, p1: float, hours: float) -> tuple[float, float]:
    """Charge and discharge kWh between two samples (trapezoid rule).

    If the power changes sign between the samples, the interval is split at
    the zero crossing so charging and discharging aren't netted off.
    """
    if hours <= 0:
        return 0.0, 0.0
    if (p0 >= 0) == (p1 >= 0):
        area_wh = (p0 + p1) / 2 * hours
        kwh = abs(area_wh) / 1000
        return (kwh, 0.0) if p0 + p1 >= 0 else (0.0, kwh)
    fraction = p0 / (p0 - p1)  # share of the interval before the crossing
    first = p0 / 2 * hours * fraction / 1000
    second = p1 / 2 * hours * (1 - fraction) / 1000
    charge = (first if first > 0 else 0.0) + (second if second > 0 else 0.0)
    discharge = (-first if first < 0 else 0.0) + (-second if second < 0 else 0.0)
    return charge, discharge


def add_samples(state: BatteryEnergyState, samples: list[dict]) -> int:
    """Count new samples into ``state``; returns how many were counted.

    Samples at or before ``state.last_ts`` are ignored, so overlapping fetches
    are safe. The first sample after a restart or a gap only sets the starting
    point.
    """
    points = sorted(
        (point for point in (sample_power(s) for s in samples or []) if point),
        key=lambda point: point[0],
    )
    counted = 0
    for ts, power in points:
        if state.last_ts is not None and ts <= state.last_ts:
            continue
        if state.last_ts is not None and state.last_power is not None:
            gap = ts - state.last_ts
            if gap <= MAX_GAP_MS:
                charge, discharge = segment_energy(
                    state.last_power, power, gap / _MS_PER_HOUR
                )
                state.charge_today += charge
                state.discharge_today += discharge
                state.charge_total += charge
                state.discharge_total += discharge
        state.last_ts = ts
        state.last_power = power
        counted += 1
    return counted
