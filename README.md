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
- **Charge Power Limit**
- **Discharge Power Limit**
- **Maximum Charge SOC** (50–100%)
- **Minimum Discharge SOC** (5–45%)
- **Grid to Battery Charge Maximum** (20–100%)
- **Charge Time Slots 1–3** — Start and End times
- **Discharge Time Slots 1–3** — Start and End times
- **Fast Charge** switch
- **Fast Discharge** switch

## Services

In addition to the automatable entities above, this integration exposes two HA services for advanced use.

### `hanchuess.fast_charge`

Trigger fast charge or discharge for a set duration directly from an automation — useful for scenarios like boost-charging when import prices go negative, without needing to use the Fast Charge/Discharge switches and a separate duration helper.

| Field | Required | Description |
|---|---|---|
| `sn` | No | Inverter serial number. Defaults to your only configured inverter if omitted. |
| `act` | Yes | Action code: `2` = start fast charge, `-2` = stop fast charge, `3` = start fast discharge, `-3` = stop fast discharge. |
| `duration` | No | Duration in seconds. Required when starting (`act` 2 or 3). |

Example automation action:
```yaml
action: hanchuess.fast_charge
data:
  act: 2
  duration: 1800
```

### `hanchuess.device_control`

Low-level service for sending arbitrary key/value control signals directly to the device — used internally by the integration's entities, but available for advanced or custom automations.

| Field | Required | Description |
|---|---|---|
| `sn` | Yes | Inverter serial number. |
| `dev_type` | Yes | Device type (e.g. `2` for inverter). |
| `value` | Yes | Key-value pairs of control signals to send. |

### Key improvements over original integration
- All control entities are proper HA entities — fully automatable, voice controllable via Alexa/Google
- Correct `iotSet` API keys mapped from live device menu response
- Startup state reading — entities populate with current device values on HA restart
- Debounced time slot entities — prevents multiple API calls when adjusting times
- Automatic kW/W scaling for power sensors (Hanchu API returns mixed units)
- Work mode reads current state on startup
- Fast Charge/Discharge as proper switch entities, plus an automatable `fast_charge` service

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

## Predbat bridge automations
Predbat controls charge/discharge by setting time slots. Add these automations to wire Predbat to the integration:

```yaml
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

## Development

### Running tests

The test suite is split into two tiers so it can run on both Windows (where the
integration is developed) and Linux (CI):

- **Offline tests** — `tests/test_api_mocked.py` (API client, mocked with
  `aioresponses`) and `tests/test_logic.py` (sensor scaling, menu parsing, time
  encode/decode). No credentials or Home Assistant runtime required. Run on any
  platform.
- **Config-flow tests** — `tests/test_config_flow.py` use the Home Assistant test
  harness (`pytest-homeassistant-custom-component`). This pulls in HA core, which
  imports Unix-only modules and **cannot run on Windows** — these tests skip
  automatically there and run on Linux/CI.
- **Live integration test** — `tests/test_api_integration.py` hits the real
  Hanchu cloud API and is opt-in: it skips unless `HANCHUESS_ACCOUNT` and
  `HANCHUESS_PASSWORD` are set.

#### Windows (local development)

Install the cross-platform dependencies and run pytest. The config-flow tests
skip cleanly; the offline tests execute.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-test.txt
pytest
```

> Do **not** install `pytest-homeassistant-custom-component` on Windows (directly,
> or via `requirements-test-ha.txt`). It brings in HA core, whose pytest plugin
> imports `fcntl` (Unix-only) at startup and breaks the **entire** local pytest
> session — every test, not just the config-flow ones, fails to collect with
> `ModuleNotFoundError: No module named 'fcntl'`.
>
> If it does end up installed in your Windows environment, recover with either:
>
> ```powershell
> pip uninstall pytest-homeassistant-custom-component   # restores a clean setup
> # ...or block its plugin for a single run without uninstalling:
> pytest -p no:homeassistant
> ```

#### Linux / CI (full suite)

`requirements-test-ha.txt` adds the HA test harness on top of the cross-platform
deps, so every test — including the config-flow tests — runs.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-test-ha.txt
pytest
```

This is exactly what the GitHub Actions **Tests** workflow
(`.github/workflows/tests.yml`) runs on every push and pull request.

#### Running the live integration test

```bash
export HANCHUESS_ACCOUNT="you@example.com"
export HANCHUESS_PASSWORD="your-password"
export HANCHUESS_SN="YOURSERIAL"          # optional, enables device-specific reads
# export HANCHUESS_ALLOW_WRITE=1          # optional, enables no-op write-path tests
pytest tests/test_api_integration.py
```

On Windows PowerShell, set these with `$env:HANCHUESS_ACCOUNT = "..."` instead of
`export`.

**Known Limitations**

- The Hanchu API returns mixed units for power sensors (watts below 1kW, kilowatts above). The integration includes a heuristic to handle most cases automatically, however readings in the 1–9W range may occasionally be misreported. A full fix using the explicit unit fields returned by the API is currently in progress.

- Battery unit sensors (individual pack SOC, SOH, temperature, voltage) are not yet implemented — these require a separate API endpoint

- Token refresh is handled automatically every 25 days

## Credits
Based on the original work by guoxiatech.
API reverse engineering and extended entity support by upton68.

## Custom Lovelace Card
The integration auto-registers a custom card Hanchuess Remote Settings which can be found under Custom cards when adding a card to your dashboard.

## Custom Card

The card provides:

- SN display at the top
- Fast Charge/Discharge — Select mode (charge/discharge), set duration, confirm or stop with real-time countdown
- Energy Settings — Load and configure work mode, charge/discharge time periods, SOC limits, and other parameters from the device menu

Note: If you cannot find the Hanchuess card when adding to dashboard, please clear your browser cache and refresh the page, or restart Home Assistant.

## License
MIT License
