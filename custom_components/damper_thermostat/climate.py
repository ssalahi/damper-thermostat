"""
Damper Thermostat Integration for Home Assistant
A custom thermostat component with advanced features extending Generic Thermostat functionality.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional
from const import *

import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity
)
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    PRESET_AWAY,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACAction,
    HVACMode
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    EVENT_HOMEASSISTANT_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import DOMAIN as HA_DOMAIN, CoreState, HomeAssistant, callback
from homeassistant.helpers import condition
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HEATER): cv.entity_id,
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_HUMIDITY_SENSOR): cv.entity_id,
        vol.Optional(CONF_MAIN_THERMOSTAT): cv.entity_id,
        vol.Optional(CONF_AC_MODE, default=False): cv.boolean,
        vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(CONF_KEEP_ALIVE): vol.All(cv.time_period, cv.positive_timedelta),
        vol.Optional(CONF_INITIAL_HVAC_MODE): vol.In(
            [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF]
        ),
        vol.Optional(CONF_AWAY_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION): vol.In(
            [UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT]
        ),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType = None,
) -> None:
    """Set up the damper thermostat platform."""
    await async_setup_reload_service(hass, DOMAIN, ["climate"])
    async_add_entities(
        [
            DamperThermostat(
                hass,
                config[CONF_NAME],
                config[CONF_HEATER],
                config[CONF_SENSOR],
                config.get(CONF_HUMIDITY_SENSOR),
                config.get(CONF_MAIN_THERMOSTAT),
                config.get(CONF_MIN_TEMP),
                config.get(CONF_MAX_TEMP),
                config[CONF_TARGET_TEMP],
                config[CONF_AC_MODE],
                config[CONF_COLD_TOLERANCE],
                config[CONF_HOT_TOLERANCE],
                config.get(CONF_KEEP_ALIVE),
                config.get(CONF_INITIAL_HVAC_MODE),
                config.get(CONF_AWAY_TEMP),
                config.get(CONF_PRECISION),
                config.get(CONF_UNIQUE_ID),
            )
        ]
    )


class DamperThermostat(ClimateEntity, RestoreEntity):
    """Damper thermostat with additional features."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        heater_entity_id: str,
        sensor_entity_id: str,
        humidity_sensor_entity_id: Optional[str],
        main_thermostat_entity_id: Optional[str],
        min_temp: Optional[float],
        max_temp: Optional[float],
        target_temp: Optional[float],
        ac_mode: bool,
        cold_tolerance: float,
        hot_tolerance: float,
        keep_alive: Optional[timedelta],
        initial_hvac_mode: Optional[HVACMode],
        away_temp: Optional[float],
        precision: Optional[float],
        unique_id: Optional[str],
    ) -> None:
        """Initialize the thermostat."""
        self.hass = hass
        self._name = name
        self._heater_entity_id = heater_entity_id
        self._sensor_entity_id = sensor_entity_id
        self._humidity_sensor_entity_id = humidity_sensor_entity_id
        self._main_thermostat_entity_id = main_thermostat_entity_id
        self._ac_mode = ac_mode
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._cold_tolerance = cold_tolerance
        self._hot_tolerance = hot_tolerance
        self._keep_alive = keep_alive
        self._initial_hvac_mode = initial_hvac_mode
        self._away_temp = away_temp
        self._precision = precision
        self._attr_unique_id = unique_id

        self._hvac_mode = initial_hvac_mode or HVACMode.OFF
        self._target_temp = target_temp
        self._current_temp = None
        self._current_humidity = None
        self._hvac_action = HVACAction.OFF
        self._preset_mode = PRESET_NONE
        
        # Track main thermostat state
        self._main_thermostat_hvac_action = HVACAction.OFF
        
        # Support for multiple HVAC modes
        self._hvac_list = [HVACMode.OFF]
        if ac_mode:
            self._hvac_list.extend([HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO])
        else:
            self._hvac_list.append(HVACMode.HEAT)

        self._active = False
        self._cur_temp = None
        self._temp_precision = self._precision
        self._enabled = True

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener for temperature sensor
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._sensor_entity_id], self._async_sensor_changed
            )
        )

        # Add listener for humidity sensor
        if self._humidity_sensor_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._humidity_sensor_entity_id], self._async_humidity_sensor_changed
                )
            )

        # Add listener for main thermostat
        if self._main_thermostat_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._main_thermostat_entity_id], self._async_main_thermostat_changed
                )
            )

        # Add listener for heater/cooler
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._heater_entity_id], self._async_switch_changed
            )
        )

        # Set up keep alive
        if self._keep_alive:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._async_keep_alive, self._keep_alive
                )
            )

        @callback
        def _async_startup(*_):
            """Init on startup."""
            self.hass.async_create_task(self._async_startup())

        if self.hass.state == CoreState.running:
            await self._async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        # Check if we have an old state
        if (old_state := await self.async_get_last_state()) is not None:
            # If we have no initial temperature, restore
            if self._target_temp is None:
                # If we have a previously saved temperature
                if old_state.attributes.get(ATTR_TEMPERATURE) is None:
                    if self._ac_mode:
                        self._target_temp = self.max_temp
                    else:
                        self._target_temp = self.min_temp
                    _LOGGER.warning(
                        "Undefined target temperature, falling back to %s",
                        self._target_temp,
                    )
                else:
                    self._target_temp = float(old_state.attributes[ATTR_TEMPERATURE])
            if old_state.attributes.get(ATTR_PRESET_MODE):
                self._preset_mode = old_state.attributes.get(ATTR_PRESET_MODE)
            if not self._hvac_mode and old_state.state:
                self._hvac_mode = old_state.state

        else:
            # No previous state, try and restore defaults
            if self._target_temp is None:
                if self._ac_mode:
                    self._target_temp = self.max_temp
                else:
                    self._target_temp = self.min_temp
            _LOGGER.warning(
                "No previously saved temperature, setting to %s", self._target_temp
            )

    async def _async_startup(self):
        """Run when entity is ready."""
        sensor_state = self.hass.states.get(self._sensor_entity_id)
        if sensor_state and sensor_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._async_update_temp(sensor_state)
            
        # Update humidity if sensor available
        if self._humidity_sensor_entity_id:
            humidity_state = self.hass.states.get(self._humidity_sensor_entity_id)
            if humidity_state and humidity_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                self._async_update_humidity(humidity_state)
                
        # Update main thermostat state
        if self._main_thermostat_entity_id:
            main_thermostat_state = self.hass.states.get(self._main_thermostat_entity_id)
            if main_thermostat_state:
                self._async_update_main_thermostat(main_thermostat_state)

        switch_state = self.hass.states.get(self._heater_entity_id)
        if switch_state and switch_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._async_update_hvac_action()

    @callback
    def _async_sensor_changed(self, event):
        """Handle temperature sensor changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_temp(new_state)
        self.async_write_ha_state()
        self.hass.async_create_task(self._async_control_heating())

    @callback
    def _async_humidity_sensor_changed(self, event):
        """Handle humidity sensor changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_humidity(new_state)
        self.async_write_ha_state()

    @callback
    def _async_main_thermostat_changed(self, event):
        """Handle main thermostat changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        self._async_update_main_thermostat(new_state)
        self.async_write_ha_state()

    @callback
    def _async_switch_changed(self, event):
        """Handle heater switch changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._async_update_hvac_action()
        self.async_write_ha_state()

    @callback
    def _async_keep_alive(self, time):
        """Call at keep alive interval."""
        self.hass.async_create_task(self._async_control_heating())

    @callback
    def _async_update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        try:
            cur_temp = float(state.state)
            if self._current_temp != cur_temp:
                self._current_temp = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    @callback
    def _async_update_humidity(self, state):
        """Update thermostat with latest humidity from sensor."""
        try:
            cur_humidity = float(state.state)
            if self._current_humidity != cur_humidity:
                self._current_humidity = cur_humidity
        except ValueError as ex:
            _LOGGER.error("Unable to update humidity from sensor: %s", ex)

    @callback
    def _async_update_main_thermostat(self, state):
        """Update HVAC action based on main thermostat."""
        if hasattr(state, 'attributes') and 'hvac_action' in state.attributes:
            main_action = state.attributes.get('hvac_action')
            if main_action != self._main_thermostat_hvac_action:
                self._main_thermostat_hvac_action = main_action
                # Update our displayed hvac_action based on main thermostat
                if self._main_thermostat_entity_id:
                    self._hvac_action = main_action or HVACAction.OFF

    @callback
    def _async_update_hvac_action(self):
        """Update thermostat's HVAC action based on switch state."""
        switch_state = self.hass.states.get(self._heater_entity_id)
        if not switch_state:
            return

        # If we have a main thermostat, use its action instead
        if self._main_thermostat_entity_id:
            return

        if self._hvac_mode == HVACMode.OFF:
            self._hvac_action = HVACAction.OFF
        elif switch_state.state == STATE_ON:
            if self._hvac_mode == HVACMode.HEAT:
                self._hvac_action = HVACAction.HEATING
            elif self._hvac_mode == HVACMode.COOL:
                self._hvac_action = HVACAction.COOLING
            else:
                self._hvac_action = HVACAction.HEATING  # Default
        else:
            self._hvac_action = HVACAction.IDLE

    async def _async_control_heating(self):
        """Control the heating/cooling."""
        if not self._active and None not in (self._current_temp, self._target_temp):
            self._active = True
            _LOGGER.info(
                "Obtained current and target temperature. "
                "Damper thermostat active. %s, %s",
                self._current_temp,
                self._target_temp,
            )

        if not self._active or self._hvac_mode == HVACMode.OFF:
            return

        # Get tolerance values
        if self._preset_mode == PRESET_AWAY and self._away_temp:
            target_temp = self._away_temp
        else:
            target_temp = self._target_temp

        cold_tolerance = self._cold_tolerance
        hot_tolerance = self._hot_tolerance

        # Determine if we need heating or cooling
        if self._hvac_mode == HVACMode.AUTO:
            # Auto mode logic
            if self._current_temp < target_temp - cold_tolerance:
                # Need heating
                await self._async_turn_on()
            elif self._current_temp > target_temp + hot_tolerance:
                # Need cooling (if in AC mode)
                if self._ac_mode:
                    await self._async_turn_on()
                else:
                    await self._async_turn_off()
            else:
                # In comfortable range
                await self._async_turn_off()
        elif self._hvac_mode == HVACMode.HEAT:
            # Heat mode
            if self._current_temp < target_temp - cold_tolerance:
                await self._async_turn_on()
            elif self._current_temp > target_temp + hot_tolerance:
                await self._async_turn_off()
        elif self._hvac_mode == HVACMode.COOL:
            # Cool mode
            if self._current_temp > target_temp + hot_tolerance:
                await self._async_turn_on()
            elif self._current_temp < target_temp - cold_tolerance:
                await self._async_turn_off()

    async def _async_turn_on(self):
        """Turn heater/cooler on."""
        data = {ATTR_ENTITY_ID: self._heater_entity_id}
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_ON, data)

    async def _async_turn_off(self):
        """Turn heater/cooler off."""
        data = {ATTR_ENTITY_ID: self._heater_entity_id}
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_OFF, data)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def precision(self):
        """Return the precision of the system."""
        if self._temp_precision is not None:
            return self._temp_precision
        return super().precision

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self.precision

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self.hass.config.units.temperature_unit

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._current_temp

    @property
    def current_humidity(self):
        """Return the sensor humidity."""
        return self._current_humidity

    @property
    def hvac_mode(self):
        """Return current operation."""
        return self._hvac_mode

    @property
    def hvac_action(self):
        """Return the current HVAC action."""
        return self._hvac_action

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return self._hvac_list

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return [PRESET_NONE, PRESET_AWAY]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            self._hvac_mode = HVACMode.HEAT
            await self._async_control_heating()
        elif hvac_mode == HVACMode.COOL:
            self._hvac_mode = HVACMode.COOL
            await self._async_control_heating()
        elif hvac_mode == HVACMode.AUTO:
            self._hvac_mode = HVACMode.AUTO
            await self._async_control_heating()
        elif hvac_mode == HVACMode.OFF:
            self._hvac_mode = HVACMode.OFF
            if self._active:
                await self._async_turn_off()
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return
        # Ensure we update the display
        self._async_update_hvac_action()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temp = temperature
        await self._async_control_heating()
        self.async_write_ha_state()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._min_temp is not None:
            return self._min_temp

        # get default temp from super class
        return super().min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._max_temp is not None:
            return self._max_temp

        # Get default temp from super class
        return super().max_temp

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        if preset_mode == PRESET_AWAY and self._away_temp:
            self._preset_mode = PRESET_AWAY
        else:
            self._preset_mode = PRESET_NONE

        await self._async_control_heating()
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attributes = {}
        
        if self._humidity_sensor_entity_id and self._current_humidity is not None:
            attributes["current_humidity"] = self._current_humidity
            
        if self._main_thermostat_entity_id:
            attributes["main_thermostat"] = self._main_thermostat_entity_id
            attributes["main_thermostat_hvac_action"] = self._main_thermostat_hvac_action
            
        attributes.update({
            "cold_tolerance": self._cold_tolerance,
            "hot_tolerance": self._hot_tolerance,
            "sensor_entity_id": self._sensor_entity_id,
            "heater_entity_id": self._heater_entity_id,
        })
        
        return attributes