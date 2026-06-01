#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# OpenJobs SDK Release Script
#
# Cuts a new version of every OpenJobs API access surface:
# @openjobs/sdk (npm), openjobs-py (PyPI), @openjobs/cli (npm),
# and the LangChain/CrewAI/OpenAI Agents toolkits.
#
# ▶ Recommended path — release from CI (tag-driven):
#     git tag sdk-v1.0.1
#     git push origin sdk-v1.0.1
#   …or run the "Release SDKs" workflow from the GitHub Actions UI
#   ("workflow_dispatch") and pick a version + target. The workflow
#   at `.github/workflows/release-sdks.yml` invokes this exact script
#   with NPM_TOKEN / PYPI_API_TOKEN from repository secrets, so the
#   published artifact is provably built from a known commit and
#   anyone with merge rights can cut a release. The workflow also
#   pre-checks that the version isn't already on npm / PyPI and
#   fails loudly instead of silently no-op'ing.
#
# ▶ Fallback — run locally from a developer's machine:
#
# Usage:
#   ./packages/release.sh <new-version> [--target all|both|ts|py|cli|integrations|langchain-py|crewai-py|openai-agents-py|langchain-ts] [--dry-run] [--skip-changelog-check]
#   ./packages/release.sh --bump patch|minor|major [--target all|...] [--yes] [--dry-run]
#
# Examples:
#   ./packages/release.sh 1.0.1
#   ./packages/release.sh 1.1.0 --target ts
#   ./packages/release.sh 0.1.0 --target cli
#   ./packages/release.sh 1.0.2 --dry-run
#   ./packages/release.sh --bump patch --target all --yes
#
# Before you run this:
#   ⚠️  Add a `## [<new-version>] — YYYY-MM-DD` entry to the matching
#       per-package CHANGELOG.md for every targeted package. The script
#       will refuse to publish without one — users upgrading from N-1 → N
#       rely on this to tell what shipped, what broke, and how to migrate.
#
# Requirements:
#   - npm (>= 9), logged in via `npm login` OR NPM_TOKEN env var
#   - python3 + `pip install build twine`, with PYPI_API_TOKEN env var
#     (or ~/.pypirc configured)
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS_DIR="$SCRIPT_DIR/sdk-js"
PY_DIR="$SCRIPT_DIR/sdk-python"
CLI_DIR="$SCRIPT_DIR/cli"
LANGCHAIN_PY_DIR="$SCRIPT_DIR/openjobs-langchain"
CREWAI_PY_DIR="$SCRIPT_DIR/openjobs-crewai"
OPENAI_AGENTS_PY_DIR="$SCRIPT_DIR/openjobs-openai"
LANGCHAIN_TS_DIR="$SCRIPT_DIR/langchain-js"
# Path to the scaffolder library that emits package.json /
# requirements.txt for newly-created agents. We bump its pinned SDK
# versions in the same release commit so brand-new agents pick up
# the just-released, smoke-tested version (and so a future regressed
# minor/patch can't silently break them — see Task #85).
SCAFFOLDER_LIB="$SCRIPT_DIR/../scripts/create-openjobs-agent/lib.js"

# Bump one of the pinned-SDK constants (SDK_VERSION_TS / SDK_VERSION_PY)
# in the scaffolder library to $VERSION. No-op (with a warning) if the
# scaffolder isn't present — keeps the SDK release usable in repo
# layouts where the scaffolder lives elsewhere.
bump_scaffolder_pin() {
  local const_name="$1"
  if [[ ! -f "$SCAFFOLDER_LIB" ]]; then
    echo "  ⚠️  scaffolder lib not found at $SCAFFOLDER_LIB — skipping pin bump for $const_name"
    return 0
  fi
  if ! grep -qE "^const ${const_name} = \"[^\"]+\";" "$SCAFFOLDER_LIB"; then
    echo "❌ $const_name not found in $SCAFFOLDER_LIB — refusing to publish without bumping the scaffolder pin."
    echo "   Add 'const ${const_name} = \"<version>\";' near the top of the file."
    exit 1
  fi
  sed -i.bak -E "s|^const ${const_name} = \"[^\"]+\";|const ${const_name} = \"$VERSION\";|" "$SCAFFOLDER_LIB"
  rm -f "$SCAFFOLDER_LIB.bak"
  echo "  scaffolder pin ($const_name) → $VERSION"
}

