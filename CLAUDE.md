# CLAUDE.md

Project context for working in this repository.

## What this is

**Damper Thermostat** (`damper_thermostat`): a Home Assistant custom integration, distributed through HACS, for zoned HVAC systems that use motorized duct dampers. Each config entry creates a virtual per-zone thermostat. It does **not** drive the furnace or AC. It watches a **main thermostat** (`climate.*`) and opens or closes the zone's **damper switches** (`switch.*`) depending on the zone temperature (the average of one or more sensors) and on what the main system is doing.

- Platforms: `climate`, `switch`, `sensor`, `select`
- `integration_type: device`, `iot_class: local_polling`. There are no external requirements and no YAML setup (config flow only).
- Minimum Home Assistant version: **2026.11.0** (`hacs.json`). Use current HA APIs freely and don't add backward-compat shims for older cores.
- Units are hard-coded to **°F**. Precision is 0.1 and the setpoint step is 0.5.
- CI: [.github/workflows/hassfest.yaml](.github/workflows/hassfest.yaml) runs hassfest on push, on PR, and nightly. There are **no tests** in the repo.

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
| `custom_components/damper_thermostat/brand/` | Icons Home Assistant shows: `icon.png` (256), `icon@2x.png` (512), `dark_icon*.png`, plus SVG sources. The design is a louvered damper inside a split warm/cool thermostat dial with a setpoint knob. Duct grey `#455A64` (dark theme `#B0BEC5`), warm `#FF7020`, cool `#1E88E5`. |
| `images/icon.png`, `images/icon.svg`, `custom_components/damper_thermostat/icon.png` | Copies of the same icon (not referenced anywhere) |
| `README.md`, `SETUP_GUIDE.md`, `info.md` | User docs (`info.md` is the short HACS summary) |
| `custom_components/damper_thermostat/CONFIG_FLOW_README.md` | Developer notes on the config and options flows |
| `install.sh` | Manual install. Copies the component into `<ha-config>/custom_components/` |

## Config entry model

There are two kinds of entry under the same domain:

1. **Global Settings** (exactly one, `data["entry_type"] == "global_settings"`, unique ID `damper_thermostat_global_settings`). The first run of the user flow creates it. Fields:
   - `global_actuator_switches`: an **ordered priority list** of every damper switch in the house (index 0 = highest priority)
   - `global_max_switches_off` (default 3)
   - `global_min_temp` / `global_max_temp` (default 60/80)
2. **Device (zone)** entries. Every run after the first goes to `async_step_device`. Fields: name, `temperature_sensor` (list), `humidity_sensor` (list, optional), `main_thermostat` (required), `actuator_switch` (list, and each switch **must already be in the global list**), cold and hot tolerance, `target_temp`, `target_temp_low`/`high`, `initial_hvac_mode` (default `auto`). The unique ID is built from the joined actuator switch IDs.

Values are read as `options.get(key, config.get(key, default))`. The device options flow can edit: name, sensors, main thermostat, actuator switches, and tolerances. A cleared `humidity_sensor` is stored as `[]`, so the fallback to `data` doesn't bring it back.

The device's platforms share state through `hass.data[DOMAIN]` keys:
- `{entry_id}_reverse_heat_cool_range`, `{entry_id}_heat_fan_mode`, `{entry_id}_cold_fan_mode`: written by the switch and select entities, read by climate through properties
- `{entry_id}_on_reverse_change`: the climate's `_async_control_heating_cooling` callback. The switch and selects call it after a change.
- `async_unload_entry` deletes every `{entry_id}_*` key along with `hass.data[DOMAIN][entry_id]`.

## Control logic (`_async_control_based_on_main_thermostat`)

Runs on: sensor changes, main thermostat changes, manual actuator changes (tracked by the `_on_by_us` flag), setpoint and mode changes, config switch and select changes, and HA start. It does nothing before the first temperature reading arrives. In `off` mode it does nothing either: `async_set_hvac_mode(OFF)` closes the actuators once, and after that the zone leaves them alone.

`should_deactivate` (close the damper) is true if any of these holds:
- **Mode conflict**: the zone is `cool` while the main *mode* is `heat`, or the reverse.
- **Fan action**: the main action is `fan`:
  - Heat Fan Mode applies when the main mode is `heat`; Cold Fan Mode applies when it is `cool`.
  - `Off` closes the damper. `Auto` adds no fan rule; the other rules still apply.
  - `Smart` closes it once the zone is already warm enough (heat) or cool enough (cool), using the `heat_cool` thresholds below. It **always uses `target_temp_low`/`target_temp_high`**, even when the zone is in `heat` or `cool` mode. That is probably a bug, since those values aren't visible in those modes.
