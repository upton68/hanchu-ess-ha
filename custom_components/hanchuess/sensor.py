"""Sensor platform for Hanchuess."""
import json
import logging
import re
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util
from .status import STATUS_OPTIONS, compute_inverter_status
from .models import (
    battery_model_name,
    inverter_model_name,
    lookup_battery_model,
)
from .const import DOMAIN
from . import HanchuessConfigEntry

_LOGGER = logging.getLogger(__name__)

SENSORS = {
    "battery_soc": {
        "key": "batSoc",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:battery",
        "scale": 100,
    },
    "battery_power": {
        "key": "batP",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-charging",
        "auto_watt": True,
        "unit_key": "batPUnit",
    },
    "battery_charge_power": {
        "key": "batP",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-plus",
        "auto_watt": True,
        "unit_key": "batPUnit",
        "derive_mode": "positive",
    },
    "battery_discharge_power": {
        "key": "batP",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-minus",
        "auto_watt": True,
        "unit_key": "batPUnit",
        "derive_mode": "negative_as_positive",
    },
    "fast_charge_time_remaining": {
        "key": "testTimeRemain",
        "name": "Fast Charge Time Remaining",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "s",
        "icon": "mdi:timer-outline",
    },
    "pv_power": {
        "key": "pvTtPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:solar-power",
        "auto_watt": True,
        "unit_key": "pvTtPwrUnit",
    },
    "grid_power": {
        "key": "meterPPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:transmission-tower",
        "auto_watt": True,
        "unit_key": "meterPPwrUnit",
    },
    "grid_import_power": {
        "key": "meterPPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:transmission-tower-import",
        "auto_watt": True,
        "unit_key": "meterPPwrUnit",
        "derive_mode": "positive",
    },
    "grid_export_power": {
        "key": "meterPPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:transmission-tower-export",
        "auto_watt": True,
        "unit_key": "meterPPwrUnit",
        "derive_mode": "negative_as_positive",
    },
    "load_power": {
        "key": "loadPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:home-lightning-bolt",
    },
    "dg_power": {
        "key": "dgPAcTotal",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:engine",
        "auto_watt": True,
        "unit_key": "dgPAcTotalUnit",
        "condition_key": "hasDg",
        "condition_value": True,
    },
    "battery_capacity": {
        "key": "bmsDesignCap",
        "name": "Battery Capacity",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:battery",
    },
    "ac_coupled_pv_power": {
        "key": "bypMeterTotalPower",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:solar-power",
        "auto_watt": True,
        "unit_key": "bypMeterTotalPowerUnit",
    },
}

STATISTICS_SENSORS = {
    "daily_load_energy": {
        "key": "load",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:home-lightning-bolt",
    },
    "daily_charge_energy": {
        "key": "batCharge",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:battery-plus",
    },
    "daily_discharge_energy": {
        "key": "batDisCharge",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:battery-minus",
    },
    "daily_pv_energy": {
        "key": "pv",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:solar-power",
    },
    "daily_grid_import": {
        "key": "gridImport",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:transmission-tower-import",
    },
    "daily_grid_export": {
        "key": "gridExport",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:transmission-tower-export",
    },
    "daily_dg_energy": {
        "key": "dgEp",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:engine",
        "condition_key": "hasDg",
        "condition_value": 1,
    },
}

BATTERY_SENSORS = {
    "battery_temperature_env": {
        "key": "tEnv",
        "precision": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_temperature_pack": {
        "key": "tPack",
        "precision": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_temperature_mos": {
        "key": "tMos",
        "precision": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_soc_pack": {
        "key": "socPack",
        "precision": 1,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
    },
    "battery_voltage": {
        "key": "vPack",
        "precision": 2,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
    },
    "battery_current": {
        "key": "iPack",
        "precision": 2,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
    },
    "battery_soh_pack": {
        "key": "sohPack",
        "precision": 0,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-heart-variant",
    },
    "battery_design_capacity": {
        "key": "designCapacity",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:battery-high",
    },
    "battery_full_capacity": {
        "key": "capFull",
        "precision": 1,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "Ah",
        "icon": "mdi:battery-arrow-up",
    },
    "battery_remaining_capacity": {
        "key": "capRemain",
        "precision": 2,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "Ah",
        "icon": "mdi:battery-arrow-down",
    },
}

# Cell-level voltage spread from queryBatteryDataDivisions. Created for a
# battery only when its data includes cell voltages. If a field is missing it is
# worked out from the individual cell voltages (vBat1..vBatN).
CELL_STAT_SENSORS = {
    "battery_cell_voltage_max": {
        "stat": "max",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "precision": 3,
        "icon": "mdi:arrow-collapse-up",
    },
    "battery_cell_voltage_min": {
        "stat": "min",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "precision": 3,
        "icon": "mdi:arrow-collapse-down",
    },
    "battery_cell_voltage_difference": {
        "stat": "diff",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "suggested_unit": UnitOfElectricPotential.MILLIVOLT,
        "precision": 0,
        "icon": "mdi:arrow-expand-vertical",
    },
}

