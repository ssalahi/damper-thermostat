# Smart Damper Thermostat for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ssalahi/damper-thermostat.svg)](https://github.com/ssalahi/damper-thermostat/releases)

A sophisticated Home Assistant custom component that creates an intelligent damper thermostat system with advanced zone control capabilities. This component is designed for HVAC systems with multiple zones and dampers, providing coordinated temperature control that works in harmony with your main thermostat system.

## What is a Damper Thermostat?

A damper thermostat controls motorized dampers in HVAC ductwork to regulate airflow to specific zones. Unlike traditional thermostats that control the HVAC unit directly, damper thermostats work by opening and closing dampers to allow or restrict conditioned air flow to individual rooms or zones. This component creates virtual thermostats that can:

- Control multiple temperature sensors for accurate zone temperature readings
- Manage damper actuator switches to control airflow
- Coordinate with your main HVAC thermostat for optimal system operation
- Implement intelligent damper management to prevent system damage
- Support multiple HVAC modes including Heat, Cool, Auto, and Heat/Cool

## Key Features

### Advanced Temperature Control
- **Multiple Temperature Sensors**: Supports multiple temperature sensors per zone with automatic averaging
- **Precision Control**: Configurable temperature tolerances and precision settings
- **Dual Setpoint Support**: Heat/Cool mode with separate high and low temperature targets
- **Temperature Limits**: Configurable minimum and maximum temperature ranges

### Intelligent Damper Management
- **Priority-Based Control**: Manages multiple damper switches with priority ordering
- **System Protection**: Configurable maximum number of dampers that can be closed simultaneously
- **Smart Switching**: Automatically manages damper states to prevent HVAC system damage

### Main Thermostat Integration
- **Coordinated Operation**: Works in harmony with your main HVAC thermostat
- **Action Mirroring**: Follows main thermostat's heating/cooling actions
- **Intelligent Logic**: Only operates dampers when main system is actively heating/cooling

### Multiple HVAC Modes
- **Heat Mode**: Opens dampers when zone needs heating and main system is heating
- **Cool Mode**: Opens dampers when zone needs cooling and main system is cooling  
- **Auto Mode**: Keeps dampers open, letting main thermostat control the system
- **Heat/Cool Mode**: Dual setpoint control with separate heating and cooling targets
- **Off Mode**: Closes dampers completely

### Enhanced Features
- **Humidity Monitoring**: Optional humidity sensor integration
- **State Persistence**: Remembers all settings across Home Assistant restarts
- **Easy Configuration**: User-friendly config flow with options for post-setup changes

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

### Prerequisites

Before setting up the integration, ensure you have:

1. **Temperature Sensors**: One or more temperature sensor entities for each zone
2. **Damper Actuator Switches**: Switch entities that control your damper motors
3. **Main Thermostat** (recommended): Your primary HVAC thermostat entity
4. **Humidity Sensor** (optional): Humidity sensor entity for the zone

### Adding a Damper Thermostat

1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"**
3. Search for and select **"Damper Thermostat"**
4. Fill out the configuration form:

#### Required Configuration
- **Name**: Descriptive name for your zone (e.g., "Living Room Zone", "Master Bedroom")
- **Temperature Sensor(s)**: Select one or more temperature sensors for the zone
- **Actuator Switch**: Select the switch entity that controls the damper motor
- **Main Thermostat**: Select your main HVAC thermostat for coordination
- **Actuator Switches List**: List of all damper switches in your system (for priority management)
- **Max Switches Off**: Maximum number of dampers that can be closed simultaneously

#### Optional Configuration
- **Humidity Sensor**: Select a humidity sensor for the zone
- **Cold/Hot Tolerance**: Temperature difference before damper activates
- **Temperature Limits**: Minimum and maximum settable temperatures
- **Initial Settings**: Starting target temperature and HVAC mode

### Configuration Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| Name | Yes | Zone name | - |
| Temperature Sensor(s) | Yes | Temperature sensor entity ID(s) | - |
| Humidity Sensor | No | Humidity sensor entity ID | - |
| Actuator Switch | Yes | Damper switch entity ID | - |
| Main Thermostat | Yes | Main HVAC thermostat entity ID | - |
| Actuator Switches | Yes | List of all damper switches for priority management | - |
| Max Switches Off | Yes | Maximum dampers that can be closed | 3 |
| Cold Tolerance | No | Temperature difference before heating | 0.5°F |
| Hot Tolerance | No | Temperature difference before cooling | 0.5°F |
| Min/Max Temperature | No | Temperature range limits | 60-80°F |
| Initial Target Temperature | No | Starting target temperature | 74°F |
| Initial HVAC Mode | No | Starting HVAC mode | Off |

