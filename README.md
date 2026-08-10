# Hanchuess Home Assistant Integration

A Home Assistant integration for the Hanchu iESS battery storage system, providing full local control and automation support via the Hanchu cloud gateway API.

This fork extends the original guoxiatech/hanchu-ess-ha integration — published by Hanchu (Guoxia Technology, the manufacturer) but not actively maintained since its initial release — with proper automatable entities, correct API mappings, and Predbat compatibility.

## Features

### Sensors
- Battery SOC (%)
- Battery Power (W) — signed (positive = charge, negative = discharge)
- Battery Charge Power (W) — charge only derived power
- Battery Discharge Power (W) — discharge only derived power
- Battery Capacity (kWh)
- Battery pack sensors (per discovered battery serial): Pack SOC (%), Pack SOH (%), Pack Voltage (V), Pack Current (A), Design Capacity (kWh), Full Capacity (Ah), Remaining Capacity (Ah), Temperature 1-N (degC, based on `numBatT`), Environment Temperature, Pack Temperature, MOS Temperature
- Grid Power (W) — signed (positive = import, negative = export)
- Grid Import Power (W) — import only derived power
- Grid Export Power (W) — export only derived power
- Load Power (W)
- PV Power (W)
- AC-Coupled PV Power (W)
- DG Power (W) — only available when generator support is present
- Fast Charge Time Remaining (s)
- Daily Charge/Discharge Energy (kWh)
- Daily Grid Import/Export (kWh)
- Daily Load/PV Energy (kWh)
- Daily DG Energy (kWh) — only available when generator support is present
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

### Settings management
Changes to all control entities above are **staged locally** and only sent to the
device when you press **Write Settings** (or call the `hanchuess.write_settings`
service). This batches all pending changes into a single `iotSet` API call,
avoiding Hanchu's rate limiter.

- **Read Settings** button — calls `iotGet` for all control keys and refreshes
  every control entity's state from the device. Also runs automatically at startup.
- **Write Settings** button — flushes all staged changes to the device in one
  `iotSet` call. Retries once on failure; creates a persistent notification if the
  retry also fails, leaving the buffer intact to retry later.
- **Pending Changes** sensor — shows the count of staged-but-unwritten
  changes (0 when clean). Useful for dashboards and automations.

## Services

In addition to the automatable entities above, this integration exposes two HA services for advanced use.

### `hanchuess.write_settings`

Flush all staged control-entity changes to the device in a single `iotSet` call.
Useful in automations that set time slots or other controls and need to ensure the
device receives the update without the user pressing the Write Settings button.

| Field | Required | Description |
|---|---|---|
| `sn` | No | Inverter serial number. Defaults to your only configured inverter if omitted; required when multiple inverters are configured. |

Example automation action:
```yaml
- action: time.set_value
  target:
    entity_id: time.hanchuess_YOURSERIAL_charge_slot_1_start
  data:
    time: "06:00:00"
- action: hanchuess.write_settings
```

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
- Power sensors normalised to watts using the Hanchu API's explicit per-field unit (the API returns mixed W/kW units)
- Automatic station + battery serial discovery during setup, with battery serial refresh from station detail
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

## Removing the integration

1. Go to **Settings → Devices & Services**, find the Hanchuess entry, and choose
   **Delete**. This removes the device and its entities.
2. HACS installs: also remove Hanchuess from HACS (or its custom repository) so
   it's no longer offered for updates — this also deletes the integration files.
3. Manual installs: additionally delete the `custom_components/hanchuess` folder
   and restart Home Assistant.
4. The integration auto-registers a Lovelace resource for the custom card on
   first setup. This resource isn't tied to the config entry's lifecycle, so it
   may still be listed under **Settings → Dashboards → Resources** after
   removal — delete it manually if you no longer need it.

## Configuration

The setup flow only asks for your Hanchu app credentials — it then discovers your
devices automatically:

1. Enter your Hanchu app **email address** and **password**.
2. The integration logs in and lists the inverters on your account. **Select the
   device(s)** you want to add. Each selected device is created as its own HA
   device; no serial number needs to be entered by hand.

### Options

