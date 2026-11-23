# Smart Damper Thermostat for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ssalahi/damper-thermostat.svg)](https://github.com/ssalahi/damper-thermostat/releases)

A Home Assistant custom integration for zoned HVAC systems that use motorized duct dampers. Each zone gets its own virtual thermostat. That thermostat follows your **main thermostat** and opens or closes the zone's **damper switches**, based on the zone's own temperature and what the main system is doing.

The integration never turns your furnace or AC on or off. Your main thermostat stays in charge of the equipment. The integration only decides which zones receive air.

## What is a damper thermostat?

Zoned systems use motorized dampers in the ductwork to send conditioned air only to the rooms that need it. This integration creates one climate entity per zone. Each one:

- averages one or more temperature sensors to get the zone temperature
- watches the main thermostat's mode (heat or cool) and its current action (heating, cooling, fan, idle)
- closes the zone's damper once the zone has reached its target, and keeps it open otherwise
- enforces a house-wide limit on how many dampers can be closed at once, so the blower always has enough open duct

## Features

- **Multiple sensors per zone**: temperature (required) and humidity (optional) are averaged across all selected sensors. Sensors that are unavailable or report non-numeric values are skipped.
- **Five modes**: Heat, Cool, Heat/Cool (two setpoints), Auto and Off.
- **Coordination with the main thermostat**: a zone closes its damper if its mode conflicts with the main system's mode, for example a Cool zone while the main thermostat is heating.
- **Fan behavior**: separate Heat Fan Mode and Cold Fan Mode settings (`Auto`, `Smart`, `Off`) decide what the damper does when the main system is only running the fan.
- **Reverse Heat/Cool Range**: a per-zone toggle that swaps which Heat/Cool setpoint is used for heating and which for cooling.
- **Damper limit with priorities**: a global priority list of every damper and a maximum number that may be closed at the same time.
- **State persistence**: setpoints, mode, the reverse toggle and the fan modes survive restarts.
- **UI setup only**: everything is configured from **Settings → Devices & Services**. There is no YAML configuration.

## Requirements

- Home Assistant **2026.11.0** or newer
- A main thermostat (`climate.*` entity) that reports its mode as `heat` or `cool` and its current action in the `hvac_action` attribute
- One `switch.*` entity per damper (on = open, off = closed)
- At least one temperature sensor per zone (`sensor.*` with device class `temperature`)
- Optional: humidity sensors (`sensor.*` with device class `humidity`)

Temperatures are handled in **°F**.

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Open the menu (⋮) in the top right and choose **Custom repositories**.
3. Add `https://github.com/ssalahi/damper-thermostat` with the type **Integration**.
4. Search for **Damper Thermostat**, open it, and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download or clone this repository.
2. Copy `custom_components/damper_thermostat` into your Home Assistant `config/custom_components/` folder. Or run the install script from the repository root:
   ```bash
   ./install.sh /path/to/homeassistant/config
   ```
3. Restart Home Assistant.

## Configuration

Setup has two parts: one **Global Settings** entry shared by the whole house, then one entry per **zone**. Both are added the same way: **Settings → Devices & Services → + Add Integration → Damper Thermostat**.

### Step 1: Global Settings (first time only)

The first time you add the integration, it asks for the Global Settings. Every later **Add Integration** creates a zone.

| Field | Required | Description | Default | Allowed |
|-------|----------|-------------|---------|---------|
| Global Actuator Switches List (Priority Order) | Yes | Every damper switch in the house, in priority order. The first one listed has the highest priority. | – | switch entities |
| Global Maximum Switches Off Limit | No | The most dampers that may be closed at the same time | 3 | 1–10 |
| Global Minimum Temperature | No | The lowest setpoint the zone thermostats allow | 60°F | 40–80 |
| Global Maximum Temperature | No | The highest setpoint the zone thermostats allow | 80°F | 50–100 |

The minimum must be lower than the maximum.

### Step 2: Add a zone

| Field | Required | Description | Default | Allowed |
|-------|----------|-------------|---------|---------|
| Name | Yes | Zone name, which also becomes the device name | – | |
| Temperature Sensor(s) | Yes | One or more sensors. Their average is the zone temperature. | – | temperature sensors |
| Humidity Sensor (Optional) | No | One or more sensors. Their average is shown as the zone humidity; it is not used for control. | – | humidity sensors |
| Main Thermostat | Yes | The thermostat that runs your HVAC equipment | – | climate entity |
| Actuator Switch | Yes | The damper switch or switches for this zone. Each one must already be in the global list. | – | switch entities |
| Cold Tolerance | No | While cooling, how far below the target the zone must drop before its damper closes | 0.5°F | 0.1–10 |
| Hot Tolerance | No | While heating, how far above the target the zone must rise before its damper closes | 0.5°F | 0.1–10 |
| Initial Target Temperature | No | Starting setpoint for Heat and Cool modes | 74°F | 50–80 |
| Target Temperature Low | No | Starting low setpoint for Heat/Cool mode | 72°F | 40–80 |
| Target Temperature High | No | Starting high setpoint for Heat/Cool mode | 76°F | 50–99 |
| Initial HVAC Mode | No | The mode the zone starts in | Auto | heat, cool, auto, heat_cool, off |

