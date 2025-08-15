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
from homeassistant.config_entries import SOURCE_RECONFIGURE
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

def _get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the config schema for setup and reconfigure (all options)."""
    if defaults is None:
        defaults = {}
    
    schema_dict = {}
    
    # Name field
    name_default = defaults.get(CONF_NAME)
    if name_default:
        schema_dict[vol.Required(CONF_NAME, default=name_default)] = cv.string
    else:
        schema_dict[vol.Required(CONF_NAME)] = cv.string
    
    # Temperature sensor field
    temp_sensor_default = defaults.get(CONF_TEMPERATURE_SENSOR)
    if temp_sensor_default and (isinstance(temp_sensor_default, list) and len(temp_sensor_default) > 0):
        schema_dict[vol.Required(CONF_TEMPERATURE_SENSOR, default=temp_sensor_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature", multiple=True)
        )
    else:
        schema_dict[vol.Required(CONF_TEMPERATURE_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature", multiple=True)
        )
    
    # Humidity sensor field (optional)
    humidity_sensor_default = defaults.get(CONF_HUMIDITY_SENSOR)
    if humidity_sensor_default:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=humidity_sensor_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )
    else:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )
    
    # Actuator switch field
    actuator_switch_default = defaults.get(CONF_ACTUATOR_SWITCH)
    if actuator_switch_default:
        schema_dict[vol.Required(CONF_ACTUATOR_SWITCH, default=actuator_switch_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        )
    else:
        schema_dict[vol.Required(CONF_ACTUATOR_SWITCH)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        )
    
    # Main thermostat field (optional)
    main_thermostat_default = defaults.get(CONF_MAIN_THERMOSTAT)
    if main_thermostat_default:
        schema_dict[vol.Optional(CONF_MAIN_THERMOSTAT, default=main_thermostat_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )
    else:
        schema_dict[vol.Optional(CONF_MAIN_THERMOSTAT)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )
    
    # Add all the configuration options to setup/reconfigure
    schema_dict.update({
        vol.Optional(
            CONF_COLD_TOLERANCE, 
            default=defaults.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE)
        ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
        vol.Optional(
            CONF_HOT_TOLERANCE, 
            default=defaults.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE)
        ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
        vol.Optional(
            CONF_MIN_TEMP, 
            default=defaults.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
        ): vol.All(vol.Coerce(float), vol.Range(min=-40, max=70)),
        vol.Optional(
            CONF_MAX_TEMP, 
            default=defaults.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
        ): vol.All(vol.Coerce(float), vol.Range(min=70, max=100)),
        vol.Optional(
            CONF_TARGET_TEMP, 
            default=defaults.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
        ): vol.All(vol.Coerce(float), vol.Range(min=-40, max=80)),
        vol.Optional(
            CONF_INITIAL_HVAC_MODE, 
            default=defaults.get(CONF_INITIAL_HVAC_MODE, HVACMode.AUTO)
        ): vol.In([HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.OFF]),
    })
    
    return vol.Schema(schema_dict)

def _get_options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the options schema for device editing."""
    if defaults is None:
        defaults = {}
    
    schema_dict = {}
    
    # Temperature sensor field
    temp_sensor_default = defaults.get(CONF_TEMPERATURE_SENSOR)
    if temp_sensor_default and (isinstance(temp_sensor_default, list) and len(temp_sensor_default) > 0):
        schema_dict[vol.Required(CONF_TEMPERATURE_SENSOR, default=temp_sensor_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature", multiple=True)
        )
    else:
        schema_dict[vol.Required(CONF_TEMPERATURE_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature", multiple=True)
        )
    
    # Humidity sensor field (optional)
    humidity_sensor_default = defaults.get(CONF_HUMIDITY_SENSOR)
    if humidity_sensor_default:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=humidity_sensor_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )
    else:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )
    
    # Main thermostat field (optional)
    main_thermostat_default = defaults.get(CONF_MAIN_THERMOSTAT)
    if main_thermostat_default:
        schema_dict[vol.Optional(CONF_MAIN_THERMOSTAT, default=main_thermostat_default)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )
    else:
        schema_dict[vol.Optional(CONF_MAIN_THERMOSTAT)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )
    
    # Add the frequently adjusted options
    schema_dict.update({
        vol.Optional(
            CONF_COLD_TOLERANCE, 
            default=defaults.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE)
        ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
        vol.Optional(
            CONF_HOT_TOLERANCE, 
            default=defaults.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE)
        ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
        vol.Optional(
            CONF_TARGET_TEMP, 
            default=defaults.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
        ): vol.All(vol.Coerce(float), vol.Range(min=-40, max=80)),
    })
    
    return vol.Schema(schema_dict)