After setup, open the integration and click **Configure** to adjust:
- **Realtime poll interval** (default 60 s, minimum 30 s)
- **Statistics poll interval** (default 5 min / 300 s, minimum 5 min)
- **Battery poll interval** (default 10 min / 600 s, minimum 5 min)
- **Fast charge/discharge duration** (default 60 min, range 5 min–4 h) — the
  duration applied when the Fast Charge / Fast Discharge switches are turned on

Changing an option reloads the device so the new values take effect immediately.

### Re-authentication

Tokens are refreshed automatically, but if a refresh ultimately fails Home
Assistant raises a repair so you can sign in again without re-adding the
integration. When the token expires, entities first show as unavailable, a repair
prompt appears, and signing in restores them.

## Configuration Options

After initial setup, polling intervals and fast charge duration can be adjusted via **Settings → Devices & Services → Hanchuess → Configure**:

| Option | Default | Range | Description |
|---|---|---|---|
| Realtime poll interval | 60s | 30–3600s | How often live sensor data is refreshed |
| Statistics poll interval | 300s | 300–86400s | How often daily energy totals are refreshed |
| Battery poll interval | 600s | 300–86400s | How often per-battery-pack diagnostics sensors are refreshed |
| Fast charge duration | 60 min | 5–240 min | Default duration when triggering fast charge/discharge |

## Predbat Integration

The Hanchu iESS integration works with Predbat via Predbat's generic Service API. Predbat calls four service hooks — charge_start_service, charge_stop_service, discharge_start_service, discharge_stop_service — which we point at a single Home Assistant script that writes the corresponding time slots to the device via hanchuess.device_control.

### 1. Create the bridge helpers

In Home Assistant, create three helpers:

input_boolean.predbat_charge_start
input_boolean.predbat_discharge_start
input_text.hanchu_last_mode_action — tracks the last mode successfully applied, so the script can skip a redundant API call when Predbat reasserts a state that's already active (see Skipping redundant calls below).

### 2. Create the bridge script

All four of Predbat's service hooks call the same script, script.hanchu_set_state_queued, passing a mode_action field to say which of the four states to apply. The script runs with mode: queued, so if Predbat ever fires two calls close together — e.g. stopping a discharge and starting a charge in the same plan-evaluation cycle — Home Assistant queues the second one behind the first rather than letting both device_control calls race each other on the wire. (The queue only guarantees the two calls don't run concurrently — it relies on Predbat itself calling stop before start, which is Predbat's normal behaviour during a mode transition.)

