"""Switch platform for Hanchuess - Fast charge and discharge controls."""
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .models import inverter_model_name
from .const import DOMAIN, CONF_FAST_CHARGE_DURATION, DEFAULT_FAST_CHARGE_DURATION
from . import HanchuessConfigEntry

_LOGGER = logging.getLogger(__name__)

# act values from Hanchu API:
# 2, -2 = fast charge, 3, -3 = fast discharge, 0 = stop


def _fast_charge_duration(entry) -> int:
    """Fast charge/discharge duration in seconds (option stored in minutes)."""
    return entry.options.get(
        CONF_FAST_CHARGE_DURATION, DEFAULT_FAST_CHARGE_DURATION
    ) * 60


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    client = data.realtime.client
    async_add_entities([
        FastChargeSwitch(client, entry),
        FastDischargeSwitch(client, entry),
    ])


class FastChargeSwitch(SwitchEntity):
    """Fast charge switch for Hanchuess."""

    _attr_has_entity_name = True
    _attr_name = "Fast Charge"
    _attr_icon = "mdi:battery-charging-high"

    def __init__(self, client, entry):
        self._client = client
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_fast_charge"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    async def async_turn_on(self, **kwargs) -> None:
        inverter_serial_number = self._entry.data["sn"]
        result = await self._client.async_fast_charge_discharge(
            inverter_serial_number, 2, _fast_charge_duration(self._entry)
        )
        if result.get("success"):
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.info("[HANCHUESS] Fast charge started for %s", inverter_serial_number)
        else:
            _LOGGER.error("[HANCHUESS] Fast charge failed: %s", result.get("msg"))

    async def async_turn_off(self, **kwargs) -> None:
        inverter_serial_number = self._entry.data["sn"]
        result = await self._client.async_fast_charge_discharge(
            inverter_serial_number, -2, 0
        )
        if result.get("success"):
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.info("[HANCHUESS] Fast charge stopped for %s", inverter_serial_number)
        else:
            _LOGGER.error("[HANCHUESS] Fast charge stop failed: %s", result.get("msg"))


class FastDischargeSwitch(SwitchEntity):
    """Fast discharge switch for Hanchuess."""

    _attr_has_entity_name = True
    _attr_name = "Fast Discharge"
    _attr_icon = "mdi:battery-arrow-down"

    def __init__(self, client, entry):
        self._client = client
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_fast_discharge"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    async def async_turn_on(self, **kwargs) -> None:
        inverter_serial_number = self._entry.data["sn"]
        result = await self._client.async_fast_charge_discharge(
            inverter_serial_number, 3, _fast_charge_duration(self._entry)
        )
        if result.get("success"):
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.info("[HANCHUESS] Fast discharge started for %s", inverter_serial_number)
        else:
            _LOGGER.error("[HANCHUESS] Fast discharge failed: %s", result.get("msg"))

    async def async_turn_off(self, **kwargs) -> None:
        inverter_serial_number = self._entry.data["sn"]
        result = await self._client.async_fast_charge_discharge(
            inverter_serial_number, -3, 0
        )
        if result.get("success"):
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.info("[HANCHUESS] Fast discharge stopped for %s", inverter_serial_number)
        else:
            _LOGGER.error("[HANCHUESS] Fast discharge stop failed: %s", result.get("msg"))
