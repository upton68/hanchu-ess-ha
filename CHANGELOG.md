# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Entries up to and including 1.2.9 are summarised from the git history and tags;
later versions are tracked here going forward.

## [Unreleased]

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

[Unreleased]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.11...HEAD
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