STATUS_MAP = {
    0: "offline",
    1: "online",
    99: "pending",
}


def _scale_auto_watt(value, unit=None):
    """Normalise a power reading to watts.

    getDeviceStatus reports each power field in W or kW and, for most fields,
    carries a sibling ``<field>Unit`` string. When a unit is present we trust it
    (kW -> *1000, W -> unchanged). When it is absent or unrecognised we fall back
    to the legacy magnitude heuristic (|value| < 10 assumed to be kW). The
    fallback only matters for fields the API doesn't tag.
    """
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    if unit:
        u = str(unit).strip().lower()
        if u == "kw":
            return round(v * 1000, 1)
        if u == "w":
            return round(v, 1)
    if abs(v) < 10:  # legacy fallback: assume kW for small magnitudes
        return round(v * 1000, 1)
    return round(v, 1)


def _parse_energy_menu(menu_data: dict) -> dict:
    result = {"work_mode_options": [], "fields": []}
    data = menu_data.get("data", {})
    energy = data.get("energy")
    if not energy:
        for key, val in data.items():
            if isinstance(val, dict) and "energy" in key:
                energy = val
                break
    if not energy:
        return result
    for group in energy.get("items", []):
        for item in group:
            item_type = item.get("itemType")
            item_code = item.get("itemCode")
            signal = item.get("itemCodeSignal") or item.get("itemCode", "")
            if item_code in ("work_mode", "WORK_MODE_CMB") and item_type == "3":
                try:
                    options = json.loads(item.get("optVal", "[]"))
                    result["work_mode_options"] = [
                        {"label": opt["name"], "value": opt["value"], "signal": signal}
                        for opt in options
                    ]
                except (json.JSONDecodeError, KeyError):
                    _LOGGER.error("[HANCHUESS] Failed to parse work mode options")
                continue
            field = {"code": item_code, "signal": signal, "type": item_type, "name": item.get("itemName", "")}
            listener = item.get("listener")
            if item_type == "1":
                field["min"] = item.get("minVal", "")
                field["max"] = item.get("maxVal", "")
                def_fmt = item.get("defFmt", "")
                if def_fmt and "." in def_fmt:
                    decimals = len(def_fmt.split(".")[-1])
                    field["step"] = round(10 ** -decimals, decimals)
                else:
                    field["step"] = 1
            if item_type == "3":
                try:
                    field["options"] = json.loads(item.get("optVal", "[]"))
                except (json.JSONDecodeError, KeyError):
                    field["options"] = []
            if item_type == "4":
                field["onVal"] = item.get("onVal")
                field["offVal"] = item.get("offVal")
            if item_type == "6":
                field["format"] = item.get("defFmt", "HH:mm")
            if item.get("structure"):
                idx_map = {"charge_mode": 1, "chg_pwr_lmt": 2, "start_time": 3, "end_time": 4}
                children = []
                for child in item.get("structure"):
                    code = child.get("itemCode", "")
                    ct = child.get("itemType", "")
                    c = {"code": code, "type": ct if ct not in ("5", "6") else "5", "name": child.get("itemName", ""), "index": idx_map.get(code, 0)}
                    if ct == "1":
                        dv = child.get("defVal", "")
                        try:
                            bounds = json.loads(dv) if dv else []
                            c["min"] = str(bounds[0]) if len(bounds) > 0 else child.get("minVal", "0")
                            c["max"] = str(bounds[1]) if len(bounds) > 1 else child.get("maxVal", "99999")
                        except (json.JSONDecodeError, ValueError):
                            c["min"] = child.get("minVal", "0")
                            c["max"] = child.get("maxVal", "99999")
                        child_fmt = child.get("defFmt", "")
                        if child_fmt and "." in child_fmt:
                            dec = len(child_fmt.split(".")[-1])
                            c["step"] = round(10 ** -dec, dec)
                        else:
                            c["step"] = 1
                    if ct == "3":
                        try:
                            c["options"] = json.loads(child.get("optVal", "[]"))
                        except (json.JSONDecodeError, KeyError):
                            c["options"] = []
                    children.append(c)
                if item_type in ("82", "83") and item.get("itemCodeSignal"):
                    base_code = item_code.rstrip("0123456789")
                    base_name = field["name"].rstrip("0123456789").rstrip()
                    for i in range(3):
                        slot = {"code": f"{base_code}{i}", "signal": f"{signal}{i}" if not signal[-1].isdigit() else f"{signal[:-1]}{i}", "type": "collapse", "name": f"{base_name}{i + 1}", "children": children}
                        if listener:
                            slot["listener_code"] = listener.get("code", "")
                            slot["listener_show"] = listener.get("show", "")
                        if item.get("hidden"):
                            slot["hidden"] = True
                        result["fields"].append(slot)
                else:
                    field["type"] = "collapse"
                    field["children"] = children
                    if listener:
                        field["listener_code"] = listener.get("code", "")
                        field["listener_show"] = listener.get("show", "")
                    if item.get("hidden"):
                        field["hidden"] = True
                    result["fields"].append(field)
                continue
            if listener:
                field["listener_code"] = listener.get("code", "")
                field["listener_show"] = listener.get("show", "")
            if item.get("hidden"):
                field["hidden"] = True
            result["fields"].append(field)
    return result


