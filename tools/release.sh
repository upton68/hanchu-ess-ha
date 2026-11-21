#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: release.sh --version X.Y.Z [options]

Automate the release prep flow from CONTRIBUTING.md:
  - bump manifest version
  - optionally update CHANGELOG.md
  - create release commit and vX.Y.Z tag
  - optionally push main + tag
Can be run on Windows using Git Bash.

Options:
  -v, --version X.Y.Z            Required SemVer (no leading v)
      --update-changelog BOOL    true/false (default: false)
      --auto-push BOOL           true/false (default: false)
  -h, --help                     Show this help

Examples:
  bash tools/release.sh --version 1.2.12 --update-changelog true
  bash tools/release.sh --version 1.2.12 --update-changelog true --auto-push true
EOF
}

err() {
  echo "Error: $*" >&2
  exit 1
}

parse_bool() {
  local raw="${1:-}"
  # tr rather than ${raw,,}: macOS ships bash 3.2, which lacks ${var,,}.
  local val
  val="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  case "$val" in
    true|1|yes|y) echo "true" ;;
    false|0|no|n) echo "false" ;;
    *) err "invalid boolean value '$raw' (expected true/false)" ;;
  esac
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || err "'$cmd' not found in PATH"
}

VERSION=""
UPDATE_CHANGELOG="false"
AUTO_PUSH="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--version)
      [[ $# -ge 2 ]] || err "--version requires a value"
      VERSION="$2"
      shift 2
      ;;
    --update-changelog)
      [[ $# -ge 2 ]] || err "--update-changelog requires true/false"
      UPDATE_CHANGELOG="$(parse_bool "$2")"
      shift 2
      ;;
    --auto-push)
      [[ $# -ge 2 ]] || err "--auto-push requires true/false"
      AUTO_PUSH="$(parse_bool "$2")"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      err "unknown argument: $1"
      ;;
  esac
done

[[ -n "$VERSION" ]] || err "--version is required"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || err "--version must be X.Y.Z (no leading v)"

require_cmd git
require_cmd awk
require_cmd sed
require_cmd mktemp
require_cmd date

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST_FILE="$REPO_ROOT/custom_components/hanchuess/manifest.json"
CHANGELOG_FILE="$REPO_ROOT/CHANGELOG.md"
TAG="v${VERSION}"
TODAY="$(date +%F)"

[[ -f "$MANIFEST_FILE" ]] || err "manifest file not found: $MANIFEST_FILE"
[[ -f "$CHANGELOG_FILE" ]] || err "changelog file not found: $CHANGELOG_FILE"

cd "$REPO_ROOT"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[[ "$CURRENT_BRANCH" == "main" ]] || err "releases must be prepared from main (current: $CURRENT_BRANCH)"

git diff --quiet || err "working tree has unstaged changes"
git diff --cached --quiet || err "working tree has staged changes"

git fetch --quiet origin main
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_MAIN_HEAD="$(git rev-parse origin/main)"
[[ "$LOCAL_HEAD" == "$REMOTE_MAIN_HEAD" ]] || err "local main is not exactly origin/main; make sure local main is up to date and has no extra commits before running release.sh"

git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && err "local tag already exists: $TAG"
git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && err "remote tag already exists: $TAG"

CURRENT_MANIFEST_VERSION="$(sed -nE 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$MANIFEST_FILE" | head -n1)"
[[ -n "$CURRENT_MANIFEST_VERSION" ]] || err "failed to read version from manifest.json"
[[ "$CURRENT_MANIFEST_VERSION" != "$VERSION" ]] || err "manifest already has version $VERSION"

manifest_tmp="$(mktemp)"
# Replace only the first "version" key. awk rather than GNU sed's
# "0,/re/" address, which macOS (BSD) sed doesn't support.
awk -v version="$VERSION" '
  !done && /"version"[[:space:]]*:[[:space:]]*"[^"]+"/ {
    sub(/"version"[[:space:]]*:[[:space:]]*"[^"]+"/, "\"version\": \"" version "\"")
    done = 1
  }
  { print }
' "$MANIFEST_FILE" > "$manifest_tmp"
mv "$manifest_tmp" "$MANIFEST_FILE"

