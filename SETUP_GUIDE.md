# Quick Setup Guide: Damper Thermostat

For full details on every option and how the damper logic works, see [README.md](README.md).

## Before you start

You need Home Assistant **2026.11.0** or newer, and these entities:

**Required**
- **Main thermostat**: the `climate.*` entity that runs your HVAC equipment (for example `climate.main_hvac`). It should report its mode as `heat` or `cool` and expose an `hvac_action` attribute.
- **Damper switches**: one `switch.*` per damper, where on = open (for example `switch.living_room_damper`).
- **Temperature sensors**: at least one per zone, with device class `temperature` (for example `sensor.living_room_temperature`).

**Optional**
- **Humidity sensors**: device class `humidity` (for example `sensor.living_room_humidity`). They are shown on the thermostat but not used for control.

## 1. Install and restart

Install through HACS (custom repository `https://github.com/ssalahi/damper-thermostat`, type **Integration**), or copy `custom_components/damper_thermostat` into your config folder. Then restart Home Assistant.

## 2. Create the Global Settings (once)

1. Go to **Settings → Devices & Services → + Add Integration**.
2. Search for **Damper Thermostat**.
3. The first time, it opens **Global Settings**:
   - **Global Actuator Switches List (Priority Order)**: select **every** damper switch in the house. Put the most important zones first.
   - **Global Maximum Switches Off Limit**: the most dampers allowed to be closed at once (default 3).
   - **Global Minimum / Maximum Temperature**: the setpoint range for all zones (default 60–80°F).
4. Click **Submit**.

## 3. Add a zone (repeat for each zone)

1. Again go to **Settings → Devices & Services → + Add Integration → Damper Thermostat**. From now on this creates a zone.
2. Fill in:
   - **Name**: for example "Living Room".
   - **Temperature Sensor(s)**: one or more. The zone uses their average.
   - **Humidity Sensor** (optional).
   - **Main Thermostat**.
   - **Actuator Switch**: this zone's damper switch or switches. They must already be in the global list.
   - **Cold / Hot Tolerance** (optional, default 0.5°F): how far past the target the zone may go before its damper closes (cold while cooling, hot while heating).
   - **Initial target temperatures and HVAC mode** (optional): used only for this first start. The default mode is **Auto**.
3. Click **Submit**. The zone appears as a device with its own thermostat card.

## 4. Fine-tune on the device page

Each zone's device page has these settings:
- **Reverse Heat/Cool Range** (switch): swaps which Heat/Cool setpoint is used for heating and which for cooling.
- **Heat Fan Mode** / **Cold Fan Mode** (select: `Auto`, `Smart`, `Off`): what the damper does while the main system runs only the fan.

It also has three diagnostic sensors: **Actuator Switch** (Open/Close), **Cold Tolerance** and **Hot Tolerance**.

## Changing settings later

Go to **Settings → Devices & Services → Damper Thermostat**, pick the entry, and click **Configure**.

| Entry | What you can change |
|-------|---------------------|
| Global Settings | Switch priority list, maximum switches off, minimum and maximum temperature. All zones reload automatically. |
| A zone | Name, temperature sensors, humidity sensors (clear the field to remove them), main thermostat, actuator switches, cold and hot tolerance |

Change **setpoints** and **mode** on the thermostat card. Set the **reverse toggle** and **fan modes** on the device page.

## Troubleshooting

**Can't find the integration?**
Restart Home Assistant after installing, and check that the files are in `config/custom_components/damper_thermostat/`.

**"Actuator Switch should be added to the global list first"**
Open Global Settings → **Configure**, add the switch to the list, then add the zone again.

**"Device is already configured"**
Another zone already uses the same damper switch or switches.

**Damper never closes**
In Auto mode the damper is always open. In the other modes, check whether the damper limit has been reached (see the README section "Damper limit and priority").

**Need more help?**
Turn on debug logging (`custom_components.damper_thermostat: debug` under `logger:`), check the [README](README.md), or [open an issue](https://github.com/ssalahi/damper-thermostat/issues).
