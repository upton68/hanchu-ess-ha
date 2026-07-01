"""Time platform for Hanchuess - Charge and discharge time slot controls."""
import asyncio
import logging
from datetime import time
from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 2

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
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["realtime"].client
    startup_values = data.get("startup_values", {})

    entities = [
        HanchuessTimeSlot(client, entry, slot_key, config, startup_values)
        for slot_key, config in TIME_SLOTS.items()
    ]
    async_add_entities(entities)


class HanchuessTimeSlot(TimeEntity):
    """Represents a charge or discharge time slot for Hanchuess."""

    _attr_has_entity_name = True

    def __init__(self, client, entry, slot_key, config, startup_values):
        self._client = client
        self._entry = entry
        self._config = config
        self._attr_name = config["name"]
        self._attr_unique_id = f"{entry.data['sn']}_{slot_key}"
        self._attr_icon = config["icon"]
        self._debounce_task = None
        self._pending_value = None

        # Set initial value from startup read
        raw = startup_values.get(config["control_key"])
        if raw is not None:
            try:
                total_seconds = int(float(raw))
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                self._attr_native_value = time(hours, minutes)
            except (ValueError, TypeError):
                self._attr_native_value = time(0, 0)
        else:
            self._attr_native_value = time(0, 0)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["sn"])},
            name=f"Hanchuess {self._entry.data['sn']}",
            manufacturer="Hanchu",
            model="ESS Device",
        )

    async def async_set_value(self, value: time) -> None:
        """Debounce time slot changes to avoid multiple API calls."""
        self._pending_value = value
        self._attr_native_value = value
        self.async_write_ha_state()

        if self._debounce_task:
            self._debounce_task.cancel()

        self._debounce_task = asyncio.ensure_future(self._send_after_delay())

    async def _send_after_delay(self) -> None:
    """Wait for debounce period then send to API."""
    try:
        await asyncio.sleep(DEBOUNCE_SECONDS)
        value = self._pending_value
        if value is None:
            return
        seconds = (value.hour * 3600) + (value.minute * 60)
        result = await self._client.async_device_control(
            self._entry.data["sn"],
            "2",
            {self._config["control_key"]: seconds},
        )
        if result and result.get("success"):
            _LOGGER.info("%s set to %s seconds", self._config["name"], seconds)
            self._pending_value = None
        else:
            _LOGGER.error(
                "Failed to set %s: %s — reverting displayed state",
                self._config["name"],
                result.get("msg") if result else "no response",
            )
            self._pending_value = None
            self._attr_native_value = self._last_confirmed_value
            self.async_write_ha_state()
    except asyncio.CancelledError:
        pass