# Keep toolkit dependency metadata aligned with the SDK release. Registry
# package metadata is immutable once published, so a stale `<3` requirement on
# a v3 toolkit cannot be corrected in-place after upload.
bump_pyproject_dependency() {
  local file="$1"
  local package="$2"
  local range="$3"
  if [[ ! -f "$file" ]]; then
    echo "❌ Cannot update dependency: $file does not exist."
    exit 1
  fi
  if ! grep -q "\"${package}[<>=]" "$file"; then
    echo "❌ ${package} dependency not found in $file — refusing to publish stale metadata."
    exit 1
  fi
  sed -i.bak -E "s|\"${package}[^\"]*\"|\"${package}${range}\"|" "$file"
  rm -f "$file.bak"
  echo "  ${file#$SCRIPT_DIR/}: ${package}${range}"
}

bump_langchain_ts_sdk_peer() {
  local file="$LANGCHAIN_TS_DIR/package.json"
  local lock="$LANGCHAIN_TS_DIR/package-lock.json"
  node - "$file" "$lock" "$NPM_ALIGNED_RANGE" <<'NODE'
const fs = require("fs");
const [pkgPath, lockPath, range] = process.argv.slice(2);
const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
pkg.peerDependencies = pkg.peerDependencies || {};
pkg.peerDependencies["@openjobs/sdk"] = range;
fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + "\n");
if (fs.existsSync(lockPath)) {
  const lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));
  if (lock.packages && lock.packages[""] && lock.packages[""].peerDependencies) {
    lock.packages[""].peerDependencies["@openjobs/sdk"] = range;
  }
  fs.writeFileSync(lockPath, JSON.stringify(lock, null, 2) + "\n");
}
NODE
  echo "  @openjobs/langchain peer @openjobs/sdk → $NPM_ALIGNED_RANGE"
}

VERSION=""
TARGET="both"
DRY_RUN=0
SKIP_CHANGELOG_CHECK=0
BUMP=""
YES=0

if [[ $# -eq 0 || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  sed -n '4,46p' "$0"
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --skip-changelog-check) SKIP_CHANGELOG_CHECK=1; shift ;;
    --bump) BUMP="$2"; shift 2 ;;
    --yes|-y) YES=1; shift ;;
    *)
      if [[ -z "$VERSION" ]]; then
        VERSION="$1"
        shift
      else
        echo "Unknown argument: $1"
        exit 1
      fi
      ;;
  esac
done

VALID_TARGETS="both ts py cli all integrations langchain-py crewai-py openai-agents-py langchain-ts"
if [[ " $VALID_TARGETS " != *" $TARGET "* ]]; then
  echo "❌ --target must be one of: $VALID_TARGETS"
  exit 1
fi

if [[ -n "$VERSION" && -n "$BUMP" ]]; then
  echo "❌ Provide either an explicit version or --bump, not both."
  exit 1
fi

if [[ -n "$BUMP" && "$BUMP" != "patch" && "$BUMP" != "minor" && "$BUMP" != "major" ]]; then
  echo "❌ --bump must be one of: patch, minor, major"
  exit 1
fi

read_npm_version() {
  node -e "const fs=require('fs'); console.log(JSON.parse(fs.readFileSync(process.argv[1], 'utf8')).version)" "$1"
}

read_pyproject_version() {
  sed -nE 's/^version = "([^"]+)"/\1/p' "$1" | head -1
}

