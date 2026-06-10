# Hanchuess Home Assistant Integration

A Home Assistant integration for the Hanchu iESS battery storage system, providing full local control and automation support via the Hanchu cloud gateway API.

This fork extends the original [guoxiatech/hanchu-ess-ha](https://github.com/guoxiatech/hanchu-ess-ha) integration with proper automatable entities, correct API mappings, and Predbat compatibility.

## Features

### Sensors
- Battery SOC (%)
- Battery Power (W) — with automatic kW/W scaling
- Battery Capacity (kWh)
- Grid Power (W) — signed (positive = import, negative = export)
- Load Power (W)
- PV Power (W)
- Daily Charge/Discharge Energy (kWh)
- Daily Grid Import/Export (kWh)
- Daily Load/PV Energy (kWh)
- Device Status (online/offline/pending)

### Controls (fully automatable)
- **Work Mode** — Self-consumption, Backup Energy, User-defined, Off-grid
- **Charge Power Limit** (0–5000W)
- **Discharge Power Limit** (0–5000W)
- **Maximum Charge SOC** (50–100%)
- **Minimum Discharge SOC** (5–45%)
- **Grid to Battery Charge Maximum** (20–100%)
- **Charge Time Slots 1–3** — Start and End times
- **Discharge Time Slots 1–3** — Start and End times
- **Fast Charge** switch
- **Fast Discharge** switch

### Key improvements over original integration
- All control entities are proper HA entities — fully automatable, voice controllable via Alexa/Google
- Correct `iotSet` API keys mapped from live device menu response
- Startup state reading — entities populate with current device values on HA restart
- Debounced time slot entities — prevents multiple API calls when adjusting times
- Automatic kW/W scaling for power sensors (Hanchu API returns mixed units)
- Work mode reads current state on startup
- Fast Charge/Discharge as proper switch entities

## Requirements

- Home Assistant 2024.1 or later
- HACS installed
- Hanchu iESS battery system with cloud connectivity
- Hanchu app account (email and password)

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/upton68/hanchu-ess-ha` as an **Integration**
4. Search for **Hanchuess** in HACS and click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **Hanchuess** and follow the setup flow

### Manual installation

1. Copy the `custom_components/hanchuess` folder to your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via **Settings → Devices & Services**

## Configuration

During setup you will need:
- Your Hanchu app email address
- Your Hanchu app password
- Your device serial number (found in the Hanchu app)

## Predbat Integration

This integration is compatible with [Predbat](https://github.com/springfall2008/batpow) for intelligent battery scheduling.

### Recommended apps.yaml mappings

```yaml
inverter_type: "HC"
inverter:
  has_service_api: true
  output_charge_control: "power"
  charge_time_format: "S"

battery_power:
  - sensor.hanchuess_YOURSERIAL_battery_power
grid_power:
  - sensor.hanchuess_YOURSERIAL_grid_power
soc_percent:
  - sensor.hanchuess_YOURSERIAL_battery_soc
battery_min_soc:
  - number.hanchuess_YOURSERIAL_minimum_discharge_soc
charge_rate:
  - number.hanchuess_YOURSERIAL_charge_power_limit
discharge_rate:
  - number.hanchuess_YOURSERIAL_discharge_power_limit

charge_start_service:
  - service: input_boolean.turn_on
    entity_id: input_boolean.predbat_charge_start
charge_stop_service:
  - service: input_boolean.turn_off
    entity_id: input_boolean.predbat_charge_start
discharge_start_service:
  - service: input_boolean.turn_on
    entity_id: input_boolean.predbat_discharge_start
discharge_stop_service:
  - service: input_boolean.turn_off
    entity_id: input_boolean.predbat_discharge_start
```

Predbat bridge automations
Predbat controls charge/discharge by setting time slots. Add these automations to wire Predbat to the integration:

```
alias: Predbat Bridge - Start Charge
triggers:
  - entity_id: input_boolean.predbat_charge_start
    to: "on"
    trigger: state
actions:
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_charge_slot_1_start
    data:
      time: "{{ now().strftime('%H:%M:%S') }}"
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_charge_slot_1_end
    data:
      time: "11:00:00"

alias: Predbat Bridge - Stop Charge
triggers:
  - entity_id: input_boolean.predbat_charge_start
    to: "off"
    trigger: state
actions:
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_charge_slot_1_start
    data:
      time: "00:00:00"
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_charge_slot_1_end
    data:
      time: "00:00:00"

alias: Predbat Bridge - Start Discharge
triggers:
  - entity_id: input_boolean.predbat_discharge_start
    to: "on"
    trigger: state
actions:
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_discharge_slot_1_start
    data:
      time: "{{ now().strftime('%H:%M:%S') }}"
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_discharge_slot_1_end
    data:
      time: "23:59:00"

alias: Predbat Bridge - Stop Discharge
triggers:
  - entity_id: input_boolean.predbat_discharge_start
    to: "off"
    trigger: state
actions:
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_discharge_slot_1_start
    data:
      time: "00:00:00"
  - action: time.set_value
    target:
      entity_id: time.hanchuess_YOURSERIAL_discharge_slot_1_end
    data:
      time: "00:00:00"
```
Replace YOURSERIAL with your device serial number throughout.

Known Limitations

Battery unit sensors (individual pack SOC, SOH, temperature, voltage) are not yet implemented — these require a separate API endpoint
The Hanchu API returns mixed units for power sensors (watts below 1kW, kilowatts above) — the integration handles this automatically
Token refresh is handled automatically every 25 days
Credits
Based on the original work by guoxiatech.
API reverse engineering and extended entity support by upton68.

Custom Lovelace Card
The integration auto-registers a custom card Hanchuess Remote Settings which can be found under Custom cards when adding a card to your dashboard.

Custom Card

The card provides:

SN display at the top
Fast Charge/Discharge — Select mode (charge/discharge), set duration, confirm or stop with real-time countdown
Energy Settings — Load and configure work mode, charge/discharge time periods, SOC limits, and other parameters from the device menu
Note: If you cannot find the Hanchuess card when adding to dashboard, please clear your browser cache and refresh the page, or restart Home Assistant.

License
MIT License
