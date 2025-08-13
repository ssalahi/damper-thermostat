# Damper Thermostat for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ssalahi/damper-thermostat.svg)](https://github.com/ssalahi/damper-thermostat/releases)

A custom Home Assistant component that creates an advanced thermostat device with enhanced features beyond the standard Generic Thermostat. The Damper Thermostat supports Cool/Heat/Auto modes and can work independently or in conjunction with a main thermostat.

## Features

- **Multiple HVAC Modes**: Supports Heat, Cool, Auto, and Off modes
- **Temperature Control**: Uses external temperature sensor for accurate readings
- **Humidity Monitoring**: Optional humidity sensor integration
- **Actuator Control**: Controls heating/cooling devices via switch entities
- **Main Thermostat Integration**: Can follow the state of a main thermostat for coordinated operation
- **Configurable Tolerances**: Separate cold and hot tolerance settings
- **Temperature Limits**: Configurable minimum and maximum temperature ranges
- **State Persistence**: Remembers settings across Home Assistant restarts
- **Easy Configuration**: User-friendly config flow setup

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/ssalahi/damper-thermostat` as a custom repository
6. Select "Integration" as the category
7. Click "Add"
8. Find "Damper Thermostat" in the integration list and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/ssalahi/damper-thermostat/releases)
2. Extract the contents
3. Copy the `custom_components/damper_thermostat` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Damper Thermostat"
4. Follow the configuration steps

### Configuration Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| Name | Yes | Name for your thermostat | - |
| Temperature Sensor | Yes | Entity ID of temperature sensor | - |
| Humidity Sensor | No | Entity ID of humidity sensor | - |
| Actuator Switch | Yes | Entity ID of switch to control heating/cooling | - |
| Main Thermostat | No | Entity ID of main thermostat to follow | - |
| Cold Tolerance | No | Temperature difference before heating activates | 0.5°F |
| Hot Tolerance | No | Temperature difference before cooling activates | 0.5°F |
| Minimum Temperature | No | Minimum settable temperature | 60°F |
| Maximum Temperature | No | Maximum settable temperature | 80°F |
| Initial Target Temperature | No | Starting target temperature | 70°F |
| Temperature Precision | No | Temperature adjustment precision | 0.1 |
| Initial HVAC Mode | No | Starting HVAC mode | Off |

## Usage

### Standalone Operation

When no main thermostat is configured, the Damper Thermostat operates independently:

- **Heat Mode**: Activates the actuator switch when temperature falls below (target - cold tolerance)
- **Cool Mode**: Activates the actuator switch when temperature rises above (target + hot tolerance)
- **Auto Mode**: Automatically switches between heating and cooling as needed
- **Off Mode**: Keeps the actuator switch off

### Main Thermostat Integration

When a main thermostat is configured, the Damper Thermostat coordinates with it:

- Monitors the main thermostat's HVAC action (heating/cooling/idle)
- Only activates the actuator when the main thermostat is actively heating/cooling
- Still respects local temperature conditions and tolerances
- Displays the main thermostat's current action status

## Examples

### Basic Setup (Standalone)

```yaml
# Example entities you might have
sensor:
  - platform: template
    sensors:
      room_temperature:
        friendly_name: "Room Temperature"
        unit_of_measurement: "°F"
        value_template: "{{ states('sensor.temperature_sensor') }}"

switch:
  - platform: template
    switches:
      room_heater:
        friendly_name: "Room Heater"
        turn_on:
          service: switch.turn_on
          target:
            entity_id: switch.heater_relay
        turn_off:
          service: switch.turn_off
          target:
            entity_id: switch.heater_relay
```

### Advanced Setup (With Main Thermostat)

This setup allows the damper thermostat to work in coordination with your main HVAC system:

1. Configure your main thermostat (e.g., `climate.main_hvac`)
2. Set up the damper thermostat with the main thermostat as input
3. The damper will only activate when the main system is running and local conditions require it

## Troubleshooting

### Common Issues

1. **Thermostat not responding**: Check that all entity IDs are correct and entities exist
2. **Temperature not updating**: Verify the temperature sensor is working and reporting values
3. **Actuator not switching**: Ensure the switch entity is controllable and not disabled

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  logs:
    custom_components.damper_thermostat: debug
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/ssalahi/damper-thermostat/issues) on GitHub.

## Changelog

### Version 1.0.0
- Initial release
- Support for Heat/Cool/Auto/Off modes
- Temperature and humidity sensor integration
- Main thermostat coordination
- Configurable tolerances and limits
- HACS compatibility
