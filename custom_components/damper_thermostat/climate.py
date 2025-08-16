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
)
from homeassistant.core import HomeAssistant, callback
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
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TARGET_TEMP,
    CONF_TARGET_TEMP_LOW,
    CONF_TARGET_TEMP_HIGH,
    CONF_INITIAL_HVAC_MODE,
    DEFAULT_TOLERANCE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TARGET_TEMP_LOW,
    DEFAULT_TARGET_TEMP_HIGH,
    DEFAULT_PRECISION,
    HVAC_MODES,
)

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
        temp_sensors = options.get(CONF_TEMPERATURE_SENSOR, config[CONF_TEMPERATURE_SENSOR])
        # Handle both single sensor (string) and multiple sensors (list)
        if isinstance(temp_sensors, list):
            self._temperature_sensor_entity_ids = temp_sensors
        else:
            self._temperature_sensor_entity_ids = [temp_sensors]
            
        self._humidity_sensor_entity_id = options.get(CONF_HUMIDITY_SENSOR, config.get(CONF_HUMIDITY_SENSOR))
        self._actuator_switch_entity_id = options.get(CONF_ACTUATOR_SWITCH, config[CONF_ACTUATOR_SWITCH])
        self._main_thermostat_entity_id = options.get(CONF_MAIN_THERMOSTAT, config.get(CONF_MAIN_THERMOSTAT))
        
        # Other configuration options
        self._cold_tolerance = options.get(CONF_COLD_TOLERANCE, config.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE))
        self._hot_tolerance = options.get(CONF_HOT_TOLERANCE, config.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE))
        self._attr_min_temp = options.get(CONF_MIN_TEMP, config.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP))
        self._attr_max_temp = options.get(CONF_MAX_TEMP, config.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP))
        self._attr_target_temperature = options.get(CONF_TARGET_TEMP, config.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP))
        self._attr_target_temperature_low = options.get(CONF_TARGET_TEMP_LOW, config.get(CONF_TARGET_TEMP_LOW, DEFAULT_TARGET_TEMP_LOW))
        self._attr_target_temperature_high = options.get(CONF_TARGET_TEMP_HIGH, config.get(CONF_TARGET_TEMP_HIGH, DEFAULT_TARGET_TEMP_HIGH))
        self._attr_precision = DEFAULT_PRECISION
        
        # Set initial HVAC mode
        self._attr_hvac_mode = options.get(CONF_INITIAL_HVAC_MODE, config.get(CONF_INITIAL_HVAC_MODE, HVACMode.OFF))
        
        # State variables
        self._attr_current_temperature = None
        self._attr_current_humidity = None
        self._attr_hvac_action = HVACAction.OFF
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        
        # Supported features and modes
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            
        self._attr_hvac_modes = HVAC_MODES
        
        # Control variables
        self._active = False
        self._cur_temp = None
        self._cur_humidity = None
        self._temp_lock = asyncio.Lock()
        self._on_by_us = False

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
        if self._humidity_sensor_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._humidity_sensor_entity_id], self._async_sensor_changed
                )
            )
        
        # Add listener for main thermostat if configured
        if self._main_thermostat_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._main_thermostat_entity_id], self._async_main_thermostat_changed
                )
            )

        # Add listener for actuator switch
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._actuator_switch_entity_id], self._async_switch_changed
            )
        )

        # Check if we have a saved state
        if (old_state := await self.async_get_last_state()) is not None:
            # If we have no initial temperature, restore
            if self._attr_target_temperature is None:
                # If we have a previously saved temperature
                if old_state.attributes.get(ATTR_TEMPERATURE) is None:
                    self._attr_target_temperature = self.min_temp
                    _LOGGER.warning(
                        "Undefined target temperature, falling back to %s",
                        self._attr_target_temperature,
                    )
                else:
                    self._attr_target_temperature = float(old_state.attributes[ATTR_TEMPERATURE])

            if old_state.state and old_state.state != STATE_UNKNOWN:
                self._attr_hvac_mode = HVACMode(old_state.state)

        else:
            # No previous state, set some defaults
            if self._attr_target_temperature is None:
                self._attr_target_temperature = self.min_temp
            _LOGGER.warning("No previously saved temperature, setting to %s", self._attr_target_temperature)

        # Set initial temperature and humidity
        self._async_update_temp(None)
        if self._humidity_sensor_entity_id:
            self._async_update_humidity(None)
        
        # Set initial main thermostat state
        if self._main_thermostat_entity_id:
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
            # Collect temperatures from all sensors
            temperatures = []
            valid_sensors = []
            
            for sensor_id in self._temperature_sensor_entity_ids:
                sensor_state = self.hass.states.get(sensor_id)
                if sensor_state is not None and sensor_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                    try:
                        temp = float(sensor_state.state)
                        temperatures.append(temp)
                        valid_sensors.append(sensor_id)
                    except ValueError as ex:
                        _LOGGER.warning("Unable to parse temperature from sensor %s: %s", sensor_id, ex)
            
            if not temperatures:
                _LOGGER.warning("No valid temperature readings from any sensors")
                return
            
            # Calculate average temperature
            avg_temp = sum(temperatures) / len(temperatures)
            self._cur_temp = avg_temp
            self._attr_current_temperature = avg_temp
            
            _LOGGER.debug(
                "Updated temperature: average %.2f°F from %d sensors (%s)",
                avg_temp,
                len(temperatures),
                ", ".join([f"{sensor}: {temp:.1f}" for sensor, temp in zip(valid_sensors, temperatures)])
            )
        except Exception as ex:
            _LOGGER.error("Error updating temperature: %s", ex)

    @callback
    def _async_update_humidity(self, state) -> None:
        """Update thermostat with latest state from humidity sensor."""
        try:
            if state is None and self._humidity_sensor_entity_id is not None:
                state = self.hass.states.get(self._humidity_sensor_entity_id)

            if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                return

            cur_humidity = int(float(state.state))
            self._cur_humidity = cur_humidity
            self._attr_current_humidity = cur_humidity
        except (ValueError, AttributeError) as ex:
            _LOGGER.error("Unable to update from humidity sensor: %s", ex)
        except Exception as ex:
            _LOGGER.error("Unexpected error updating humidity: %s", ex)

    @callback
    def _async_update_main_thermostat_state(self, state) -> None:
        """Update thermostat action based on main thermostat state."""
        try:
            if state is None and self._main_thermostat_entity_id is not None:
                state = self.hass.states.get(self._main_thermostat_entity_id)

            if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                return

            # Map main thermostat's hvac_action to our hvac_action
            main_action = state.attributes.get("hvac_action", HVACAction.OFF) if state.attributes else HVACAction.OFF
            
            if main_action == HVACAction.HEATING:
                self._attr_hvac_action = HVACAction.HEATING
            elif main_action == HVACAction.COOLING:
                self._attr_hvac_action = HVACAction.COOLING
            elif main_action == HVACAction.FAN:
                self._attr_hvac_action = HVACAction.FAN
            elif main_action == HVACAction.IDLE:
                self._attr_hvac_action = HVACAction.IDLE
            else:
                self._attr_hvac_action = HVACAction.OFF
        except Exception as ex:
            _LOGGER.error("Error updating main thermostat state: %s", ex)
            self._attr_hvac_action = HVACAction.OFF

    @callback
    def _async_sensor_changed(self, event) -> None:
        """Handle temperature/humidity sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        entity_id = event.data.get("entity_id")
        
        if entity_id in self._temperature_sensor_entity_ids:
            self._async_update_temp(new_state)
        elif entity_id == self._humidity_sensor_entity_id:
            self._async_update_humidity(new_state)
            
        self.async_write_ha_state()
        # Use async_create_task with proper error handling
        task = self.hass.async_create_task(self._async_control_heating_cooling())
        task.add_done_callback(self._handle_control_task_done)

    @callback
    def _async_main_thermostat_changed(self, event) -> None:
        """Handle main thermostat state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
            
        self._async_update_main_thermostat_state(new_state)
        self.async_write_ha_state()

    @callback
    def _async_switch_changed(self, event) -> None:
        """Handle actuator switch state changes."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
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

                # If we don't have a main thermostat, we control based on our own logic
                if not self._main_thermostat_entity_id:
                    await self._async_control_based_on_temperature()
                else:
                    # If we have a main thermostat, we follow its state but still control our actuator
                    await self._async_control_based_on_main_thermostat()
        except Exception as ex:
            _LOGGER.error("Error in control heating/cooling: %s", ex)

    async def _async_control_based_on_temperature(self) -> None:
        """Control heating/cooling based on temperature difference."""
        try:
            too_cold = self._attr_target_temperature >= self._cur_temp + self._cold_tolerance
            too_hot = self._cur_temp >= self._attr_target_temperature + self._hot_tolerance
            
            current_device_active = await self._async_is_device_active()
            if current_device_active:
                if self._attr_hvac_mode == HVACMode.HEAT and not too_cold:
                    _LOGGER.info("Turning off heater %s", self._actuator_switch_entity_id)
                    await self._async_actuator_turn_off()
                elif self._attr_hvac_mode == HVACMode.COOL and not too_hot:
                    _LOGGER.info("Turning off cooler %s", self._actuator_switch_entity_id)
                    await self._async_actuator_turn_off()
                elif self._attr_hvac_mode == HVACMode.AUTO:
                    if not too_cold and not too_hot:
                        _LOGGER.info("Turning off actuator %s", self._actuator_switch_entity_id)
                        await self._async_actuator_turn_off()
            else:
                if self._attr_hvac_mode == HVACMode.HEAT and too_cold:
                    _LOGGER.info("Turning on heater %s", self._actuator_switch_entity_id)
                    await self._async_actuator_turn_on()
                elif self._attr_hvac_mode == HVACMode.COOL and too_hot:
                    _LOGGER.info("Turning on cooler %s", self._actuator_switch_entity_id)
                    await self._async_actuator_turn_on()
                elif self._attr_hvac_mode == HVACMode.AUTO:
                    if too_cold:
                        _LOGGER.info("Turning on heater (auto) %s", self._actuator_switch_entity_id)
                        await self._async_actuator_turn_on()
                    elif too_hot:
                        _LOGGER.info("Turning on cooler (auto) %s", self._actuator_switch_entity_id)
                        await self._async_actuator_turn_on()
        except Exception as ex:
            _LOGGER.error("Error in temperature-based control: %s", ex)

    async def _async_control_based_on_main_thermostat(self) -> None:
        """Control actuator based on main thermostat state and our temperature."""
        try:
            if self._main_thermostat_entity_id is None: 
                return;
            main_state = self.hass.states.get(self._main_thermostat_entity_id)
            if main_state is None:
                _LOGGER.warning("Main thermostat %s not found", self._main_thermostat_entity_id)
                return
                
            main_action = main_state.attributes.get("hvac_action", HVACAction.OFF)
            
            # Only activate our actuator if the main thermostat is actively heating/cooling
            # and our temperature conditions warrant it
            should_activate = False
            
            if main_action == HVACAction.HEATING and self._attr_hvac_mode in [HVACMode.HEAT, HVACMode.AUTO]:
                too_cold = self._attr_target_temperature >= self._cur_temp + self._cold_tolerance
                should_activate = too_cold
            elif main_action == HVACAction.COOLING and self._attr_hvac_mode in [HVACMode.COOL, HVACMode.AUTO]:
                too_hot = self._cur_temp >= self._attr_target_temperature + self._hot_tolerance
                should_activate = too_hot
                
            current_device_active = await self._async_is_device_active()
            if should_activate and not current_device_active:
                _LOGGER.info("Main thermostat active, turning on actuator %s", self._actuator_switch_entity_id)
                await self._async_actuator_turn_on()
            elif not should_activate and current_device_active:
                _LOGGER.info("Conditions not met, turning off actuator %s", self._actuator_switch_entity_id)
                await self._async_actuator_turn_off()
        except Exception as ex:
            _LOGGER.error("Error in main thermostat control: %s", ex)

    async def _async_is_device_active(self) -> bool:
        """Check if the actuator switch is currently on."""
        try:
            state = self.hass.states.get(self._actuator_switch_entity_id)
            return state is not None and state.state == "on"
        except Exception as ex:
            _LOGGER.error("Error checking device state: %s", ex)
            return False

    async def _async_actuator_turn_on(self) -> None:
        """Turn actuator on."""
        try:
            data = {"entity_id": self._actuator_switch_entity_id}
            self._on_by_us = True
            await self.hass.services.async_call("switch", SERVICE_TURN_ON, data, blocking=False)
        except Exception as ex:
            _LOGGER.error("Error turning on actuator %s: %s", self._actuator_switch_entity_id, ex)
            self._on_by_us = False

    async def _async_actuator_turn_off(self) -> None:
        """Turn actuator off."""
        try:
            data = {"entity_id": self._actuator_switch_entity_id}
            self._on_by_us = True
            await self.hass.services.async_call("switch", SERVICE_TURN_OFF, data, blocking=False)
        except Exception as ex:
            _LOGGER.error("Error turning off actuator %s: %s", self._actuator_switch_entity_id, ex)
            self._on_by_us = False

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            self._attr_hvac_mode = HVACMode.HEAT
            await self._async_control_heating_cooling()
        elif hvac_mode == HVACMode.COOL:
            self._attr_hvac_mode = HVACMode.COOL
            await self._async_control_heating_cooling()
        elif hvac_mode == HVACMode.AUTO:
            self._attr_hvac_mode = HVACMode.AUTO
            await self._async_control_heating_cooling()
        elif hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.OFF
            if await self._async_is_device_active():
                await self._async_actuator_turn_off()
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return
        # Ensure we update the display
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._attr_target_temperature = temperature
        await self._async_control_heating_cooling()
        self.async_write_ha_state()

    @callback
    def _handle_control_task_done(self, task) -> None:
        """Handle completion of control task."""
        if task.exception():
            _LOGGER.error("Control task failed: %s", task.exception())
    
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
