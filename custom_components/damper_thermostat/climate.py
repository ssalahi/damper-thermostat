"""Support for Damper Thermostat."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from types import MappingProxyType

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
    PRECISION_HALVES
)
from homeassistant.core import HomeAssistant, callback, Event, EventStateChangedData
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ACTUATOR_SWITCH,
    CONF_MAIN_THERMOSTAT,
    CONF_COLD_TOLERANCE,
    CONF_HOT_TOLERANCE,
    CONF_TARGET_TEMP,
    CONF_TARGET_TEMP_LOW,
    CONF_TARGET_TEMP_HIGH,
    CONF_INITIAL_HVAC_MODE,
    CONF_GLOBAL_ACTUATOR_SWITCHES,
    CONF_GLOBAL_MAX_SWITCHES_OFF,
    CONF_GLOBAL_MIN_TEMP,
    CONF_GLOBAL_MAX_TEMP,
    DEFAULT_TOLERANCE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TARGET_TEMP_LOW,
    DEFAULT_TARGET_TEMP_HIGH,
    DEFAULT_PRECISION,
    DEFAULT_MAX_SWITCHES_OFF,
    HVAC_MODES,
    SUPPORT_FLAGS,
)

from . import get_global_setting

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Damper Thermostat platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    options = config_entry.options
    
    async_add_entities([DamperThermostat(hass, config, config_entry.entry_id, options)])


class DamperThermostat(ClimateEntity, RestoreEntity):
    """Representation of a Damper Thermostat device."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], entry_id: str, options: MappingProxyType[str, Any] = MappingProxyType({})) -> None:
        """Initialize the thermostat."""
        self.hass = hass
        self._entry_id = entry_id
        
        # Use options if available, otherwise fall back to config
        if options is None:
            options = {}
        
        # Name and unique ID
        self._attr_name = options.get(CONF_NAME, config.get(CONF_NAME, "Damper Thermostat"))
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"
        
        # Entity configurations (can be changed via options)
        self._temperature_sensor_entity_ids = options.get(CONF_TEMPERATURE_SENSOR, config[CONF_TEMPERATURE_SENSOR])
        self._humidity_sensor_entity_ids = options.get(CONF_HUMIDITY_SENSOR, config.get(CONF_HUMIDITY_SENSOR))
        self._actuator_switch_entity_ids = options.get(CONF_ACTUATOR_SWITCH, config[CONF_ACTUATOR_SWITCH])
        
        # Handle actuator switches list - use global settings
        self._actuator_switches_entity_ids = get_global_setting(hass, CONF_GLOBAL_ACTUATOR_SWITCHES, [])
        if not isinstance(self._actuator_switches_entity_ids, list):
            self._actuator_switches_entity_ids = [self._actuator_switches_entity_ids] if self._actuator_switches_entity_ids else []
        
        # Max switches off limit - use global settings
        self._max_switches_off = get_global_setting(
            hass, CONF_GLOBAL_MAX_SWITCHES_OFF, DEFAULT_MAX_SWITCHES_OFF
        )
        
        self._main_thermostat_entity_id = options.get(CONF_MAIN_THERMOSTAT, config.get(CONF_MAIN_THERMOSTAT))
        
        # Other configuration options
        self._cold_tolerance = options.get(CONF_COLD_TOLERANCE, config.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE))
        self._hot_tolerance = options.get(CONF_HOT_TOLERANCE, config.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE))
        # Temperature limits - use global settings
        self._attr_min_temp = get_global_setting(hass, CONF_GLOBAL_MIN_TEMP, DEFAULT_MIN_TEMP)
        self._attr_max_temp = get_global_setting(hass, CONF_GLOBAL_MAX_TEMP, DEFAULT_MAX_TEMP)
        self._attr_target_temperature = options.get(CONF_TARGET_TEMP, config.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP))
        self._attr_target_temperature_low = options.get(CONF_TARGET_TEMP_LOW, config.get(CONF_TARGET_TEMP_LOW, DEFAULT_TARGET_TEMP_LOW))
        self._attr_target_temperature_high = options.get(CONF_TARGET_TEMP_HIGH, config.get(CONF_TARGET_TEMP_HIGH, DEFAULT_TARGET_TEMP_HIGH))
        self._attr_precision = DEFAULT_PRECISION
        self._attr_target_temperature_step = PRECISION_HALVES
        
        # Set initial HVAC mode
        self._attr_hvac_mode = options.get(CONF_INITIAL_HVAC_MODE, config.get(CONF_INITIAL_HVAC_MODE, HVACMode.AUTO))
        
        # State variables
        self._attr_current_temperature = None
        self._attr_current_humidity = None
        self._attr_hvac_action = HVACAction.OFF
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        
        # Supported features and modes
        self._attr_supported_features = SUPPORT_FLAGS
            
        self._attr_hvac_modes = HVAC_MODES
        
        # Control variables
        self._active = False
        self._cur_temp = None
        self._cur_humidity = None
        self._temp_lock = asyncio.Lock()
        self._on_by_us = False
        self._main_thermostat_target_temperature = self._attr_target_temperature

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listeners for temperature sensors
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._temperature_sensor_entity_ids, self._async_sensor_changed
            )
        )
        
        # Add listener for humidity sensor if configured
        if self._humidity_sensor_entity_ids:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, self._humidity_sensor_entity_ids, self._async_sensor_changed
                )
            )
        
        # Add listener for main thermostat if configured
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._main_thermostat_entity_id], self._async_main_thermostat_changed
            )
        )

        # Add listener for actuator switch
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._actuator_switch_entity_ids, self._async_switch_changed
            )
        )

        # Check if we have a saved state
        old_state = await self.async_get_last_state()
        if old_state is not None:
            # Restore target_temperature available
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._attr_target_temperature = float(old_state.attributes[ATTR_TEMPERATURE])

            # Restore target_temperature_low if available
            if old_state.attributes.get(ATTR_TARGET_TEMP_LOW) is not None:
                self._attr_target_temperature_low = float(old_state.attributes[ATTR_TARGET_TEMP_LOW])

            # Restore target_temperature_high if available
            if old_state.attributes.get(ATTR_TARGET_TEMP_HIGH) is not None:
                self._attr_target_temperature_high = float(old_state.attributes[ATTR_TARGET_TEMP_HIGH])

            if old_state.state and old_state.state != STATE_UNKNOWN:
                self._attr_hvac_mode = HVACMode(old_state.state)

        else:
            # No previous state, set some defaults
            if self._attr_target_temperature is None:
                self._attr_target_temperature = self.min_temp
            _LOGGER.warning("No previously saved temperature, setting to %s", self._attr_target_temperature)

        # Set initial temperature and humidity
        self._async_update_temp(None)
        if self._humidity_sensor_entity_ids:
            self._async_update_humidity(None)
        
        # Set initial main thermostat state
        self._async_update_main_thermostat_state(None)

        # Call control logic on startup
        if self.hass.state == "running":
            await self._async_control_heating_cooling()
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_START, self._async_control_heating_cooling
            )
    
    @callback
    def _async_update_temp(self, state) -> None:
        """Update thermostat with average temperature from all temperature sensors."""
        try:
            # Calculate average temperature
            avg_temp = self._async_calculate_average_sensor_state(self._temperature_sensor_entity_ids)
            if not avg_temp:
                # Only log warning if this is not the initial startup call
                if state is not None:
                    _LOGGER.warning("No valid temperature readings from any sensors")
                return None
            self._cur_temp = avg_temp
            self._attr_current_temperature = avg_temp
        
        except Exception as ex:
            _LOGGER.error("Error updating temperature: %s", ex)

    @callback
    def _async_update_humidity(self, state) -> None:
        """Update thermostat with latest state from humidity sensors."""
        try:
             # Calculate average temperature
            avg_humidity = self._async_calculate_average_sensor_state(self._humidity_sensor_entity_ids)
            if not avg_humidity:
                # Only log warning if this is not the initial startup call
                if state is not None:
                    _LOGGER.warning("No valid humidity readings from any sensors")
                return None
            self._cur_humidity = int(avg_humidity)
            self._attr_current_humidity = int(avg_humidity)

        except Exception as ex:
            _LOGGER.error("Error updating humidities: %s", ex)

    @callback
    def _async_update_main_thermostat_state(self, state) -> None:
        """Update thermostat action based on main thermostat state."""
        try:
            if state is None:
                state = self.hass.states.get(self._main_thermostat_entity_id)

            if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                return

            # Map main thermostat's hvac_action to our hvac_action
            main_action = HVACAction(state.attributes.get("hvac_action", HVACAction.OFF)) if state.attributes else HVACAction.OFF
            self._attr_hvac_action = main_action
            # Kepp track of main thermostat's target_temperature
            self._main_thermostat_target_temperature = float(state.attributes.get("temperature", self._attr_target_temperature))
            
            # Update the current thermostat's based on the main thermostat change
            task = self.hass.async_create_task(self._async_control_heating_cooling())
            task.add_done_callback(self._handle_control_task_done)
        except Exception as ex:
            _LOGGER.error("Error updating main thermostat state: %s", ex)
            self._attr_hvac_action = HVACAction.OFF

    @callback
    def _async_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature/humidity sensor state changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        entity_id = event.data["entity_id"]
        
        if entity_id in self._temperature_sensor_entity_ids:
            self._async_update_temp(new_state)
        elif self._humidity_sensor_entity_ids is not None and entity_id in self._humidity_sensor_entity_ids:
            self._async_update_humidity(new_state)
            
        self.async_write_ha_state()
        # Use async_create_task with proper error handling
        task = self.hass.async_create_task(self._async_control_heating_cooling())
        task.add_done_callback(self._handle_control_task_done)

    @callback
    def _async_main_thermostat_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle main thermostat state changes."""
        new_state = event.data["new_state"]
        if new_state is None:
            return
            
        self._async_update_main_thermostat_state(new_state)
        self.async_write_ha_state()

    @callback
    def _async_switch_changed(self, event) -> None:
        """Handle actuator switch state changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self.async_write_ha_state()
        if not self._on_by_us:
            # If the switch was turned on/off manually, we need to update our control logic
            task = self.hass.async_create_task(self._async_control_heating_cooling())
            task.add_done_callback(self._handle_control_task_done)
        
        # Reset the flag after processing
        self._on_by_us = False
                                
    async def _async_control_heating_cooling(self, time=None) -> None:
        """Check if we need to turn heating/cooling on or off."""
        try:
            async with self._temp_lock:
                if not self._active and None not in (self._cur_temp, self._attr_target_temperature):
                    self._active = True
                    _LOGGER.info(
                        "Obtained current and target temperature. "
                        "Damper Thermostat active. %s, %s",
                        self._cur_temp,
                        self._attr_target_temperature,
                    )

                if not self._active or self._attr_hvac_mode == HVACMode.OFF:
                    return

                await self._async_control_based_on_main_thermostat()
                
        except Exception as ex:
            _LOGGER.error("Error in control heating/cooling: %s", ex)

    async def _async_control_based_on_main_thermostat(self) -> None:
        """Control actuator based on main thermostat state and our temperature."""
        try:
            main_state = self.hass.states.get(self._main_thermostat_entity_id)
            if main_state is None:
                _LOGGER.warning("Main thermostat %s not found", self._main_thermostat_entity_id)
                return
                
            main_action = HVACAction(main_state.attributes.get("hvac_action", HVACAction.OFF))
            main_mode = HVACMode(main_state.state)
            
            # Deciding based on the low/high target temp and main thermostat current state
            # and our temperature to know if actuator needs to be closed or not
            should_deactivate = False
            enough_cold = False
            enough_heat = False
            
            # The heat/cool is opposite of each other, so we need to deactivate
            if self._attr_hvac_mode == HVACMode.COOL and main_mode == HVACMode.HEAT:
                should_deactivate = True
            if self._attr_hvac_mode == HVACMode.HEAT and main_mode == HVACMode.COOL:
                should_deactivate = True

            # Handle heat_cool mode
            if self._attr_hvac_mode == HVACMode.HEAT_COOL:
                if main_mode == HVACMode.COOL and main_action == HVACAction.COOLING:
                    enough_cold = self._attr_target_temperature_low >= (self._cur_temp + self._cold_tolerance)
                if main_mode == HVACMode.HEAT and main_action in [HVACAction.HEATING, HVACAction.PREHEATING]:
                    enough_heat = self._attr_target_temperature_high <= (self._cur_temp - self._hot_tolerance)
            should_deactivate = should_deactivate or enough_cold or enough_heat

            # Handle heat and cool modes
            if self._attr_hvac_mode == HVACMode.COOL and main_action == HVACAction.COOLING:
                enough_cold = self._attr_target_temperature >= (self._cur_temp + self._cold_tolerance)
            if self._attr_hvac_mode == HVACMode.HEAT and main_action in [HVACAction.HEATING, HVACAction.PREHEATING]:
                enough_heat = self._attr_target_temperature <= (self._cur_temp - self._hot_tolerance)
            should_deactivate = should_deactivate or enough_cold or enough_heat

            # Auto mode will always keep the actuator on
            if self._attr_hvac_mode == HVACMode.AUTO:
                should_deactivate = False

            current_device_active = await self._async_is_device_active()
            if should_deactivate and current_device_active:
                _LOGGER.info("Thermostat Control: Conditions not met, turning off actuator")
                await self._async_actuators_turn_off()
            elif not should_deactivate and not current_device_active:
                _LOGGER.info("Thermostat Control: Turning on actuator")
                await self._async_actuators_turn_on()
        except Exception as ex:
            _LOGGER.error("Error in main thermostat control: %s", ex)

    async def _async_is_device_active(self) -> bool:
        """Check if the actuator switch is currently on."""
        try:
            for actuator in self._actuator_switch_entity_ids:
                state = self.hass.states.get(actuator)
                if state is not None and state.state == "on":
                    return True
            return False
        except Exception as ex:
            _LOGGER.error("Error checking device state: %s", ex)
            return False
    
    def _async_calculate_average_sensor_state(self, sensor_ids) -> float | None:
        """Calculate the average state of sensors."""
        states = []
        for sensor_id in sensor_ids:
            sensor_state = self.hass.states.get(sensor_id)
            if sensor_state is not None and sensor_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                try:
                    states.append(float(sensor_state.state))
                except ValueError as ex:
                    _LOGGER.warning("Unable to parse state from sensor %s: %s", sensor_id, ex)

        if not states:
            return None

        return sum(states) / len(states)
    
    async def _async_get_actuator_switches_status(self) -> dict[str, str]:
        """Get the current status of all actuator switches."""
        try:
            status = {}
            for switch_id in self._actuator_switches_entity_ids:
                state = self.hass.states.get(switch_id)
                if state is not None:
                    status[switch_id] = state.state
                else:
                    status[switch_id] = "unavailable"
            return status
        except Exception as ex:
            _LOGGER.error("Error getting actuator switches status: %s", ex)
            return {}

    async def _async_actuators_turn_on(self) -> None:
        """Turn actuator on."""
        try:
            for actuator in self._actuator_switch_entity_ids: 
                data = {"entity_id": actuator}
                self._on_by_us = True
                await self.hass.services.async_call("switch", SERVICE_TURN_ON, data, blocking=False)
                _LOGGER.info("Turned on my actuator switch %s", actuator)
        except Exception as ex:
            _LOGGER.error("Error turning on actuator: %s", ex)
            self._on_by_us = False

    async def _async_actuators_turn_off(self) -> None:
        for actuator in self._actuator_switch_entity_ids:
            await self._async_actuator_turn_off(actuator)
    
    async def _async_actuator_turn_off(self, actuator_switch_entity_id) -> None:
        """Turn actuator off."""
        try:
            # Check if we can turn off more switches
            switches_status = await self._async_get_actuator_switches_status()
            current_off_count = sum(1 for status in switches_status.values() if status == "off")
            if current_off_count < self._max_switches_off:
                data = {"entity_id": actuator_switch_entity_id}
                self._on_by_us = True
                await self.hass.services.async_call("switch", SERVICE_TURN_OFF, data, blocking=False)
                _LOGGER.info("Turned off my actuator switch %s.",actuator_switch_entity_id)
                return
            
            # Find my position in the priority list
            try:
                my_position = self._actuator_switches_entity_ids.index(actuator_switch_entity_id)
            except ValueError:
                _LOGGER.error("My actuator switch %s not found in actuator_switches list", actuator_switch_entity_id)
                return
            
            # Look for a lower priority switch that's currently off to turn ON first
            lower_priority_switch_to_turn_on = None
            for i in range(len(self._actuator_switches_entity_ids) - 1, my_position, -1):
                switch_id = self._actuator_switches_entity_ids[i]
                if switches_status.get(switch_id) == "off":
                    lower_priority_switch_to_turn_on = switch_id
                    break
            
            # If no lower priority switch is available to turn on, don't turn off
            if lower_priority_switch_to_turn_on is None:
                _LOGGER.info(
                    "Cannot turn off actuator %s: no lower priority switch available to turn on",
                    actuator_switch_entity_id
                )
                return
            
            # Turn ON the lower priority switch first
            data = {"entity_id": lower_priority_switch_to_turn_on}
            await self.hass.services.async_call("switch", SERVICE_TURN_ON, data, blocking=False)
            
            # Now turn OFF my own switch
            data = {"entity_id": actuator_switch_entity_id}
            self._on_by_us = True
            await self.hass.services.async_call("switch", SERVICE_TURN_OFF, data, blocking=False)
            _LOGGER.info(
                "Turned off my actuator switch %s after turning on lower priority switch (switches off: %d/%d)",
                actuator_switch_entity_id,
                current_off_count,
                self._max_switches_off
            )
        except Exception as ex:
            _LOGGER.error("Error turning off actuator: %s", ex)
            self._on_by_us = False

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set hvac mode."""
        if hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.OFF
            if await self._async_is_device_active():
                await self._async_actuators_turn_off()
        else:
            self._attr_hvac_mode = hvac_mode
            await self._async_control_heating_cooling()
        # Ensure we update the display
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        # Handle single temperature setpoint
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None and self.hvac_mode is not HVACMode.AUTO:
            self._attr_target_temperature = temperature
        
        # Handle dual temperature setpoints for AUTO and HEAT_COOL modes
        target_temp_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        if target_temp_low is not None and self.hvac_mode == HVACMode.HEAT_COOL:
            self._attr_target_temperature_low = target_temp_low
        
        target_temp_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        if target_temp_high is not None and self.hvac_mode == HVACMode.HEAT_COOL:
            self._attr_target_temperature_high = target_temp_high
        
        # Only proceed if we actually got a temperature to set
        if any(temp is not None for temp in [temperature, target_temp_low, target_temp_high]):
            await self._async_control_heating_cooling()
            self.async_write_ha_state()

    @callback
    def _handle_control_task_done(self, task) -> None:
        """Handle completion of control task."""
        if task.exception():
            _LOGGER.error("Control task failed: %s", task.exception())
    
    @property
    def supported_features(self) -> float | None:
        """Return supported feature based on HVACMode"""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._attr_supported_features
        return ClimateEntityFeature.TARGET_TEMPERATURE
    
    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self.hvac_mode in [HVACMode.COOL, HVACMode.HEAT]:
            return self._attr_target_temperature
        elif self.hvac_mode == HVACMode.AUTO: 
            return self._main_thermostat_target_temperature
        return None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach."""
        if self.hvac_mode in [HVACMode.HEAT_COOL]:
            return self._attr_target_temperature_high
        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach."""
        if self.hvac_mode in [HVACMode.HEAT_COOL]:
            return self._attr_target_temperature_low
        return None

    @property
    def icon(self):
        """Return the icon based on current HVAC state."""
        # Dynamic icons based on mode and action
        if self._attr_hvac_mode == HVACMode.OFF:
            return "mdi:thermostat-off"
        elif self._attr_hvac_action == HVACAction.HEATING:
            return "mdi:fire"
        elif self._attr_hvac_action == HVACAction.COOLING:
            return "mdi:snowflake"
        elif self._attr_hvac_mode == HVACMode.AUTO:
            if self._attr_hvac_action == HVACAction.IDLE:
                return "mdi:thermostat-auto"
            else:
                return "mdi:thermostat-auto"
        elif self._attr_hvac_mode == HVACMode.HEAT_COOL:
            return "mdi:sun-snowflake-variant"
        elif self._attr_hvac_mode == HVACMode.HEAT:
            return "mdi:radiator"
        elif self._attr_hvac_mode == HVACMode.COOL:
            return "mdi:air-conditioner"
        elif self._attr_hvac_mode == HVACMode.FAN_ONLY:
            return "mdi:fan-auto"
        else:
            return "mdi:thermostat"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this thermostat."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._attr_name,
            manufacturer="SSalahi",
            model="Smart Damper Thermostat",
            sw_version="1.0.0"
        )
