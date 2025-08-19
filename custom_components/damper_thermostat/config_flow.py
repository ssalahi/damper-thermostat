"""Config flow for Damper Thermostat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, OptionsFlowWithReload
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ACTUATOR_SWITCH,
    CONF_ACTUATOR_SWITCHES,
    CONF_MAX_SWITCHES_OFF,
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
    DEFAULT_MAX_SWITCHES_OFF,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor", 
                device_class="temperature",
                multiple=True
            )
        ),
        vol.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        ),
        vol.Required(CONF_MAIN_THERMOSTAT): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        ),
        vol.Required(CONF_ACTUATOR_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Required(CONF_ACTUATOR_SWITCHES): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="switch",
                multiple=True
            )
        ),
        vol.Optional(CONF_MAX_SWITCHES_OFF, default=DEFAULT_MAX_SWITCHES_OFF): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=10)
        ),
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.All(
            vol.Coerce(float), vol.Range(min=40, max=70)
        ),
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.All(
            vol.Coerce(float), vol.Range(min=70, max=100)
        ),
        vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.All(
            vol.Coerce(float), vol.Range(min=40, max=80)
        ),
        vol.Optional(CONF_TARGET_TEMP_LOW, default=DEFAULT_TARGET_TEMP_LOW): vol.All(
            vol.Coerce(float), vol.Range(min=60, max=80)
        ),
        vol.Optional(CONF_TARGET_TEMP_HIGH, default=DEFAULT_TARGET_TEMP_HIGH): vol.All(
            vol.Coerce(float), vol.Range(min=70, max=90)
        ),
        vol.Optional(CONF_INITIAL_HVAC_MODE, default=HVACMode.AUTO): vol.In(
            [HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.HEAT_COOL, HVACMode.OFF]
        ),
    }
)


class DamperThermostatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Damper Thermostat."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        # Validate entities exist
        errors.update(await self._validate_entities(user_input))
        
        # Validate temperature ranges
        errors.update(self._validate_temperature_ranges(user_input))

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        # Create a unique ID based on the actuator switch entity
        actuator_switch = user_input[CONF_ACTUATOR_SWITCH]
        await self.async_set_unique_id(f"{actuator_switch}_{DOMAIN}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def _validate_entities(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate that all required entities exist."""
        errors = {}

        # Validate temperature sensors (can be single entity or list of entities)
        temp_sensors = user_input[CONF_TEMPERATURE_SENSOR]
        if isinstance(temp_sensors, str):
            # Single sensor
            if not self.hass.states.get(temp_sensors):
                errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
        elif isinstance(temp_sensors, list):
            # Multiple sensors
            for sensor in temp_sensors:
                if not self.hass.states.get(sensor):
                    errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
                    break
        else:
            errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
        
        # Validate optional humidity sensor
        if user_input.get(CONF_HUMIDITY_SENSOR) and not self.hass.states.get(user_input[CONF_HUMIDITY_SENSOR]):
            errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"
            
        # Validate main actuator switch
        if not self.hass.states.get(user_input[CONF_ACTUATOR_SWITCH]):
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
            
        # Validate actuator switches list
        actuator_switches = user_input[CONF_ACTUATOR_SWITCHES]
        if isinstance(actuator_switches, list):
            for switch in actuator_switches:
                if not self.hass.states.get(switch):
                    errors[CONF_ACTUATOR_SWITCHES] = "entity_not_found"
                    break
        else:
            errors[CONF_ACTUATOR_SWITCHES] = "entity_not_found"
            
        # Validate main thermostat
        if not self.hass.states.get(user_input[CONF_MAIN_THERMOSTAT]):
            errors[CONF_MAIN_THERMOSTAT] = "entity_not_found"

        return errors

    def _validate_temperature_ranges(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate temperature range settings."""
        errors = {}
        
        min_temp = user_input.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
        max_temp = user_input.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
        target_temp = user_input.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
        target_temp_low = user_input.get(CONF_TARGET_TEMP_LOW, DEFAULT_TARGET_TEMP_LOW)
        target_temp_high = user_input.get(CONF_TARGET_TEMP_HIGH, DEFAULT_TARGET_TEMP_HIGH)

        if min_temp >= max_temp:
            errors[CONF_MIN_TEMP] = "min_temp_must_be_less_than_max_temp"
        
        if target_temp < min_temp or target_temp > max_temp:
            errors[CONF_TARGET_TEMP] = "target_temp_out_of_range"
        
        if target_temp_low >= target_temp_high:
            errors[CONF_TARGET_TEMP_LOW] = "temp_low_must_be_less_than_temp_high"
        
        if target_temp_low < min_temp or target_temp_high > max_temp:
            errors[CONF_TARGET_TEMP_LOW] = "temp_range_out_of_bounds"

        return errors

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return DamperThermostatOptionsFlow()


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor", 
                device_class="temperature",
                multiple=True
            )
        ),
        vol.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        ),
        vol.Required(CONF_MAIN_THERMOSTAT): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        ),
        vol.Required(CONF_ACTUATOR_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Required(CONF_ACTUATOR_SWITCHES): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="switch",
                multiple=True
            )
        ),
        vol.Optional(CONF_MAX_SWITCHES_OFF): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=10)
        ),
        vol.Optional(CONF_COLD_TOLERANCE): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
        vol.Optional(CONF_HOT_TOLERANCE): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
        vol.Optional(CONF_MIN_TEMP): vol.All(
            vol.Coerce(float), vol.Range(min=40, max=70)
        ),
        vol.Optional(CONF_MAX_TEMP): vol.All(
            vol.Coerce(float), vol.Range(min=70, max=100)
        ),
    }
)


class DamperThermostatOptionsFlow(OptionsFlowWithReload):
    """Handle options flow for Damper Thermostat."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Basic validation for temperature ranges
            errors = {}
            min_temp = user_input.get(CONF_MIN_TEMP)
            max_temp = user_input.get(CONF_MAX_TEMP)
            
            if min_temp is not None and max_temp is not None and min_temp >= max_temp:
                errors[CONF_MIN_TEMP] = "min_temp_must_be_less_than_max_temp"

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self.add_suggested_values_to_schema(
                        OPTIONS_SCHEMA, user_input
                    ),
                    errors=errors,
                    description_placeholders={
                        "name": self.config_entry.title,
                    },
                )
            
            # Update the config entry title if name changed
            if user_input.get(CONF_NAME) and user_input[CONF_NAME] != self.config_entry.title:
                self.hass.config_entries.async_update_entry(
                    self.config_entry, title=user_input[CONF_NAME]
                )
            
            return self.async_create_entry(data=user_input)

        # Merge current config data and options for suggested values
        suggested_values = {**self.config_entry.data, **self.config_entry.options}
        
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, suggested_values
            ),
            description_placeholders={
                "name": self.config_entry.title,
            },
        )
