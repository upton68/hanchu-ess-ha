# Contributing

Thanks for your interest in improving the Hanchuess Home Assistant integration!
This document covers how to get set up, test your changes, and submit them.

## Reporting issues

Please use the GitHub issue templates (Bug report / Feature request). For bugs,
include your Home Assistant version, the integration version, and relevant log
lines. The integration logs under the `[HANCHUESS]` prefix — enable debug logging
to capture them:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.hanchuess: debug
```

A redacted diagnostics download (integration → **Download diagnostics**) is the
most useful attachment — it strips tokens and serials automatically.

## Development setup

Create and activate a virtual environment, then install the test dependencies
for your platform (see [Running the test suite](#running-the-test-suite) below):

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

## Running the test suite

The suite is split into tiers so it can run on both Windows (where the
integration is typically developed) and Linux (CI):

- **Offline tests** — `tests/test_api_mocked.py` (API client, mocked with
  `aioresponses`) and `tests/test_logic.py` (sensor scaling, menu parsing, time
  encode/decode, fast-charge option conversion). No credentials or Home Assistant
  runtime required, so they run on any platform.
- **Config-flow tests** — `tests/test_config_flow.py` use the Home Assistant test
  harness (`pytest-homeassistant-custom-component`). This pulls in HA core, which
  imports Unix-only modules and **cannot run on Windows** — these tests skip
  automatically there and run on Linux/CI.
- **Live integration test** — `tests/test_api_integration.py` hits the real
  Hanchu cloud API and is opt-in: it skips unless `HANCHUESS_ACCOUNT` and
  `HANCHUESS_PASSWORD` are set (see [below](#running-the-live-integration-test)).

### Windows (local development)

Install the cross-platform dependencies and run pytest. The config-flow tests
skip cleanly; the offline tests execute.

```powershell
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

### Linux / CI (full suite)

`requirements-test-ha.txt` adds the HA test harness on top of the cross-platform
deps, so every test — including the config-flow tests — runs.

```bash
pip install -r requirements-test-ha.txt
pytest
```

This is exactly what the GitHub Actions **Tests** workflow
(`.github/workflows/tests.yml`) runs on every push and pull request, so a green
run here should mean a green run in CI.

### Useful pytest invocations

Once the dependencies are installed, you can scope and shape runs:

```bash
pytest -q                                       # quiet, just the summary line
pytest -v                                       # one line per test
pytest -rs                                      # report why tests were skipped
pytest tests/test_logic.py                      # a single file
pytest tests/test_logic.py::test_scale_factor_applied   # a single test
pytest -k "fast_charge"                         # tests whose name matches a keyword
pytest -x                                       # stop at the first failure
pytest --lf                                     # re-run only last-failed tests
pytest -s                                       # show print()/log output
```

On Windows, `pytest -rs` is a quick way to confirm the config-flow tests skipped
for the expected reason rather than erroring.

### Running the live integration test

```bash
export HANCHUESS_ACCOUNT="you@example.com"
export HANCHUESS_PASSWORD="your-password"
export HANCHUESS_SN="YOURSERIAL"          # optional, enables device-specific reads
# export HANCHUESS_ALLOW_WRITE=1          # optional, enables no-op write-path tests
pytest tests/test_api_integration.py
```

On Windows PowerShell, set these with `$env:HANCHUESS_ACCOUNT = "..."` instead of
`export`.

### Where to add tests

Add or update tests alongside code changes:
- Pure logic (scaling, parsing, encode/decode, option conversion) →
  `tests/test_logic.py`.
- Config/options flow behaviour → `tests/test_config_flow.py`.
- API client request/response handling → `tests/test_api_mocked.py`.

## Testing against a live Home Assistant

There is no way to fully exercise the entities without a running HA instance.
Copy `custom_components/hanchuess/` into your HA instance's `custom_components/`
directory and restart HA, then watch the logs for `[HANCHUESS]` entries. The API
base URL can be pointed at a mock server for local testing:

```bash
HANCHUESS_URL=http://your-mock-server
```

## CI checks

Every push and pull request runs three checks that must pass:

- **Tests** (`.github/workflows/tests.yml`) — the pytest suite on Linux.
- **HACS validation** (`.github/workflows/hacs.yml`) — validates `hacs.json`,
  the manifest, and the integration structure.
- **Hassfest** (`.github/workflows/hassfest.yml`) — validates Home Assistant
  integration standards.

## Pull requests

1. Branch from `main`.
2. Keep changes focused; update tests and docs (README / `CHANGELOG.md`) as
   needed.
3. Reference the related issue in the PR description and commit message (e.g.
   `#15 Add diagnostics support`).
4. Add a note under the `## [Unreleased]` heading in `CHANGELOG.md`.
5. Make sure the test suite passes locally before opening the PR.

## Versioning & releases

The integration follows [Semantic Versioning](https://semver.org/). The version
lives in `custom_components/hanchuess/manifest.json`. On release, the
`## [Unreleased]` section of `CHANGELOG.md` is renamed to the new version with a
date, and a matching `vX.Y.Z` git tag is pushed.
