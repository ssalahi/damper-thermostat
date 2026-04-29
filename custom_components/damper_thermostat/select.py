"""Select platform for Damper Thermostat configuration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_GLOBAL_SETTINGS,
    CONF_HEAT_FAN_MODE,
    CONF_COLD_FAN_MODE,
)

_LOGGER = logging.getLogger(__name__)

FAN_MODE_OPTIONS = ["Auto", "Off"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Damper Thermostat select platform."""
    # Skip global settings entries
    if config_entry.data.get("entry_type") == CONF_GLOBAL_SETTINGS:
        return

    config = hass.data[DOMAIN][config_entry.entry_id]
    options = config_entry.options

    heat_fan_initial = options.get(
        CONF_HEAT_FAN_MODE,
        config.get(CONF_HEAT_FAN_MODE, "Auto")
    )
    cold_fan_initial = options.get(
        CONF_COLD_FAN_MODE,
        config.get(CONF_COLD_FAN_MODE, "Auto")
    )

    async_add_entities([
        DamperThermostatHeatFanModeSelect(config_entry.entry_id, heat_fan_initial),
        DamperThermostatColdFanModeSelect(config_entry.entry_id, cold_fan_initial),
    ])


class DamperThermostatHeatFanModeSelect(SelectEntity, RestoreEntity):
    """Dropdown select for Heat Fan Mode configuration (Auto/Off)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_options = FAN_MODE_OPTIONS

    def __init__(self, entry_id: str, initial_value: str) -> None:
        """Initialize the select."""
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{CONF_HEAT_FAN_MODE}"
        self._attr_name = "Heat Fan Mode"
        self._attr_current_option = initial_value if initial_value in FAN_MODE_OPTIONS else "Auto"

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        old_state = await self.async_get_last_state()
        if old_state is not None and old_state.state in FAN_MODE_OPTIONS:
            self._attr_current_option = old_state.state
            _LOGGER.debug(
                "Restored Heat Fan Mode select state: %s", self._attr_current_option
            )

        # Publish current state to hass.data for climate entity to read
        self.hass.data[DOMAIN][f"{self._entry_id}_{CONF_HEAT_FAN_MODE}"] = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in FAN_MODE_OPTIONS:
            _LOGGER.warning("Invalid option selected: %s", option)
            return

        self._attr_current_option = option
        self._apply_state_change()

    def _apply_state_change(self) -> None:
        """Persist state and notify the climate entity."""
        self.hass.data[DOMAIN][f"{self._entry_id}_{CONF_HEAT_FAN_MODE}"] = self._attr_current_option
        self.async_write_ha_state()

        # Trigger climate control re-evaluation via registered callback
        callback_fn = self.hass.data[DOMAIN].get(f"{self._entry_id}_on_reverse_change")
        if callback_fn:
            self.hass.async_create_task(callback_fn())
        else:
            _LOGGER.debug("No climate callback registered yet for entry %s", self._entry_id)

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._attr_current_option

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def icon(self):
        return "mdi:fan" if self._attr_current_option == "Auto" else "mdi:fan-off"


class DamperThermostatColdFanModeSelect(SelectEntity, RestoreEntity):
    """Dropdown select for Cold Fan Mode configuration (Auto/Off)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_options = FAN_MODE_OPTIONS

    def __init__(self, entry_id: str, initial_value: str) -> None:
        """Initialize the select."""
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{CONF_COLD_FAN_MODE}"
        self._attr_name = "Cold Fan Mode"
        self._attr_current_option = initial_value if initial_value in FAN_MODE_OPTIONS else "Auto"

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        old_state = await self.async_get_last_state()
        if old_state is not None and old_state.state in FAN_MODE_OPTIONS:
            self._attr_current_option = old_state.state
            _LOGGER.debug(
                "Restored Cold Fan Mode select state: %s", self._attr_current_option
            )

        # Publish current state to hass.data for climate entity to read
        self.hass.data[DOMAIN][f"{self._entry_id}_{CONF_COLD_FAN_MODE}"] = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in FAN_MODE_OPTIONS:
            _LOGGER.warning("Invalid option selected: %s", option)
            return

        self._attr_current_option = option
        self._apply_state_change()

    def _apply_state_change(self) -> None:
        """Persist state and notify the climate entity."""
        self.hass.data[DOMAIN][f"{self._entry_id}_{CONF_COLD_FAN_MODE}"] = self._attr_current_option
        self.async_write_ha_state()

        # Trigger climate control re-evaluation via registered callback
        callback_fn = self.hass.data[DOMAIN].get(f"{self._entry_id}_on_reverse_change")
        if callback_fn:
            self.hass.async_create_task(callback_fn())
        else:
            _LOGGER.debug("No climate callback registered yet for entry %s", self._entry_id)

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._attr_current_option

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def icon(self):
        return "mdi:snowflake-thermometer" if self._attr_current_option == "Auto" else "mdi:snowflake-off"