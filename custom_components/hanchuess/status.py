"""Derive what the inverter is doing right now (the Inverter Status sensor).

The result is inferred from data the integration already has:

- Fast charge/discharge from the realtime ``deviceStatusOfTestFastChg`` field
  (1 = charging, 2 = discharging).
- Scheduled charge/discharge from the inverter's own work mode, slot times and
  SOC limits, read with iotGet by the schedule coordinator. These are read from
  the inverter rather than taken from this integration's control entities, so
  slots written by anything else (Predbat's Hanchu ESS integration, the Hanchu
  app, the web console) are seen too.
- Otherwise charging, discharging or idle from the sign of battery power.

"Scheduled" means the conditions for a scheduled charge or discharge are met;
the inverter itself doesn't report it.
"""
from __future__ import annotations

from datetime import time

FAST_CHARGING = "fast_charging"
FAST_DISCHARGING = "fast_discharging"
SCHEDULED_CHARGE = "scheduled_charge"
SCHEDULED_DISCHARGE = "scheduled_discharge"
CHARGING = "charging"
DISCHARGING = "discharging"
IDLE = "idle"

STATUS_OPTIONS = [
    FAST_CHARGING,
    FAST_DISCHARGING,
    SCHEDULED_CHARGE,
    SCHEDULED_DISCHARGE,
    CHARGING,
    DISCHARGING,
    IDLE,
]

USER_DEFINED_MODE = "3"

# Battery power within this many watts of zero counts as idle, so measurement
# noise doesn't flip the status between charging and discharging.
IDLE_DEADBAND_W = 20

CHARGE_SLOTS = [("TCT_START_%d" % n, "TCT_END_%d" % n) for n in (1, 2, 3)]
DISCHARGE_SLOTS = [("TDT_START_%d" % n, "TDT_END_%d" % n) for n in (1, 2, 3)]


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _seconds(value) -> int | None:
    number = _to_float(value)
    return None if number is None else int(number)


def slot_active(start, end, now_seconds: int) -> bool:
    """Return True if ``now_seconds`` falls inside the slot.

    Slot times are seconds since midnight. A slot is switched off only when
    both start and end are 0, so slots that start or end at midnight still
    count. A slot whose end is earlier than its start runs past midnight.
    """
    start_s = _seconds(start)
    end_s = _seconds(end)
    if start_s is None or end_s is None:
        return False
    if start_s == 0 and end_s == 0:
        return False
    if start_s == end_s:
        return False
    if start_s < end_s:
        return start_s <= now_seconds < end_s
    return now_seconds >= start_s or now_seconds < end_s


def _any_slot_active(schedule: dict, slots, now_seconds: int) -> bool:
    return any(
        slot_active(schedule.get(start), schedule.get(end), now_seconds)
        for start, end in slots
    )


def compute_inverter_status(
    realtime: dict | None,
    schedule: dict | None,
    now: time,
    battery_power_w: float | None,
) -> str | None:
    """Return one of STATUS_OPTIONS, or None if there is no realtime data."""
    if not realtime:
        return None

    fast = _seconds(realtime.get("deviceStatusOfTestFastChg"))
    if fast == 1:
        return FAST_CHARGING
    if fast == 2:
        return FAST_DISCHARGING

    schedule = schedule or {}
    mode = schedule.get("WORK_MODE_CMB", realtime.get("workModeCmb"))
    if mode is not None and str(mode).strip() == USER_DEFINED_MODE:
        now_seconds = now.hour * 3600 + now.minute * 60 + now.second
        soc_fraction = _to_float(realtime.get("batSoc"))
        soc = None if soc_fraction is None else soc_fraction * 100

        if _any_slot_active(schedule, CHARGE_SLOTS, now_seconds):
            charge_max = _to_float(schedule.get("DTU_AC_CHG_SOC_LMT"))
            if soc is None or charge_max is None or soc < charge_max:
                return SCHEDULED_CHARGE

        if _any_slot_active(schedule, DISCHARGE_SLOTS, now_seconds):
            discharge_min = _to_float(schedule.get("DSCHG_BAT_SOC_LMT"))
            if soc is None or discharge_min is None or soc > discharge_min:
                return SCHEDULED_DISCHARGE

    if battery_power_w is None:
        return IDLE
    if battery_power_w > IDLE_DEADBAND_W:
        return CHARGING
    if battery_power_w < -IDLE_DEADBAND_W:
        return DISCHARGING
    return IDLE