Create a new script (Settings → Automations & Scenes → Scripts → Add Script → Edit in YAML) and paste:
```
mode: queued
fields:
  mode_action:
    required: true
    selector:
      select:
        options:
          - charge_start
          - charge_stop
          - discharge_start
          - discharge_stop
sequence:
  - variables:
      # mode_action is sometimes only populated under `data` rather than as a
      # bare template variable, depending on whether the script is invoked from
      # the HA "Run script" UI or by a real service call from Predbat's
      # AppDaemon-based dispatch. Check both so it works reliably either way.
      act: >-
        {% if mode_action is defined %}{{ mode_action }}
        {% elif data is defined and data.mode_action is defined %}{{ data.mode_action }}
        {% else %}unknown{% endif %}
  - if:
      - condition: template
        value_template: "{{ act == states('input_text.hanchu_last_mode_action') }}"
    then:
      - stop: "No change — same action already applied, skipping API call"
  - variables:
      start_seconds: "{{ (now() - now().replace(hour=0, minute=0, second=0, microsecond=0)).seconds }}"
      tct_start: "{{ start_seconds if act == 'charge_start' else 0 }}"
      tct_end: "{{ 39600 if act == 'charge_start' else 0 }}"      # 11:00:00
      tdt_start: "{{ start_seconds if act == 'discharge_start' else 0 }}"
      tdt_end: "{{ 86340 if act == 'discharge_start' else 0 }}"   # 23:59:00
  - action: hanchuess.device_control
    data:
      sn: YOURSERIAL
      dev_type: "2"
      value:
        TCT_START_1: "{{ tct_start }}"
        TCT_END_1: "{{ tct_end }}"
        TDT_START_1: "{{ tdt_start }}"
        TDT_END_1: "{{ tdt_end }}"
    response_variable: result
  - if:
      - condition: template
        value_template: "{{ not result.success }}"
    then:
      - delay:
          seconds: 5
      - action: hanchuess.device_control
        data:
          sn: YOURSERIAL
          dev_type: "2"
          value:
            TCT_START_1: "{{ tct_start }}"
            TCT_END_1: "{{ tct_end }}"
            TDT_START_1: "{{ tdt_start }}"
            TDT_END_1: "{{ tdt_end }}"
        response_variable: result2
      - if:
          - condition: template
            value_template: "{{ not result2.success }}"
        then:
          - action: notify.notify
            data:
              title: "⚠️ Hanchu {{ act }} FAILED"
              message: >-
                {{ act }} write failed after retry ({{ result2.message }})
                — check manually.
          - stop: "Both attempts failed — leaving last_mode_action unchanged for retry"
  - action: input_text.set_value
    target:
      entity_id: input_text.hanchu_last_mode_action
    data:
      value: "{{ act }}"
  - choose:
      - conditions: "{{ act == 'charge_start' }}"
        sequence:
          - action: input_boolean.turn_on
            entity_id: input_boolean.predbat_charge_start
      - conditions: "{{ act == 'charge_stop' }}"
        sequence:
          - action: input_boolean.turn_off
            entity_id: input_boolean.predbat_charge_start
      - conditions: "{{ act == 'discharge_start' }}"
        sequence:
          - action: input_boolean.turn_on
            entity_id: input_boolean.predbat_discharge_start
      - conditions: "{{ act == 'discharge_stop' }}"
        sequence:
          - action: input_boolean.turn_off
            entity_id: input_boolean.predbat_discharge_start
```
Replace YOURSERIAL and notify.notify (with your actual mobile app notify service) throughout. Note the script always writes all four fields (TCT_START_1/TCT_END_1/TDT_START_1/TDT_END_1) on every call, zeroing whichever pair isn't the active mode — this keeps charge and discharge mutually exclusive on the device without relying on separate stop/start calls landing in the right order.

**Skipping redundant calls**

Predbat re-evaluates its plan on its normal cycle (every 5 minutes by default) and can re-issue the same service call mid-window — e.g. calling discharge_start_service again 30 minutes into an already-active discharge, simply reasserting the plan rather than changing anything. Before this optimisation, each reassertion triggered a full device_control API call to Hanchu's cloud (and visibly nudged the device's recorded start time forward each time). The input_text.hanchu_last_mode_action check above skips the API call entirely when the requested mode is already the last one successfully applied — in testing this cut 3 redundant calls out of a single 2h20m discharge window, with zero change in actual battery behaviour. The tracker only updates after a confirmed successful write, so a failed attempt still retries correctly on the next cycle rather than being silently skipped.