target_versions() {
  case "$TARGET" in
    both)
      read_npm_version "$TS_DIR/package.json"
      read_pyproject_version "$PY_DIR/pyproject.toml"
      ;;
    all)
      read_npm_version "$TS_DIR/package.json"
      read_pyproject_version "$PY_DIR/pyproject.toml"
      read_npm_version "$CLI_DIR/package.json"
      read_pyproject_version "$LANGCHAIN_PY_DIR/pyproject.toml"
      read_pyproject_version "$CREWAI_PY_DIR/pyproject.toml"
      read_pyproject_version "$OPENAI_AGENTS_PY_DIR/pyproject.toml"
      read_npm_version "$LANGCHAIN_TS_DIR/package.json"
      ;;
    ts) read_npm_version "$TS_DIR/package.json" ;;
    py) read_pyproject_version "$PY_DIR/pyproject.toml" ;;
    cli) read_npm_version "$CLI_DIR/package.json" ;;
    integrations)
      read_pyproject_version "$LANGCHAIN_PY_DIR/pyproject.toml"
      read_pyproject_version "$CREWAI_PY_DIR/pyproject.toml"
      read_pyproject_version "$OPENAI_AGENTS_PY_DIR/pyproject.toml"
      read_npm_version "$LANGCHAIN_TS_DIR/package.json"
      ;;
    langchain-py) read_pyproject_version "$LANGCHAIN_PY_DIR/pyproject.toml" ;;
    crewai-py) read_pyproject_version "$CREWAI_PY_DIR/pyproject.toml" ;;
    openai-agents-py) read_pyproject_version "$OPENAI_AGENTS_PY_DIR/pyproject.toml" ;;
    langchain-ts) read_npm_version "$LANGCHAIN_TS_DIR/package.json" ;;
  esac
}

compute_bumped_version() {
  node - "$BUMP" "$@" <<'NODE'
const bump = process.argv[2];
const versions = process.argv.slice(3);
function parse(v) {
  const match = /^(\d+)\.(\d+)\.(\d+)$/.exec(v);
  if (!match) throw new Error(`--bump only supports stable semver versions. Found: ${v}`);
  return match.slice(1).map(Number);
}
let max = [0, 0, 0];
for (const version of versions) {
  const parts = parse(version);
  if (
    parts[0] > max[0] ||
    (parts[0] === max[0] && parts[1] > max[1]) ||
    (parts[0] === max[0] && parts[1] === max[1] && parts[2] > max[2])
  ) {
    max = parts;
  }
}
if (bump === "major") max = [max[0] + 1, 0, 0];
if (bump === "minor") max = [max[0], max[1] + 1, 0];
if (bump === "patch") max = [max[0], max[1], max[2] + 1];
console.log(max.join("."));
NODE
}

if [[ -n "$BUMP" ]]; then
  mapfile -t CURRENT_TARGET_VERSIONS < <(target_versions)
  VERSION="$(compute_bumped_version "${CURRENT_TARGET_VERSIONS[@]}")"
  echo "Computed --bump $BUMP for target '$TARGET': ${CURRENT_TARGET_VERSIONS[*]} → $VERSION"
  if [[ $YES -ne 1 && $DRY_RUN -ne 1 ]]; then
    read -r -p "Proceed with release $VERSION for target '$TARGET'? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
      echo "Aborted."
      exit 1
    fi
  fi
fi

if [[ -z "$VERSION" ]]; then
  echo "❌ Provide a semver version or --bump patch|minor|major."
  exit 1
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?$ ]]; then
  echo "❌ Version must be semver (e.g. 1.2.3 or 1.2.3-beta.1). Got: $VERSION"
  exit 1
fi

NEXT_MAJOR="$(node -e "const m=/^(\\d+)\\./.exec(process.argv[1]); if (!m) process.exit(1); console.log(Number(m[1]) + 1)" "$VERSION")"
PY_ALIGNED_RANGE=">=${VERSION},<${NEXT_MAJOR}.0.0"
NPM_ALIGNED_RANGE=">=${VERSION} <${NEXT_MAJOR}.0.0"

echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│           OpenJobs SDK Release                  │"
echo "└─────────────────────────────────────────────────┘"
echo "  Version: $VERSION"
echo "  Target:  $TARGET"
echo "  Dry run: $([[ $DRY_RUN -eq 1 ]] && echo yes || echo no)"
echo ""

# ── Changelog reminder ───────────────────────────────────────
# Every published version must have a corresponding entry in the
# per-package CHANGELOG.md so users upgrading from N-1 → N can tell
# what shipped, what broke, and how to migrate. We check before doing
# any of the slow build/publish work so the fix loop is fast.
#
# Bypass with --skip-changelog-check (e.g. emergency hotfix). Dry-runs
# only warn — they're meant to preview a release and a missing entry
# is exactly what you'd want a dry-run to surface.
check_changelog() {
  local label="$1"
  local file="$2"
  if [[ ! -f "$file" ]]; then
    echo "❌ Changelog reminder: $label — $file does not exist."
    echo "   Create it (see the other SDK's CHANGELOG.md for the format)."
    return 1
  fi
  # Match either '## 1.2.3' or '## [1.2.3]' headings.
  if ! grep -qE "^## (\[)?${VERSION//./\\.}(\])?( |$)" "$file"; then
    echo "❌ Changelog reminder: $label — no entry for $VERSION in $file."
    echo "   Add a '## [$VERSION] — YYYY-MM-DD' section describing what"
    echo "   changed before publishing. Users on the previous version"
    echo "   need this to know whether the upgrade is safe."
    echo "   Bypass (not recommended): re-run with --skip-changelog-check."
    return 1
  fi
  echo "  ✅ $label CHANGELOG.md has a $VERSION entry."
  return 0
}

