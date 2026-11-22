# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Entries up to and including 1.2.9 are summarised from the git history and tags;
later versions are tracked here going forward.

## [Unreleased]

## [2.11.0-beta.1] - 2026-11-22

Beta for #78 (Home-ESS-HV high-voltage battery stacks).

### Changed
- Batteries without per-module detail, such as Home-ESS-HV high-voltage
  stacks (the cloud answers `90060 Not Found Data!`), now show the SOC, SOH,
  model, online status and firmware the station list carries, on inverter
  installs as well as battery-only ones. The station list is only read when
  a battery needs it, so installs whose batteries already work make no
  extra calls (#78).

## [2.10.1] - 2026-11-22

Fix for HESS-HY-T three-phase systems with ESS-HV batteries (#76), tested by
the reporter on 2.10.1-beta.1.

### Fixed
- Since 2.6.0, the whole integration failed to load (retrying setup
  forever) if the cloud returned no battery detail, as it does for the
  battery on some HESS-HY-T three-phase systems. 2.5.0 accepted this. The
  inverter now loads as normal, and the battery sensors show unavailable
  until the cloud provides battery data (#76).
- Adding an account whose inverter is already set up now says "already
  configured" instead of "No Hanchu inverters or batteries found" (#76).

## [2.10.0] - 2026-11-22

### Added
- **Weather Optimize and Octopus cards** (`custom:hanchuess-weather-card` and
  `custom:hanchuess-octopus-card`), laid out like the Hanchu app's Weather
  Optimize and Electricity Price Strategy screens. Built on the 2.9.0
  strategy entities: changes are staged through the normal entity services
  and sent with the strategy's Save button. They show unsaved changes, save
  errors, disabled entities and strategies never saved in the app, in English
  and Simplified Chinese. Shipped with the integration and registered as
  dashboard resources automatically, like the energy card. (#74)
- `hanchuess/strategy_entities` WebSocket command, which returns the strategy
  entities' ids for an inverter by unique id, so renamed entities are found.
  (#74)

## [2.9.0] - 2026-11-21

### Added
- **Weather Optimize and Octopus (Electricity Price Strategy) settings**, as on
  the Hanchu app's strategy screens. Weather Optimize: on/off, charge start and
  end, and the SOC for each of the 11 weather conditions. Octopus: on/off,
  schema type (Price or Point settings), the two enable switches **Octopus
  Switch 00:00-08:00 / Charge Price** and **Octopus Switch 12:00-19:00 /
  Discharge Price** (the windows in Point settings, the price strategies in
  Price settings, with an `applies_to` attribute saying which), charge and
  discharge price thresholds (0–50 p/kWh), the half-hour charge slots for
  00:00-08:00 and 12:00-19:00 (0–10 each) and the postcode. Plus the Strategy
  Priority both screens share. All disabled by default; nothing is read from
  the cloud until one is enabled. Changes are staged and sent with a **Save**
  button per strategy, which reads the latest settings first, changes only
  what was staged, and keeps any fields or weather categories it doesn't know.
  Read every 5 minutes. As in the app, Octopus changes saved before 22:00
  apply from the next day, after 22:00 from the day after. A charge-slot window the record doesn't include
  (the app leaves them out when saving in Price mode) shows 0 and can still
  be set. A strategy never saved in the app stays unavailable
  and is not saved from Home Assistant. These run in the Hanchu cloud and can
  conflict with battery control from Home Assistant if both are used. (#72)
- **Reconfigure** to change the stored Hanchu password, e.g. after changing it
  in the app, without waiting for the re-authentication repair. (#72)

### Changed
- The **Pending Changes** sensor also counts staged Weather Optimize and
  Octopus changes, with a breakdown in its attributes.
- Diagnostics include the Weather Optimize and Octopus settings (postcode
  redacted).

### Development
- `tools/release.sh` now runs on macOS (bash 3.2 and BSD sed) as well as
  Git Bash and Linux.
- Fixed the CHANGELOG compare links, which still pointed at 2.5.0.

## [2.8.0] - 2026-11-19

Energy figures for the batteries, the PV strings and the whole station.

### Added
- **Monthly, Yearly and Lifetime energy** (kWh) for PV, Load, Grid Import,
  Grid Export, Battery Charge and Battery Discharge, on the inverter device.
  Taken from the cloud's own statistics (`pcs/historyStaticsChart`, as the
  web console's Statistics charts use), so they stay right across Home
  Assistant downtime and replace `utility_meter` helpers. Lifetime suits the
  Energy dashboard. Not on battery-only stations. (Discussion #69, #70)
- **Charge Today, Discharge Today, Charge Total and Discharge Total** (kWh)
  per battery, on normal installs and battery-only stations. Calculated from
  each battery's minute-by-minute voltage and current in the cloud
  (`bmsInfo/powerMinuteChart`), fetched incrementally. Today resets at local
  midnight. Totals are saved across restarts (missed time is filled in, up
  to 3 days) and work in the Energy dashboard. Gaps over 5 minutes are
  skipped. (#68)
- **Battery State** per battery: Idle, Charging or Discharging. (#68)
- **PV string sensors**: Power (W) and Voltage (V) for each PV input the
  inverter reports (PV1, PV2, PV3 on 3-MPPT models), plus Current (A)
  calculated as power ÷ voltage (0 A when the string has no output, e.g.
  after dark; unknown only if there is output but under 10 V). The cloud reports
  string power to 0.01 kW, so each string is accurate to about 10 W. Read
  from the realtime data the integration already polls, so there are no
  extra cloud calls. Strings the cloud leaves out at startup (seen
  overnight) are added as soon as it reports them. Disabled by default on
  AC-coupled systems. (#67)
- Options: **Battery energy poll interval** (default 5 minutes, minimum 1
  minute, on both the normal and battery-only screens) and **Energy history
  poll interval** (default 1 hour, minimum 15 minutes).
- Diagnostics include each battery's energy state (anonymised) and the
  energy history figures, with any errors.

### Fixed
- Battery reads on battery-only stations now refresh the token on a 401 like
  the other endpoints, instead of failing until the next scheduled refresh.
- Translation files had a duplicate "battery_power" key (inverter and
  per-battery sensors). Both names were identical, so nothing displayed
  differently. A test now guards against duplicate keys.

## [2.7.0] - 2026-11-15

### Added
- **Battery Power** (W) per battery: pack voltage × current, positive when
  charging and negative when discharging, matching the inverter's Battery
  Power sensor (#61).
- **Remaining Energy** (kWh) per battery: SOC × Design Capacity, alongside
  Remaining Capacity (Ah).
- **Last Data Update** per battery (diagnostic, disabled by default): when the
  battery's logger last uploaded to the cloud, to spot stale readings.

### Changed
- "Full Capacity" (Ah) is now named **Full Charge Capacity**. Entity IDs are
  unchanged.

### Documentation
- README: how to build charge/discharge energy (kWh) per battery from Battery
  Power with Home Assistant's Template, Integral and Utility Meter helpers.
  The cloud provides no live per-battery energy counters.

## [2.6.0] - 2026-11-15

### Added
- **Battery-only stations**: Hanchu batteries with a third-party inverter
  (e.g. LuxPower) can now be added. When no Hanchu inverter is found during
  setup, stations with Hanchu batteries are offered instead; third-party
  inverters that appear as placeholders are ignored. Each battery gets its own
  device under a Hanchu Station device, with the full battery and cell sensor
  set, polled every 60 seconds by default (minimum 60). No inverter sensors or
  controls in this mode. Tested on LuxPower systems with 4 and 6 batteries
  (#61).
- Diagnostics: for a battery-only station, a redacted outline of the station
  (inverter brands, battery count, models, shortened serials); for every
  install, per battery (anonymised), where its last data came from and the
  error the cloud returned, if any.

### Fixed
- Batteries are read by the device ID the station lists for them, falling
  back to the serial. Older batteries registered under a device ID that
  differs from their serial previously showed Unknown for every sensor. This
  applies to installs with a Hanchu inverter too.
- Battery-only stations: if a battery's detail data is unavailable, its SOC,
  SOH and model are taken from the station list instead of showing Unknown.
- Battery voltage and current show 2 decimal places and temperatures 1 (pack
  voltage was shown rounded to whole volts).

### Changed
- Diagnostics now also redact the station name.
- Release workflow: tags with a suffix (e.g. `v2.6.0-beta.1`) are published as
  GitHub pre-releases and may be cut from a branch; `vX.Y.Z` tags are
  unchanged.

## [2.5.0] - 2026-11-13

### Added
- **Battery cell sensors** for each battery that reports cell data: Max Cell
  Voltage, Min Cell Voltage and Cell Voltage Difference (shown in mV), plus
  one voltage sensor per cell (Cell 1-N Voltage), disabled by default. Useful
  for spotting imbalanced or weak batteries (#61).

### Documentation
- Predbat bridge setup moved here from the Predbat docs as
  [docs/predbat-bridge.md](docs/predbat-bridge.md), with its `apps.yaml`
  template [docs/hanchu_cloud.yaml](docs/hanchu_cloud.yaml). It includes the
  placeholder charge/discharge rate helpers and a note on EV chargers wired
  outside the Hanchu meter. The README now points new installs at Predbat's
  native Hanchu component (v9.7.10 or later).

## [2.4.0] - 2026-11-11

### Added
- **Inverter Status** sensor: Fast Charging, Fast Discharging, Scheduled
  Charge, Scheduled Discharge, Charging, Discharging or Idle. The work mode,
  slots and SOC limits are read from the inverter every 5 minutes, so slots
  set by Predbat's Hanchu ESS integration, the Hanchu app or the web console
  are picked up too; changes made through this integration apply immediately.
  The poll interval can be lowered to 1 minute in Options. Disabling the
  sensor stops the extra poll. Based on @lancedfr's recipe (#33).

### Documentation
- Inverter status recipe: added a variant for systems controlled by
  Predbat's built-in Hanchu ESS integration, which uses `predbat.status` for
  the Scheduled Charge / Scheduled Discharge statuses, because Predbat's slot
  writes aren't reflected in this integration's slot time entities.

## [2.3.1] - 2026-11-10

### Fixed
- The **Hanchuess Remote Settings** card failed to load on Home Assistant
  2026.11, where the built-in Marketplace replaced HACS and took over the
  `/hacsfiles` URLs the card was served from. The card is now served from the
  integration's own path (`/hanchuess_card/`), and the existing dashboard
  resource is updated automatically on startup. A version number in the URL
  makes browsers load the new card after each update. If your dashboard
  resources are managed in YAML, change the card's URL to
  `/hanchuess_card/hanchuess-energy-card.js`.

### Documentation
- Added an [inverter status sensor recipe](docs/inverter-status.md)
  (Fast Charging / Scheduled Charge / Charging / Idle, etc.) built from
  helpers, template sensors and an automation. Contributed by @lancedfr (#33).

## [2.3.0] - 2026-11-04

### Changed
- The integration now stores your Hanchu account and password with the
  config entry, so when the cloud rejects a token refresh it logs in again
  automatically instead of asking you to re-authenticate. You are only
  prompted if the stored password no longer works. As with most Home
  Assistant cloud integrations, the credentials are kept in Home Assistant's
  config storage (`.storage/core.config_entries`); they are redacted from
  diagnostics.
- Existing installs keep the previous behaviour until the next time you
  complete a re-authentication prompt, which saves the credentials. New
  installs store them during setup.

## [2.2.2] - 2026-11-03

### Fixed
- Re-adding the integration after a token failure no longer fails with
  401 / "90076 Account or password incorrect". The shared API client is now
  dropped when the last entry unloads, and setup adopts the entry's fresh
  token instead of reusing a dead one (#52).
- Authentication failures now raise Home Assistant's re-auth prompt reliably,
  instead of retrying setup every few seconds (#52).
- Battery discovery restored. Hanchu has deprecated
  `/platform/station/detail`, so new or re-added installs found no batteries.
  Discovery now uses `/platform/homePage/stationInfo`, with the old endpoint
  as a fallback. Existing installs were unaffected because their battery
  serials were already stored (#52).
- `hacs.json` now sets the minimum Home Assistant version to 2026.8.0. The
  2.0.4 release notes and the README already gave 2026.8.0 as the minimum,
  but `hacs.json` still said 2024.1.0, so HACS would offer the integration
  to installs that can't run it.

## [2.2.1] - 2026-10-25

### Changed
- The "Could not load battery details" setup error now explains the most
  common cause: the Hanchu cloud doesn't give an account access to its
  battery details until it has logged into the web console once. The message
  tells the user to log in at https://iess3.hanchuess.com/login, log out and
  try again. README has a new **First-time setup** section covering the same
  (#40, #48).

### Fixed
- README listed Home Assistant 2024.1 as the minimum; it is 2026.8.0, as
  already enforced by `hacs.json`.

### Removed
- Unused `strings.json`. Custom integrations load only `translations/*.json`,
  and the file had drifted out of sync with `translations/en.json`.

## [2.2.0] - 2026-10-22

### Added
- Battery model detection. Each pack's `devModel` from
  `queryBatteryDataDivisions` is looked up in a table of Hanchu battery models,
  taken from the Hanchu web console's own mapping.
  - Each battery's device card shows its model name instead of "Battery Pack".
  - New per-pack **Battery Model** diagnostic sensor, with the raw code, the
    pack's software version, LV/HV class and, where known, whether it is a
    heated model as attributes.
  - Code `3_1` (heated Home-ESS-LV-9.4K) is shown as Home-ESS-LV-9.4K-H,
    matching Hanchu's own name for the heated version, and `3` as the unheated
    Home-ESS-LV-9.4K. Both confirmed by owners.

## [2.1.0] - 2026-10-21

### Added
- Inverter model detection. The model code (`devModel`) from `getDeviceStatus`
  is looked up in a table of all 32 Hanchu inverter models, taken from the
  Hanchu web console's own mapping, with power ratings from Hanchu's manuals.
  - The device card shows the real model name (e.g. HESS-HY-S-5.0K) instead of
    "ESS Device".
  - New diagnostic sensors: **Inverter Model**, **Rated AC Power** and
    **Battery Power Maximum**. These give Predbat users the right
    `inverter_limit` and `battery_rate_max`, which differ on single-phase
    3.0K–6.0K units.
  - Diagnostics now include the identified model.

### Changed
- The maximum for Charge and Discharge Power Limit now comes from the model
  table when the model is known. The cloud menu offers a single 0–5000 W range
  for the whole single-phase range, which capped 7, 8 and 10 kW single-phase
  inverters at 5000 W. A warning is logged when the table and the menu
  disagree. Unrecognised models, and models whose battery maximum isn't
  documented, keep the menu values.

## [2.0.6] - 2026-10-10

### Fixed
- Energy card auto-registration could wipe all other dashboard resources on
  startup ([#41](https://github.com/upton68/hanchu-ess-ha/issues/41)). Home
  Assistant loads the storage-mode Lovelace resource collection lazily; if this
  integration set up before anything else had loaded it (most likely on a slow
  startup), it saw an empty list and saved `.storage/lovelace_resources` with
  only the energy card in it. The collection is now loaded first via
  `async_get_info()`. On newer Home Assistant versions, which load the
  collection inside `async_create_item()` themselves, the same race would have
  added a duplicate card entry instead; that is fixed too. Thanks to
  @adexandros for the diagnosis.

## [2.0.5] - 2026-09-10

### Fixed
- Test suite: `tests/test_diagnostics.py`'s `_make_runtime_data()` helper didn't
  supply `inverter_device_id`, which `HanchuessData` started requiring in 2.0.4
  (the `via_device_id` fix). No functional change to the integration itself —
  test-only fix.

## [2.0.4] - 2026-09-09

### Fixed
- **Battery sensors no longer go `unavailable` on Home Assistant 2026.9+.**
  `BatterySensor.device_info` linked each battery pack device to its parent
  inverter using the deprecated `via_device` parameter. HA 2026.9 turned this
  from a deprecation warning into a hard `RuntimeError` for calls that HA's
  own `entity_platform` makes on an integration's behalf (no integration
  frame is left on the stack for HA to attribute the warning to, so it falls
  back to raising), which aborted battery entity creation entirely. The
  inverter device is now explicitly registered during `async_setup_entry`
  and its registry id is passed to battery entities via `via_device_id`.

### Changed
- **Minimum supported Home Assistant version is now 2026.8.0** (was
  unbounded/untested below that). `via_device_id` on `DeviceInfo` and
  `device_registry.async_get_or_create()` was only introduced in 2026.8,
  so this integration requires it going forward. On HA versions prior to
  2026.9 this change is a no-op safety net; the fix itself only matters on
  2026.9+.

## [2.0.3] - 2026-08-11

### Fixed
- **Control sensors now populate automatically on Home Assistant restart.**
  Discharge Power Limit, Charge Power Limit, Max Charge SOC, Min Discharge SOC,
  Grid to Battery Max, and Work Mode previously stayed `unavailable` after a
  restart until the **Read Settings** button was pressed manually. The startup
  values were already being fetched via `iotGet` during setup, but were never
  applied to the (not-yet-registered-at-fetch-time) control entities. They're
  now applied automatically once entity setup completes.
- **Startup value fetch no longer times out prematurely.** The `iotGet` call
  that fetches these startup values was wrapped in a fixed 8-second timeout,
  separate from and shorter than the API client's own per-attempt timeout
  (15s as of the previous release) — meaning the fetch was very likely to be
  cut off before it could complete, especially since Hanchu's cloud API
  response time varies considerably (observed 7s–45s across different
  restarts). The outer timeout has been removed; the fetch now relies solely
  on the API client's own internal retry/timeout handling. As a result, HA
  startup may occasionally take longer than before while this fetch
  completes, in exchange for it actually succeeding.
  
## [2.0.2] - 2026-08-10

### Changed
- **HanchuessApiClient now reuses Home Assistant's shared aiohttp session** (via async_get_clientsession) instead of opening a new ClientSession per request, and the per-attempt request timeout is increased from 10s to 15s. Reduces spurious timeouts and retries during periods of slow response from Hanchu's cloud API — in testing, writes that previously needed 2–3 attempts now mostly land on the first try. HanchuessApiClient.__init__ now requires hass as its first argument (internal API change; only affects direct users of the client class, not the integration's public services/entities).
- **Predbat bridge automations replaced with a single queued script.** Previously, Predbat's four service hooks each triggered a separate HA automation making its own independent hanchuess.device_control call, with no guarantee against two calls (e.g. a discharge-stop and charge-start landing in the same Predbat cycle) racing each other and being rejected by Hanchu's server. All four hooks now call one script running with mode: queued, so calls are serialised rather than racing. See the Predbat Integration section for the updated setup.
- **Predbat bridge script now skips redundant writes.** When Predbat re-asserts a charge/discharge state that's already active (which it does routinely on its normal plan-evaluation cycle), the bridge script now detects this via a new input_text.hanchu_last_mode_action helper and skips the device_control call entirely, rather than sending an unnecessary write to Hanchu's cloud API on every cycle.

## [2.0.1] - 2026-07-16

### Fixed
- **`hanchuess.device_control` service and Lovelace card Load/Set buttons** 
  now refreshes the corresponding control entities (Work Mode, charge/discharge power and SOC limits, all time slots)
  immediately after a successful write, instead of leaving them stale until
  "Read Settings" is pressed. Any conflicting staged-but-unwritten value for the
  same key is also discarded so a later "Write Settings" press can't overwrite
  the direct write.

## [2.0.0] - 2026-07-15

### Added
- `button.py` new integration platform registering the Read Settings and Write
  Settings button entities.
- **Read Settings** and **Write Settings** button entities on the inverter device.
  - **Read Settings** calls `iotGet` for all control keys and refreshes the state
    of every control entity (Work Mode, charge/discharge power limits, SOC limits,
    all time slots) from the device.
  - **Write Settings** flushes all staged changes to the device in a single
    `iotSet` call. On failure it retries once after 5 s; if the retry also fails a
    persistent HA notification is created listing the pending keys and the buffer is
    left intact so the user can retry.
- **Pending Changes** sensor entity — exposes the number of
  staged-but-unwritten settings as a real-time HA sensor (unique ID
  `{sn}_pending_settings_changes`). Useful for automations and dashboards.
- **`hanchuess.write_settings` service** — flushes staged settings from an
  automation. Accepts an optional `sn` field (defaults to the only configured
  inverter; required when multiple inverters are configured).
- `staging.py` — new `SettingsStagingBuffer` class that accumulates control-entity
  changes in memory with no HA dependencies. Holds the pending payload, count, and
  an `on_change` callback that drives the pending sensor.
- **`hanchuess/clear_staging` WebSocket command** — lightweight command called by
  the Lovelace card after a successful Load or Set to clear the HA staging buffer
  without a second API call. Also usable from browser dev tools.

### Changed
- **All control entities now stage changes locally instead of calling `iotSet`
  immediately.** Work Mode (`select`), charge/discharge power limits, SOC limits
  (`number`), and all 12 charge/discharge time slots (`time`) write to the staging
  buffer when changed in the UI or via automation. The device is only updated when
  the user presses **Write Settings** or calls `hanchuess.write_settings`.
- Lovelace card "Set" button (`hanchuess/iot_set` websocket): after a successful
  direct write via the card, the HA staging buffer is now cleared so the two write
  paths stay in sync.
- `number.py`, `select.py`, `time.py`: removed the per-entity `async_device_control`
  call from every write method. The revert-on-failure logic in `time.py` has also
  been removed (no immediate API call means no immediate failure to revert from).
- `HanchuessData` dataclass extended with two new fields: `staging`
  (`SettingsStagingBuffer`) and `control_registry` (`dict[str, entity]`).
- Each control entity registers itself in `control_registry` on
  `async_added_to_hass`, exposing an `apply_value(raw)` method used by
  `apply_iot_values` (called by Read Settings and in future read-back paths).
- **Read Settings button** now clears the staging buffer after successfully
  applying fresh device values, so `Pending Changes` drops to zero immediately
  after a read.
- **Lovelace card Load button** now calls `hanchuess/clear_staging` after a
  successful `iotGet`, clearing the HA staging buffer in sync with the card's
  own state.
- **Lovelace card Set button** now explicitly calls `hanchuess/clear_staging`
  after a successful `iotSet` via a shared `_clearStaging()` helper, replacing
  the implicit server-side `staging.clear()` side-effect that previously lived
  in `ws_iot_set`. Both card operations now use the same code path.
- `ws_iot_set` no longer clears the staging buffer itself; the card is now
  solely responsible for clearing after a direct write.
- **Entity sections reorganised** to reduce clutter on the HA device page:
  - **Configuration section** — Work Mode, all 5 number controls (charge/discharge
    power limits, SOC limits, grid charge limit), all 12 charge/discharge time
    slot entities.
  - **Controls section** (default, no category) — Read Settings, Write Settings,
    Fast Charge, Fast Discharge switches.
  - **Diagnostic section** — Device Status, Pending Changes.
- Migrated config entry state to Home Assistant's `runtime_data` pattern and moved
  service registration to `async_setup`, satisfying the `runtime-data` and
  `action-setup` Home Assistant Bronze quality-scale rules.
- Sensors now always set `has_entity_name`, ensuring device-name prefixing is
  consistent across all entities (`has-entity-name` rule).
- Declared `"quality_scale": "bronze"` in `manifest.json`; all Bronze rules are now
  met except `brands`, which is documented as pending an external PR to
  `home-assistant/brands`.
- **`hanchuess.device_control` service now returns a response** —
  `{"success": bool, "message": str}` — so automations can read
  `response_variable` to know whether the write succeeded and, if not, why.
  Registered with `supports_response: optional`, so calls that don't request a
  response are unaffected.

### ⚠️ Breaking change — Predbat bridge automations
Control writes (time slots, work mode, power limits) **no longer reach the device
immediately**. Any automation that sets a control entity and expects the device to
act on it straight away must now call `hanchuess.write_settings` after the write:


## [1.4.1] - 2026-07-13

### Fixed
- `battery_design_capacity` sensor no longer declares an invalid `energy`
  device class with `measurement` state class (Home Assistant only allows
  `total`/`total_increasing` for that combination). Design capacity is a
  fixed rating, not a changing measurement, so it now has no device class or
  state class, matching `battery_full_capacity` and `battery_remaining_capacity`.

## [1.4.0] - 2026-07-08

### Changed
- Migrated config entry state to Home Assistant's `runtime_data` pattern and moved
  service registration to `async_setup`, satisfying the `runtime-data` and
  `action-setup` Home Assistant Bronze quality-scale rules.
- Sensors now always set `has_entity_name`, ensuring device-name prefixing is
  consistent across all entities (`has-entity-name` rule).
- Declared `"quality_scale": "bronze"` in `manifest.json`; all Bronze rules are now
  met except `brands`, which is documented as pending an external PR to
  `home-assistant/brands`.

### Added
- Config flow test coverage for the "device already configured" abort path.
- Removal instructions in `README.md` and brand-asset submission guidance in
  `CONTRIBUTING.md`.

## [1.3.0] - 2026-07-06

### Added
- Per-battery-pack sensor support using discovered battery serials, including pack
  SOC, voltage, current, and temperature sensors.
- Battery polling coordinator and a new **Battery poll interval** option
  (default 600s, configurable in the options flow).
- Battery diagnostics payload support with anonymised per-battery buckets and
  coordinator metadata.
- Additional per-battery BMS sensors: state of health (`sohPack`), design
  capacity (`designCapacity`), full capacity (`capFull`), and remaining
  capacity (`capRemain`).

### Changed
- Config flow now resolves and stores `stationId`, fetches station detail during
  setup, and persists discovered `battery_serials`.
- Runtime setup now refreshes battery serials from station detail and syncs
  updates across entries sharing the same station.
- API locale header handling now normalises to `zh` for Chinese locales and `en`
  otherwise.
- Battery pack temperature sensors now surface dynamically as `tBat1..tBatN`
  based on each battery payload's `numBatT` value.

### Fixed
- `stationId` resolution can now reuse pre-fetched device status to avoid
  redundant API calls during setup.
- Diagnostics redaction expanded to include battery identifiers and related
  device IDs (`battery_serials`, `devId`, `deviceId`).


## [1.2.12] - 2026-07-04

### Added
- Four directional power sensors derived from signed realtime power values:
  Battery Charge Power, Battery Discharge Power, Grid Import Power, and Grid
  Export Power (all reported as positive-only watts).

### Fixed
- Directional derived power sensors now canonicalize zero so they never display
  a negative zero value (`-0 W`); zero flow is always shown as `0 W`.

## [1.2.11] - 2026-07-01

### Fixed
- `iotSet` requests to Hanchu's cloud API now retry up to 3 times with
  backoff (2s, 4s) on timeout or connection error, instead of failing
  silently on the first attempt. Addresses an issue where a transient
  network fault (e.g. an ISP-side outage) could cause a time-slot write to
  time out with no retry, leaving the previous schedule active on the
  device despite the write appearing to have been sent.
- Time slot entities (`time.py`) now revert to the last *confirmed* value
  if a write ultimately fails after all retries, instead of permanently
  showing the requested value regardless of whether the device actually
  accepted it. Previously a failed write left the entity's displayed state
  incorrect indefinitely, which meant automations checking the entity state
  after a write could not detect the failure.

## [1.2.10] - 2026-06-30

### Added
- `CONTRIBUTING.md`, `CHANGELOG.md`, GitHub issue/PR templates, and a Dependabot
  config (GitHub Actions + pip).
- Automated GitHub Release workflow — pushing a `vX.Y.Z` tag to `main` builds
  `hanchuess.zip` and publishes a release using the matching CHANGELOG section.
- `loggers` key in `manifest.json` for proper HA logger registration (#13).

### Changed
- README trimmed: development/testing instructions moved to `CONTRIBUTING.md`;
  Configuration section corrected to reflect account/password setup with device
  selection (no manual serial entry).
- `hacs.json`: added `zip_release` and `filename` so HACS installs from the
  release zip asset.

### Removed
- Unused screenshot images under `docs/`.

## [1.2.9] - 2026-06-29

### Added
- Options flow (integration → **Configure**) to set the realtime and statistics
  poll intervals and the fast charge/discharge duration, without re-adding the
  integration. The entry reloads automatically when options change.

### Changed
- README: corrected the setup instructions (account/password + device selection,
  no manual serial entry) and documented the options flow.

## [1.2.8] - 2026-06-29

### Added
- Diagnostics support — downloadable, token/serial-redacted JSON from the
  integration and device pages, including the cached device status, statistics,
  resolved menu limits, and startup values.
`quality_scale.yaml` tracking progress against Home Assistant's integration
    quality scale.

## [1.2.7] - 2026-06-29

### Changed
- Power sensors are normalised to watts using the Hanchu API's explicit per-field
  unit (`<field>Unit`), falling back to the legacy magnitude heuristic only when
  no unit is present.

## [1.2.6] - 2026-06-24

### Added
- Test suite (offline logic, mocked API, config-flow, opt-in live API) and a
  GitHub Actions **Tests** workflow.

## [1.2.5] - 2026-06-24

### Added
- Sensor translations (English and Simplified Chinese).

## [1.2.4] - 2026-06-20

### Added
- `hanchuess.fast_charge` service for triggering fast charge/discharge for a set
  duration from automations.
- `hanchuess.device_control` low-level service for arbitrary control signals.
- Fast Charge / Fast Discharge switch entities.

## [1.2.3] - 2026-06-12

### Changed
- Adjusted fast charge/discharge parameters and duration handling.

## [1.2.0] - 2026-06-12

### Added
- Automatable control entities: work mode selector, charge/discharge power
  limits, SOC limits, and charge/discharge time-slot entities.

## [1.1.0] - 2026-06-10

### Added
- Initial fork of the original integration with read-only battery, grid, PV, and
  load sensors and the custom Lovelace card.

[Unreleased]: https://github.com/upton68/hanchu-ess-ha/compare/v2.10.0...HEAD
[2.10.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.9.0...v2.10.0
[2.9.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.8.0...v2.9.0
[2.8.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.3.1...v2.4.0
[2.3.1]: https://github.com/upton68/hanchu-ess-ha/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.2.2...v2.3.0
[2.2.2]: https://github.com/upton68/hanchu-ess-ha/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/upton68/hanchu-ess-ha/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.6...v2.1.0
[2.0.6]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.5...v2.0.6
[2.0.5]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.4...v2.0.5
[2.0.4]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.3...v2.0.4
[2.0.3]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.2...v2.0.3
[2.0.2]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/upton68/hanchu-ess-ha/compare/v1.4.1...v2.0.0
[1.4.1]: https://github.com/upton68/hanchu-ess-ha/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/upton68/hanchu-ess-ha/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.12...v1.3.0
[1.2.12]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.11...v1.2.12
[1.2.11]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.10...v1.2.11
[1.2.10]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.9...v1.2.10
[1.2.9]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.8...v1.2.9
[1.2.8]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.7...v1.2.8
[1.2.7]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.6...v1.2.7
[1.2.6]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.0...v1.2.3
[1.2.0]: https://github.com/upton68/hanchu-ess-ha/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/upton68/hanchu-ess-ha/releases/tag/v1.1.0
