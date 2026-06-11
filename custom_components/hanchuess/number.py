"""Number platform for Hanchuess."""
import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfPower, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

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
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["realtime"].client
    number_limits = data.get("number_limits", {})
    startup_values = data.get("startup_values", {})
    entities = [
        HanchuessNumber(client, entry, number_key, config, number_limits, startup_values)
        for number_key, config in NUMBERS.items()
    ]
    async_add_entities(entities)


class HanchuessNumber(NumberEntity):
    """Represents a numeric control for Hanchuess."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(self, client, entry, number_key, config, number_limits, startup_values):
        self._client = client
        self._entry = entry
        self._config = config
        self._attr_name = config["name"]
        self._attr_unique_id = f"{entry.data['sn']}_{number_key}"
        self._attr_icon = config["icon"]
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_native_step = config.get("step", 1)

        # Use device-specific limits from menu, fall back to defaults
        limits = number_limits.get(config["control_key"], {})
        self._attr_native_min_value = limits.get("min", 0)
        self._attr_native_max_value = limits.get("max", 5000)

        # Set initial value from startup read
        value = startup_values.get(config["control_key"])
        if value is not None:
            try:
                self._attr_native_value = float(value)
            except (ValueError, TypeError):
                self._attr_native_value = None
        else:
            self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    async def async_set_native_value(self, value: float) -> None:
        result = await self._client.async_device_control(
            self._entry.data["sn"],
            "2",
            {self._config["control_key"]: int(value)},
        )
        if result.get("success"):
            self._attr_native_value = value
            self.async_write_ha_state()
            _LOGGER.info("%s set to %s", self._config["name"], value)
        else:
            _LOGGER.error(
                "Failed to set %s: %s", self._config["name"], result.get("msg")
            )
