# Predbat bridge setup for Hanchu iESS (cloud)

This page explains how to run [Predbat](https://github.com/springfall2008/batpred) against a Hanchu iESS inverter through this integration, using a Home Assistant bridge script.

> **New installs: use Predbat's native Hanchu component instead.** Since v9.7.10 Predbat talks to the Hanchu cloud directly, with no bridge script, helpers or automations to maintain - see [Hanchu ESS Cloud](https://springfall2008.github.io/batpred/inverter-setup/#hanchu-ess-cloud) in the Predbat docs. This bridge is kept here for existing setups.

> **Status:** this is a community setup, not part of the official Predbat documentation, and is not supported by Hanchu or the Predbat project. This page is the maintained reference. Test carefully and keep Predbat in read-only mode (`switch.predbat_set_read_only`) until you have verified each step.

Control is implemented via Predbat's generic Service API: Predbat calls four service hooks (`charge_start_service`, `charge_stop_service`, `discharge_start_service`, `discharge_stop_service`), all of which point at a single Home Assistant script that writes the corresponding time slots directly to the device via `hanchuess.device_control`.

Copy the template [hanchu_cloud.yaml](hanchu_cloud.yaml) in this folder over your `apps.yaml` and follow the steps below.

## Prerequisites

Install this integration from the Marketplace (Home Assistant 2026.11 or newer) or HACS (2026.10 or older) - see the [README](../README.md#installation) - and configure it with your Hanchu cloud account credentials. Confirm that inverter and battery sensors are appearing in Home Assistant before proceeding.

## Step 1 — Create helpers

Create the following helpers in Home Assistant (Settings → Devices & Services → Helpers):

**Toggle helpers** (toggle type):

| Entity ID | Name |
| --------- | ---- |
| `input_boolean.predbat_charge_start` | Predbat Charge Start |
| `input_boolean.predbat_discharge_start` | Predbat Discharge Start |

**Text helper** (text type):

| Entity ID | Name |
| --------- | ---- |
| `input_text.hanchu_last_mode_action` | Hanchu Last Mode Action |

`input_text.hanchu_last_mode_action` tracks the last mode successfully applied so the bridge script can skip a redundant API call when Predbat reasserts a state that is already active.

**Number helpers** (number type, min 0, max your inverter's rated power in W, step 1, unit W, initial value your inverter's rated power):

| Entity ID | Name |
| --------- | ---- |
| `input_number.predbat_charge_rate` | Predbat Charge Rate |
| `input_number.predbat_discharge_rate` | Predbat Discharge Rate |

These are placeholders for Predbat's `charge_rate`/`discharge_rate` — see the note on charge and discharge rates under [Notes](#notes).

## Step 2 — Create the bridge script

All four of Predbat's service hooks call the same script, `script.hanchu_set_state_queued`, passing a `mode_action` field to indicate which state to apply. The script runs with `mode: queued` so if Predbat fires two calls close together — for example stopping a discharge and starting a charge in the same plan-evaluation cycle — Home Assistant queues the second call behind the first rather than letting both `device_control` calls race each other.

Create a new script (Settings → Automations & Scenes → Scripts → Add Script → Edit in YAML) and paste the following, replacing `YOURSERIAL` with your device serial number as it appears in your HA entity IDs, and replacing `notify.notify` with your own mobile notification service:

```yaml
alias: Hanchu Set State Queued
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
      # the HA UI or by a real service call from Predbat's AppDaemon dispatch.
      # Check both so it works reliably either way.
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
      # Convert HH:MM:SS time strings from Predbat sensors to seconds since midnight
      charge_start_seconds: >-
        {% set t = states('sensor.predbat_HC_0_charge_start_time').split(':') %}
        {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
      charge_end_seconds: >-
        {% set t = states('sensor.predbat_HC_0_charge_end_time').split(':') %}
        {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
      discharge_start_seconds: >-
        {% set t = states('sensor.predbat_HC_0_discharge_start_time').split(':') %}
        {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
      discharge_end_seconds: >-
        {% set t = states('sensor.predbat_HC_0_discharge_end_time').split(':') %}
        {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
      # Set slot values based on action — zeroise inactive slots
      tct_start: "{{ charge_start_seconds if act == 'charge_start' else 0 }}"
      tct_end: "{{ charge_end_seconds if act == 'charge_start' else 0 }}"
      tdt_start: "{{ discharge_start_seconds if act == 'discharge_start' else 0 }}"
      tdt_end: "{{ discharge_end_seconds if act == 'discharge_start' else 0 }}"
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
          - action: notify.notify  # Replace with your own notification service
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

The script always writes all four time slot fields (`TCT_START_1`, `TCT_END_1`, `TDT_START_1`, `TDT_END_1`) on every call, zeroing whichever pair is not the active mode. This keeps charge and discharge mutually exclusive on the device without relying on separate stop/start calls landing in the right order.

## Step 3 — Create the mid-window time update automation

Predbat may revise its planned charge or discharge end time mid-window without issuing a new charge_start or discharge_start service call. Without this automation, the Hanchu would continue using the original end time written at the start of the window, potentially stopping charge or discharge earlier than Predbat intended.

Create a new automation (Settings → Automations & Scenes → Automations → Add Automation → Edit in YAML) and paste the following, replacing YOURSERIAL with your device serial number:

```yaml
alias: Predbat - Update Hanchu Charge/Discharge Window Times
description: >
  Watches Predbat's charge and discharge end time sensors and updates the
  Hanchu time slots when they change mid-window during an active charge or
  discharge session.
triggers:
  - trigger: state
    entity_id: sensor.predbat_HC_0_charge_end_time
    id: charge_end_changed
  - trigger: state
    entity_id: sensor.predbat_HC_0_discharge_end_time
    id: discharge_end_changed
conditions:
  - condition: template
    value_template: >-
      {{ trigger.to_state.state not in ['unknown', 'unavailable', '00:00:00'] }}
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: charge_end_changed
          - condition: template
            value_template: >-
              {{ is_state('input_boolean.predbat_charge_start', 'on') }}
        sequence:
          - variables:
              charge_start_seconds: >-
                {% set t = states('sensor.predbat_HC_0_charge_start_time').split(':') %}
                {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
              charge_end_seconds: >-
                {% set t = trigger.to_state.state.split(':') %}
                {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
          - action: hanchuess.device_control
            data:
              sn: YOURSERIAL
              dev_type: "2"
              value:
                TCT_START_1: "{{ charge_start_seconds }}"
                TCT_END_1: "{{ charge_end_seconds }}"
                TDT_START_1: 0
                TDT_END_1: 0
      - conditions:
          - condition: trigger
            id: discharge_end_changed
          - condition: template
            value_template: >-
              {{ is_state('input_boolean.predbat_discharge_start', 'on') }}
        sequence:
          - variables:
              discharge_start_seconds: >-
                {% set t = states('sensor.predbat_HC_0_discharge_start_time').split(':') %}
                {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
              discharge_end_seconds: >-
                {% set t = trigger.to_state.state.split(':') %}
                {{ (t[0]|int * 3600) + (t[1]|int * 60) + (t[2]|int) }}
          - action: hanchuess.device_control
            data:
              sn: YOURSERIAL
              dev_type: "2"
              value:
                TCT_START_1: 0
                TCT_END_1: 0
                TDT_START_1: "{{ discharge_start_seconds }}"
                TDT_END_1: "{{ discharge_end_seconds }}"
mode: queued
```

## Step 4 — Add the soc_kw template sensor

Predbat requires a `soc_kw` sensor reporting battery state of charge in kWh. Add the following to your `configuration.yaml`:

```yaml
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

Replace `YOURSERIAL` with your device serial number and `NN.NN` with your total battery capacity in kWh (for example `18.80` for a dual 9.4 kWh system). Restart Home Assistant after adding this.

## Step 5 — Configure apps.yaml

- Replace `YOURSERIAL` throughout the template with your device serial number as it appears in your HA entity IDs
- Adjust `inverter_limit`, `inverter_limit_charge`, `inverter_limit_discharge`, `inverter_limit_export` and `battery_rate_max` to match your inverter and battery rated capacity in watts
- If your EV charger is wired outside the Hanchu meter, keep `import_today` on the integration's daily grid import sensor (not your smart meter's consumption sensor), set `car_charging_energy` to your charger's energy sensor, and turn **switch.predbat_car_energy_reported_load** off: Predbat then adds the car's charging to today's cost itself. A smart meter sensor that already includes the car would count it twice
- Delete the `template: True` line to allow Predbat to start
- Configure your energy rates — see [Energy Rates](https://springfall2008.github.io/batpred/energy-rates/)

> **Note:** Double-check that `inverter_limit` is spelled exactly as shown — an accented character (for example `é` instead of `e` from autocorrect) will cause Predbat to silently ignore the setting and fall back to its own default.

## Notes

- **Skipping redundant calls:** Predbat re-evaluates its plan on its normal cycle and can re-issue the same service call mid-window, simply reasserting the plan rather than changing anything. The `input_text.hanchu_last_mode_action` check skips the API call entirely when the requested mode is already the last one successfully applied. The tracker only updates after a confirmed successful write, so a failed attempt still retries correctly on the next cycle.
- **Behaviour on Predbat restart:** Whenever Predbat restarts it issues both `charge_stop_service` and `discharge_stop_service` in quick succession to put the inverter into a known neutral state. This is expected behaviour. The queued script handles this cleanly — if one of the calls matches the already-active state it is skipped as redundant; the other runs if it represents a real change. You may see one or both fire immediately after any restart.
- **Automation latency:** Start/stop commands are occasionally delayed by up to ~2 minutes due to HA scheduling. This has not caused any practical issues in production use.
- **No charge/discharge enable toggle:** Hanchu has no explicit enable/disable for charge or discharge. The slot zeroing mechanism (setting both start and end to `00:00:00`) is the disable method.
- **Charge and discharge rates:** `charge_rate`/`discharge_rate` point at the placeholder helpers from Step 1, not at the integration's charge/discharge power limit entities, so the inverter's power limits stay at whatever you set them to. Predbat writes these rates directly rather than through the bridge script (for example, setting the discharge rate to 0 for "Hold for car"). The integration only stages such a write — the bridge script's `device_control` call sends just the time-slot settings — so it is never applied on its own, but stays pending and would be sent by the next press of the Write Settings button, possibly long after Predbat has moved on. The trade-off is that features which rely on rate control (car charging hold, low-power charge/export) have no effect on the inverter.
- **Min SOC:** Managed via `battery_min_soc` pointing directly to the Hanchu entity — no separate Predbat reserve setting needed.
- **Mid-window time updates:** Predbat may revise its planned charge or discharge end time mid-window without issuing a new start service call. The mid-window automation above catches these changes and updates the Hanchu time slots accordingly, ensuring the inverter honours Predbat's revised plan rather than the original end time.