def _derive_directional_power(value, mode):
    """Derive positive-directional power values from a signed source."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    if mode == "positive":
        result = round(max(v, 0), 1)
    elif mode == "negative_as_positive":
        result = round(max(-v, 0), 1)
    else:
        result = round(v, 1)
    return 0.0 if result == 0 else result


# --- PV strings (MPPT inputs) from getDeviceStatus pvListVo -------------------

_QUANTITY = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$")
_POWER_SCALE = {"": 1, "w": 1, "kw": 1000, "mw": 1_000_000}
_VOLTAGE_SCALE = {"": 1, "v": 1, "mv": 0.001, "kv": 1000}

# Below this string voltage, power / voltage isn't a meaningful current
# (panels at night or an unused input read a fraction of a volt).
PV_MIN_VOLTAGE_FOR_CURRENT = 10.0


def parse_quantity(value, scales: dict[str, float]):
    """Parse '1.23kW' / '850W' / '412.5V' (or a plain number) to base units."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _QUANTITY.match(str(value))
    if not match:
        return None
    factor = scales.get(match.group(2).lower())
    if factor is None:
        return None
    return float(match.group(1)) * factor


def pv_strings(realtime_data: dict | None) -> dict[str, dict]:
    """PV strings by name ('PV1', ...) -> {'power', 'voltage', 'current'}."""
    strings = {}
    for item in (realtime_data or {}).get("pvListVo") or []:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        power = parse_quantity(item.get("power"), _POWER_SCALE)
        voltage = parse_quantity(item.get("voltage"), _VOLTAGE_SCALE)
        current = None
        if power is not None and power <= 0:
            current = 0.0  # no output (e.g. after dark): no current, whatever the voltage
        elif power is not None and voltage is not None and voltage >= PV_MIN_VOLTAGE_FOR_CURRENT:
            current = round(power / voltage, 2)
        strings[name] = {
            "power": None if power is None else round(power, 1),
            "voltage": None if voltage is None else round(voltage, 1),
            "current": current,
        }
    return strings


PV_STRING_SENSORS = {
    "power": {
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "precision": 0,
        "icon": "mdi:solar-power",
    },
    "voltage": {
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "precision": 1,
        "icon": "mdi:solar-panel",
    },
    "current": {
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "precision": 2,
        "icon": "mdi:current-dc",
    },
}


def _ac_coupled(realtime_data: dict | None) -> bool:
    """bypMeterSwitch 1 = AC-coupled PV (PV inputs usually unused)."""
    try:
        return int((realtime_data or {}).get("bypMeterSwitch")) == 1
    except (TypeError, ValueError):
        return False


def _new_pv_string_sensors(realtime, entry, known: set[str]) -> list:
    """Sensors for PV strings in the realtime data that aren't in known."""
    pv_enabled = not _ac_coupled(realtime.data)
    return [
        PvStringSensor(realtime, entry, string_name, measure, pv_enabled)
        for string_name in pv_strings(realtime.data)
        if string_name not in known
        for measure in PV_STRING_SENSORS
    ]


def battery_power_w(battery_data: dict):
    """Battery power in watts: pack voltage x current.

    Positive = charging, negative = discharging (the sign of iPack), matching
    the inverter's Battery Power sensor.
    """
    voltage = _float_or_none(battery_data.get("vPack"))
    current = _float_or_none(battery_data.get("iPack"))
    if voltage is None or current is None:
        return None
    return round(voltage * current, 1)


def remaining_energy_kwh(battery_data: dict):
    """Energy left in the battery: SOC x Design Capacity (kWh)."""
    soc = _float_or_none(battery_data.get("socPack"))
    design = _float_or_none(battery_data.get("designCapacity"))
    if soc is None or design is None:
        return None
    return round(soc / 100 * design, 3)


