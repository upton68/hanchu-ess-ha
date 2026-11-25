"""Time platform for Hanchuess - Charge and discharge time slot controls."""
import logging
from datetime import time
from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .models import inverter_model_name
from .const import DOMAIN
from . import HanchuessConfigEntry
from .strategy_entity import strategy_times

_LOGGER = logging.getLogger(__name__)


TIME_SLOTS = {
    "charge_slot_1_start": {
        "name": "Charge Slot 1 Start",
        "control_key": "TCT_START_1",
        "icon": "mdi:battery-clock",
    },
    "charge_slot_1_end": {
        "name": "Charge Slot 1 End",
        "control_key": "TCT_END_1",
        "icon": "mdi:battery-clock",
    },
    "charge_slot_2_start": {
        "name": "Charge Slot 2 Start",
        "control_key": "TCT_START_2",
        "icon": "mdi:battery-clock",
    },
    "charge_slot_2_end": {
        "name": "Charge Slot 2 End",
        "control_key": "TCT_END_2",
        "icon": "mdi:battery-clock",
    },
    "charge_slot_3_start": {
        "name": "Charge Slot 3 Start",
        "control_key": "TCT_START_3",
        "icon": "mdi:battery-clock",
    },
    "charge_slot_3_end": {
        "name": "Charge Slot 3 End",
        "control_key": "TCT_END_3",
        "icon": "mdi:battery-clock",
    },
    "discharge_slot_1_start": {
        "name": "Discharge Slot 1 Start",
        "control_key": "TDT_START_1",
        "icon": "mdi:battery-clock-outline",
    },
    "discharge_slot_1_end": {
        "name": "Discharge Slot 1 End",
        "control_key": "TDT_END_1",
        "icon": "mdi:battery-clock-outline",
    },
    "discharge_slot_2_start": {
        "name": "Discharge Slot 2 Start",
        "control_key": "TDT_START_2",
        "icon": "mdi:battery-clock-outline",
    },
    "discharge_slot_2_end": {
        "name": "Discharge Slot 2 End",
        "control_key": "TDT_END_2",
        "icon": "mdi:battery-clock-outline",
    },
    "discharge_slot_3_start": {
        "name": "Discharge Slot 3 Start",
        "control_key": "TDT_START_3",
        "icon": "mdi:battery-clock-outline",
    },
    "discharge_slot_3_end": {
        "name": "Discharge Slot 3 End",
        "control_key": "TDT_END_3",
        "icon": "mdi:battery-clock-outline",
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = entry.runtime_data
    client = data.realtime.client
    startup_values = data.startup_values

    entities = [
        HanchuessTimeSlot(entry, slot_key, config, startup_values)
        for slot_key, config in TIME_SLOTS.items()
    ]
    entities.extend(strategy_times(entry))
    async_add_entities(entities)


def _decode_time_value(raw) -> time:
    """Decode a raw iotGet seconds-since-midnight value to a time object."""
    if raw is None:
        return time(0, 0)
    try:
        total_seconds = int(float(raw))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return time(hours, minutes)
    except (ValueError, TypeError):
        return time(0, 0)


class HanchuessTimeSlot(TimeEntity):
    """Represents a charge or discharge time slot for Hanchuess."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, slot_key, config, startup_values):
        self._entry = entry
        self._config = config
        self._attr_name = config["name"]
        inverter_serial_number = entry.data["sn"]
        self._attr_unique_id = f"{inverter_serial_number}_{slot_key}"
        self._attr_icon = config["icon"]
        self._attr_native_value = _decode_time_value(
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
        self._attr_native_value = _decode_time_value(raw)

    async def async_set_value(self, value: time) -> None:
        """Stage the new slot time straight away.

        Nothing reaches the inverter until Write Settings, and the staging
        buffer keeps only the latest value per key, so rapid changes already
        coalesce. Staging late (the old 2 s debounce) let a Write Settings
        pressed straight after miss the change (#84).
        """
        seconds = (value.hour * 3600) + (value.minute * 60)
        self._entry.runtime_data.staging.stage(self._config["control_key"], seconds)
        self._attr_native_value = value
        self.async_write_ha_state()
        _LOGGER.info(
            "[HANCHUESS] %s staged: %s seconds (pending write)",
            self._config["name"],
            seconds,
        )
