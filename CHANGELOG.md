# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Entries up to and including 1.2.9 are summarised from the git history and tags;
later versions are tracked here going forward.

## [Unreleased]

### Added
- `README.md` updates,  `CONTRIBUTING.md`, `CHANGELOG.md`, GitHub issue/PR templates, and a
  Dependabot config (GitHub Actions + pip).
- Publish content is in a zipped archive when releases are published on GitHub

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

[Unreleased]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.9...HEAD
[1.2.9]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.8...v1.2.9
[1.2.8]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.7...v1.2.8
[1.2.7]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.6...v1.2.7
[1.2.6]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/upton68/hanchu-ess-ha/compare/v1.2.0...v1.2.3
[1.2.0]: https://github.com/upton68/hanchu-ess-ha/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/upton68/hanchu-ess-ha/releases/tag/v1.1.0
