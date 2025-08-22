"""Constants for the Damper Thermostat integration."""
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)

from homeassistant.const import (
    PRECISION_TENTHS
)

DOMAIN = "damper_thermostat"

# Global configuration keys
CONF_GLOBAL_SETTINGS = "global_settings"
CONF_GLOBAL_ACTUATOR_SWITCHES = "global_actuator_switches"
CONF_GLOBAL_MAX_SWITCHES_OFF = "global_max_switches_off"
CONF_GLOBAL_MIN_TEMP = "global_min_temp"
CONF_GLOBAL_MAX_TEMP = "global_max_temp"

# Configuration keys
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_ACTUATOR_SWITCH = "actuator_switch"
CONF_MAIN_THERMOSTAT = "main_thermostat"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HOT_TOLERANCE = "hot_tolerance"
CONF_TARGET_TEMP = "target_temp"
CONF_TARGET_TEMP_LOW = "target_temp_low"
CONF_TARGET_TEMP_HIGH = "target_temp_high"
CONF_INITIAL_HVAC_MODE = "initial_hvac_mode"

# Default values
DEFAULT_TOLERANCE = 0.5
DEFAULT_MIN_TEMP = 60
DEFAULT_MAX_TEMP = 80
DEFAULT_TARGET_TEMP = 74
DEFAULT_TARGET_TEMP_LOW = 72
DEFAULT_TARGET_TEMP_HIGH = 76
DEFAULT_PRECISION = PRECISION_TENTHS
DEFAULT_MAX_SWITCHES_OFF = 3

# Supported features
SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
)

# Supported HVAC modes
HVAC_MODES = [
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.AUTO,
    HVACMode.HEAT_COOL,
    HVACMode.OFF,
]
