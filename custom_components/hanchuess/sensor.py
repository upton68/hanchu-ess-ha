"""Sensor platform for Hanchuess."""
import json
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

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
    },
    "fast_charge_time_remaining": {
        "key": "testTimeRemain",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "min",
        "icon": "mdi:timer-outline",
    },
    "pv_power": {
        "key": "pvTtPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:solar-power",
        "auto_watt": True,
    },
    "grid_power": {
        "key": "meterPPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:transmission-tower",
        "auto_watt": True,
    },
    "load_power": {
        "key": "loadPwr",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:home-lightning-bolt",
        "auto_watt": True,
    },
    "dg_power": {
        "key": "dgPAcTotal",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:engine",
        "auto_watt": True,
        "condition_key": "hasDg",
        "condition_value": True,
    },
    "battery_capacity": {
        "key": "bmsDesignCap",
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

STATUS_MAP = {
    0: "offline",
    1: "online",
    99: "pending",
}


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
                    _LOGGER.error("Failed to parse work mode options")
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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = hass.data[DOMAIN][entry.entry_id]
    realtime = data["realtime"]
    statistics = data["statistics"]
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
    async_add_entities(entities)


class HanchueSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, sensor_key, config):
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._config = config
        self._attr_translation_key = sensor_key
        self._attr_unique_id = f"{entry.data['sn']}_{sensor_key}"
        self._attr_icon = config.get("icon")
        if "device_class" in config:
            self._attr_device_class = config["device_class"]
        if "state_class" in config:
            self._attr_state_class = config["state_class"]
        if "unit" in config:
            self._attr_native_unit_of_measurement = config["unit"]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._config["key"])
        if value is None:
            return None
        if self._config.get("auto_watt"):
            try:
                v = float(value)
                # API returns watts below 10, kW at 10 and above
                if abs(v) < 10:
                    return round(v * 1000, 1)
                else:
                    return round(v, 1)
            except (ValueError, TypeError):
                return None
        if "scale" in self._config:
            try:
                return round(float(value) * self._config["scale"], 1)
            except (ValueError, TypeError):
                return None
        return value


class DeviceStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "device_status"
    _attr_icon = "mdi:check-circle"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['sn']}_device_status"
        self._work_mode_options = []
        self._energy_fields = []
        self._menu_loaded = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
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
        attrs = {
            "sn": self._entry.data["sn"],
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
        sn = self._entry.data["sn"]
        menu_data = await self.coordinator.client.async_get_menu(sn, language)
        parsed = _parse_energy_menu(menu_data)
        if parsed["work_mode_options"]:
            self._work_mode_options = parsed["work_mode_options"]
            self._energy_fields = parsed["fields"]
            self._menu_loaded = True
