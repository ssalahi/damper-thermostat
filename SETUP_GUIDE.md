# Quick Setup Guide - Damper Thermostat

## After Installation Steps

### 1. Restart Home Assistant
After installing via HACS or manually, restart Home Assistant completely.

### 2. Add the Integration
1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"** (bottom right)
3. Search for **"Damper Thermostat"**
4. Click on it when it appears

### 3. Required Information
Before starting setup, have these entity IDs ready:

**Required:**
- Temperature sensor (e.g., `sensor.living_room_temperature`)
- Switch for heater/cooler (e.g., `switch.heater_relay`)

**Optional:**
- Humidity sensor (e.g., `sensor.living_room_humidity`)
- Main thermostat (e.g., `climate.main_hvac`)

### 4. Configuration Form
Fill out the form with:
- **Name**: "Living Room Damper" (or your preferred name)
- **Temperature Sensor**: Select from dropdown
- **Actuator Switch**: Select from dropdown
- **Other settings**: Use defaults or customize as needed

### 5. Complete Setup
- Click **Submit**
- Your new thermostat will appear in Devices & Services
- Find it in your Climate dashboard section

## Common Entity Examples

### Temperature Sensors
- `sensor.living_room_temperature`
- `sensor.bedroom_temp`
- `sensor.office_temperature`

### Switch Entities
- `switch.heater_relay`
- `switch.fan_control`
- `switch.damper_actuator`

### Humidity Sensors
- `sensor.living_room_humidity`
- `sensor.bedroom_humidity`

### Main Thermostats
- `climate.main_hvac`
- `climate.nest_thermostat`
- `climate.ecobee`

## Troubleshooting

**Can't find the integration?**
- Make sure you restarted Home Assistant after installation
- Check that files are in `custom_components/damper_thermostat/`

**Entity not found errors?**
- Verify entity IDs exist in Developer Tools → States
- Make sure sensors are reporting values (not "unavailable")

**Need help?**
- Check the full README.md for detailed documentation
- Enable debug logging for troubleshooting
- Open an issue on GitHub if needed
