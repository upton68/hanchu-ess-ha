"""Entities for the Weather Optimize and Octopus strategies (issue #72).

All are disabled by default and on the inverter device. A change is staged in
the strategy's own buffer and saved with that strategy's Save button; while a
field is staged, its entity shows the staged value, so a poll cannot undo it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time as dt_time
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.text import TextEntity
from homeassistant.components.time import TimeEntity
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .models import inverter_model_name
from .strategy import (
    OCTOPUS,
    OCTOPUS_PRICE_MAX,
    OCTOPUS_SLOTS_MAX,
    OCTOPUS_TYPES,
    OCTOPUS_WINDOWS,
    PRIORITY_KEY,
    PRIORITY_OPTIONS,
    WEATHER,
    WEATHER_BANDS,
    decode_flag,
    decode_hhmm,
    decode_number,
    decode_option,
    encode_hhmm,
    has_settings,
    record_value,
    slots_key,
    soc_key,
)

_LOGGER = logging.getLogger(__name__)

PRICE_UNIT = "p/kWh"


@dataclass(frozen=True)
class StrategyField:
    """One setting: which record(s) it lives in and its key there."""

    key: str          # unique-id suffix
    name: str
    icon: str
    kinds: tuple[str, ...]
    field: str
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    unit: str | None = None
    options: dict[str, str] | None = None
    # Switches whose meaning depends on the Octopus Schema Type: type code
    # ("1" Price, "2" Point settings) -> what the switch turns on in it.
    applies_to: dict[str, str] | None = None


SWITCHES = (
    StrategyField("weather_optimize", "Weather Optimize", "mdi:weather-partly-cloudy",
                  (WEATHER,), "weatherOpen"),
    StrategyField("octopus_strategy", "Octopus Strategy", "mdi:cash-clock",
                  (OCTOPUS,), "octopusOpen"),
    # The same two fields switch the windows in Point settings and the price
    # strategies in Price settings; the unique ids keep their original keys.
    StrategyField("octopus_charge", "Octopus Switch 00:00-08:00 / Charge Price",
                  "mdi:battery-charging", (OCTOPUS,), "octopusPriceEnable",
                  applies_to={
                      OCTOPUS_TYPES["Point settings"]: "Charge slots 00:00-08:00",
                      OCTOPUS_TYPES["Price settings"]: "Charging Price strategy",
                  }),
    StrategyField("octopus_discharge", "Octopus Switch 12:00-19:00 / Discharge Price",
                  "mdi:toggle-switch-outline", (OCTOPUS,), "octopusDischargeEnable",
                  applies_to={
                      OCTOPUS_TYPES["Point settings"]: "Charge slots 12:00-19:00",
                      OCTOPUS_TYPES["Price settings"]: "Discharge Price strategy",
                  }),
)

OCTOPUS_TYPE_FIELD = "octopusType"

TIMES = (
    StrategyField("weather_charge_start", "Weather Charge Start", "mdi:clock-start",
                  (WEATHER,), "weatherChargeTimeStart"),
    StrategyField("weather_charge_end", "Weather Charge End", "mdi:clock-end",
                  (WEATHER,), "weatherChargeTimeEnd"),
)


def _window_key(window: str) -> str:
    return window.replace(":", "").replace("-", "_")


NUMBERS = (
    *(
        StrategyField(f"weather_soc_{band.key}", f"Weather SOC {band.label}",
                      "mdi:battery-high", (WEATHER,), soc_key(band.key),
                      0, 100, 1, PERCENTAGE)
        for band in WEATHER_BANDS
    ),
    *(
        StrategyField(f"octopus_charge_slots_{_window_key(window)}",
                      f"Octopus Charge Slots {window}", "mdi:timer-sand",
                      (OCTOPUS,), slots_key(window), 0, OCTOPUS_SLOTS_MAX, 1)
        for window in OCTOPUS_WINDOWS
    ),
    StrategyField("octopus_charge_price", "Octopus Charge Price", "mdi:cash-plus",
                  (OCTOPUS,), "octopusPrice", 0, OCTOPUS_PRICE_MAX, 0.01, PRICE_UNIT),
    StrategyField("octopus_discharge_price", "Octopus Discharge Price", "mdi:cash-minus",
                  (OCTOPUS,), "octopusDischargePrice", 0, OCTOPUS_PRICE_MAX, 0.01,
                  PRICE_UNIT),
)

SELECTS = (
    StrategyField("octopus_schema_type", "Octopus Schema Type", "mdi:format-list-bulleted-type",
                  (OCTOPUS,), OCTOPUS_TYPE_FIELD, options=OCTOPUS_TYPES),
    StrategyField("strategy_priority", "Strategy Priority", "mdi:priority-high",
                  (WEATHER, OCTOPUS), PRIORITY_KEY, options=PRIORITY_OPTIONS),
)

TEXTS = (
    StrategyField("octopus_postcode", "Octopus Postcode", "mdi:map-marker",
                  (OCTOPUS,), "postalCode"),
)

SAVE_BUTTONS = (
    (WEATHER, "save_weather_optimize", "Save Weather Optimize"),
    (OCTOPUS, "save_octopus_strategy", "Save Octopus Strategy"),
)


def _coordinator(entry):
    data = getattr(entry, "runtime_data", None)
    return getattr(data, "strategy", None) if data is not None else None


class HanchuessStrategyEntity(CoordinatorEntity):
    """Base for a Weather Optimize / Octopus setting."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry, spec: StrategyField) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._spec = spec
        self._attr_name = spec.name
        self._attr_icon = spec.icon
        self._attr_unique_id = f"{entry.data['sn']}_{spec.key}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.coordinator.async_ensure_loaded()

    @property
    def device_info(self) -> DeviceInfo:
        inverter_serial_number = self._entry.data["sn"]
        return DeviceInfo(
            identifiers={(DOMAIN, inverter_serial_number)},
            name=f"Hanchuess {inverter_serial_number}",
            manufacturer="Hanchu",
            model=inverter_model_name(self._entry),
        )

    @property
    def available(self) -> bool:
        """Unavailable until a record with saved settings has been read."""
        return any(has_settings(self.coordinator.record(kind)) for kind in self._spec.kinds)

    @property
    def raw_value(self) -> Any:
        """The staged value if there is one, else the latest record's."""
        return self._value_of(self._spec.field)

    def _value_of(self, field: str) -> Any:
        for kind in self._spec.kinds:
            pending = self.coordinator.staging[kind].pending
            if field in pending:
                return pending[field]
        for kind in self._spec.kinds:
            value = record_value(self.coordinator.record(kind), field)
            if value is not None:
                return value
        return None

    def _stage(self, value: Any) -> None:
        for kind in self._spec.kinds:
            self.coordinator.staging[kind].stage(self._spec.field, value)
        self.async_write_ha_state()
        _LOGGER.info("[HANCHUESS] %s staged: %s (pending save)", self._spec.name, value)


