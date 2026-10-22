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
- Battery pack sensors (per discovered battery serial): Battery Model (diagnostic, see [Battery model detection](#battery-model-detection)), Pack SOC (%), Pack SOH (%), Pack Voltage (V), Pack Current (A), Design Capacity (kWh), Full Capacity (Ah), Remaining Capacity (Ah), Temperature 1-N (degC, based on `numBatT`), Environment Temperature, Pack Temperature, MOS Temperature
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
- Inverter Model, Rated AC Power (W) and Battery Power Maximum (W), diagnostic, see [Inverter model detection](#inverter-model-detection)

### Controls (fully automatable)
- **Work Mode** — Self-consumption, Backup Energy, User-defined, Off-grid
- **Charge Power Limit** (maximum set from your inverter model, see below)
- **Discharge Power Limit** (maximum set from your inverter model, see below)
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

### Inverter model detection

At startup the integration reads the inverter's model code (`devModel`) from the cloud and looks it up in a table of Hanchu models. This is the same mapping the Hanchu web console uses. The result is used to:

- **Show the real model name** on the device card (e.g. HESS-HY-S-5.0K) instead of "ESS Device".
- **Set the maximum for Charge and Discharge Power Limit.** The cloud's settings menu gives one 0–5000 W range for the whole single-phase range, so on its own it can't tell a 5 kW inverter from a 10 kW one.
- **Provide three diagnostic sensors:** Inverter Model, Rated AC Power and Battery Power Maximum.

Battery power and AC rating aren't always the same, which matters for Predbat:

| Inverter | Battery Power Maximum | Rated AC Power |
|---|---|---|
| Single-phase HESS-HY-S-3.0K / 3.68K / 4.0K / 5.0K / 6.0K | 5000 W | 3000 / 3680 / 4000 / 5000 / 6000 W |
| Single-phase HESS-HY-S-7.0K / 8.0K / 10.0K | Same as AC | 7000 / 8000 / 10000 W |
| Three-phase HESS-HY-T and commercial CESS-HY models | Same as AC | Model rating |

For Predbat, **Battery Power Maximum** is the value for `battery_rate_max`, and **Rated AC Power** is the value for `inverter_limit`.

If the model code isn't recognised, or the model's battery maximum isn't documented (the 48 V HESS-HY-S-6K-S / 12K-S), the power limits fall back to the cloud menu values, as before, and the three sensors show as unknown. If you have a model that isn't recognised, please open an issue with your diagnostics file, which includes the model code.

> **7, 8 and 10 kW single-phase owners:** your power limits can now go above 5000 W, matching your inverter's rating. A warning is logged at startup when the model table and the cloud menu disagree. If the inverter rejects a value above 5000 W, please report it.

### Battery model detection

Each battery pack's model code (`devModel`) is looked up in a table of Hanchu battery models, the same mapping the Hanchu web console uses. The model name is shown on the pack's device card and in a **Battery Model** diagnostic sensor. The sensor's attributes include the raw code, the pack's software version, whether it's a low-voltage (LV) or high-voltage (HV) pack, and, where known, whether it's a **heated** model.

Some packs come in more than one version, shown by a suffix on the code. Code `3_1` is the heated Home-ESS-LV-9.4K, shown as Home-ESS-LV-9.4K-H, and `3` is the unheated version (both confirmed by owners). What the other variants differ by isn't known yet.

If a pack's code isn't in the table, the sensor shows `Unknown (<code>)`. Please open an issue with that value so it can be added.

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

The Hanchu iESS works with [Predbat](https://github.com/springfall2008/batpred) — a Home Assistant battery prediction and optimisation add-on — via Predbat's generic Service API.

Full setup instructions, including the bridge script, helper configuration, `apps.yaml` template, and `configuration.yaml` additions, are documented in the [Predbat inverter setup docs](https://springfall2008.github.io/batpred/inverter-setup/#hanchu-iess).

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

The report includes system information, integration config, live device state, statistics, battery payload metadata, and the identified inverter model. The following sensitive fields are automatically redacted:

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