if [[ $SKIP_CHANGELOG_CHECK -eq 1 ]]; then
  echo "⚠️  --skip-changelog-check set — not verifying CHANGELOG entries."
else
  echo "─── Changelog check ────────────────────────────"
  changelog_ok=1
  if [[ "$TARGET" == "both" || "$TARGET" == "ts" || "$TARGET" == "all" ]]; then
    check_changelog "@openjobs/sdk"  "$TS_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "both" || "$TARGET" == "py" || "$TARGET" == "all" ]]; then
    check_changelog "openjobs-py"    "$PY_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "cli" || "$TARGET" == "all" ]]; then
    check_changelog "@openjobs/cli"  "$CLI_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "langchain-py" || "$TARGET" == "integrations" || "$TARGET" == "all" ]]; then
    check_changelog "openjobs-langchain" "$LANGCHAIN_PY_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "crewai-py" || "$TARGET" == "integrations" || "$TARGET" == "all" ]]; then
    check_changelog "openjobs-crewai" "$CREWAI_PY_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "openai-agents-py" || "$TARGET" == "integrations" || "$TARGET" == "all" ]]; then
    check_changelog "openjobs-openai" "$OPENAI_AGENTS_PY_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ "$TARGET" == "langchain-ts" || "$TARGET" == "integrations" || "$TARGET" == "all" ]]; then
    check_changelog "@openjobs/langchain" "$LANGCHAIN_TS_DIR/CHANGELOG.md" || changelog_ok=0
  fi
  if [[ $changelog_ok -eq 0 ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "⚠️  Continuing dry-run despite missing changelog entry."
    else
      echo ""
      echo "Refusing to publish without a changelog entry."
      echo "Add the entry, commit, and re-run."
      exit 1
    fi
  fi
  echo ""
fi

# ── TypeScript / npm ──────────────────────────────────────────
release_ts() {
  echo "─── @openjobs/sdk → npm ────────────────────────"
  cd "$TS_DIR"

  # Bump version in package.json (no git tag — platform-managed VCS).
  node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    pkg.version = '$VERSION';
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
    console.log('  package.json → ' + pkg.version);
  "
  # Keep the User-Agent header in sync with the published version.
  sed -i.bak -E "s|openjobs-sdk-ts/[0-9]+\.[0-9]+\.[0-9]+([-A-Za-z0-9.]*)|openjobs-sdk-ts/$VERSION|g" src/index.ts
  rm -f src/index.ts.bak

  # Roll the create-openjobs-agent scaffolder pin forward to this
  # release in the same commit. See SCAFFOLDER_LIB above and Task #85.
  bump_scaffolder_pin "SDK_VERSION_TS"

  echo "  Installing devDependencies (typedoc)..."
  npm install --silent >/dev/null 2>&1 || true

  echo "  Building..."
  npm run build >/dev/null

  echo "  Generating API reference (typedoc)..."
  if npm run docs >/dev/null 2>&1; then
    echo "  ✅ docs/ → ready to host at https://openjobs.bot/sdks/reference/typescript"
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  ⚠️  typedoc failed — continuing (dry-run)"
    else
      echo "❌ typedoc failed — refusing to publish without API reference."
      echo "   Re-run after fixing 'npm run docs', or use --dry-run to preview."
      exit 1
    fi
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] npm publish --access public"
    npm pack --dry-run 2>&1 | tail -20
  else
    if [[ -n "${NPM_TOKEN:-}" ]]; then
      echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > "$HOME/.npmrc"
    fi
    npm publish --access public
    echo "  ✅ Published @openjobs/sdk@$VERSION"
  fi
  cd - >/dev/null
}

# ── Python / PyPI ─────────────────────────────────────────────
release_py() {
  echo "─── openjobs-py → PyPI ─────────────────────────"
  cd "$PY_DIR"

  # Bump version in pyproject.toml + __init__.py.
  sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"$VERSION\"/" pyproject.toml
  rm -f pyproject.toml.bak
  sed -i.bak -E "s/^__version__ = \"[^\"]+\"/__version__ = \"$VERSION\"/" openjobs/__init__.py
  rm -f openjobs/__init__.py.bak
  # Keep the User-Agent header in sync with the published version.
  sed -i.bak -E "s|openjobs-sdk-python/[0-9]+\.[0-9]+\.[0-9]+([-A-Za-z0-9.]*)|openjobs-sdk-python/$VERSION|g" openjobs/client.py
  rm -f openjobs/client.py.bak
  echo "  pyproject.toml + __init__.py + client.py UA → $VERSION"

  # Roll the create-openjobs-agent scaffolder pin forward to this
  # release in the same commit. See SCAFFOLDER_LIB above and Task #85.
  bump_scaffolder_pin "SDK_VERSION_PY"

  PY="$(command -v python3 || command -v python || true)"
  if [[ -z "$PY" ]]; then
    echo "❌ python3 not found in PATH"
    exit 1
  fi

  echo "  Building sdist + wheel..."
  rm -rf dist build *.egg-info
  # Make sure `build` and `twine` are importable. Only invoke pip if they
  # aren't already there — this keeps the script working both on clean
  # machines (pip install succeeds) and on PEP 668 / externally-managed
  # interpreters like Replit/Nix (where pip install would fail but the
  # tools are already pre-installed via `uv tool install` or similar).
  if ! "$PY" -c 'import build, twine' >/dev/null 2>&1; then
    if ! "$PY" -m pip install --quiet --upgrade build twine 2>/dev/null; then
      if ! "$PY" -m pip install --quiet --upgrade --user build twine 2>/dev/null; then
        echo "❌ 'build' and 'twine' are required but pip install failed."
        echo "   Install them once with one of:"
        echo "     pip install --user build twine"
        echo "     uv tool install build && uv tool install twine"
        echo "     pipx install build && pipx install twine"
        exit 1
      fi
    fi
  fi
  # Strip Nix/Replit "user-site" env vars so the isolated build venv that
  # `python -m build` creates can run pip without falling over with
  # `Can not perform a '--user' install. User site-packages are not visible
  # in this virtualenv.` On a vanilla machine these vars are unset and this
  # is a harmless no-op.
  #
  # PIP_CONFIG_FILE is also unset because Nix's global pip.conf sets
  # `user = yes`, which the fresh isolated build venv created by
  # `python -m build` would otherwise inherit. The `sitecustomize.py`
  # shipped by Nix only unsets it for $REPL_HOME/.pythonlibs venvs, not
  # for /tmp/build-env-* venvs.
  env -u PIP_USER -u PYTHONUSERBASE -u POETRY_USE_USER_SITE -u PIP_CONFIG_FILE \
    "$PY" -m build >/dev/null

  echo "  Generating API reference (pdoc)..."
  pdoc_ok=0
  if "$PY" -c 'import pdoc' >/dev/null 2>&1 \
     || "$PY" -m pip install --quiet --upgrade pdoc 2>/dev/null \
     || "$PY" -m pip install --quiet --upgrade --user pdoc 2>/dev/null; then
    if "$PY" -m pdoc -o docs openjobs >/dev/null 2>&1; then
      echo "  ✅ docs/ → ready to host at https://openjobs.bot/sdks/reference/python"
      pdoc_ok=1
    fi
  fi
  if [[ $pdoc_ok -eq 0 ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  ⚠️  pdoc failed — continuing (dry-run)"
    else
      echo "❌ pdoc failed — refusing to publish without API reference."
      echo "   Install with 'pip install pdoc' (or 'pip install -e .[docs]') then retry,"
      echo "   or use --dry-run to preview."
      exit 1
    fi
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] twine upload dist/*"
    "$PY" -m twine check dist/*
    ls -1 dist/
  else
    if [[ -n "${PYPI_API_TOKEN:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
    else
      "$PY" -m twine upload dist/*
    fi
    echo "  ✅ Published openjobs-py==$VERSION"
  fi
  cd - >/dev/null
}

# ── CLI / npm (@openjobs/cli) ────────────────────────────────
release_cli() {
  echo "─── @openjobs/cli → npm ────────────────────────"
  cd "$CLI_DIR"

  # Bump version in package.json (no git tag — platform-managed VCS).
  node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    pkg.version = '$VERSION';
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
    console.log('  package.json → ' + pkg.version);
  "
  # Keep the User-Agent header in sync with the published version.
  sed -i.bak -E "s|openjobs-cli/[0-9]+\.[0-9]+\.[0-9]+([-A-Za-z0-9.]*)|openjobs-cli/$VERSION|g" src/index.ts
  rm -f src/index.ts.bak
  sed -i.bak -E "s|export const CLI_VERSION = \"[^\"]+\"|export const CLI_VERSION = \"$VERSION\"|g" src/index.ts
  rm -f src/index.ts.bak

  # Bump the `latest` field served by GET /api/cli/version so
  # `openjobs upgrade` and `doctor` actually see the new release.
  # Without this, the API keeps reporting the old version as latest
  # and every freshly-installed CLI thinks it's already current.
  # No-op (with a warning) if the file isn't present in the repo
  # layout — keeps the script usable for downstream forks.
  ROUTES_FILE="$SCRIPT_DIR/../server/routes.ts"
  if [[ -f "$ROUTES_FILE" ]]; then
    if grep -qE '^[[:space:]]*latest:[[:space:]]*"[^"]+",' "$ROUTES_FILE"; then
      # Match only the FIRST `latest: "..."` line (the CLI_RELEASE block).
      # macOS sed needs the empty `''` arg after -i; we use -i.bak for portability.
      sed -i.bak -E "0,/^([[:space:]]*)latest:[[:space:]]*\"[^\"]+\",/ s||\\1latest: \"$VERSION\",|" "$ROUTES_FILE"
      rm -f "$ROUTES_FILE.bak"
      echo "  server/routes.ts CLI_RELEASE.latest → $VERSION"
    else
      echo "  ⚠️  server/routes.ts present but no \`latest: \"…\"\` line found — skipping API bump."
      echo "     Update the CLI_RELEASE.latest field manually before deploying, or"
      echo "     openjobs upgrade will keep advertising the old version."
    fi
  else
    echo "  ⚠️  server/routes.ts not found — skipping CLI_RELEASE.latest bump."
    echo "     If this repo serves /api/cli/version, update it manually before deploying."
  fi

  echo "  Installing dependencies..."
  npm install --silent >/dev/null 2>&1 || true

  echo "  Building..."
  npm run build >/dev/null

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] npm publish --access public"
    npm pack --dry-run 2>&1 | tail -20
  else
    if [[ -n "${NPM_TOKEN:-}" ]]; then
      echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > "$HOME/.npmrc"
    fi
    npm publish --access public
    echo "  ✅ Published @openjobs/cli@$VERSION"
  fi
  cd - >/dev/null
}

# ── Integration: openjobs-langchain (PyPI) ───────────────────
release_langchain_py() {
  echo "─── openjobs-langchain → PyPI ──────────────────"
  cd "$LANGCHAIN_PY_DIR"

  sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"$VERSION\"/" pyproject.toml
  rm -f pyproject.toml.bak
  sed -i.bak -E "s/^__version__ = \"[^\"]+\"/__version__ = \"$VERSION\"/" openjobs_langchain/__init__.py
  rm -f openjobs_langchain/__init__.py.bak
  echo "  pyproject.toml + __init__.py → $VERSION"
  bump_pyproject_dependency "$LANGCHAIN_PY_DIR/pyproject.toml" "openjobs-py" "$PY_ALIGNED_RANGE"

  bump_scaffolder_pin "TOOLKIT_VERSION_LANGCHAIN_PY"

  PY="$(command -v python3 || command -v python || true)"
  [[ -z "$PY" ]] && { echo "❌ python3 not found"; exit 1; }

  echo "  Building sdist + wheel..."
  rm -rf dist build *.egg-info
  if ! "$PY" -c 'import build, twine' >/dev/null 2>&1; then
    "$PY" -m pip install --quiet --upgrade build twine 2>/dev/null \
      || "$PY" -m pip install --quiet --upgrade --user build twine 2>/dev/null \
      || { echo "❌ 'build' and 'twine' required but pip install failed."; exit 1; }
  fi
  env -u PIP_USER -u PYTHONUSERBASE -u POETRY_USE_USER_SITE -u PIP_CONFIG_FILE \
    "$PY" -m build >/dev/null

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] twine upload dist/*"
    "$PY" -m twine check dist/*
    ls -1 dist/
  else
    if [[ -n "${PYPI_API_TOKEN_LANGCHAIN:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN_LANGCHAIN" dist/*
    elif [[ -n "${PYPI_API_TOKEN:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
    else
      "$PY" -m twine upload dist/*
    fi
    echo "  ✅ Published openjobs-langchain==$VERSION"
  fi
  cd - >/dev/null
}

# ── Integration: openjobs-crewai (PyPI) ──────────────────────
release_crewai_py() {
  echo "─── openjobs-crewai → PyPI ─────────────────────"
  cd "$CREWAI_PY_DIR"

  sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"$VERSION\"/" pyproject.toml
  rm -f pyproject.toml.bak
  sed -i.bak -E "s/^__version__ = \"[^\"]+\"/__version__ = \"$VERSION\"/" openjobs_crewai/__init__.py
  rm -f openjobs_crewai/__init__.py.bak
  echo "  pyproject.toml + __init__.py → $VERSION"
  bump_pyproject_dependency "$CREWAI_PY_DIR/pyproject.toml" "openjobs-py" "$PY_ALIGNED_RANGE"
  bump_pyproject_dependency "$CREWAI_PY_DIR/pyproject.toml" "openjobs-langchain" "$PY_ALIGNED_RANGE"

  bump_scaffolder_pin "TOOLKIT_VERSION_CREWAI_PY"

  PY="$(command -v python3 || command -v python || true)"
  [[ -z "$PY" ]] && { echo "❌ python3 not found"; exit 1; }

  echo "  Building sdist + wheel..."
  rm -rf dist build *.egg-info
  if ! "$PY" -c 'import build, twine' >/dev/null 2>&1; then
    "$PY" -m pip install --quiet --upgrade build twine 2>/dev/null \
      || "$PY" -m pip install --quiet --upgrade --user build twine 2>/dev/null \
      || { echo "❌ 'build' and 'twine' required but pip install failed."; exit 1; }
  fi
  env -u PIP_USER -u PYTHONUSERBASE -u POETRY_USE_USER_SITE -u PIP_CONFIG_FILE \
    "$PY" -m build >/dev/null

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] twine upload dist/*"
    "$PY" -m twine check dist/*
    ls -1 dist/
  else
    if [[ -n "${PYPI_API_TOKEN_CREWAI:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN_CREWAI" dist/*
    elif [[ -n "${PYPI_API_TOKEN:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
    else
      "$PY" -m twine upload dist/*
    fi
    echo "  ✅ Published openjobs-crewai==$VERSION"
  fi
  cd - >/dev/null
}

# ── Integration: openjobs-openai (PyPI) ──────────────────────
release_openai_agents_py() {
  echo "─── openjobs-openai → PyPI ─────────────────────"
  cd "$OPENAI_AGENTS_PY_DIR"

  sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"$VERSION\"/" pyproject.toml
  rm -f pyproject.toml.bak
  sed -i.bak -E "s/^__version__ = \"[^\"]+\"/__version__ = \"$VERSION\"/" openjobs_openai/__init__.py
  rm -f openjobs_openai/__init__.py.bak
  echo "  pyproject.toml + __init__.py → $VERSION"
  bump_pyproject_dependency "$OPENAI_AGENTS_PY_DIR/pyproject.toml" "openjobs-py" "$PY_ALIGNED_RANGE"
  bump_pyproject_dependency "$OPENAI_AGENTS_PY_DIR/pyproject.toml" "openjobs-langchain" "$PY_ALIGNED_RANGE"

  bump_scaffolder_pin "TOOLKIT_VERSION_OPENAI_AGENTS_PY"

  PY="$(command -v python3 || command -v python || true)"
  [[ -z "$PY" ]] && { echo "❌ python3 not found"; exit 1; }

  echo "  Building sdist + wheel..."
  rm -rf dist build *.egg-info
  if ! "$PY" -c 'import build, twine' >/dev/null 2>&1; then
    "$PY" -m pip install --quiet --upgrade build twine 2>/dev/null \
      || "$PY" -m pip install --quiet --upgrade --user build twine 2>/dev/null \
      || { echo "❌ 'build' and 'twine' required but pip install failed."; exit 1; }
  fi
  env -u PIP_USER -u PYTHONUSERBASE -u POETRY_USE_USER_SITE -u PIP_CONFIG_FILE \
    "$PY" -m build >/dev/null

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] twine upload dist/*"
    "$PY" -m twine check dist/*
    ls -1 dist/
  else
    if [[ -n "${PYPI_API_TOKEN_OPENAI_AGENTS:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN_OPENAI_AGENTS" dist/*
    elif [[ -n "${PYPI_API_TOKEN:-}" ]]; then
      "$PY" -m twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
    else
      "$PY" -m twine upload dist/*
    fi
    echo "  ✅ Published openjobs-openai==$VERSION"
  fi
  cd - >/dev/null
}

# ── Integration: @openjobs/langchain (npm) ───────────────────
release_langchain_ts() {
  echo "─── @openjobs/langchain → npm ──────────────────"
  cd "$LANGCHAIN_TS_DIR"

  node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    pkg.version = '$VERSION';
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
    console.log('  package.json → ' + pkg.version);
  "
  bump_langchain_ts_sdk_peer

  bump_scaffolder_pin "TOOLKIT_VERSION_LANGCHAIN_TS"

  echo "  Installing devDependencies..."
  npm install --silent >/dev/null 2>&1 || true

  echo "  Building..."
  npm run build >/dev/null

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  [dry-run] npm publish --access public"
    npm pack --dry-run 2>&1 | tail -20
  else
    if [[ -n "${NPM_TOKEN:-}" ]]; then
      echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > "$HOME/.npmrc"
    fi
    npm publish --access public
    echo "  ✅ Published @openjobs/langchain@$VERSION"
  fi
  cd - >/dev/null
}

case "$TARGET" in
  both) release_ts; echo ""; release_py ;;
  all)
    release_ts; echo ""
    release_py; echo ""
    release_cli; echo ""
    release_langchain_py; echo ""
    release_crewai_py; echo ""
    release_openai_agents_py; echo ""
    release_langchain_ts
    ;;
  ts)   release_ts ;;
  py)   release_py ;;
  cli)  release_cli ;;
  langchain-py)      release_langchain_py ;;
  crewai-py)         release_crewai_py ;;
  openai-agents-py)  release_openai_agents_py ;;
  langchain-ts)      release_langchain_ts ;;
  integrations)
    release_langchain_py; echo ""
    release_crewai_py; echo ""
    release_openai_agents_py; echo ""
    release_langchain_ts
    ;;
esac

echo ""
echo "═════════════════════════════════════════════════════"
echo "  Release $VERSION complete."
[[ "$TARGET" == "both"         || "$TARGET" == "ts"  || "$TARGET" == "all" ]] && echo "    npm:  https://www.npmjs.com/package/@openjobs/sdk/v/$VERSION"
[[ "$TARGET" == "both"         || "$TARGET" == "py"  || "$TARGET" == "all" ]] && echo "    pypi: https://pypi.org/project/openjobs-py/$VERSION/"
[[ "$TARGET" == "cli"          || "$TARGET" == "all" ]] && echo "    npm:  https://www.npmjs.com/package/@openjobs/cli/v/$VERSION"
[[ "$TARGET" == "langchain-py" || "$TARGET" == "integrations" || "$TARGET" == "all" ]] && echo "    pypi: https://pypi.org/project/openjobs-langchain/$VERSION/"
[[ "$TARGET" == "crewai-py"    || "$TARGET" == "integrations" || "$TARGET" == "all" ]] && echo "    pypi: https://pypi.org/project/openjobs-crewai/$VERSION/"
[[ "$TARGET" == "openai-agents-py" || "$TARGET" == "integrations" || "$TARGET" == "all" ]] && echo "    pypi: https://pypi.org/project/openjobs-openai/$VERSION/"
[[ "$TARGET" == "langchain-ts" || "$TARGET" == "integrations" || "$TARGET" == "all" ]] && echo "    npm:  https://www.npmjs.com/package/@openjobs/langchain/v/$VERSION"
echo ""
