#!/usr/bin/env bash
# Build the openjobs-py API reference site with pdoc.
#
# Usage:
#   ./scripts/build-docs.sh           # writes ./docs/
#   ./scripts/build-docs.sh ../out    # writes anywhere you want
#
# Requires: pip install -e .[docs]   (or `pip install pdoc`)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${1:-$PKG_DIR/docs}"

# Pick the right interpreter — prefer ./.venv if present.
if [[ -x "$PKG_DIR/.venv/bin/python" ]]; then
  PY="$PKG_DIR/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

# Make sure pdoc is importable; install on demand if not.
if ! "$PY" -c 'import pdoc' >/dev/null 2>&1; then
  echo "ℹ️  pdoc not installed — attempting 'pip install pdoc' ..."
  "$PY" -m pip install --quiet --upgrade pdoc \
    || "$PY" -m pip install --quiet --upgrade --user pdoc \
    || { echo "❌ Could not install pdoc. Run: pip install -e .[docs]"; exit 1; }
fi

cd "$PKG_DIR"
echo "📝 Building docs into $OUT_DIR ..."
"$PY" -m pdoc -o "$OUT_DIR" openjobs
echo "✅ Done. Open $OUT_DIR/openjobs.html"