## How It Works

### Standalone Operation
When no main thermostat is configured, the damper thermostat operates independently:
- **Heat Mode**: Opens damper when zone temperature < (target - cold tolerance)
- **Cool Mode**: Opens damper when zone temperature > (target + hot tolerance)
- **Auto Mode**: Automatically switches between heating and cooling logic
- **Heat/Cool Mode**: Uses separate high/low setpoints for dual-zone comfort

### Coordinated Operation
When a main thermostat is configured, the damper thermostat coordinates intelligently:
- Monitors main thermostat's current action (heating/cooling/idle)
- Only opens dampers when main system is actively heating/cooling AND zone needs conditioning
- Respects local temperature conditions and tolerances
- Prevents unnecessary damper operation when main system is idle

### Priority Management
When multiple damper thermostats are configured with the actuator switches list:
- Maintains a priority order for damper operation
- Ensures minimum number of dampers remain open to prevent system damage
- Automatically manages damper switching to maintain system balance
- Higher priority zones get preference when damper limits are reached

## Usage Examples

### Basic Zone Control
```yaml
# Example: Living room zone with single temperature sensor
Name: "Living Room Zone"
Temperature Sensor: sensor.living_room_temperature
Actuator Switch: switch.living_room_damper
Main Thermostat: climate.main_hvac
```

### Multi-Sensor Zone
```yaml
# Example: Large zone with multiple temperature sensors
Name: "Open Floor Plan"
Temperature Sensors: 
  - sensor.kitchen_temperature
  - sensor.dining_room_temperature
  - sensor.living_room_temperature
Actuator Switch: switch.main_floor_damper
```

### Complete System Setup
```yaml
# Example: Full system with priority management
Name: "Master Bedroom"
Temperature Sensor: sensor.master_bedroom_temperature
Humidity Sensor: sensor.master_bedroom_humidity
Actuator Switch: switch.master_bedroom_damper
Main Thermostat: climate.main_hvac
Actuator Switches:
  - switch.master_bedroom_damper    # Priority 1
  - switch.living_room_damper       # Priority 2
  - switch.guest_bedroom_damper     # Priority 3
Max Switches Off: 2
```

## Advanced Features

### Heat/Cool Mode
Perfect for zones that need both heating and cooling with different comfort ranges:
- Set target temperature low (e.g., 72°F) for heating threshold
- Set target temperature high (e.g., 76°F) for cooling threshold
- Damper opens for heating when temp < 72°F and main system is heating
- Damper opens for cooling when temp > 76°F and main system is cooling

### Auto Mode
Ideal for zones that should always receive conditioned air:
- Keeps damper open regardless of local temperature
- Lets main thermostat control overall system operation
- Perfect for critical zones or areas with poor air circulation

### System Protection
The component includes several safety features:
- Prevents all dampers from closing simultaneously
- Manages damper priority to maintain system airflow
- Coordinates with main thermostat to prevent conflicts
- Includes error handling and recovery mechanisms

## Troubleshooting

### Common Issues

**Damper not responding**
- Verify actuator switch entity is correct and controllable
- Check that switch responds to manual on/off commands
- Ensure damper motor is properly wired and powered

**Temperature not updating**
- Confirm temperature sensor entities are working
- Check sensor values in Developer Tools → States
- Verify sensors report numeric temperature values

**No coordination with main thermostat**
- Ensure main thermostat entity ID is correct
- Verify main thermostat reports hvac_action attribute
- Check main thermostat is actively heating/cooling

**Multiple dampers closing unexpectedly**
- Review Max Switches Off setting
- Check Actuator Switches list configuration
- Verify priority order is correct

### Debug Logging

Enable detailed logging by adding to `configuration.yaml`:

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
- Initial release with advanced damper control
- Multiple temperature sensor support with averaging
- Priority-based damper management system
- Main thermostat coordination and action mirroring
- Support for Heat/Cool/Auto/Heat_Cool/Off modes
- Configurable system protection limits
- State persistence and restore functionality
- Dynamic icons and comprehensive device information
- HACS compatibility and easy configuration flow