def last_data_update(battery_data: dict):
    """When the battery's logger last uploaded data, as a UTC datetime."""
    stamp = _float_or_none(
        battery_data.get("dataTimeTs") or battery_data.get("latestDataTimeTs")
    )
    if stamp is None or stamp <= 0:
        return None
    return dt_util.utc_from_timestamp(stamp / 1000)


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cell_voltages(battery_data: dict) -> list[float]:
    """Individual cell voltages (vBat1..vBatN) that carry a number."""
    voltages = []
    for index in range(1, _battery_cell_count(battery_data) + 1):
        value = _float_or_none(battery_data.get(f"vBat{index}"))
        if value is not None:
            voltages.append(value)
    return voltages


def _battery_cell_count(battery_data: dict) -> int:
    """Number of cells to surface: numBat, or the vBatN fields present."""
    count = _float_or_none(battery_data.get("numBat"))
    if count is not None and count > 0:
        return int(count)
    index = 0
    while f"vBat{index + 1}" in battery_data:
        index += 1
    return index


def _has_cell_data(battery_data: dict) -> bool:
    return bool(
        _cell_voltages(battery_data)
        or battery_data.get("maxVoltage") is not None
        or battery_data.get("minVoltage") is not None
    )


def cell_voltage_stat(battery_data: dict, stat: str):
    """Max, min or difference of the cell voltages, in volts."""
    cells = _cell_voltages(battery_data)
    high = _float_or_none(battery_data.get("maxVoltage"))
    low = _float_or_none(battery_data.get("minVoltage"))
    if high is None and cells:
        high = max(cells)
    if low is None and cells:
        low = min(cells)
    if stat == "max":
        return high
    if stat == "min":
        return low
    diff = _float_or_none(battery_data.get("maxVoltageDifference"))
    if diff is None and high is not None and low is not None:
        diff = high - low
    return None if diff is None else round(diff, 4)


def _battery_temperature_count(battery_data: dict) -> int:
    """Return the number of tBat sensors to surface for a battery."""
    try:
        value = int(float(battery_data.get("numBatT")))
        return max(value, 0)
    except (TypeError, ValueError):
        return 4


def _battery_entities(entry, battery_coordinator) -> list:
    """Sensors for every battery serial on the entry."""
    entities = []
    if battery_coordinator and entry.data.get("battery_serials"):
        for battery_serial in entry.data.get("battery_serials", []):
            battery_data = battery_coordinator.data.get(battery_serial, {})
            for temp_index in range(1, _battery_temperature_count(battery_data) + 1):
                sensor_key = f"battery_temperature_{temp_index}"
                config = BATTERY_SENSORS.get(sensor_key, {
                    "key": f"tBat{temp_index}",
                    "name": f"Battery Temperature {temp_index}",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "unit": UnitOfTemperature.CELSIUS,
                    "precision": 1,
                })
                entities.append(
                    BatterySensor(battery_coordinator, entry, battery_serial, sensor_key, config)
                )
            entities.append(
                BatteryModelSensor(battery_coordinator, entry, battery_serial)
            )
            entities.append(BatteryStateSensor(battery_coordinator, entry, battery_serial))
            energy = getattr(getattr(entry, "runtime_data", None), "energy", None)
            if energy is not None:
                for sensor_key in BATTERY_ENERGY_SENSORS:
                    entities.append(
                        BatteryEnergySensor(energy, entry, battery_serial, sensor_key)
                    )
            for sensor_key, config in DERIVED_BATTERY_SENSORS.items():
                entities.append(
                    BatteryDerivedSensor(
                        battery_coordinator, entry, battery_serial, sensor_key, config
                    )
                )
            if _has_cell_data(battery_data):
                for sensor_key, config in CELL_STAT_SENSORS.items():
                    entities.append(
                        BatteryCellStatSensor(
                            battery_coordinator, entry, battery_serial, sensor_key, config
                        )
                    )
                for cell in range(1, _battery_cell_count(battery_data) + 1):
                    entities.append(
                        BatteryCellVoltageSensor(
                            battery_coordinator, entry, battery_serial, cell
                        )
                    )
            for sensor_key, config in BATTERY_SENSORS.items():
                if (
                    sensor_key.startswith("battery_temperature_")
                    and sensor_key.replace("battery_temperature_", "").isdigit()
                ):
                    continue
                entities.append(
                    BatterySensor(battery_coordinator, entry, battery_serial, sensor_key, config)
                )
    return entities


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    realtime = data.realtime
    statistics = data.statistics
    battery_coordinator = data.battery
    entities = []
    if realtime is None:
        # Battery-only station: no inverter sensors, settings or model sensors.
        async_add_entities(_battery_entities(entry, battery_coordinator))
        return
    entities.append(DeviceStatusSensor(realtime, entry))
    history = getattr(entry.runtime_data, "history", None)
    if history is not None:
        entities.extend(
            HistoryEnergySensor(history, entry, period, metric)
            for period in HISTORY_PERIODS
            for metric in HISTORY_METRICS
        )
    entities.append(InverterStatusSensor(realtime, entry))
    # One set of sensors per PV string the inverter reports. On AC-coupled
    # systems the inputs are usually unused, so they start disabled there.
    # The cloud can leave the string list out (seen overnight), so strings
    # that turn up after startup are added when they first appear.
    entities.extend(_new_pv_string_sensors(realtime, entry, set()))
    known_strings = set(pv_strings(realtime.data))

    @callback
    def _add_new_pv_strings() -> None:
        new = _new_pv_string_sensors(realtime, entry, known_strings)
        if new:
            known_strings.update(s._string_name for s in new)
            async_add_entities(new)

    remove = realtime.async_add_listener(_add_new_pv_strings)
    on_unload = getattr(entry, "async_on_unload", None)
    if callable(on_unload):
        on_unload(remove)
    for sensor_key, config in SENSORS.items():
        cond_key = config.get("condition_key")
        if cond_key:
            if realtime.data.get(cond_key) != config.get("condition_value"):
                continue
        entities.append(HanchueSensor(realtime, entry, sensor_key, config))
    for sensor_key, config in STATISTICS_SENSORS.items():
        cond_key = config.get("condition_key")
        if cond_key:
            if statistics.data.get(cond_key) != config.get("condition_value"):
                continue
        entities.append(HanchueSensor(statistics, entry, sensor_key, config))
    entities.extend(_battery_entities(entry, battery_coordinator))
    async_add_entities(entities)
    # Add the pending settings count sensor (no coordinator — driven by staging buffer)
    async_add_entities([HanchuessSettingsPendingSensor(entry)])
    # Static model/rating sensors, resolved once at setup from devModel
    async_add_entities(
        [
            HanchuessModelSensor(entry, "inverter_model"),
            HanchuessModelSensor(entry, "rated_ac_power"),
            HanchuessModelSensor(entry, "battery_power_max"),
        ]
    )


class HanchueSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, entry, sensor_key, config):
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._config = config
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_{sensor_key}"
        self._attr_icon = config.get("icon")
        self._attr_has_entity_name = True
        if "name" in config:
            self._attr_name = config["name"]
        else:
            self._attr_translation_key = sensor_key
        if "device_class" in config:
            self._attr_device_class = config["device_class"]
        if "state_class" in config:
            self._attr_state_class = config["state_class"]
        if "unit" in config:
            self._attr_native_unit_of_measurement = config["unit"]

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._config["key"])
        if value is None:
            return None
        if self._config.get("auto_watt"):
            unit = self.coordinator.data.get(self._config.get("unit_key"))
            value = _scale_auto_watt(value, unit)
            if value is None:
                return None
        if "scale" in self._config:
            try:
                value = round(float(value) * self._config["scale"], 1)
            except (ValueError, TypeError):
                return None
        derive_mode = self._config.get("derive_mode")
        if derive_mode:
            return _derive_directional_power(value, derive_mode)
        return value


class BatterySensor(CoordinatorEntity, SensorEntity):
    """Battery sensor entity backed by the battery data coordinator."""

    def __init__(self, coordinator, entry, battery_serial, sensor_key, config):
        super().__init__(coordinator)
        self._entry = entry
        self._battery_serial = battery_serial
        self._sensor_key = sensor_key
        self._config = config
        self._attr_unique_id = f"{battery_serial}_{sensor_key}"
        self._attr_icon = config.get("icon")
        self._attr_has_entity_name = True
        if "name" in config:
            self._attr_name = config["name"]
        else:
            self._attr_translation_key = sensor_key
        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        self._attr_native_unit_of_measurement = config.get("unit")
        if config.get("precision") is not None:
            self._attr_suggested_display_precision = config["precision"]

    @property
    def device_info(self) -> DeviceInfo:
        return _battery_device_info(self._entry, self.coordinator, self._battery_serial)

    @property
    def native_value(self):
        battery_data = self.coordinator.data.get(self._battery_serial, {})
        value = battery_data.get(self._config["key"])
        if value is None:
            return None
        try:
            return round(float(value), 3)
        except (ValueError, TypeError):
            return value


DERIVED_BATTERY_SENSORS = {
    "battery_power": {
        "derive": battery_power_w,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "precision": 0,
        "icon": "mdi:battery-charging",
    },
    "battery_remaining_energy": {
        "derive": remaining_energy_kwh,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "precision": 2,
        "icon": "mdi:battery-50",
    },
    "battery_last_data_update": {
        "derive": last_data_update,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "icon": "mdi:clock-check-outline",
        "diagnostic": True,
        "enabled_default": False,
    },
}