The low setpoint must be lower than the high setpoint. A set of damper switches can belong to only one zone. Adding a second zone with the same switches is rejected as "already configured".

The initial target temperatures and mode apply only when the zone is first created. After that, change them on the thermostat card. The zone remembers them across restarts.

### Changing settings later

Open **Settings → Devices & Services → Damper Thermostat**, pick the entry, and click **Configure**.

- **Global Settings**: all four fields can be changed. Every zone reloads automatically and picks up the new values.
- **A zone**: you can change the name, temperature sensors, humidity sensors (clear the field to remove them), main thermostat, actuator switches, and cold and hot tolerance. The zone reloads after you save.

Setpoints and mode are changed on the thermostat card. The reverse toggle and the fan modes are entities on the zone's device page (see below).

## Entities created per zone

All of these belong to the zone's device:

| Entity | Type | Category | Purpose |
|--------|------|----------|---------|
| *Zone name* | Climate | – | The zone thermostat |
| Reverse Heat/Cool Range | Switch | Configuration | Swaps which Heat/Cool setpoint is used for heating and which for cooling |
| Heat Fan Mode | Select | Configuration | Damper behavior while the main system is in Heat mode but only running the fan |
| Cold Fan Mode | Select | Configuration | Damper behavior while the main system is in Cool mode but only running the fan |
| Actuator Switch | Sensor | Diagnostic | `Open` if any of the zone's damper switches is on, otherwise `Close` |
| Cold Tolerance | Sensor | Diagnostic | The configured cold tolerance |
| Hot Tolerance | Sensor | Diagnostic | The configured hot tolerance |

The climate entity also exposes `actuator_switch`, `cold_tolerance` and `hot_tolerance` as attributes. Its **action** shows what the zone itself is getting:
- **Off**: the zone is in Off mode.
- **Idle**: the zone's damper is closed.
- **The main thermostat's action** (heating, cooling, fan, idle and so on): the damper is open.

## How it works

The zone re-checks its damper whenever any of these change: a zone sensor, the main thermostat, the zone's damper switch (when someone else changes it), a setpoint, the mode, the reverse toggle, or a fan mode. Nothing happens until the zone has its first temperature reading.

By default the damper is **open**. It is closed when any of the conditions below applies. The one exception is **Auto** mode, where the damper always stays open.

### Modes

In the table, *T* is the zone temperature (the sensor average).

| Zone mode | Damper closes when |
|-----------|--------------------|
| **Heat** | The main system is heating (or preheating) and T ≥ target + hot tolerance. Also whenever the main thermostat is in **Cool** mode. |
| **Cool** | The main system is cooling and T ≤ target − cold tolerance. Also whenever the main thermostat is in **Heat** mode. |
| **Heat/Cool** | The main thermostat is in Heat mode and heating, and T ≥ low + hot tolerance. Or the main thermostat is in Cool mode and cooling, and T ≤ high − cold tolerance. With **Reverse Heat/Cool Range** on, the setpoints swap: heating runs until T ≥ high + hot tolerance, and cooling until T ≤ low − cold tolerance. |
| **Auto** | Never. The damper stays open and the main thermostat decides everything. The card shows the main thermostat's target, and the zone target can't be changed in this mode. |
| **Off** | Switching to Off closes the damper once. After that the zone leaves its damper alone until you pick another mode. |

The damper also stays open while the main system is idle (unless one of the rules above applies). It reopens as soon as the closing condition stops being true. There is no extra gap between the close and reopen points.

### Fan behavior

When the main thermostat is in **Heat** mode but its action is `fan`, **Heat Fan Mode** applies. When it is in **Cool** mode with action `fan`, **Cold Fan Mode** applies.

| Fan mode | Damper |
|----------|--------|
| **Auto** | The fan setting adds no rule of its own. The other rules still apply. |
| **Off** | Closes while only the fan is running. |
| **Smart** | Closes only if the zone is already warm enough (Heat Fan Mode) or cool enough (Cold Fan Mode). This uses the same thresholds as Heat/Cool mode, including the reverse toggle. |

