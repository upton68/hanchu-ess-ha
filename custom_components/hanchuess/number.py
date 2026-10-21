"""Number platform for Hanchuess."""
import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfPower, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .models import inverter_model_name
from .const import DOMAIN
from . import HanchuessConfigEntry

_LOGGER = logging.getLogger(__name__)

NUMBERS = {
    "charge_power_limit": {
        "name": "Charge Power Limit",
        "control_key": "CHG_PWR_LMT",
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-charging",
        "step": 100,
    },
    "discharge_power_limit": {
        "name": "Discharge Power Limit",
        "control_key": "DSCHG_PWR_LMT",
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-arrow-down",
        "step": 100,
    },
    "max_charge_soc": {
        "name": "Maximum Charge SOC",
        "control_key": "CHG_BAT_SOC_LMT",
        "unit": PERCENTAGE,
        "icon": "mdi:battery-high",
        "step": 1,
    },
    "min_discharge_soc": {
        "name": "Minimum Discharge SOC",
        "control_key": "DSCHG_BAT_SOC_LMT",
        "unit": PERCENTAGE,
        "icon": "mdi:battery-low",
        "step": 1,
    },
    "grid_charge_soc_limit": {
        "name": "Grid to Battery Charge Maximum",
        "control_key": "DTU_AC_CHG_SOC_LMT",
        "unit": PERCENTAGE,
        "icon": "mdi:transmission-tower",
        "step": 1,
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    client = data.realtime.client
    number_limits = data.number_limits
    startup_values = data.startup_values
    entities = [
        HanchuessNumber(entry, number_key, config, number_limits, startup_values)
        for number_key, config in NUMBERS.items()
    ]
    async_add_entities(entities)


def _decode_number_value(raw) -> float | None:
    """Decode a raw iotGet value to a float, or None on failure."""
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


class HanchuessNumber(NumberEntity):
    """Represents a numeric control for Hanchuess."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, number_key, config, number_limits, startup_values):
        self._entry = entry
        self._config = config
        self._attr_name = config["name"]
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_{number_key}"
        self._attr_icon = config["icon"]
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_native_step = config.get("step", 1)

        # Use device-specific limits from menu, fall back to defaults
        limits = number_limits.get(config["control_key"], {})
        self._attr_native_min_value = limits.get("min", 0)
        self._attr_native_max_value = limits.get("max", 5000)

        # Set initial value from startup read
        self._attr_native_value = _decode_number_value(
            startup_values.get(config["control_key"])
        )

    async def async_added_to_hass(self) -> None:
        """Register with the control registry for apply_iot_values support."""
        self._entry.runtime_data.control_registry[self._config["control_key"]] = self

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    def apply_value(self, raw) -> None:
        """Apply a raw iotGet value to this entity's state (no HA state write)."""
        value = _decode_number_value(raw)
        if value is not None:
            self._attr_native_value = value

    async def async_set_native_value(self, value: float) -> None:
        """Stage the new value; do not call iotSet directly."""
        self._entry.runtime_data.staging.stage(
            self._config["control_key"], int(value)
        )
        self._attr_native_value = value
        self.async_write_ha_state()
        _LOGGER.info(
            "[HANCHUESS] %s staged: %s (pending write)",
            self._config["name"],
            value,
        )