class PvStringSensor(HanchueSensor):
    """Power, voltage or (calculated) current of one PV string."""

    def __init__(self, coordinator, entry, string_name: str, measure: str, enabled: bool):
        slug = string_name.lower().replace(" ", "_")
        config = PV_STRING_SENSORS[measure]
        super().__init__(coordinator, entry, f"{slug}_{measure}", config)
        self._string_name = string_name
        self._measure = measure
        self._attr_translation_key = f"pv_string_{measure}"
        self._attr_translation_placeholders = {"string": string_name}
        self._attr_suggested_display_precision = config["precision"]
        self._attr_entity_registry_enabled_default = enabled

    @property
    def native_value(self):
        string = pv_strings(self.coordinator.data).get(self._string_name)
        return None if string is None else string[self._measure]


# Per-battery energy from the minute samples (HanchuessBatteryEnergyCoordinator).
BATTERY_ENERGY_SENSORS = {
    "battery_charge_today": {"field": "charge_today", "icon": "mdi:battery-arrow-up"},
    "battery_discharge_today": {"field": "discharge_today", "icon": "mdi:battery-arrow-down"},
    "battery_charge_total": {"field": "charge_total", "icon": "mdi:battery-arrow-up-outline"},
    "battery_discharge_total": {"field": "discharge_total", "icon": "mdi:battery-arrow-down-outline"},
}

# stateBat from the battery data.
BATTERY_STATES = {0: "idle", 1: "charging", 2: "discharging"}


class BatteryEnergySensor(CoordinatorEntity, SensorEntity):
    """Charge/discharge energy for one battery, today or in total."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, entry, battery_serial: str, sensor_key: str):
        super().__init__(coordinator)
        self._entry = entry
        self._battery_serial = battery_serial
        self._sensor_key = sensor_key
        self._field = BATTERY_ENERGY_SENSORS[sensor_key]["field"]
        self._attr_unique_id = f"{battery_serial}_{sensor_key}"
        self._attr_translation_key = sensor_key
        self._attr_icon = BATTERY_ENERGY_SENSORS[sensor_key]["icon"]

    @property
    def device_info(self) -> DeviceInfo:
        return _battery_device_info(
            self._entry, self._entry.runtime_data.battery, self._battery_serial
        )

    @property
    def native_value(self):
        state = (self.coordinator.data or {}).get(self._battery_serial)
        if not state or state.get("last_ts") is None:
            return None
        if self._field.endswith("_today") and state.get("day") != dt_util.now().date().isoformat():
            return 0.0  # no samples counted yet for the new day
        return round(float(state.get(self._field) or 0.0), 3)


class BatteryStateSensor(BatterySensor):
    """Idle, charging or discharging, from the battery's own state (stateBat)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(BATTERY_STATES.values())

    def __init__(self, coordinator, entry, battery_serial):
        super().__init__(
            coordinator, entry, battery_serial, "battery_state",
            {"key": "stateBat", "icon": "mdi:battery-sync"},
        )
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None

    @property
    def native_value(self):
        battery_data = (self.coordinator.data or {}).get(self._battery_serial) or {}
        try:
            return BATTERY_STATES.get(int(battery_data.get("stateBat")))
        except (TypeError, ValueError):
            pass
        # No stateBat in this payload: go by the current's direction.
        try:
            current = float(battery_data.get("iPack"))
        except (TypeError, ValueError):
            return None
        if current > 0.1:
            return "charging"
        if current < -0.1:
            return "discharging"
        return "idle"


# Station energy for this month, this year and in total (console Statistics).
HISTORY_PERIODS = {"month": "monthly", "year": "yearly", "lifetime": "lifetime"}
HISTORY_METRICS = {
    "pv": "mdi:solar-power",
    "load": "mdi:home-lightning-bolt",
    "grid_import": "mdi:transmission-tower-import",
    "grid_export": "mdi:transmission-tower-export",
    "battery_charge": "mdi:battery-arrow-up",
    "battery_discharge": "mdi:battery-arrow-down",
}


class HistoryEnergySensor(HanchueSensor):
    """Station energy for the current month, year or in total, from the cloud."""

    def __init__(self, coordinator, entry, period: str, metric: str):
        super().__init__(
            coordinator, entry, f"{HISTORY_PERIODS[period]}_{metric}_energy",
            {
                "device_class": SensorDeviceClass.ENERGY,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "icon": HISTORY_METRICS[metric],
            },
        )
        self._period = period
        self._metric = metric
        self._attr_suggested_display_precision = 1

    @property
    def native_value(self):
        figures = (self.coordinator.data or {}).get(self._period)
        if not figures:
            return None
        return figures.get(self._metric)


