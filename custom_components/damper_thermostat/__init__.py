"""The Damper Thermostat integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
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

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SWITCH, Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Damper Thermostat from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Check if this is a global settings entry
    if entry.data.get("entry_type") == CONF_GLOBAL_SETTINGS:
        # Options (edited via the options flow) override the original data
        hass.data[DOMAIN][CONF_GLOBAL_SETTINGS] = {**entry.data, **entry.options}

        # Device entities read global settings only at construction, so reload
        # any already-loaded device entries to pick up the new values. This also
        # covers devices that were set up before this entry and got defaults.
        for other in hass.config_entries.async_entries(DOMAIN):
            if (
                other.entry_id != entry.entry_id
                and other.data.get("entry_type") != CONF_GLOBAL_SETTINGS
                and other.state is ConfigEntryState.LOADED
            ):
                hass.config_entries.async_schedule_reload(other.entry_id)
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
    if entry.data.get("entry_type") == CONF_GLOBAL_SETTINGS:
        # No platforms were forwarded for the global entry; keep the stored
        # settings so loaded devices still see them until setup runs again.
        return True

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        domain_data = hass.data[DOMAIN]
        domain_data.pop(entry.entry_id, None)
        # Drop per-entry state shared between platforms (switch/select values
        # and the climate re-control callback) so nothing points at removed
        # entities. Switch/select restore their values on the next setup.
        prefix = f"{entry.entry_id}_"
        for key in [k for k in domain_data if k.startswith(prefix)]:
            del domain_data[key]

    return unload_ok


def get_global_setting(hass: HomeAssistant, setting_key: str, default_value=None):
    """Get a global setting value."""
    global_settings = hass.data.get(DOMAIN, {}).get(CONF_GLOBAL_SETTINGS, {})
    return global_settings.get(setting_key, default_value)