- **`heat_cool` zone**:
  - While the main system is cooling, close when `high >= cur + cold_tol`.
  - While it is heating or preheating, close when `low <= cur - hot_tol`.
  - **Reverse Heat/Cool Range** swaps which bound is used (cooling compares against `low`, heating against `high`).
- **`cool` or `heat` zone**: the same comparisons, made against the single `target_temp`. These check only the main *action*, so they also work when the main thermostat is in `heat_cool` mode. The `heat_cool` zone rules and the fan rules check the main *mode* and need it to be `heat` or `cool`.
- **`auto` zone**: the damper always stays **open**. The reported target is the main thermostat's target.

The code then turns the zone's actuators on or off only if their current state differs.

**Closing with the airflow guard** (`_async_actuator_turn_off`): if fewer than `max_switches_off` switches in the global list are off, the damper closes. Otherwise the code looks, from the lowest-priority end, for an **off** switch with lower priority than this one. It turns that switch **on** first, then closes this one. If there is no such switch, the damper stays open. The goal is that the number of closed dampers never goes above the limit. However, service calls use `blocking=False` and each zone has its own lock, so concurrent closes, or a zone with several switches, can go over it (a known bug).

The climate entity uses the **native temperature API** and is based on `RestoreClimate`. Use `_attr_native_target_temperature[_low|_high]`, `_attr_native_current_temperature` and `_attr_native_temperature_unit`, and override `native_target_temperature*`. The old non-native names are deprecated and will be removed in HA 2027.11. Setpoints are restored with `async_get_last_climate_data(validate_range=True)`; the HVAC mode comes from `async_get_last_state()`. `async_set_temperature` receives values already converted to the native unit (°F).

`hvac_action` is a derived property: `off` in `off` mode, `idle` while all the zone's actuators are off, and otherwise the main thermostat's action (stored in `_main_hvac_action`). The `icon` uses the derived value.

Restored on restart (`RestoreEntity`): target, low and high setpoints, HVAC mode, the reverse switch, and the fan selects.

## Known gaps / gotchas

- Global settings are stored as `{**entry.data, **entry.options}`. Device entities read them only once, at construction. So whenever the global entry is set up or reloaded (for example after an options edit), it schedules a reload of every device entry that is already loaded. Unloading the global entry returns early because it has no platforms.
- `hacs.json` declares `"filename": "damper_thermostat.zip"` (release-zip install) and lists `domains: ["climate"]` only.
- `manifest.json` `version` and `DeviceInfo.sw_version` are both `1.0.2` in code. Bump both together, and keep the README changelog in step with GitHub releases (tags look like `V1.0.1`).
- The select icons only distinguish `Auto` from everything else, so `Smart` shows the "off" icon.
- `translations/en.json` lists options-flow fields (`reverse_heat_cool_range`, `heat_fan_mode`, `cold_fan_mode`) that are no longer in `OPTIONS_SCHEMA`. They moved to entities.
- All `.md` docs were rewritten on 2026-11-21 to match the code. When behavior changes, update the README's mode, fan and damper-limit tables, its **Known limitations** section, and `CONFIG_FLOW_README.md`.
- Open control bugs, also listed in the README's Known limitations:
  - the damper limit can be exceeded (not race-proof)
  - dampers can flap between zones, because opening a lower-priority damper looks like a manual change to that zone
  - `float(None)` on the main thermostat's `temperature` attribute in its `heat_cool` mode stops re-evaluation when the main thermostat changes
  - there is no hysteresis between closing and reopening

## Dev notes

- There is no build step. To test, copy the folder into an HA instance (`./install.sh /path/to/ha/config`) and restart. For debug logs, set `logger: logs: custom_components.damper_thermostat: debug`.
- Local Home Assistant for tests: `.venv/` (gitignored) holds `homeassistant==2026.11.2` on Python 3.14. HA 2026.11 requires Python ≥ 3.14.2. Run checks with `.venv/bin/python`, and put the repo root on `sys.path` to import `custom_components.damper_thermostat`. The system `python3` is Homebrew 3.15, which doesn't have Home Assistant, so don't use it for HA tests. `uv` comes from Homebrew. To recreate the environment: `uv venv .venv --python 3.14 && uv pip install --python .venv/bin/python homeassistant==<latest>`.
- Validation: the hassfest GitHub Action. Keep `manifest.json` keys sorted after `domain` and `name`.