class BatteryDerivedSensor(BatterySensor):
    """A battery value worked out from the battery's own data."""

    def __init__(self, coordinator, entry, battery_serial, sensor_key, config):
        super().__init__(coordinator, entry, battery_serial, sensor_key, config)
        if config.get("diagnostic"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if config.get("enabled_default") is False:
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        battery_data = self.coordinator.data.get(self._battery_serial) or {}
        return self._config["derive"](battery_data)


class BatteryCellStatSensor(BatterySensor):
    """Highest cell voltage, lowest cell voltage or the spread between them."""

    def __init__(self, coordinator, entry, battery_serial, sensor_key, config):
        super().__init__(coordinator, entry, battery_serial, sensor_key, config)
        self._attr_suggested_display_precision = config.get("precision")
        if config.get("suggested_unit"):
            self._attr_suggested_unit_of_measurement = config["suggested_unit"]

    @property
    def native_value(self):
        battery_data = self.coordinator.data.get(self._battery_serial, {})
        return cell_voltage_stat(battery_data, self._config["stat"])


class BatteryCellVoltageSensor(BatterySensor):
    """One cell's voltage. Disabled by default: enable when investigating."""

    _attr_entity_registry_enabled_default = False
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator, entry, battery_serial, cell: int):
        super().__init__(
            coordinator,
            entry,
            battery_serial,
            f"battery_cell_voltage_{cell}",
            {
                "key": f"vBat{cell}",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfElectricPotential.VOLT,
                "icon": "mdi:battery-outline",
            },
        )
        self._attr_translation_key = "battery_cell_voltage"
        self._attr_translation_placeholders = {"cell": str(cell)}


class InverterStatusSensor(CoordinatorEntity, SensorEntity):
    """What the battery is doing now: fast, scheduled, charging, discharging or idle.

    Updates with the realtime coordinator and whenever the schedule
    coordinator reads new slot/work-mode values from the inverter.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "inverter_status"
    _attr_icon = "mdi:battery-sync"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUS_OPTIONS

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['sn']}_inverter_status"

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    def _schedule(self):
        data = getattr(self._entry, "runtime_data", None)
        return getattr(data, "schedule", None) if data is not None else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        schedule = self._schedule()
        if schedule is not None:
            self.async_on_remove(
                schedule.async_add_listener(self._handle_coordinator_update)
            )

    @property
    def native_value(self):
        realtime = self.coordinator.data or {}
        battery_power = _scale_auto_watt(realtime.get("batP"), realtime.get("batPUnit"))
        schedule = self._schedule()
        return compute_inverter_status(
            realtime,
            schedule.data if schedule is not None else None,
            dt_util.now().time(),
            battery_power,
        )

    @property
    def extra_state_attributes(self):
        schedule = self._schedule()
        if schedule is None or schedule.last_read is None:
            return None
        return {"schedule_last_read": schedule.last_read.isoformat()}


class DeviceStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "device_status"
    _attr_icon = "mdi:check-circle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_device_status"
        self._work_mode_options = []
        self._energy_fields = []
        self._menu_loaded = False

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get("devStatus")
        if value is None:
            return None
        try:
            return STATUS_MAP.get(int(value), "unknown")
        except (ValueError, TypeError):
            return "unknown"

    @property
    def extra_state_attributes(self):
        fast_chg = self.coordinator.data.get("deviceStatusOfTestFastChg")
        remain = self.coordinator.data.get("testTimeRemain")
        inverter_serial_number = self._entry.data["sn"]
        attrs = {
            "sn": inverter_serial_number,
            "energy_fields": self._energy_fields,
            "work_mode_options": self._work_mode_options,
        }
        if fast_chg is not None:
            attrs["fast_chg_status"] = fast_chg
        if remain is not None:
            attrs["fast_chg_remain"] = remain
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._refresh_menu()

    async def async_update(self) -> None:
        if not self._menu_loaded:
            await self._refresh_menu()
        await super().async_update()

    async def _refresh_menu(self) -> None:
        language = self.hass.config.language or "en"
        inverter_serial_number = self._entry.data["sn"]
        menu_data = await self.coordinator.client.async_get_menu(
            inverter_serial_number, language
        )
        parsed = _parse_energy_menu(menu_data)
        if parsed["work_mode_options"]:
            self._work_mode_options = parsed["work_mode_options"]
            self._energy_fields = parsed["fields"]
            self._menu_loaded = True



class HanchuessSettingsPendingSensor(SensorEntity):
    """Sensor that exposes the number of staged-but-unwritten settings changes.

    Driven by the SettingsStagingBuffer's on_change callback rather than a
    polling coordinator, so it updates immediately whenever a control entity
    stages a value or the buffer is cleared.
    """

    _attr_has_entity_name = True
    _attr_name = "Pending Changes"
    _attr_icon = "mdi:content-save-edit"
    _attr_state_class = None  # count, not a time-series measurement
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry) -> None:
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_pending_settings_changes"

    def _strategy_buffers(self) -> dict:
        """Weather Optimize / Octopus buffers, or {} when there are none."""
        strategy = getattr(self._entry.runtime_data, "strategy", None)
        staging = getattr(strategy, "staging", None)
        return staging if isinstance(staging, dict) else {}

    async def async_added_to_hass(self) -> None:
        """Register as the staging buffers' on_change callback."""
        self._entry.runtime_data.staging.set_on_change(self._on_staging_change)
        for buffer in self._strategy_buffers().values():
            buffer.set_on_change(self._on_staging_change)

    def _on_staging_change(self) -> None:
        """Called by a staging buffer whenever pending changes."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Number of staged settings not yet written or saved.

        A staged Strategy priority counts once per record it will be saved to.
        """
        return self._entry.runtime_data.staging.count + sum(
            buffer.count for buffer in self._strategy_buffers().values()
        )

    @property
    def extra_state_attributes(self) -> dict:
        buffers = self._strategy_buffers()
        attrs = {"inverter_settings": self._entry.runtime_data.staging.count}
        if "weather" in buffers:
            attrs["weather_optimize"] = buffers["weather"].count
        if "octopus" in buffers:
            attrs["octopus_strategy"] = buffers["octopus"].count
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )


