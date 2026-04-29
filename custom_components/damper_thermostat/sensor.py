"""Sensor platform for Damper Thermostat diagnostics."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback, Event, EventStateChangedData
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CONF_ACTUATOR_SWITCH,
    CONF_COLD_TOLERANCE,
    CONF_HOT_TOLERANCE,
    DEFAULT_TOLERANCE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Damper Thermostat sensor platform."""
    # Skip global settings entries
    if config_entry.data.get("entry_type") == "global_settings":
        return

    config = hass.data[DOMAIN][config_entry.entry_id]
    options = config_entry.options
    entry_id = config_entry.entry_id

    actuator_switch_entity_ids = options.get(
        CONF_ACTUATOR_SWITCH, config[CONF_ACTUATOR_SWITCH]
    )
    if not isinstance(actuator_switch_entity_ids, list):
        actuator_switch_entity_ids = [actuator_switch_entity_ids] if actuator_switch_entity_ids else []

    cold_tolerance = options.get(
        CONF_COLD_TOLERANCE, config.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE)
    )
    hot_tolerance = options.get(
        CONF_HOT_TOLERANCE, config.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE)
    )

    async_add_entities([
        DamperThermostatActuatorSensor(entry_id, actuator_switch_entity_ids),
        DamperThermostatColdToleranceSensor(entry_id, cold_tolerance),
        DamperThermostatHotToleranceSensor(entry_id, hot_tolerance),
    ])


class DamperThermostatActuatorSensor(SensorEntity):
    """Diagnostic sensor showing actuator switch status (Open/Close)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, entry_id: str, actuator_switch_entity_ids: list[str]) -> None:
        """Initialize the actuator status sensor."""
        self._entry_id = entry_id
        self._actuator_switch_entity_ids = actuator_switch_entity_ids
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_actuator_status"
        self._attr_name = "Actuator Switch"
        self._attr_icon = "mdi:valve"
        self._attr_native_value = "Close"

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Determine initial state now that hass is available
        self._update_state()

        # Subscribe to actuator switch state changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._actuator_switch_entity_ids,
                self._async_actuator_switch_changed,
            )
        )

    @callback
    def _async_actuator_switch_changed(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle actuator switch state changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._update_state()
        self.async_write_ha_state()

    def _update_state(self) -> None:
        """Read current actuator switch states and update native_value."""
        for switch_id in self._actuator_switch_entity_ids:
            state = self.hass.states.get(switch_id)
            if state is not None and state.state == "on":
                self._attr_native_value = "Open"
                return
        self._attr_native_value = "Close"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )


class DamperThermostatColdToleranceSensor(SensorEntity):
    """Diagnostic sensor showing the cold tolerance value."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, entry_id: str, cold_tolerance: float) -> None:
        """Initialize the cold tolerance sensor."""
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_cold_tolerance"
        self._attr_name = "Cold Tolerance"
        self._attr_native_value = cold_tolerance
        self._attr_icon = "mdi:thermometer-chevron-down"
        self._attr_state_class = "measurement"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )


class DamperThermostatHotToleranceSensor(SensorEntity):
    """Diagnostic sensor showing the hot tolerance value."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, entry_id: str, hot_tolerance: float) -> None:
        """Initialize the hot tolerance sensor."""
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_hot_tolerance"
        self._attr_name = "Hot Tolerance"
        self._attr_native_value = hot_tolerance
        self._attr_icon = "mdi:thermometer-chevron-up"
        self._attr_state_class = "measurement"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the thermostat device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )