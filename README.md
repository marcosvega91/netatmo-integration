[![](https://img.shields.io/github/release/marcomoretti/netatmo-integration/all.svg?style=for-the-badge)](https://github.com/marcomoretti/netatmo-integration/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/marcomoretti/netatmo-integration?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40marcomoretti-red?style=for-the-badge)](https://github.com/marcomoretti)

# Netatmo Video Intercom Integration for Home Assistant

A Home Assistant custom integration to control Netatmo Video Intercom door locks remotely.

This integration allows you to open doors connected to your Netatmo Video Intercom system directly from Home Assistant, enabling automation and remote access to your building entrances.

## Features

- **Door Control**: Open doors remotely through Netatmo Video Intercom system
- **Multiple Doors**: Supports multiple door modules per home  
- **Home Assistant Integration**: Full integration with automations, scenes, and scripts
- **Momentary Switch**: Switches automatically turn off after 2 seconds (like pressing a physical button)

## Prerequisites

Before installing this integration, you need:

1. **Netatmo Developer Account**: Create an account at [https://dev.netatmo.com](https://dev.netatmo.com)
2. **Netatmo App Registration**: Create a new app in your developer dashboard to get:
   - Client ID
   - Client Secret
3. **Netatmo Account Credentials**: Your regular Netatmo username and password
4. **Video Intercom System**: A configured Netatmo Video Intercom with door control modules

## Installation

### Option A: Installing via HACS
1. Add this repository to HACS as a custom repository
2. Search for "Netatmo Video Intercom Integration" in HACS
3. Click Install
4. **Restart Home Assistant**

### Option B: Manual Installation
1. Download the latest release archive
2. Extract the `netatmo_intercom` folder to your `custom_components` directory
3. Your directory structure should look like:
    ```
    └── configuration.yaml
    └── custom_components
        └── netatmo_intercom
            └── __init__.py
            └── manifest.json
            └── ...
    ```
4. **Restart Home Assistant**

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Netatmo Video Intercom"
4. Enter your credentials:
   - **Username**: Your Netatmo account email
   - **Password**: Your Netatmo account password  
   - **Client ID**: From your Netatmo developer app
   - **Client Secret**: From your Netatmo developer app

The integration will automatically discover all door modules in your Netatmo homes and create switches for each one.

## Usage

After configuration, you'll see switches named like:
- `Casa - Citofono interno` 
- `Casa - Citofono esterno`

Each switch represents a door that can be opened. When you turn on a switch:
1. The door opens immediately
2. The switch shows "ON" for 2 seconds
3. The switch automatically turns "OFF"

### Automation Example

```yaml
automation:
  - alias: "Open front door when doorbell pressed"
    trigger:
      platform: state
      entity_id: binary_sensor.doorbell
      to: 'on'
    action:
      service: switch.turn_on
      entity_id: switch.casa_citofono_esterno
```

## Troubleshooting

### Authentication Issues
- Verify your Netatmo credentials are correct
- Check that your Client ID and Client Secret are from the correct app
- Ensure your Netatmo developer app has the necessary permissions

### No Doors Detected  
- Verify your Netatmo Video Intercom is properly configured
- Check that door modules are visible in the official Netatmo app
- Look at Home Assistant logs for detailed error messages

### Integration Not Loading
- Check Home Assistant logs for errors
- Ensure all required files are in the correct directory
- Verify Home Assistant was restarted after installation

# Disclaimer

Author is in no way affiliated with Netatmo.

Author does not guarantee functionality of this integration and is not responsible for any damage.

All product names, trademarks and registered trademarks in this repository, are property of their respective owners.
