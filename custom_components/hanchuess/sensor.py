"""Sensor platform for Hanchuess."""
import json
import logging
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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
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
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_temperature_pack": {
        "key": "tPack",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_temperature_mos": {
        "key": "tMos",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
    },
    "battery_soc_pack": {
        "key": "socPack",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
    },
    "battery_voltage": {
        "key": "vPack",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
    },
    "battery_current": {
        "key": "iPack",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
    },
    "battery_soh_pack": {
        "key": "sohPack",
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
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "Ah",
        "icon": "mdi:battery-arrow-up",
    },
    "battery_remaining_capacity": {
        "key": "capRemain",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "Ah",
        "icon": "mdi:battery-arrow-down",
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


def _battery_temperature_count(battery_data: dict) -> int:
    """Return the number of tBat sensors to surface for a battery."""
    try:
        value = int(float(battery_data.get("numBatT")))
        return max(value, 0)
    except (TypeError, ValueError):
        return 4


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    realtime = data.realtime
    statistics = data.statistics
    battery_coordinator = data.battery
    entities = []
    entities.append(DeviceStatusSensor(realtime, entry))
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
                })
                entities.append(
                    BatterySensor(battery_coordinator, entry, battery_serial, sensor_key, config)
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
    async_add_entities(entities)
    # Add the pending settings count sensor (no coordinator — driven by staging buffer)
    async_add_entities([HanchuessSettingsPendingSensor(entry)])


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
            model="ESS Device",
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

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, self._battery_serial)},
            via_device_id=self._entry.runtime_data.inverter_device_id,
            name=f"Hanchuess Battery {self._battery_serial}",
            manufacturer="Hanchu",
            model="Battery Pack",
        )

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
            model="ESS Device",
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

    async def async_added_to_hass(self) -> None:
        """Register as the staging buffer's on_change callback."""
        self._entry.runtime_data.staging.set_on_change(self._on_staging_change)

    def _on_staging_change(self) -> None:
        """Called by the staging buffer whenever pending changes."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Return the number of pending (unwritten) staged settings."""
        return self._entry.runtime_data.staging.count

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model="ESS Device",
        )
