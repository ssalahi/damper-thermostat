"""Constants for Damper Thermostat."""

DOMAIN = "damper_thermostat"

DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = "Damper Thermostat"

CONF_HEATER = "heater"
CONF_SENSOR = "target_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_MAIN_THERMOSTAT = "main_thermostat"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TARGET_TEMP = "target_temp"
CONF_AC_MODE = "ac_mode"
CONF_MIN_DUR = "min_cycle_duration"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HOT_TOLERANCE = "hot_tolerance"
CONF_KEEP_ALIVE = "keep_alive"
CONF_INITIAL_HVAC_MODE = "initial_hvac_mode"
CONF_AWAY_TEMP = "away_temp"
CONF_PRECISION = "precision"

SUPPORT_FLAGS = (
    "TARGET_TEMPERATURE | TURN_OFF | TURN_ON | PRESET_MODE"
)
