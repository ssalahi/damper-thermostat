#!/bin/bash

# Damper Thermostat Installation Script
# This script helps install the Damper Thermostat custom component

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Damper Thermostat Installation Script${NC}"
echo "======================================"

# Check if Home Assistant config directory is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <path-to-home-assistant-config>${NC}"
    echo "Example: $0 /config"
    echo "Example: $0 ~/.homeassistant"
    exit 1
fi

CONFIG_DIR="$1"

# Validate config directory
if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${RED}Error: Directory $CONFIG_DIR does not exist${NC}"
    exit 1
fi

if [ ! -f "$CONFIG_DIR/configuration.yaml" ]; then
    echo -e "${RED}Error: $CONFIG_DIR does not appear to be a Home Assistant config directory${NC}"
    echo "Could not find configuration.yaml"
    exit 1
fi

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$CONFIG_DIR/custom_components"
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo "Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Create damper_thermostat directory
COMPONENT_DIR="$CUSTOM_COMPONENTS_DIR/damper_thermostat"
echo "Installing Damper Thermostat to $COMPONENT_DIR..."

# Remove existing installation if present
if [ -d "$COMPONENT_DIR" ]; then
    echo "Removing existing installation..."
    rm -rf "$COMPONENT_DIR"
fi

# Create component directory
mkdir -p "$COMPONENT_DIR"

# Copy component files
echo "Copying component files..."
cp custom_components/damper_thermostat/* "$COMPONENT_DIR/"

# Set permissions
chmod 644 "$COMPONENT_DIR"/*

echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Settings → Devices & Services"
echo "3. Click 'Add Integration'"
echo "4. Search for 'Damper Thermostat'"
echo "5. Follow the configuration steps"
echo ""
echo -e "${YELLOW}Note: Make sure you have the required temperature sensor and switch entities before configuring.${NC}"
