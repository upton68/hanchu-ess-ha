"""Inverter model identification from the cloud's devModel code.

getDeviceStatus returns a numeric ``devModel`` code. The Hanchu web console
maps it to a model name with a table in its JavaScript bundle (``pcsEnMap``),
reproduced here. Confirmed on hardware for code 4 (HESS-HY-S-5.0K), where the
console's Inverter Information panel shows the same name.

Battery charge/discharge maximums and AC ratings come from Hanchu's product
manuals and datasheets:

- Single-phase HESS-HY-S-3.0K to 6.0K share one battery stage capped at
  5000 W (100 A), whatever their AC rating.
- Single-phase 7.0K/8.0K/10.0K and every three-phase and commercial model
  have a battery maximum equal to the AC rating.
- The 48 V HESS-HY-S-6K-S/12K-S datasheets give only charge currents, so no
  battery maximum is assumed for them.

Codes are not in size order (7.0K/8.0K/10.0K were added as 30-32), so this
must be a lookup, never an ordinal. Unknown codes return None and callers
fall back to the menu values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL_NAME = "ESS Device"


@dataclass(frozen=True)
class InverterModel:
    """A known inverter model and its power ratings."""

    code: int
    name: str
    ac_rating_w: int
    battery_max_w: int | None  # None when the manuals don't state one


def _same_as_ac(code: int, name: str, ac: int) -> InverterModel:
    return InverterModel(code, name, ac, ac)


INVERTER_MODELS: dict[int, InverterModel] = {
    m.code: m
    for m in (
        # Single-phase 3-6 kW: battery stage capped at 5000 W
        InverterModel(1, "HESS-HY-S-3.0K", 3000, 5000),
        InverterModel(2, "HESS-HY-S-3.68K", 3680, 5000),
        InverterModel(3, "HESS-HY-S-4.0K", 4000, 5000),
        InverterModel(4, "HESS-HY-S-5.0K", 5000, 5000),
        InverterModel(5, "HESS-HY-S-6.0K", 6000, 5000),
        # Three-phase
        _same_as_ac(6, "HESS-HY-T-05K", 5000),
        _same_as_ac(7, "HESS-HY-T-06K", 6000),
        _same_as_ac(8, "HESS-HY-T-08K", 8000),
        _same_as_ac(9, "HESS-HY-T-10K", 10000),
        _same_as_ac(10, "HESS-HY-T-12K", 12000),
        _same_as_ac(11, "HESS-HY-T-4K-M", 4000),
        _same_as_ac(12, "HESS-HY-T-5K-M", 5000),
        _same_as_ac(13, "HESS-HY-T-6K-M", 6000),
        _same_as_ac(14, "HESS-HY-T-8K-M", 8000),
        _same_as_ac(15, "HESS-HY-T-10K-M", 10000),
        _same_as_ac(16, "HESS-HY-T-12K-M", 12000),
        _same_as_ac(17, "HESS-HY-T-10K-M4", 10000),
        _same_as_ac(18, "HESS-HY-T-12K-M4", 12000),
        _same_as_ac(19, "HESS-HY-T-15K-M4", 15000),
        _same_as_ac(20, "HESS-HY-T-20K-M4", 20000),
        # Commercial
        _same_as_ac(21, "CESS-HY-25K", 25000),
        _same_as_ac(22, "CESS-HY-30K", 30000),
        _same_as_ac(23, "CESS-HY-36K", 36000),
        _same_as_ac(24, "CESS-HY-40K", 40000),
        _same_as_ac(25, "CESS-HY-50K", 50000),
        _same_as_ac(26, "CESS-HY-40K-P", 40000),
        _same_as_ac(27, "CESS-HY-50K-P", 50000),
        # 48 V single-phase: manuals give charge current only
        InverterModel(28, "HESS-HY-S-6K-S", 6000, None),
        InverterModel(29, "HESS-HY-S-12K-S", 12000, None),
        # Single-phase 7-10 kW (added later, out of size order)
        _same_as_ac(30, "HESS-HY-S-7.0K", 7000),
        _same_as_ac(31, "HESS-HY-S-8.0K", 8000),
        _same_as_ac(32, "HESS-HY-S-10.0K", 10000),
    )
}


def lookup_inverter_model(dev_model: Any) -> InverterModel | None:
    """Return the model for a getDeviceStatus ``devModel`` value, or None."""
    if dev_model is None or isinstance(dev_model, bool):
        return None
    try:
        code = int(str(dev_model).strip())
    except (TypeError, ValueError):
        return None
    return INVERTER_MODELS.get(code)


def apply_model_power_limits(
    number_limits: dict, model: InverterModel | None
) -> list[tuple[str, float, float]]:
    """Set the charge/discharge maximums from the model table, in place.

    The menu's single 0-5000 power entry is shared by the whole single-phase
    range, so it can't distinguish a 5 kW unit from a 10 kW one. Where the
    table states a battery maximum it wins. Returns (signal, menu_max,
    table_max) for every limit the table changed, so the caller can log it.
    """
    changed: list[tuple[str, float, float]] = []
    if model is None or model.battery_max_w is None:
        return changed
    for signal in ("CHG_PWR_LMT", "DSCHG_PWR_LMT"):
        limits = number_limits.get(signal)
        if limits is None:
            continue
        menu_max = float(limits.get("max", 0))
        table_max = float(model.battery_max_w)
        if menu_max != table_max:
            changed.append((signal, menu_max, table_max))
        limits["max"] = table_max
    return changed


def inverter_model_name(entry: Any) -> str:
    """Model name for an entry's DeviceInfo, or the generic default."""
    data = getattr(entry, "runtime_data", None)
    model = getattr(data, "inverter_model", None) if data is not None else None
    if isinstance(model, InverterModel):
        return model.name
    return DEFAULT_MODEL_NAME