### 3. apps.yaml configuration
```
num_inverters: 1

inverter_type: "HC"
inverter:
  name: "Hanchu iESS"
  has_rest_api: false
  has_mqtt_api: false
  has_service_api: true
  output_charge_control: "power"
  charge_control_immediate: true
  has_charge_enable_time: false
  has_discharge_enable_time: false
  has_target_soc: false
  has_reserve_soc: false
  has_timed_pause: false
  charge_time_format: "S"
  charge_time_entity_is_option: false
  soc_units: "%"
  num_load_entities: 1
  has_ge_inverter_mode: false
  has_fox_inverter_mode: false
  time_button_press: false
  clock_time_format: "%d-%m-%y %H:%M:%S"
  write_and_poll_sleep: 2
  has_time_window: false
  support_charge_freeze: false
  support_discharge_freeze: false

balance_inverters_seconds: 0

# All four hooks call the same queued script (see step 2 above), passing
# mode_action so it knows which state to apply.
charge_start_service:
  - service: script.hanchu_set_state_queued
    data:
      mode_action: charge_start
charge_stop_service:
  - service: script.hanchu_set_state_queued
    data:
      mode_action: charge_stop
discharge_start_service:
  - service: script.hanchu_set_state_queued
    data:
      mode_action: discharge_start
discharge_stop_service:
  - service: script.hanchu_set_state_queued
    data:
      mode_action: discharge_stop

charge_rate:
- number.hanchuess_YOURSERIAL_charge_power_limit
discharge_rate:
- number.hanchuess_YOURSERIAL_discharge_power_limit

battery_power:
- sensor.hanchuess_YOURSERIAL_battery_power
grid_power:
- sensor.hanchuess_YOURSERIAL_grid_power

soc_percent:
- sensor.hanchuess_YOURSERIAL_battery_soc
# soc_max must be your battery's total usable capacity in kWh
# (NOT a raw SoC or generic "battery" sensor) — Predbat uses it
# together with soc_kw to convert between % and kWh.
soc_max:
- sensor.hanchuess_YOURSERIAL_battery_capacity_kwh
soc_kw:
- sensor.home_battery_state_of_charge_kwh

battery_min_soc:
- number.hanchuess_YOURSERIAL_minimum_discharge_soc

inverter_limit:
- 5000
inverter_limit_charge:
- 5000
inverter_limit_discharge:
- 5000
inverter_limit_export:
- 5000
battery_rate_max:
- 5000
```
Replace YOURSERIAL with your inverter's serial as it appears in your entity IDs.

**Note:** double-check inverter_limit is spelled exactly like that — a stray accented character (e.g. é instead of e, easy to get from autocorrect) will make Predbat silently ignore the setting and fall back to its own default rather than your inverter's real limit.

In addition the hardcoded numbered limits above at 5000 are numbered to my own limit requirements. Please adjust these to your own limits.

### 4. Add to configuration.yaml
```
template:
- sensor:
    - name: "Home Battery State of Charge kWh"
      unique_id: home_battery_soc_kwh
      unit_of_measurement: "kWh"
      state_class: measurement
      device_class: energy
      state: >
          {{ ((states('sensor.hanchuess_YOURSERIAL_battery_soc') | float(0)) / 100 * NN.NN) | round(2) }}
```
NN.NN = size of your battery (i.e. 18.80)

## Development

Setup, the test suite (offline / config-flow / live tiers), platform-specific
instructions, CI checks, and the contribution workflow are documented in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Known Limitations

- Token refresh is handled automatically every 25 days
- Control entity changes (Work Mode, power limits, SOC limits, time slots) are
  **staged locally** and only written to the device when you press **Write Settings**
  or call `hanchuess.write_settings`. Existing automations that write these entities
  must be updated to add a `hanchuess.write_settings` call after the write sequence.

## Diagnostics

This integration supports Home Assistant's built-in diagnostics download. To download a diagnostics report:

1. Go to **Settings → Devices & Services**
2. Find the Hanchuess integration and click **three dots → Download diagnostics**

The report includes system information, integration config, live device state, statistics, and battery payload metadata. The following sensitive fields are automatically redacted:

`token`, `account`, `password`, `sn`, `stationId`, `username`, `pwd`, `unique_id`, `title`, `devId`, `deviceId`, `battery_serials`

This is useful when reporting issues — you can share the diagnostics file without exposing credentials.

## Credits
Based on the original work by [guoxiatech](https://github.com/guoxiatech/hanchu-ess-ha) (Guoxia Technology / Hanchu, the manufacturer).
API reverse engineering and extended entity support by upton68.
Significant ongoing contributions — unit fixes, diagnostics, options flow, release automation, directional power sensors, and battery unit support — by [lancedfr](https://github.com/lancedfr).

## Custom Lovelace Card
The integration auto-registers a custom card **Hanchuess Remote Settings** which
can be found under **Custom cards** when adding a card to your dashboard.

The card provides:

- SN display at the top
- Fast Charge/Discharge — Select mode (charge/discharge), set duration, confirm or stop with real-time countdown
- Energy Settings — Load and configure work mode, charge/discharge time periods, SOC limits, and other parameters from the device menu

Note: If you cannot find the Hanchuess card when adding to dashboard, please clear your browser cache and refresh the page, or restart Home Assistant.

## License
MIT License
