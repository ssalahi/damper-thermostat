"""Config flow for Damper Thermostat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

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
    CONF_INITIAL_HVAC_MODE,
    DEFAULT_TOLERANCE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP
)

_LOGGER = logging.getLogger(__name__)

# Define schema as a function to avoid recreation issues
def _get_user_schema() -> vol.Schema:
    """Get the user schema."""
    return vol.Schema(
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
            vol.Required(CONF_ACTUATOR_SWITCH): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch")
            ),
            vol.Optional(CONF_MAIN_THERMOSTAT): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10.0)
            ),
            vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10.0)
            ),
            vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.All(
                vol.Coerce(float), vol.Range(min=-40, max=70)
            ),
            vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.All(
                vol.Coerce(float), vol.Range(min=70, max=100)
            ),
            vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.All(
                vol.Coerce(float), vol.Range(min=-40, max=80)
            ),
            vol.Optional(CONF_INITIAL_HVAC_MODE, default=HVACMode.AUTO): vol.In(
                [HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.OFF]
            ),
        }
    )


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Damper Thermostat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Create unique ID based on actuator switch (primary identifier)
                actuator_switch = user_input.get(CONF_ACTUATOR_SWITCH)
                if actuator_switch:
                    unique_id = f"{DOMAIN}_{actuator_switch}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                # Validate entities exist
                errors = await self._validate_entities(user_input)
                
                if not errors:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], 
                        data=user_input
                    )

            except Exception as ex:
                _LOGGER.exception("Unexpected error during validation: %s", ex)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", 
            data_schema=_get_user_schema(), 
            errors=errors
        )

    async def _validate_entities(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate that all entities exist."""
        errors: dict[str, str] = {}

        # Validate temperature sensors (can be single entity or list of entities)
        temp_sensors = user_input.get(CONF_TEMPERATURE_SENSOR)
        if not temp_sensors:
            errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
        elif isinstance(temp_sensors, str):
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
        
        # Validate humidity sensor
        humidity_sensor = user_input.get(CONF_HUMIDITY_SENSOR)
        if humidity_sensor and not self.hass.states.get(humidity_sensor):
            errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"
                
        # Validate actuator switch
        actuator_switch = user_input.get(CONF_ACTUATOR_SWITCH)
        if not actuator_switch:
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
        elif not self.hass.states.get(actuator_switch):
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
                
        # Validate main thermostat
        main_thermostat = user_input.get(CONF_MAIN_THERMOSTAT)
        if main_thermostat and not self.hass.states.get(main_thermostat):
            errors[CONF_MAIN_THERMOSTAT] = "entity_not_found"

        return errors

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Damper Thermostat."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Validate entities exist
                errors = await self._validate_options_entities(user_input)
                
                if not errors:
                    # Update the config entry title if name changed
                    if user_input.get(CONF_NAME) and user_input[CONF_NAME] != self.config_entry.title:
                        self.hass.config_entries.async_update_entry(
                            self.config_entry, title=user_input[CONF_NAME]
                        )
                    
                    return self.async_create_entry(title="", data=user_input)

            except Exception as ex:
                _LOGGER.exception("Unexpected error during options validation: %s", ex)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
            errors=errors,
            description_placeholders={
                "name": self.config_entry.title,
            },
        )

    def _get_options_schema(self) -> vol.Schema:
        """Get the options schema with current values."""
        try:
            # Get current values from both config entry data and options
            current_data = self.config_entry.data or {}
            current_options = self.config_entry.options or {}
            
            # Use options if available, otherwise fall back to config data
            def get_current_value(key: str, default: Any) -> Any:
                try:
                    return current_options.get(key, current_data.get(key, default))
                except (AttributeError, TypeError):
                    return default
            
            return vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, 
                        default=get_current_value(CONF_NAME, self.config_entry.title or "Damper Thermostat")
                    ): cv.string,
                    vol.Required(
                        CONF_TEMPERATURE_SENSOR,
                        default=get_current_value(CONF_TEMPERATURE_SENSOR, [])
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor", 
                            device_class="temperature",
                            multiple=True
                        )
                    ),
                    vol.Optional(
                        CONF_HUMIDITY_SENSOR,
                        default=get_current_value(CONF_HUMIDITY_SENSOR, None)
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
                    ),
                    vol.Required(
                        CONF_ACTUATOR_SWITCH,
                        default=get_current_value(CONF_ACTUATOR_SWITCH, "")
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch")
                    ),
                    vol.Optional(
                        CONF_MAIN_THERMOSTAT,
                        default=get_current_value(CONF_MAIN_THERMOSTAT, None)
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="climate")
                    ),
                    vol.Optional(
                        CONF_COLD_TOLERANCE, 
                        default=get_current_value(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
                    vol.Optional(
                        CONF_HOT_TOLERANCE, 
                        default=get_current_value(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
                    vol.Optional(
                        CONF_MIN_TEMP, 
                        default=get_current_value(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
                    ): vol.All(vol.Coerce(float), vol.Range(min=-40, max=70)),
                    vol.Optional(
                        CONF_MAX_TEMP, 
                        default=get_current_value(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
                    ): vol.All(vol.Coerce(float), vol.Range(min=70, max=100)),
                    vol.Optional(
                        CONF_TARGET_TEMP, 
                        default=get_current_value(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
                    ): vol.All(vol.Coerce(float), vol.Range(min=-60, max=80)),
                    vol.Optional(
                        CONF_INITIAL_HVAC_MODE, 
                        default=get_current_value(CONF_INITIAL_HVAC_MODE, HVACMode.AUTO)
                    ): vol.In([HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.OFF]),
                }
            )
        except Exception as ex:
            _LOGGER.exception("Error creating options schema: %s", ex)
            # Return a minimal schema as fallback
            return vol.Schema({
                vol.Optional(CONF_NAME, default="Damper Thermostat"): cv.string,
            })

    async def _validate_options_entities(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate that all entities exist for options flow."""
        errors: dict[str, str] = {}

        # Validate temperature sensors (can be single entity or list of entities)
        temp_sensors = user_input.get(CONF_TEMPERATURE_SENSOR)
        if not temp_sensors:
            errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
        elif isinstance(temp_sensors, str):
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
        
        # Validate humidity sensor
        humidity_sensor = user_input.get(CONF_HUMIDITY_SENSOR)
        if humidity_sensor and not self.hass.states.get(humidity_sensor):
            errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"
                
        # Validate actuator switch
        actuator_switch = user_input.get(CONF_ACTUATOR_SWITCH)
        if not actuator_switch:
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
        elif not self.hass.states.get(actuator_switch):
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
                
        # Validate main thermostat
        main_thermostat = user_input.get(CONF_MAIN_THERMOSTAT)
        if main_thermostat and not self.hass.states.get(main_thermostat):
            errors[CONF_MAIN_THERMOSTAT] = "entity_not_found"

        return errors
