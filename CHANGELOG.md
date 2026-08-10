# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Entries up to and including 1.2.9 are summarised from the git history and tags;
later versions are tracked here going forward.

## [Unreleased]

### Fixed
- **Control sensors now populate automatically on Home Assistant restart.**
  Discharge Power Limit, Charge Power Limit, Max Charge SOC, Min Discharge SOC,
  Grid to Battery Max, and Work Mode previously stayed `unavailable` after a
  restart until the **Read Settings** button was pressed manually. The startup
  values were already being fetched via `iotGet` during setup, but were never
  applied to the (not-yet-registered-at-fetch-time) control entities. They're
  now applied automatically once entity setup completes.

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

[Unreleased]: https://github.com/upton68/hanchu-ess-ha/compare/v2.0.2...HEAD
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
