"""Select platform for Hanchuess - Work Mode control."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .models import inverter_model_name
from .const import DOMAIN
from . import HanchuessConfigEntry

_LOGGER = logging.getLogger(__name__)

WORK_MODES = {
    "Self-consumption": "1",
    "Backup Energy": "2",
    "User-defined": "3",
    "Off-grid": "4",
}

WORK_MODES_REVERSE = {v: k for k, v in WORK_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    startup_values = data.startup_values
    async_add_entities([WorkModeSelect(entry, startup_values)])


def _decode_work_mode(raw) -> str | None:
    """Decode a raw iotGet value to a work mode option name, or None on failure."""
    if raw is None:
        return None
    return WORK_MODES_REVERSE.get(str(raw).strip())


class WorkModeSelect(SelectEntity):
    """Work mode selector for Hanchuess."""

    _attr_has_entity_name = True
    _attr_name = "Work Mode"
    _attr_icon = "mdi:dip-switch"
    _attr_options = list(WORK_MODES.keys())
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, startup_values):
        self._entry = entry
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_work_mode"
        self._attr_current_option = _decode_work_mode(startup_values.get("WORK_MODE_CMB"))

    async def async_added_to_hass(self) -> None:
        """Register with the control registry for apply_iot_values support."""
        self._entry.runtime_data.control_registry["WORK_MODE_CMB"] = self

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
        mode = _decode_work_mode(raw)
        if mode is not None:
            self._attr_current_option = mode

    async def async_select_option(self, option: str) -> None:
        """Stage the work mode change; do not call iotSet directly."""
        value = WORK_MODES.get(option)
        if value is None:
            _LOGGER.error("[HANCHUESS] Unknown work mode: %s", option)
            return
        self._entry.runtime_data.staging.stage("WORK_MODE_CMB", value)
        self._attr_current_option = option
        self.async_write_ha_state()
        _LOGGER.info("[HANCHUESS] Work mode staged: %s (pending write)", option)
