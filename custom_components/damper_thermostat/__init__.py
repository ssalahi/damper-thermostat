"""The Damper Thermostat integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_GLOBAL_SETTINGS,
    CONF_GLOBAL_ACTUATOR_SWITCHES,
    CONF_GLOBAL_MAX_SWITCHES_OFF,
    CONF_GLOBAL_MIN_TEMP,
    CONF_GLOBAL_MAX_TEMP,
    DEFAULT_MAX_SWITCHES_OFF,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Damper Thermostat from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Check if this is a global settings entry
    if entry.data.get("entry_type") == "global_settings":
        # Store global settings
        hass.data[DOMAIN][CONF_GLOBAL_SETTINGS] = entry.data
        return True
    
    # Initialize global settings with defaults if not present
    if CONF_GLOBAL_SETTINGS not in hass.data[DOMAIN]:
        hass.data[DOMAIN][CONF_GLOBAL_SETTINGS] = {
            CONF_GLOBAL_ACTUATOR_SWITCHES: [],
            CONF_GLOBAL_MAX_SWITCHES_OFF: DEFAULT_MAX_SWITCHES_OFF,
            CONF_GLOBAL_MIN_TEMP: DEFAULT_MIN_TEMP,
            CONF_GLOBAL_MAX_TEMP: DEFAULT_MAX_TEMP,
        }
    
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def get_global_setting(hass: HomeAssistant, setting_key: str, default_value=None):
    """Get a global setting value."""
    global_settings = hass.data.get(DOMAIN, {}).get(CONF_GLOBAL_SETTINGS, {})
    return global_settings.get(setting_key, default_value)


def set_global_setting(hass: HomeAssistant, setting_key: str, value):
    """Set a global setting value."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(CONF_GLOBAL_SETTINGS, {})
    hass.data[DOMAIN][CONF_GLOBAL_SETTINGS][setting_key] = value


def get_effective_setting(hass: HomeAssistant, config: dict, options: dict, setting_key: str, global_setting_key: str, default_value):
    """Get the effective setting value, considering global settings preference."""
    use_global_key = f"use_{global_setting_key}"
    use_global = options.get(use_global_key, config.get(use_global_key, False))
    
    if use_global:
        return get_global_setting(hass, global_setting_key, default_value)
    else:
        return options.get(setting_key, config.get(setting_key, default_value))
