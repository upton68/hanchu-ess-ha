# Inverter status sensor

This recipe creates `sensor.hanchu_inverter_status`, which shows what the
battery is doing right now:

| Status | Meaning |
|---|---|
| **Fast Charging** | The Fast Charge switch is on |
| **Fast Discharging** | The Fast Discharge switch is on |
| **Scheduled Charge** | Work mode is User-defined, the time is inside an active charge slot, and the SOC is below the grid charge maximum |
| **Scheduled Discharge** | Work mode is User-defined, the time is inside an active discharge slot, and the SOC is above the minimum discharge SOC |
| **Charging** | Battery power is positive (e.g. charging from solar) |
| **Discharging** | Battery power is negative |
| **Idle** | None of the above |

The statuses are checked in that order, so a fast charge always wins over a
scheduled one, and a schedule wins over plain charging. This lets you tell
whether the battery is charging from solar or because of a schedule.

It's built from Home Assistant helpers, a few template sensors and one
automation, so you can adapt it to your own setup. It isn't part of the
integration itself.

*Recipe contributed by [@lancedfr](https://github.com/lancedfr) (#33).*

## Before you start

- The Hanchuess integration must be installed and working.
- Your entity IDs contain your inverter's serial number, for example
  `sensor.hanchuess_h0123456789_battery_soc`. Wherever the YAML below says
  `SERIAL`, put your serial in **lower case**. A find-and-replace in a text
  editor is the quickest way.
- Check the entities exist under **Settings → Devices & services → Entities**
  by searching for `hanchuess_`. If any of yours are named differently, change
  them in the YAML to match.

## How it works

1. A **dropdown helper** holds the current status.
2. An **automation** watches the inverter and sets the dropdown.
3. Twelve **template sensors** turn the charge and discharge slot times into
   timestamps, so the automation runs exactly when a slot starts or ends.
4. A **template sensor**, `sensor.hanchu_inverter_status`, mirrors the
   dropdown so you can use it in dashboards and automations like any other
   sensor.

## Step 1: The status dropdown

Go to **Settings → Devices & services → Helpers → Create helper → Dropdown**.

- **Name:** Hanchu Inverter Status
- **Icon:** `mdi:battery-sync`
- **Options**, in this order: `Fast Charging`, `Fast Discharging`,
  `Scheduled Charge`, `Scheduled Discharge`, `Charging`, `Discharging`, `Idle`

This creates `input_select.hanchu_inverter_status`.

## Step 2: The template sensors

Add this to `configuration.yaml`. If you already have a `template:` section,
add these items under it rather than adding a second `template:` key.

```yaml
template:
  - sensor:
      - name: Hanchu Inverter Status
        unique_id: hanchu_inverter_status
        icon: mdi:battery-sync
        state: "{{ states('input_select.hanchu_inverter_status') }}"

      # Slot times as today's timestamps, so the automation can trigger on them
      - name: Hanchu Charge Slot 1 Start
        unique_id: hanchu_charge_slot_1_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_1_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Charge Slot 1 End
        unique_id: hanchu_charge_slot_1_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_1_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Charge Slot 2 Start
        unique_id: hanchu_charge_slot_2_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_2_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Charge Slot 2 End
        unique_id: hanchu_charge_slot_2_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_2_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Charge Slot 3 Start
        unique_id: hanchu_charge_slot_3_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_3_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Charge Slot 3 End
        unique_id: hanchu_charge_slot_3_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_charge_slot_3_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 1 Start
        unique_id: hanchu_discharge_slot_1_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_1_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 1 End
        unique_id: hanchu_discharge_slot_1_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_1_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 2 Start
        unique_id: hanchu_discharge_slot_2_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_2_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 2 End
        unique_id: hanchu_discharge_slot_2_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_2_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 3 Start
        unique_id: hanchu_discharge_slot_3_start
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_3_start' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
      - name: Hanchu Discharge Slot 3 End
        unique_id: hanchu_discharge_slot_3_end
        device_class: timestamp
        state: >
          {% set src = 'time.hanchuess_SERIAL_discharge_slot_3_end' %}
          {{ today_at(states(src)) if has_value(src) else today_at('00:00:00') }}
```

Then go to **Developer Tools → YAML**, click **Check configuration**, and
reload **Template entities**. If that reload isn't listed, restart Home
Assistant.

## Step 3: The automation

Go to **Settings → Automations & scenes → Create automation → Create new
automation**. Open the ⋮ menu, choose **Edit in YAML**, replace everything
with the YAML below, and save.

```yaml
alias: Hanchu Inverter Status
description: >-
  Sets input_select.hanchu_inverter_status. Fast Charging/Fast Discharging come
  first. Next is Scheduled Charge/Discharge, when the work mode is User-defined,
  the time is inside a slot and the SOC allows it. Otherwise it is Charging,
  Discharging or Idle, depending on battery power.
mode: queued
max: 3
triggers:
  - trigger: state
    entity_id:
      - number.hanchuess_SERIAL_grid_to_battery_charge_maximum
      - number.hanchuess_SERIAL_minimum_discharge_soc
      - sensor.hanchuess_SERIAL_battery_power
      - sensor.hanchuess_SERIAL_battery_soc
      - select.hanchuess_SERIAL_work_mode
  - trigger: state
    entity_id:
      - time.hanchuess_SERIAL_charge_slot_1_start
      - time.hanchuess_SERIAL_charge_slot_1_end
      - time.hanchuess_SERIAL_charge_slot_2_start
      - time.hanchuess_SERIAL_charge_slot_2_end
      - time.hanchuess_SERIAL_charge_slot_3_start
      - time.hanchuess_SERIAL_charge_slot_3_end
      - time.hanchuess_SERIAL_discharge_slot_1_start
      - time.hanchuess_SERIAL_discharge_slot_1_end
      - time.hanchuess_SERIAL_discharge_slot_2_start
      - time.hanchuess_SERIAL_discharge_slot_2_end
      - time.hanchuess_SERIAL_discharge_slot_3_start
      - time.hanchuess_SERIAL_discharge_slot_3_end
  - trigger: time
    at:
      - sensor.hanchu_charge_slot_1_start
      - sensor.hanchu_charge_slot_1_end
      - sensor.hanchu_charge_slot_2_start
      - sensor.hanchu_charge_slot_2_end
      - sensor.hanchu_charge_slot_3_start
      - sensor.hanchu_charge_slot_3_end
      - sensor.hanchu_discharge_slot_1_start
      - sensor.hanchu_discharge_slot_1_end
      - sensor.hanchu_discharge_slot_2_start
      - sensor.hanchu_discharge_slot_2_end
      - sensor.hanchu_discharge_slot_3_start
      - sensor.hanchu_discharge_slot_3_end
  - trigger: state
    entity_id:
      - switch.hanchuess_SERIAL_fast_charge
      - switch.hanchuess_SERIAL_fast_discharge
  - trigger: homeassistant
    event: start
actions:
  - choose:
      - alias: Fast Charging
        conditions:
          - condition: state
            entity_id: switch.hanchuess_SERIAL_fast_charge
            state: "on"
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Fast Charging
      - alias: Fast Discharging
        conditions:
          - condition: state
            entity_id: switch.hanchuess_SERIAL_fast_discharge
            state: "on"
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Fast Discharging
      - alias: Scheduled Charge
        conditions:
          - condition: state
            entity_id: select.hanchuess_SERIAL_work_mode
            state: User-defined
          - condition: or
            conditions:
              # A slot is switched off when both its start and end are 00:00
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_charge_slot_1_start
                    before: time.hanchuess_SERIAL_charge_slot_1_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_charge_slot_1_start
                          - time.hanchuess_SERIAL_charge_slot_1_end
                        match: all
                        state: "00:00:00"
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_charge_slot_2_start
                    before: time.hanchuess_SERIAL_charge_slot_2_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_charge_slot_2_start
                          - time.hanchuess_SERIAL_charge_slot_2_end
                        match: all
                        state: "00:00:00"
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_charge_slot_3_start
                    before: time.hanchuess_SERIAL_charge_slot_3_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_charge_slot_3_start
                          - time.hanchuess_SERIAL_charge_slot_3_end
                        match: all
                        state: "00:00:00"
          - condition: numeric_state
            entity_id: sensor.hanchuess_SERIAL_battery_soc
            below: number.hanchuess_SERIAL_grid_to_battery_charge_maximum
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Scheduled Charge
      - alias: Scheduled Discharge
        conditions:
          - condition: state
            entity_id: select.hanchuess_SERIAL_work_mode
            state: User-defined
          - condition: or
            conditions:
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_discharge_slot_1_start
                    before: time.hanchuess_SERIAL_discharge_slot_1_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_discharge_slot_1_start
                          - time.hanchuess_SERIAL_discharge_slot_1_end
                        match: all
                        state: "00:00:00"
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_discharge_slot_2_start
                    before: time.hanchuess_SERIAL_discharge_slot_2_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_discharge_slot_2_start
                          - time.hanchuess_SERIAL_discharge_slot_2_end
                        match: all
                        state: "00:00:00"
              - condition: and
                conditions:
                  - condition: time
                    after: time.hanchuess_SERIAL_discharge_slot_3_start
                    before: time.hanchuess_SERIAL_discharge_slot_3_end
                  - condition: not
                    conditions:
                      - condition: state
                        entity_id:
                          - time.hanchuess_SERIAL_discharge_slot_3_start
                          - time.hanchuess_SERIAL_discharge_slot_3_end
                        match: all
                        state: "00:00:00"
          - condition: numeric_state
            entity_id: sensor.hanchuess_SERIAL_battery_soc
            above: number.hanchuess_SERIAL_minimum_discharge_soc
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Scheduled Discharge
      - alias: Discharging
        conditions:
          - condition: numeric_state
            entity_id: sensor.hanchuess_SERIAL_battery_power
            below: 0
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Discharging
      - alias: Charging
        conditions:
          - condition: numeric_state
            entity_id: sensor.hanchuess_SERIAL_battery_power
            above: 0
        sequence:
          - action: input_select.select_option
            target:
              entity_id: input_select.hanchu_inverter_status
            data:
              option: Charging
    default:
      - action: input_select.select_option
        target:
          entity_id: input_select.hanchu_inverter_status
        data:
          option: Idle
```

## Step 4: Check it works

Open the automation's ⋮ menu and choose **Run actions**. Then look at
`sensor.hanchu_inverter_status` in **Developer Tools → States**. It should
show a status, not `unknown`.

## Notes

- Use the integration's **Battery Power** sensor, where negative means
  discharging. If you use a different battery power sensor with the opposite
  sign, swap the Charging and Discharging labels.
- A slot is treated as switched off only when **both** its start and end are
  00:00, matching how the inverter handles it. Slots that start or end at
  midnight (e.g. 00:00–05:30 or 23:30–00:00) count as active.
- Slots that cross midnight (e.g. 23:30–05:30) work: Home Assistant's time
  condition handles the wrap-around.
- The Scheduled statuses use the slot times stored in Home Assistant. If you've
  changed a slot but haven't pressed **Write Settings** yet, the inverter may
  still be running the old times.
- "Scheduled" means the conditions for a scheduled charge or discharge are met,
  not a confirmation from the inverter. If you want to be strict, you could add
  a battery power check to those two options as well.

## Variant: Predbat integration (Hanchu ESS)

If the inverter is controlled by Predbat's built-in **Hanchu ESS** integration,
Predbat writes the charge and discharge slots straight to the inverter through
the Hanchu cloud. The slot time entities in this integration don't see those
writes, so they stay at 00:00. With the automation above, a Predbat charge
would then only ever show as **Charging** and a Predbat export as
**Discharging**, never as Scheduled.

In that setup, use Predbat's own status instead of the slot times. It reports
what Predbat is telling the inverter to do.

1. In the automation, replace the **Scheduled Charge** and **Scheduled
   Discharge** options with:

   ```yaml
         - alias: Scheduled Charge
           conditions:
             - condition: template
               value_template: "{{ states('predbat.status') is match('Charging') }}"
           sequence:
             - action: input_select.select_option
               target:
                 entity_id: input_select.hanchu_inverter_status
               data:
                 option: Scheduled Charge
         - alias: Scheduled Discharge
           conditions:
             - condition: template
               value_template: "{{ states('predbat.status') is match('Exporting|Discharging') }}"
           sequence:
             - action: input_select.select_option
               target:
                 entity_id: input_select.hanchu_inverter_status
               data:
                 option: Scheduled Discharge
   ```

2. Add a trigger so the automation runs whenever Predbat changes state:

   ```yaml
     - trigger: state
       entity_id: predbat.status
   ```

3. Remove the two slot triggers (the `time.hanchuess_SERIAL_..._slot_...`
   state trigger and the `sensor.hanchu_..._slot_...` time trigger), and the
   twelve slot template sensors from Step 2. They're no longer used. Keep the
   `Hanchu Inverter Status` template sensor.

Notes for this variant:

- If your Predbat instance uses a prefix other than `predbat`, change
  `predbat.status` to match. Check in **Developer Tools → States**.
- `match` checks the start of the status, so `Charging` matches but
  `Hold charging` and `Freeze charging` don't. Those fall through to
  Charging, Discharging or Idle based on battery power. Check which states
  your Predbat shows during a charge and an export, and adjust the patterns
  if needed.
- This variant is only for Predbat's built-in Hanchu ESS integration.
