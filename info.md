# Damper Thermostat

Per-zone virtual thermostats for zoned HVAC systems with motorized duct dampers. Each zone follows your **main thermostat** and opens or closes its **damper switches** based on the zone's own temperature. Your furnace or AC is never switched directly.

## Key features

- **Zone thermostats** in Heat, Cool, Heat/Cool (two setpoints), Auto (always open) and Off modes
- **Multiple sensors per zone**, averaged (temperature required, humidity optional)
- **Coordination with the main thermostat**: dampers close when the zone reaches its target or when the zone's mode conflicts with the main system's mode
- **Fan behavior**: Heat and Cold Fan Mode (`Auto` / `Smart` / `Off`) decide what happens while only the blower runs
- **Reverse Heat/Cool Range** toggle per zone
- **Damper limit with priorities**: a house-wide cap on closed dampers. Higher-priority zones close first, opening lower-priority dampers if needed.
- **UI setup only**, and settings survive restarts

## Requirements

- Home Assistant 2026.11.0 or newer
- A main `climate` thermostat that reports `heat`/`cool` mode and `hvac_action`
- One `switch` per damper (on = open) and at least one temperature sensor per zone
- Temperatures are in °F

## Setup in brief

1. **Add Integration → Damper Thermostat** the first time creates **Global Settings**: the priority list of every damper switch, the maximum closed dampers, and the setpoint range.
2. Each later **Add Integration** creates a **zone**: its name, sensors, main thermostat and damper switches.

See the README for the full documentation.
