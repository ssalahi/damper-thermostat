# Damper Thermostat

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

A custom Home Assistant component that provides an damper thermostat with additional features beyond the standard Generic Thermostat.

## Features

- 🌡️ Support for Heat/Cool/Auto modes
- 📊 Temperature and humidity sensor integration
- 🏠 Main thermostat integration for status display
- ⚙️ Configurable cold and heat tolerance
- 🏃‍♂️ Away preset mode
- 🔄 Auto mode with intelligent switching
- 📱 Full Home Assistant UI integration

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/yourusername/damper-thermostat`
6. Select category "Integration"
7. Click "Add"
8. Find "Damper Thermostat" and click "Install"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/damper_thermostat` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration to your `configuration.yaml`

## Configuration

Add to your `configuration.yaml`:

```yaml
climate:
  - platform: damper_thermostat
    name: "Living Room Thermostat"
    heater: switch.living_room_heater
    target_sensor: sensor.living_room_temperature
    humidity_sensor: sensor.living_room_humidity  # Optional
    main_thermostat: climate.main_hvac  # Optional
    min_temp: 15
    max_temp: 30
    target_temp: 21
    cold_tolerance: 0.5
    hot_tolerance: 0.5
    ac_mode: true
    initial_hvac_mode: "off"
    away_temp: 18
    unique_id: "living_room_damper_thermostat"