_MODEL_SENSORS = {
    "inverter_model": {
        "name": "Inverter Model",
        "icon": "mdi:information-outline",
    },
    "rated_ac_power": {
        "name": "Rated AC Power",
        "icon": "mdi:flash",
        "attr": "ac_rating_w",
    },
    "battery_power_max": {
        "name": "Battery Power Maximum",
        "icon": "mdi:battery-arrow-up-outline",
        "attr": "battery_max_w",
    },
}


class HanchuessModelSensor(SensorEntity):
    """Static diagnostic sensors describing the identified inverter model.

    Values come from the model table in models.py, looked up once at setup
    from getDeviceStatus devModel. Rated AC Power is what Predbat calls
    inverter_limit; Battery Power Maximum is its battery_rate_max. They
    differ on single-phase 3.0K-6.0K units, whose battery stage is capped
    at 5000 W. All three read unknown if the model isn't recognised.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(self, entry, sensor_key: str) -> None:
        self._entry = entry
        self._sensor_key = sensor_key
        config = _MODEL_SENSORS[sensor_key]
        self._attr_name = config["name"]
        self._attr_icon = config["icon"]
        self._value_attr = config.get("attr")
        self._attr_unique_id = f"{entry.data['sn']}_{sensor_key}"
        if self._value_attr:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    @property
    def _model(self):
        return getattr(self._entry.runtime_data, "inverter_model", None)

    @property
    def native_value(self):
        model = self._model
        if model is None:
            return None
        if self._value_attr is None:
            return model.name
        return getattr(model, self._value_attr)

    @property
    def extra_state_attributes(self) -> dict:
        model = self._model
        if model is not None:
            return {"dev_model": model.code}
        realtime = getattr(self._entry.runtime_data, "realtime", None)
        data = getattr(realtime, "data", None) or {}
        return {"dev_model": data.get("devModel")}


def _battery_device_info(entry, coordinator, battery_serial: str) -> DeviceInfo:
    """DeviceInfo for one battery pack, with its model when recognised."""
    battery_data = (getattr(coordinator, "data", None) or {}).get(battery_serial, {})
    return DeviceInfo(
        identifiers={(DOMAIN, battery_serial)},
        via_device_id=entry.runtime_data.inverter_device_id,
        name=f"Hanchuess Battery {battery_serial}",
        manufacturer="Hanchu",
        model=battery_model_name(battery_data),
    )


class BatteryModelSensor(CoordinatorEntity, SensorEntity):
    """Battery pack model, from queryBatteryDataDivisions devModel.

    Shows the model name when the code is in the table in models.py, or the
    raw code otherwise so it can be reported and added. Attributes carry the
    raw code, the pack's software version, and whether it is a heated model
    where that is known.
    """

    _attr_has_entity_name = True
    _attr_name = "Battery Model"
    _attr_icon = "mdi:information-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, battery_serial: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._battery_serial = battery_serial
        self._attr_unique_id = f"{battery_serial}_battery_model"

    @property
    def device_info(self) -> DeviceInfo:
        return _battery_device_info(self._entry, self.coordinator, self._battery_serial)

    @property
    def _battery_data(self) -> dict:
        return (self.coordinator.data or {}).get(self._battery_serial, {}) or {}

    @property
    def native_value(self):
        dev_model = self._battery_data.get("devModel")
        model = lookup_battery_model(dev_model)
        if model is not None:
            return model.name
        if dev_model in (None, ""):
            return None
        return f"Unknown ({dev_model})"

    @property
    def extra_state_attributes(self) -> dict:
        data = self._battery_data
        model = lookup_battery_model(data.get("devModel"))
        attrs = {
            "dev_model": data.get("devModel"),
            "software_version": data.get("softwareVer"),
        }
        if model is not None:
            attrs["voltage_class"] = "HV" if model.high_voltage else "LV"
            if model.heated is not None:
                attrs["heated"] = model.heated
        return attrs
