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

Note: this is an independent, unofficial fork. Issues with the Hanchu app or cloud API itself (rather than this integration) should be reported to Hanchu directly, not here.

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

### Crypto debug utility

For local AES payload debugging, use the CLI helper in `tools/crypto_tool.py`.
It uses the integration's default key/IV unless you override them.

```bash
py tools/crypto_tool.py encrypt '{"sn":"SN123456","devType":"2"}'
py tools/crypto_tool.py decrypt 'BASE64_CIPHERTEXT'
py tools/crypto_tool.py decrypt --pretty 'BASE64_CIPHERTEXT'
```

You can also pipe JSON or ciphertext through stdin:

```powershell
Get-Content payload.json | py tools/crypto_tool.py encrypt
Get-Content cipher.txt | py tools/crypto_tool.py decrypt --pretty
```

Optional `--key-text` and `--iv-text` overrides are available when you need to
test non-default material.

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

## Submitting brand assets to home-assistant/brands

Home Assistant's brand icons/logos live in a separate repository
([home-assistant/brands](https://github.com/home-assistant/brands)), not in this
one. `custom_components/hanchuess/brand/icon.png` and `logo.png` already exist
here, but they still need to be submitted upstream: open a PR against
`home-assistant/brands` adding them under
`custom_integrations/hanchuess/icon.png` and `custom_integrations/hanchuess/logo.png`,
sourced from this repo's `custom_components/hanchuess/brand/` folder. The
`brands` rule in `quality_scale.yaml` stays `todo` until that PR merges — it's
the only Bronze rule this repo can't complete on its own.

## Pull requests

1. Branch from `main`.
2. Keep changes focused; update tests and docs (README / `CHANGELOG.md`) as
   needed.
3. Reference the related issue in the PR description and commit message (e.g.
   `#15 Add diagnostics support`).
4. Add a note under the `## [Unreleased]` heading in `CHANGELOG.md`.
5. Make sure the test suite passes locally before opening the PR.

## Versioning & releases

The integration follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- **PATCH** (`1.2.6` → `1.2.7`) — bug fixes and internal changes only.
- **MINOR** (`1.2.6` → `1.3.0`) — new, backwards-compatible entities, services,
  or options.
- **MAJOR** (`1.2.6` → `2.0.0`) — breaking changes (renamed/removed entities or
  services, config that requires user action after upgrade).

Releases are **automated**. Pushing a `vX.Y.Z` tag triggers the **Release**
workflow (`.github/workflows/release.yml`), which extracts the matching section
from `CHANGELOG.md`, builds a zip of the integration (`hanchuess.zip`), and
publishes a GitHub Release with that zip attached. HACS then offers the new tag
to users. Maintainers (codeowners) perform releases; the steps below document the
full process.

Releases can only be cut from `main`. The workflow's first step verifies the
tagged commit is contained in `origin/main` (`git merge-base --is-ancestor`) and
**fails before building or publishing anything** if it isn't. A tag pushed on a
feature branch that was never merged to `main` will not produce a release.

`hacs.json` sets `"zip_release": true` and `"filename": "hanchuess.zip"`, so HACS
installs the integration **from this attached zip**, not from the tagged source
tree. The zip is therefore load-bearing: if the Release workflow fails to build
or attach `hanchuess.zip`, HACS cannot install that version even though the tag
exists. The `filename` in `hacs.json` must stay in sync with the asset name the
workflow uploads (`files: hanchuess.zip`).

### Before you start

Releases are cut from `main`, so make sure it is up to date and green:

- The **Tests**, **HACS validation**, and **Hassfest** workflows are passing on
  `main` (see [CI checks](#ci-checks)).
- Every change you intend to ship has a `CHANGELOG.md` entry under
  `## [Unreleased]`.

### 1. Choose the version

Pick the next `X.Y.Z` per the SemVer rules above, based on what sits under
`## [Unreleased]` in `CHANGELOG.md`.

### 2. Bump the manifest version

Edit `custom_components/hanchuess/manifest.json` and set `"version"` to the new
`X.Y.Z` (no `v` prefix). This is the version Home Assistant and HACS display, so
it **must** match the tag you push in step 5.

### 3. Update the changelog

In `CHANGELOG.md`:

1. Add a heading between `## [Unreleased]` and the last release heading; 
   `## [X.Y.Z] - YYYY-MM-DD` (today's date, ISO format).
2. Move any changes from the `## [Unreleased]` section to your new heading,
   keeping the `## [Unreleased]` section intact.
3. Update the link reference definitions at the bottom of the file:
   - Point the `[Unreleased]` link at `compare/vX.Y.Z...HEAD`.
   - Add a `[X.Y.Z]` link, e.g.
     `compare/v<previous>...vX.Y.Z`.

The Release workflow reads the body between `## [X.Y.Z]` and the next `## [`
heading and uses it as the GitHub Release notes. It **fails the release** if no
section matches the tagged version, so the heading must read exactly
`## [X.Y.Z]` — no `v` prefix, matching the tag with the `v` stripped.

### 4. Commit the bump

Open a PR (or push to `main` if you have rights) with the manifest and changelog
changes, using a clear message, e.g.:

```bash
git commit -m "Release v1.2.7"
```

Wait for CI to go green and merge to `main` before tagging.

### 5. Tag and push

Tag the merge commit on `main` and push the tag — this is what starts the
release:

```bash
git checkout main && git pull
git tag v1.2.7          # matches manifest.json "version", with a leading v
git push origin v1.2.7
```

### 6. Verify the release

- Watch the **Release** workflow run under the repo's **Actions** tab; it should
  finish green.
- Check the **Releases** page: a `Hanchu ESS X.Y.Z` release should exist, with
  the changelog section as its notes and a `hanchuess.zip` asset attached. HACS
  installs from this asset, so confirm it is present and non-empty.
- In a Home Assistant instance with HACS, the integration should offer the new
  version as an available update and install it from the attached zip.

If the workflow fails, the most common causes are a `CHANGELOG.md` heading that
doesn't match the tag (step 3), a manifest/tag version mismatch (steps 2 and 5),
or a tag placed on a commit that isn't on `main` (step 5 — the workflow rejects
it). Fix the cause on `main`, delete and re-push the tag
(`git push origin :v1.2.7` then re-tag), and the workflow will run again.


## Quick deploy to test Home Assistant (Git Bash)

For repeat local testing, use:

```bash
bash tools/deploy-ha.sh
```

Defaults match a typical local setup (`root@192.168.0.110`, uploading
`custom_components/hanchuess` to `homeassistant/custom_components/hanchuess`).
Override with flags when needed:

```bash
bash tools/deploy-ha.sh \
  --host 192.168.0.110 \
  --user root \
  --local-dir "/c/Projects/hanchu-ess-ha/custom_components/hanchuess" \
  --remote-dir "homeassistant/custom_components/hanchuess"
```

Each deployment run first calls `tools/backup-ha.sh`, which downloads the current
remote integration directory to a timestamped local backup folder under
`.ha-deploy-backups/` at the repo root. Override backup location with
`--backup-root`.

If you want to skip that pre-deploy backup for a one-off deploy, pass
`--skip-backup` to `tools/deploy-ha.sh`.

Authentication prompts normally at runtime. For non-interactive runs, set
`HANCHUESS_SFTP_PASSWORD` or pass `--password` (requires `sshpass`).

To run backup manually:

```bash
bash tools/backup-ha.sh \
  --host 192.168.0.110 \
  --user root
```

To restore from a backup:

```bash
bash tools/restore-ha.sh \
  --host 192.168.0.110 \
  --user root \
  --restore-from "/c/Projects/hanchu-ess-ha/.ha-deploy-backups/20260703-230000"
```

## Automated release script for maintainers with permission only (Git Bash, macOS or Linux)

You can run the release flow with:

```bash
bash tools/release.sh --version X.Y.Z --update-changelog true
```

This script automates steps 2–5 above:

- bumps `custom_components/hanchuess/manifest.json` to `X.Y.Z`,
- optionally updates `CHANGELOG.md` when `--update-changelog true`,
- creates `Release vX.Y.Z` commit and local `vX.Y.Z` tag.

By default it **does not push** to remote; it prints explicit push commands so
you can confirm before triggering the release workflow:

```bash
git push origin main
git push origin vX.Y.Z
```

To push automatically from the script, pass:

```bash
bash tools/release.sh --version X.Y.Z --update-changelog true --auto-push true
```
