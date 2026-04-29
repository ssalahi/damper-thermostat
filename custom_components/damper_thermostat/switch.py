"""Switch platform for Damper Thermostat."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_GLOBAL_SETTINGS,
    CONF_REVERSE_HEAT_COOL_RANGE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Damper Thermostat switch platform."""
    # Skip global settings entries
    if config_entry.data.get("entry_type") == CONF_GLOBAL_SETTINGS:
        return

    config = hass.data[DOMAIN][config_entry.entry_id]
    options = config_entry.options

    initial_value = options.get(
        CONF_REVERSE_HEAT_COOL_RANGE,
        config.get(CONF_REVERSE_HEAT_COOL_RANGE, False)
    )

    async_add_entities([
        DamperThermostatReverseSwitch(config_entry.entry_id, initial_value)
    ])


class DamperThermostatReverseSwitch(SwitchEntity, RestoreEntity):
    """Toggle switch for Reverse Heat/Cool Range configuration."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, entry_id: str, initial_value: bool) -> None:
        """Initialize the switch."""
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_reverse_heat_cool_range"
        self._attr_name = "Reverse Heat/Cool Range"
        self._attr_is_on = initial_value

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        old_state = await self.async_get_last_state()
        if old_state is not None:
            self._attr_is_on = old_state.state == "on"
            _LOGGER.debug(
                "Restored Reverse Heat/Cool Range switch state: %s", self._attr_is_on
            )

        # Publish current state to hass.data for climate entity to read
        self.hass.data[DOMAIN][f"{self._entry_id}_reverse_heat_cool_range"] = self._attr_is_on

    def _apply_state_change(self) -> None:
        """Persist state and notify the climate entity."""
        # Update shared state store
        self.hass.data[DOMAIN][f"{self._entry_id}_reverse_heat_cool_range"] = self._attr_is_on
        self.async_write_ha_state()

        # Trigger climate control re-evaluation via registered callback
        callback_fn = self.hass.data[DOMAIN].get(f"{self._entry_id}_on_reverse_change")
        if callback_fn:
            self.hass.async_create_task(callback_fn())
        else:
            _LOGGER.debug("No climate callback registered yet for entry %s", self._entry_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        self._apply_state_change()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._attr_is_on = False
        self._apply_state_change()

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return self._attr_is_on

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )
    
    @property
    def icon(self):
        return "mdi:rotate-right"