def _get_user_schema() -> vol.Schema:
    """Get the user schema for initial setup (all options)."""
    return _get_config_schema()


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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # For reconfigure, we need to validate the new actuator switch
                # and ensure unique ID consistency
                actuator_switch = user_input.get(CONF_ACTUATOR_SWITCH)
                if actuator_switch:
                    unique_id = f"{DOMAIN}_{actuator_switch}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_mismatch()

                # Validate entities exist
                errors = await self._validate_entities(user_input)
                
                if not errors:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )

            except Exception as ex:
                _LOGGER.exception("Unexpected error during reconfiguration: %s", ex)
                errors["base"] = "unknown"

        # Get current config entry for pre-filling the form
        reconfigure_entry = self._get_reconfigure_entry()
        current_data = reconfigure_entry.data or {}
        
        # Add the entry title as the default name and include all current data
        defaults = {**current_data, CONF_NAME: current_data.get(CONF_NAME, reconfigure_entry.title)}
        
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_config_schema(defaults),
            errors=errors,
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
        
        try:
            # Ensure we have a valid config entry
            if not self.config_entry:
                _LOGGER.error("Config entry is None in options flow init")
                return self.async_abort(reason="unknown")
            
            if user_input is not None:
                try:
                    # Validate options data
                    errors = await self._validate_options_data(user_input)
                    
                    if not errors:
                        # Update the config entry title if name changed
                        current_title = getattr(self.config_entry, 'title', None)
                        if user_input.get(CONF_NAME) and user_input[CONF_NAME] != current_title:
                            self.hass.config_entries.async_update_entry(
                                self.config_entry, title=user_input[CONF_NAME]
                            )
                        
                        return self.async_create_entry(title="", data=user_input)

                except Exception as ex:
                    _LOGGER.exception("Unexpected error during options validation: %s", ex)
                    errors["base"] = "unknown"

            # Get schema safely
            try:
                schema = self._get_options_flow_schema()
            except Exception as ex:
                _LOGGER.exception("Error getting options schema: %s", ex)
                return self.async_abort(reason="unknown")

            # Get title safely
            entry_title = getattr(self.config_entry, 'title', None) or "Damper Thermostat"

            return self.async_show_form(
                step_id="init",
                data_schema=schema,
                errors=errors,
                description_placeholders={
                    "name": entry_title,
                },
            )
            
        except Exception as ex:
            _LOGGER.exception("Critical error in options flow init: %s", ex)
            return self.async_abort(reason="unknown")

    def _get_options_flow_schema(self) -> vol.Schema:
        """Get the options schema with current values (only mutable options)."""
        try:
            # Ensure config_entry exists and has required attributes
            if not self.config_entry:
                _LOGGER.error("Config entry is None in options flow")
                return _get_options_schema()
            
            # Get current values from both config entry data and options
            current_data = getattr(self.config_entry, 'data', None) or {}
            current_options = getattr(self.config_entry, 'options', None) or {}
            
            # Use options if available, otherwise fall back to config data
            def get_current_value(key: str, default: Any) -> Any:
                try:
                    if isinstance(current_options, dict) and key in current_options:
                        return current_options[key]
                    if isinstance(current_data, dict) and key in current_data:
                        return current_data[key]
                    return default
                except (AttributeError, TypeError, KeyError):
                    return default
            
            # Build defaults dictionary with safe access (sensors and frequently adjusted options)
            defaults = {
                CONF_TEMPERATURE_SENSOR: get_current_value(CONF_TEMPERATURE_SENSOR, []),
                CONF_HUMIDITY_SENSOR: get_current_value(CONF_HUMIDITY_SENSOR, None),
                CONF_MAIN_THERMOSTAT: get_current_value(CONF_MAIN_THERMOSTAT, None),
                CONF_COLD_TOLERANCE: get_current_value(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE),
                CONF_HOT_TOLERANCE: get_current_value(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE),
                CONF_TARGET_TEMP: get_current_value(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP),
            }
            
            return _get_options_schema(defaults)
            
        except Exception as ex:
            _LOGGER.exception("Error creating options schema: %s", ex)
            # Return a minimal schema as fallback
            return _get_options_schema()

    async def _validate_options_data(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate options data including entities."""
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
                
        # Validate main thermostat
        main_thermostat = user_input.get(CONF_MAIN_THERMOSTAT)
        if main_thermostat and not self.hass.states.get(main_thermostat):
            errors[CONF_MAIN_THERMOSTAT] = "entity_not_found"
        
        return errors