Smart always compares against the zone's Heat/Cool **low and high setpoints**, even when the zone is in Heat or Cool mode. A zone in Auto mode ignores the fan settings and stays open.

### Damper limit and priority

The global list sets the priority of each damper (first = highest), and **Global Maximum Switches Off Limit** caps how many can be closed at once. When a zone wants to close its damper:

1. If fewer dampers than the limit are closed, it closes.
2. Otherwise, it looks for a closed damper with **lower** priority than its own, starting from the bottom of the list. It opens that damper first, then closes its own.
3. If there is no lower-priority damper to open, the damper stays open.

So higher-priority zones can always close, at the cost of lower-priority zones. The number of closed dampers is meant to never go above the limit.

### Example

Global Settings:

```text
Global Actuator Switches List:
  1. switch.master_bedroom_damper   (highest priority)
  2. switch.living_room_damper
  3. switch.guest_bedroom_damper    (lowest priority)
Global Maximum Switches Off Limit: 2
```

Zone:

```text
Name:                 Master Bedroom
Temperature Sensor(s): sensor.master_bedroom_temperature, sensor.master_bedroom_temperature_2
Humidity Sensor:      sensor.master_bedroom_humidity
Main Thermostat:      climate.main_hvac
Actuator Switch:      switch.master_bedroom_damper
Initial HVAC Mode:    heat_cool  (low 70°F, high 76°F)
```

Suppose the guest bedroom and living room dampers are both closed (2 of 2). When the master bedroom reaches its setpoint, it opens the guest bedroom damper and then closes its own.

## Known limitations

- **The main thermostat should be in Heat or Cool mode.** Heat/Cool zones and the fan settings look at the main thermostat's mode. If the main thermostat runs in its own heat_cool or auto mode, they never close the damper. Also, when the main thermostat has no single target temperature, its changes don't trigger a re-check; zone sensor changes still do.
- **The damper limit is not fully race-proof.** Switch commands are sent without waiting for them to finish. So zones that close at the same moment, or a zone with several damper switches, can briefly go over the limit.
- **No gap between closing and reopening.** If a sensor hovers right at the threshold, the damper can open and close often.
- **Units are fixed to °F.**

## Troubleshooting

**"Actuator Switch should be added to the global list first"**
Add the switch to **Global Actuator Switches List** (Global Settings → Configure), then add or edit the zone again.

**"Device is already configured"**
Another zone already uses the same damper switch or switches.

**Damper doesn't move**
- Check that the switch responds to manual on/off in **Developer Tools → Actions**.
- Check the zone's mode. In Auto mode the damper is always open; in Off mode it isn't controlled.
- If the damper should close but doesn't, the limit has probably been reached and no lower-priority damper can be opened. Look for "Cannot turn off actuator" in the debug log.

**Temperature doesn't update**
Check the sensors in **Developer Tools → States**. They must report plain numbers.

**Zone doesn't react to the main thermostat**
Make sure the main thermostat shows an `hvac_action` attribute and that its mode is `heat` or `cool` (see Known limitations).

### Debug logging

```yaml
logger:
  logs:
    custom_components.damper_thermostat: debug
```

## Contributing

Pull requests are welcome. CI validates the integration with [hassfest](https://github.com/home-assistant/actions).

## License

MIT. See [LICENSE](LICENSE).

## Support

Please [open an issue](https://github.com/ssalahi/damper-thermostat/issues) on GitHub.

## Changelog

### 1.0.2 (unreleased)
- New icon (a louvered damper inside a warm/cool thermostat dial) with light and dark versions at the sizes Home Assistant expects
- `install.sh` now installs the `translations/` and `brand/` folders and works from any directory
- The zone's action now shows **idle** while its damper is closed, and **off** in Off mode. Before, it always copied the main thermostat's action. The icon follows the same rule.
- Updated the climate entity to Home Assistant's `native_*` temperature API, ahead of the old one being removed in 2027.11. This removes the deprecation warnings from the log. Setpoints are now restored after a restart in the right unit, and dropped if they fall outside the min/max range.

### 1.0.1
- Global Settings entry: a shared damper priority list, the damper limit, and min/max setpoints
- Reverse Heat/Cool Range switch per zone
- Heat Fan Mode and Cold Fan Mode selects (`Auto`, `Smart`, `Off`)
- Diagnostic sensors for damper state and tolerances
- Global Settings changes now take effect and reload all zones
- A cleared humidity sensor now stays removed
- Minimum Home Assistant version raised to 2026.11.0

### 1.0.0
- Initial release: multi-sensor averaging, main thermostat coordination, priority-based damper limit, Heat/Cool/Auto/Heat-Cool/Off modes, state restore, UI configuration
