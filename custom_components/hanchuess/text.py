"""Text platform for Hanchuess - Octopus postcode."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HanchuessConfigEntry
from .strategy_entity import strategy_texts


async def async_setup_entry(
    hass: HomeAssistant, entry: HanchuessConfigEntry, async_add_entities: AddEntitiesCallback
):
    async_add_entities(strategy_texts(entry))