if [[ "$UPDATE_CHANGELOG" == "true" ]]; then
  grep -q '^## \[Unreleased\]' "$CHANGELOG_FILE" || err "CHANGELOG.md missing '## [Unreleased]' heading"
  grep -q "^\[Unreleased\]: " "$CHANGELOG_FILE" || err "CHANGELOG.md missing '[Unreleased]:' link reference"
  grep -q "^## \[$VERSION\]" "$CHANGELOG_FILE" && err "CHANGELOG.md already has a section for $VERSION"
  grep -q "^\[$VERSION\]: " "$CHANGELOG_FILE" && err "CHANGELOG.md already has a link for $VERSION"

  unreleased_line="$(grep -E '^\[Unreleased\]: ' "$CHANGELOG_FILE" | head -n1)"
  previous_version="$(printf '%s\n' "$unreleased_line" | sed -nE 's#^\[Unreleased\]: .*/compare/v([0-9]+\.[0-9]+\.[0-9]+)\.\.\.HEAD$#\1#p')"
  compare_base="$(printf '%s\n' "$unreleased_line" | sed -nE 's#^\[Unreleased\]: (.*)/compare/v[0-9]+\.[0-9]+\.[0-9]+\.\.\.HEAD$#\1#p')"
  [[ -n "$previous_version" ]] || err "failed to parse previous version from [Unreleased] link"
  [[ -n "$compare_base" ]] || err "failed to parse compare URL base from [Unreleased] link"

  unreleased_body_tmp="$(mktemp)"
  prefix_tmp="$(mktemp)"
  suffix_tmp="$(mktemp)"
  changelog_tmp="$(mktemp)"
  links_tmp="$(mktemp)"

  awk '/^## \[Unreleased\]/{in_section=1; next} in_section && /^## \[/{exit} in_section{print}' "$CHANGELOG_FILE" > "$unreleased_body_tmp"
  grep -q '[^[:space:]]' "$unreleased_body_tmp" || err "Unreleased section is empty; nothing to move into $VERSION"

  awk '{print} /^## \[Unreleased\]/{exit}' "$CHANGELOG_FILE" > "$prefix_tmp"
  awk '/^## \[Unreleased\]/{in_section=1; next} in_section && /^## \[/{start=1} start{print}' "$CHANGELOG_FILE" > "$suffix_tmp"
  [[ -s "$suffix_tmp" ]] || err "failed to find section after [Unreleased]"

  {
    cat "$prefix_tmp"
    echo
    echo "## [$VERSION] - $TODAY"
    echo
    cat "$unreleased_body_tmp"
    echo
    cat "$suffix_tmp"
  } > "$changelog_tmp"

  sed -E "s#^\[Unreleased\]: .*/compare/v[0-9]+\.[0-9]+\.[0-9]+\.\.\.HEAD\$#[Unreleased]: ${compare_base}/compare/v${VERSION}...HEAD#" "$changelog_tmp" > "$links_tmp"

  awk -v version="$VERSION" -v prev="$previous_version" -v base="$compare_base" '
    {
      print
      if ($0 ~ /^\[Unreleased\]: /) {
        print "[" version "]: " base "/compare/v" prev "...v" version
      }
    }
  ' "$links_tmp" > "$changelog_tmp"

  mv "$changelog_tmp" "$CHANGELOG_FILE"
  rm -f "$unreleased_body_tmp" "$prefix_tmp" "$suffix_tmp" "$links_tmp"
fi

git add "$MANIFEST_FILE"
if [[ "$UPDATE_CHANGELOG" == "true" ]]; then
  git add "$CHANGELOG_FILE"
fi

git commit -m "Release $TAG"
git tag "$TAG"

echo "Created local release commit and tag: $TAG"

if [[ "$AUTO_PUSH" == "true" ]]; then
  git push origin main
  git push origin "$TAG"
  echo "Pushed main and $TAG to origin."
else
  echo "Manual push required:"
  echo "  git push origin main"
  echo "  git push origin $TAG"
fi

echo "Next: verify the Release workflow and GitHub Release asset (hanchuess.zip)."
