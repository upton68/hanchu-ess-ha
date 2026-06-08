"""Select platform for Hanchuess - Work Mode control."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

WORK_MODES = {
    "Self-consumption": "1",
    "Backup Energy": "2",
    "User-defined": "3",
    "Off-grid": "4",
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["realtime"].client
    async_add_entities([WorkModeSelect(client, entry)])


class WorkModeSelect(SelectEntity):
    """Work mode selector for Hanchuess."""

    _attr_has_entity_name = True
    _attr_name = "Work Mode"
    _attr_icon = "mdi:dip-switch"
    _attr_options = list(WORK_MODES.keys())

    def __init__(self, client, entry):
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.data['sn']}_work_mode"
        self._attr_current_option = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    async def async_select_option(self, option: str) -> None:
        """Send work mode change to device."""
        value = WORK_MODES.get(option)
        if value is None:
            _LOGGER.error("Unknown work mode: %s", option)
            return
        result = await self._client.async_device_control(
            self._entry.data["sn"],
            "inverter",
            {"WORK_MODE_CMB": value},
        )
        if result.get("success"):
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Work mode set to %s", option)
        else:
            _LOGGER.error("Failed to set work mode: %s", result.get("msg"))
