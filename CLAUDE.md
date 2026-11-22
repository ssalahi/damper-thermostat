# CLAUDE.md

Project context for working in this repository.

## What this is

**Damper Thermostat** (`damper_thermostat`): a Home Assistant custom integration, distributed through HACS, for zoned HVAC systems that use motorized duct dampers. Each config entry creates a virtual per-zone thermostat. It does **not** drive the furnace or AC. It watches a **main thermostat** (`climate.*`) and opens or closes the zone's **damper switches** (`switch.*`) depending on the zone temperature (the average of one or more sensors) and on what the main system is doing.

- Platforms: `climate`, `switch`, `sensor`, `select`
- `integration_type: device`, `iot_class: local_polling`. There are no external requirements and no YAML setup (config flow only).
- Minimum Home Assistant version: **2026.11.0** (`hacs.json`). Use current HA APIs freely and don't add backward-compat shims for older cores.
- Units are hard-coded to **°F**. Precision is 0.1 and the setpoint step is 0.5.
- CI: [.github/workflows/hassfest.yaml](.github/workflows/hassfest.yaml) runs hassfest on push, on PR, and nightly. There are **no tests** in the repo, even though `CONFIG_FLOW_README.md` mentions `test_config_flow.py`.

## Layout

| File | Role |
|------|------|
| [custom_components/damper_thermostat/__init__.py](custom_components/damper_thermostat/__init__.py) | Entry setup. Stores the global settings or device config in `hass.data[DOMAIN]` and provides the `get_global_setting()` helper |
| [custom_components/damper_thermostat/const.py](custom_components/damper_thermostat/const.py) | `CONF_*` keys, defaults, the `FanMode` enum (`Auto`/`Smart`/`Off`), `HVAC_MODES`, `SUPPORT_FLAGS` |
| [custom_components/damper_thermostat/config_flow.py](custom_components/damper_thermostat/config_flow.py) | Config flow and options flow (`OptionsFlowWithReload`) |
| [custom_components/damper_thermostat/climate.py](custom_components/damper_thermostat/climate.py) | `DamperThermostat`: all of the control logic |
| [custom_components/damper_thermostat/switch.py](custom_components/damper_thermostat/switch.py) | CONFIG switch "Reverse Heat/Cool Range" |
| [custom_components/damper_thermostat/select.py](custom_components/damper_thermostat/select.py) | CONFIG selects "Heat Fan Mode" and "Cold Fan Mode" |
| [custom_components/damper_thermostat/sensor.py](custom_components/damper_thermostat/sensor.py) | DIAGNOSTIC sensors: actuator Open/Close, cold tolerance, hot tolerance |
| `translations/en.json` | UI strings for the config and options steps |
| `brand/`, `images/`, `icon.png` | Icons |
| `README.md`, `info.md`, `SETUP_GUIDE.md`, `CONFIG_FLOW_README.md` | User docs (partly stale, see below) |
| `install.sh` | Manual install. Copies the component into `<ha-config>/custom_components/` |

## Config entry model

There are two kinds of entry under the same domain:

1. **Global Settings** (exactly one, `data["entry_type"] == "global_settings"`, unique ID `damper_thermostat_global_settings`). The first run of the user flow creates it. Fields:
   - `global_actuator_switches`: an **ordered priority list** of every damper switch in the house (index 0 = highest priority)
   - `global_max_switches_off` (default 3)
   - `global_min_temp` / `global_max_temp` (default 60/80)
2. **Device (zone)** entries. Every run after the first goes to `async_step_device`. Fields: name, `temperature_sensor` (list), `humidity_sensor` (list, optional), `main_thermostat` (required), `actuator_switch` (list, and each switch **must already be in the global list**), cold and hot tolerance, `target_temp`, `target_temp_low`/`high`, `initial_hvac_mode` (default `auto`). The unique ID is built from the joined actuator switch IDs.

Values are read as `options.get(key, config.get(key, default))`. The device options flow can edit: name, sensors, main thermostat, actuator switches, and tolerances.

The device's platforms share state through `hass.data[DOMAIN]` keys:
- `{entry_id}_reverse_heat_cool_range`, `{entry_id}_heat_fan_mode`, `{entry_id}_cold_fan_mode`: written by the switch and select entities, read by climate through properties
- `{entry_id}_on_reverse_change`: the climate's `_async_control_heating_cooling` callback. The switch and selects call it after a change.

## Control logic (`_async_control_based_on_main_thermostat`)

Runs on: sensor changes, main thermostat changes, manual actuator changes (tracked by the `_on_by_us` flag), setpoint and mode changes, config switch and select changes, and HA start. It does nothing while the zone mode is `off` or before the first temperature reading arrives.

`should_deactivate` (close the damper) is true if any of these holds:
- **Mode conflict**: the zone is `cool` while the main thermostat is `heat`, or the reverse.
- **Fan action**: the main action is `fan`:
  - Heat Fan Mode applies when the main mode is `heat`; Cold Fan Mode applies when it is `cool`.
  - `Off` always closes the damper. `Auto` never closes it.
  - `Smart` closes it once the zone is already warm enough (heat) or cool enough (cool), using the same thresholds as below.
- **`heat_cool` zone**:
  - While the main system is cooling, close when `high >= cur + cold_tol`.
  - While it is heating or preheating, close when `low <= cur - hot_tol`.
  - **Reverse Heat/Cool Range** swaps which bound is used (cooling compares against `low`, heating against `high`).
- **`cool` or `heat` zone**: the same comparisons, made against the single `target_temp`.
- **`auto` zone**: the damper always stays **open**. The reported target is the main thermostat's target.

The code then turns the zone's actuators on or off only if their current state differs.

**Closing with the airflow guard** (`_async_actuator_turn_off`): if fewer than `max_switches_off` switches in the global list are off, the damper closes. Otherwise the code looks, from the lowest-priority end, for an **off** switch with lower priority than this one. It turns that switch **on** first, then closes this one. If there is no such switch, the damper stays open. Static pressure is protected this way: the number of closed dampers never goes above the limit.

Restored on restart (`RestoreEntity`): target, low and high setpoints, HVAC mode, the reverse switch, and the fan selects.

## Known gaps / gotchas

- Global settings are stored as `{**entry.data, **entry.options}`. Device entities read them only once, at construction. So whenever the global entry is set up or reloaded (for example after an options edit), it schedules a reload of every device entry that is already loaded. Unloading the global entry returns early because it has no platforms.
- `hacs.json` declares `"filename": "damper_thermostat.zip"` (release-zip install) and lists `domains: ["climate"]` only.
- `manifest.json` `version` and `DeviceInfo.sw_version` are both `1.0.0` in code. Bump both together.
- The select icons only distinguish `Auto` from everything else, so `Smart` shows the "off" icon.
- `translations/en.json` lists options-flow fields (`reverse_heat_cool_range`, `heat_fan_mode`, `cold_fan_mode`) that are no longer in `OPTIONS_SCHEMA`. They moved to entities.
- The docs describe a "standalone" mode without a main thermostat and an "Off" default mode. In the code the main thermostat is required and the default mode is `auto`.

## Dev notes

- There is no build step. To test, copy the folder into an HA instance (`./install.sh /path/to/ha/config`) and restart. For debug logs, set `logger: logs: custom_components.damper_thermostat: debug`.
- Validation: the hassfest GitHub Action. Keep `manifest.json` keys sorted after `domain` and `name`.
