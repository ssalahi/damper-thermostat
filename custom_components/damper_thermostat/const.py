"""Constants for the Damper Thermostat integration."""
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)

DOMAIN = "damper_thermostat"

# Configuration keys
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_ACTUATOR_SWITCH = "actuator_switch"
CONF_MAIN_THERMOSTAT = "main_thermostat"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HOT_TOLERANCE = "hot_tolerance"
CONF_COLD_TOLERANCE_AUTO = "cold_tolerance_auto"
CONF_HOT_TOLERANCE_AUTO = "hot_tolerance_auto"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TARGET_TEMP = "target_temp"
CONF_PRECISION = "precision"
CONF_INITIAL_HVAC_MODE = "initial_hvac_mode"

# Default values
DEFAULT_TOLERANCE = 0.5
DEFAULT_MIN_TEMP = 60
DEFAULT_MAX_TEMP = 80
DEFAULT_TARGET_TEMP = 74
DEFAULT_PRECISION = 0.1

# Supported features
SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TARGET_HUMIDITY | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
)

# Supported HVAC modes
HVAC_MODES = [
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.AUTO,
    HVACMode.OFF,
]
