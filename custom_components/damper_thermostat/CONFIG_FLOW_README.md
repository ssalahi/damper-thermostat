# Damper Thermostat Config Flow

Developer notes for [config_flow.py](config_flow.py). For end-user setup instructions, see the repository [README](../../README.md).

## Overview

All configuration is done through the UI; there is no YAML setup. A single config flow creates two kinds of entries under the `damper_thermostat` domain:

| Entry | `entry.data["entry_type"]` | Unique ID | Title | Count |
|-------|---------------------------|-----------|-------|-------|
| Global Settings | `"global_settings"` | `damper_thermostat_global_settings` | "Global Settings" | exactly one |
| Zone (device) | *(not set)* | `<actuator switch IDs joined by "_">_damper_thermostat` | the zone name | one per zone |

`DamperThermostatConfigFlow` (`VERSION = 1`, `MINOR_VERSION = 1`) handles creation. `DamperThermostatOptionsFlow` (an `OptionsFlowWithReload`) handles edits.

## Config flow steps

### `async_step_user`

This step decides where the user goes. If no Global Settings entry exists yet, it forwards to `async_step_global_settings`. Otherwise it forwards to `async_step_device`.

### `async_step_global_settings` (step id `global_settings`)

Schema `GLOBAL_SETTINGS_SCHEMA`:

| Key | Required | Selector / type | Default | Range |
|-----|----------|-----------------|---------|-------|
| `global_actuator_switches` | Yes | switch entities, multiple, **ordered by priority** (index 0 = highest) | – | – |
| `global_max_switches_off` | No | int | 3 | 1–10 |
| `global_min_temp` | No | float | 60 | 40–80 |
| `global_max_temp` | No | float | 80 | 50–100 |

- Validation: `global_min_temp < global_max_temp`. Otherwise the error is `min_temp_must_be_less_than_max_temp`.
- Before saving, it sets `entry_type = "global_settings"` and the fixed unique ID. If the entry already exists, the flow aborts with `already_configured`.

### `async_step_device` (step id `device`)

Schema `STEP_USER_DATA_SCHEMA`:

| Key | Required | Selector / type | Default | Range |
|-----|----------|-----------------|---------|-------|
| `name` | Yes | string | – | – |
| `temperature_sensor` | Yes | sensor, device class `temperature`, multiple | – | – |
| `humidity_sensor` | No | sensor, device class `humidity`, multiple | – | – |
| `main_thermostat` | Yes | climate entity | – | – |
| `actuator_switch` | Yes | switch entities, multiple | – | – |
| `cold_tolerance` | No | float | 0.5 | 0.1–10 |
| `hot_tolerance` | No | float | 0.5 | 0.1–10 |
| `target_temp` | No | float | 74 | 50–80 |
| `target_temp_low` | No | float | 72 | 40–80 |
| `target_temp_high` | No | float | 76 | 50–99 |
| `initial_hvac_mode` | No | dropdown: heat, cool, auto, heat_cool, off | auto | – |

Validation:
- `target_temp_low < target_temp_high`. Otherwise the error is `temp_low_must_be_less_than_temp_high`.
- Every `actuator_switch` must be in the global priority list. Otherwise the error is `actuator_switch_not_in_global` (from `check_inside_global_actuator_switches`).
- The unique ID comes from the selected switches. Reusing the same set aborts with `already_configured`.

The target temperatures and initial mode are only starting values. Once the climate entity has run, it restores its setpoints and mode from the last saved state.

## Options flow

`async_step_init` sends the user to the step that matches the entry type.

### `async_step_global_settings`

This step uses the same schema and validation as the config step, pre-filled with `{**entry.data, **entry.options}`, and saves the result to `entry.options`.

`OptionsFlowWithReload` then reloads the Global Settings entry. `async_setup_entry` in [__init__.py](__init__.py) does three things with it:
- merges `data` and `options` into `hass.data[DOMAIN]["global_settings"]`
- schedules a reload of every loaded zone entry, because zone entities read global settings only when they are created
- handles unloading the global entry, which returns `True` without unloading platforms because it never forwarded any

### `async_step_device`

Schema `OPTIONS_SCHEMA`. The editable keys are `name`, `temperature_sensor`, `humidity_sensor`, `main_thermostat`, `actuator_switch`, `cold_tolerance` and `hot_tolerance`.

- It runs the same `actuator_switch_not_in_global` check.
- If `humidity_sensor` is missing from the input (the user cleared the field), it stores `[]`. Otherwise the entity would fall back to the sensor in `entry.data`.
- If the name changes, it also updates the entry title.
- The entry reloads after saving.

The entities read every value as `options.get(key, data.get(key, default))`.

Settings that aren't in the options flow:
- setpoints and HVAC mode: changed on the climate entity
- Reverse Heat/Cool Range: a switch entity
- Heat Fan Mode / Cold Fan Mode: select entities

Each of these restores its last state on restart.

## Error keys

Defined in [translations/en.json](translations/en.json):

| Key | Where | Meaning |
|-----|-------|---------|
| `min_temp_must_be_less_than_max_temp` | global (config + options) | min ≥ max |
| `temp_low_must_be_less_than_temp_high` | device (config) | low ≥ high |
| `actuator_switch_not_in_global` | device (config + options) | the switch isn't in the global priority list |
| `already_configured` (abort) | both | a duplicate unique ID |

The translations file also defines `entity_not_found`, `invalid_name`, `target_temp_out_of_range` and `temp_range_out_of_bounds`, but the flow doesn't currently raise them.

## Tests

There are no automated tests yet. CI runs only [hassfest](../../.github/workflows/hassfest.yaml).