# ---------------------------------------------------------------------------
# Battery packs
# ---------------------------------------------------------------------------

DEFAULT_BATTERY_MODEL_NAME = "Battery Pack"


@dataclass(frozen=True)
class BatteryModel:
    """A known battery pack model.

    ``heated`` is True/False only where it has been confirmed or follows
    directly from a confirmed sibling; None means not known.
    """

    code: str
    name: str
    high_voltage: bool
    heated: bool | None = None


def _battery(code: str, name: str, heated: bool | None = None) -> BatteryModel:
    return BatteryModel(code, name, "-HV-" in name.upper(), heated)


# queryBatteryDataDivisions returns a string devModel (e.g. "3_1"). The names
# are the Hanchu web console's own DevModel mapping. A "_n" suffix is a
# variant of the same pack: "3_1" is the heated Home-ESS-LV-9.4K (confirmed on
# hardware; Hanchu's heating settings call it HOME-ESS-LV-9.4K-H), so plain
# "3" is the unheated one. Other variants' differences aren't known yet.
BATTERY_MODELS: dict[str, BatteryModel] = {
    m.code: m
    for m in (
        _battery("1", "Home-ESS-LV-3.2K"),
        _battery("3", "Home-ESS-LV-9.4K", heated=False),
        _battery("3_1", "Home-ESS-LV-9.4K-H", heated=True),
        _battery("4", "Home-ESS-HV-2.7K"),
        _battery("4_1", "Home-ESS-HV-2.7K(RC)"),
        _battery("6", "Home-ESS-HV-5.3K"),
        _battery("7", "CESS-HV-9.4K"),
        _battery("8", "Home-ESS-LV-5.12K"),
        _battery("9", "Home-ESS-HV-5.12K"),
        _battery("10", "Home-ESS-LV-3.68K"),
        _battery("11", "HOME-ESS-LV-16K"),
        _battery("12", "HOME-ESS-LV-16K-S"),
        _battery("8_1", "HOME-ESS-LV-5.12K-M"),
        _battery("8_2", "HOME-ESS-LV-5.12K-M"),
    )
}


def lookup_battery_model(dev_model: Any) -> BatteryModel | None:
    """Return the battery model for a queryBatteryDataDivisions devModel."""
    if dev_model is None or isinstance(dev_model, bool):
        return None
    code = str(dev_model).strip()
    return BATTERY_MODELS.get(code)


def battery_model_name(battery_data: dict | None) -> str:
    """Model name for a battery pack's DeviceInfo, or the generic default."""
    model = lookup_battery_model((battery_data or {}).get("devModel"))
    return model.name if model is not None else DEFAULT_BATTERY_MODEL_NAME
