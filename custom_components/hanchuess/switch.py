"""Switch platform for Hanchuess - Fast charge and discharge controls."""
import asyncio
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# act values from Hanchu API:
# 1 = fast charge, -1 = fast discharge, 0 = stop
FAST_CHARGE_DURATION = 60  # minutes


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["realtime"].client
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
        self._attr_unique_id = f"{entry.data['sn']}_fast_charge"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    async def async_turn_on(self, **kwargs) -> None:
        result = await self._client.async_fast_charge_discharge(
            self._entry.data["sn"], 2, FAST_CHARGE_DURATION
        )
        if result.get("success"):
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.info("Fast charge started for %s", self._entry.data["sn"])
        else:
            _LOGGER.error("Fast charge failed: %s", result.get("msg"))

    async def async_turn_off(self, **kwargs) -> None:
        result = await self._client.async_fast_charge_discharge(
            self._entry.data["sn"], -2, 0
        )
        if result.get("success"):
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.info("Fast charge stopped for %s", self._entry.data["sn"])
        else:
            _LOGGER.error("Fast charge stop failed: %s", result.get("msg"))


class FastDischargeSwitch(SwitchEntity):
    """Fast discharge switch for Hanchuess."""

    _attr_has_entity_name = True
    _attr_name = "Fast Discharge"
    _attr_icon = "mdi:battery-arrow-down"

    def __init__(self, client, entry):
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.data['sn']}_fast_discharge"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    async def async_turn_on(self, **kwargs) -> None:
        result = await self._client.async_fast_charge_discharge(
            self._entry.data["sn"], 3, FAST_CHARGE_DURATION
        )
        if result.get("success"):
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.info("Fast discharge started for %s", self._entry.data["sn"])
        else:
            _LOGGER.error("Fast discharge failed: %s", result.get("msg"))

    async def async_turn_off(self, **kwargs) -> None:
        result = await self._client.async_fast_charge_discharge(
            self._entry.data["sn"], -3, 0
        )
        if result.get("success"):
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.info("Fast discharge stopped for %s", self._entry.data["sn"])
        else:
            _LOGGER.error("Fast discharge stop failed: %s", result.get("msg"))