class HanchuessStrategySwitch(HanchuessStrategyEntity, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        return decode_flag(self.raw_value)

    @property
    def extra_state_attributes(self) -> dict | None:
        """``applies_to``: what the switch controls in the current schema type.

        Follows the Octopus Schema Type as shown (staged or saved); left out
        while the type is unknown.
        """
        if not self._spec.applies_to:
            return None
        schema_type = self._value_of(OCTOPUS_TYPE_FIELD)
        meaning = self._spec.applies_to.get(str(schema_type).strip()) if schema_type is not None else None
        return {"applies_to": meaning} if meaning else None

    async def async_turn_on(self, **kwargs) -> None:
        self._stage("1")

    async def async_turn_off(self, **kwargs) -> None:
        self._stage("0")


class HanchuessStrategyTime(HanchuessStrategyEntity, TimeEntity):
    @property
    def native_value(self) -> dt_time | None:
        decoded = decode_hhmm(self.raw_value)
        return dt_time(*decoded) if decoded else None

    async def async_set_value(self, value: dt_time) -> None:
        self._stage(encode_hhmm(value.hour, value.minute))


class HanchuessStrategyNumber(HanchuessStrategyEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry, spec: StrategyField) -> None:
        super().__init__(coordinator, entry, spec)
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step
        self._attr_native_unit_of_measurement = spec.unit

    @property
    def native_value(self) -> float | None:
        return decode_number(self.raw_value)

    async def async_set_native_value(self, value: float) -> None:
        if self._spec.step >= 1:
            self._stage(int(round(value)))
        else:
            self._stage(round(value, 2))


class HanchuessStrategySelect(HanchuessStrategyEntity, SelectEntity):
    def __init__(self, coordinator, entry, spec: StrategyField) -> None:
        super().__init__(coordinator, entry, spec)
        self._attr_options = list(spec.options)

    @property
    def current_option(self) -> str | None:
        return decode_option(self.raw_value, self._spec.options)

    async def async_select_option(self, option: str) -> None:
        if option not in self._spec.options:
            raise HomeAssistantError(f"Unknown option: {option}")
        self._stage(self._spec.options[option])


class HanchuessStrategyText(HanchuessStrategyEntity, TextEntity):
    _attr_native_max = 16

    @property
    def native_value(self) -> str | None:
        raw = self.raw_value
        return None if raw is None else str(raw)

    async def async_set_value(self, value: str) -> None:
        self._stage(value.strip())


class HanchuessStrategySaveButton(HanchuessStrategyEntity, ButtonEntity):
    """Save one strategy's staged changes (read latest, merge, save, re-read)."""

    def __init__(self, coordinator, entry, kind: str, key: str, name: str) -> None:
        super().__init__(
            coordinator, entry, StrategyField(key, name, "mdi:content-save", (kind,), "")
        )
        self._kind = kind

    async def async_press(self) -> None:
        if not await self.coordinator.async_save(self._kind):
            raise HomeAssistantError(
                f"{self._spec.name} failed; the changes are still staged"
            )


def _build(entry, cls, specs):
    coordinator = _coordinator(entry)
    if coordinator is None:
        return []
    return [cls(coordinator, entry, spec) for spec in specs]


def strategy_switches(entry):
    return _build(entry, HanchuessStrategySwitch, SWITCHES)


def strategy_times(entry):
    return _build(entry, HanchuessStrategyTime, TIMES)


def strategy_numbers(entry):
    return _build(entry, HanchuessStrategyNumber, NUMBERS)


def strategy_selects(entry):
    return _build(entry, HanchuessStrategySelect, SELECTS)


def strategy_texts(entry):
    return _build(entry, HanchuessStrategyText, TEXTS)


def strategy_buttons(entry):
    coordinator = _coordinator(entry)
    if coordinator is None:
        return []
    return [
        HanchuessStrategySaveButton(coordinator, entry, kind, key, name)
        for kind, key, name in SAVE_BUTTONS
    ]


# The Pending Changes sensor (sensor.py); the cards read its per-strategy
# counts. Its unique-id suffix predates the strategies.
PENDING_CHANGES_KEY = "pending_changes"
PENDING_CHANGES_SUFFIX = "pending_settings_changes"


def card_entity_keys() -> dict[str, tuple[str, str]]:
    """key -> (platform, unique-id suffix) for every entity the strategy cards use.

    The keys are the unique-id suffixes above, so they survive entity renames
    (and the pre-rename ``octopus_charge`` / ``octopus_discharge`` entity ids).
    """
    keys: dict[str, tuple[str, str]] = {}
    for platform, specs in (
        ("switch", SWITCHES),
        ("time", TIMES),
        ("number", NUMBERS),
        ("select", SELECTS),
        ("text", TEXTS),
    ):
        for spec in specs:
            keys[spec.key] = (platform, spec.key)
    for _kind, key, _name in SAVE_BUTTONS:
        keys[key] = ("button", key)
    keys[PENDING_CHANGES_KEY] = ("sensor", PENDING_CHANGES_SUFFIX)
    return keys
