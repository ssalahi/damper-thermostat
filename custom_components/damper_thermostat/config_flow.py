"""Config flow for Damper Thermostat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
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
    CONF_PRECISION,
    CONF_INITIAL_HVAC_MODE,
    DEFAULT_TOLERANCE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_PRECISION,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
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
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): vol.In([0.1, 0.5, 1.0]),
        vol.Optional(CONF_INITIAL_HVAC_MODE, default=HVACMode.OFF): vol.In(
            [HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.OFF]
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Damper Thermostat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        # Validate that entities exist
        if not self.hass.states.get(user_input[CONF_TEMPERATURE_SENSOR]):
            errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
        
        if user_input.get(CONF_HUMIDITY_SENSOR) and not self.hass.states.get(user_input[CONF_HUMIDITY_SENSOR]):
            errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"
            
        if not self.hass.states.get(user_input[CONF_ACTUATOR_SWITCH]):
            errors[CONF_ACTUATOR_SWITCH] = "entity_not_found"
            
        if user_input.get(CONF_MAIN_THERMOSTAT) and not self.hass.states.get(user_input[CONF_MAIN_THERMOSTAT]):
            errors[CONF_MAIN_THERMOSTAT] = "entity_not_found"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
