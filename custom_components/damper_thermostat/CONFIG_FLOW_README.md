# Damper Thermostat Config Flow

This document describes the configuration flow for the Damper Thermostat integration, which has been updated to follow Home Assistant best practices.

## Overview

The config flow allows users to configure the Damper Thermostat integration through the Home Assistant UI, eliminating the need for YAML configuration.

## Features

- **User-friendly setup**: Step-by-step configuration through the Home Assistant UI
- **Entity validation**: Automatically validates that configured entities exist
- **Temperature range validation**: Ensures logical temperature ranges
- **Options flow**: Allows users to modify configuration after initial setup
- **Unique ID handling**: Prevents duplicate configurations
- **Comprehensive error handling**: Clear error messages for validation failures

## Configuration Options

### Required Options
- **Name**: A friendly name for the damper thermostat
- **Temperature Sensor**: One or more temperature sensors (supports multiple sensors)
- **Actuator Switch**: The switch that controls the damper

### Optional Options
- **Humidity Sensor**: Optional humidity sensor for enhanced control
- **Main Thermostat**: Optional main thermostat for coordination
- **Cold Tolerance**: Temperature tolerance for heating mode (default: 0.5°F)
- **Hot Tolerance**: Temperature tolerance for cooling mode (default: 0.5°F)
- **Minimum Temperature**: Lower temperature limit (default: 60°F)
- **Maximum Temperature**: Upper temperature limit (default: 80°F)
- **Initial Target Temperature**: Starting target temperature (default: 74°F)
- **Target Temperature Low**: Low temperature for range mode (default: 72°F)
- **Target Temperature High**: High temperature for range mode (default: 76°F)
- **Initial HVAC Mode**: Starting HVAC mode (default: AUTO)

## Validation Rules

The config flow includes several validation checks:

1. **Entity Existence**: All configured entities must exist in Home Assistant
2. **Temperature Ranges**: 
   - Minimum temperature must be less than maximum temperature
   - Target temperatures must be within the min/max range
   - Low/high temperature range must be logical
3. **Tolerance Values**: Must be between 0.1°F and 10.0°F

## Error Messages

The integration provides clear error messages for common issues:

- `entity_not_found`: The specified entity doesn't exist
- `min_temp_must_be_less_than_max_temp`: Temperature range is invalid
- `target_temp_out_of_range`: Target temperature is outside allowed range
- `temp_low_must_be_less_than_temp_high`: Temperature range is invalid
- `temp_range_out_of_bounds`: Temperature range exceeds limits

## Usage

### Initial Setup

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Damper Thermostat"
4. Fill in the required configuration
5. Click **Submit**

### Modifying Configuration

1. Go to **Settings** > **Devices & Services**
2. Find your Damper Thermostat integration
3. Click **Configure**
4. Modify the desired settings
5. Click **Submit**

## Technical Implementation

### Class Structure

- `DamperThermostatConfigFlow`: Main configuration flow handler
- `DamperThermostatOptionsFlow`: Options flow handler for configuration updates

### Key Methods

- `async_step_user()`: Handles the main configuration step
- `async_get_options_flow()`: Returns the options flow handler
- `_get_options_schema()`: Generates the options form schema

### Version Handling

- `VERSION = 1`: Main version for configuration entries
- `MINOR_VERSION = 1`: Minor version for incremental updates

### Unique ID Generation

The integration generates unique IDs based on the configuration name to prevent duplicate entries:
```python
unique_id = f"{user_input[CONF_NAME]}_{DOMAIN}"
```

## Testing

The integration includes comprehensive tests in `test_config_flow.py` that verify:

- Form display and validation
- Successful configuration creation
- Error handling for invalid entities
- Temperature range validation

## Best Practices Followed

1. **Proper Class Naming**: Uses descriptive class names following Home Assistant conventions
2. **Version Management**: Implements proper version handling for configuration entries
3. **Error Handling**: Comprehensive validation with clear error messages
4. **Options Flow**: Proper implementation of configuration updates
5. **Unique IDs**: Prevents duplicate configurations
6. **Entity Validation**: Ensures all configured entities exist
7. **Translation Support**: Full internationalization support
8. **Type Hints**: Proper type annotations throughout the code

## Migration from YAML

If you previously configured this integration via YAML, you can:

1. Remove the YAML configuration
2. Use the config flow to recreate the configuration
3. The integration will automatically handle the transition

## Troubleshooting

### Common Issues

1. **"Entity not found" errors**: Ensure all configured entities exist and are accessible
2. **Temperature validation errors**: Check that your temperature ranges are logical
3. **Configuration not saving**: Verify that all required fields are filled

### Getting Help

If you encounter issues:

1. Check the Home Assistant logs for detailed error messages
2. Verify that all configured entities exist and are working
3. Ensure your temperature ranges are logical
4. Check the integration's GitHub repository for known issues
