#!/usr/bin/env bash
set -euo pipefail

# bootstrap-env.sh - Ensure Python env tools and project deps are installed
# - Installs uv if missing (policy-compliant via pip; no curl)
# - Ensures requested Python version is available via uv
# - Syncs Python dependencies (dev)
# - Installs external tools used by Lintro
# - Ensures ~/.local/bin is on PATH for the current workflow

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Bootstraps CI environment with Python, uv, and external tools.

Usage:
  scripts/utils/bootstrap-env.sh [--help|-h] [PYTHON_VERSION]

Actions:
  - Install uv if missing and add ~/.local/bin to PATH
  - Ensure specified Python via 'uv python install'
  - uv sync --dev --no-progress
  - ./scripts/utils/install-tools.sh --local
  - Persist ~/.local/bin to GITHUB_PATH when available
EOF
  exit 0
fi

REQ_PY_VER="${1:-3.13}"
echo "[setup] Bootstrapping environment (Python ${REQ_PY_VER})..."

# Ensure uv is available (no nested actions, no curl)
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] 'uv' not found; installing via pip (user)"
  python -m pip install --upgrade pip
  python -m pip install --user uv
  if [ -n "${GITHUB_PATH:-}" ] && [ -d "$HOME/.local/bin" ]; then
    echo "$HOME/.local/bin" >> "$GITHUB_PATH"
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "[setup] Failed to provision 'uv'" >&2
    exit 1
  fi
fi

echo "[setup] Ensuring Python ${REQ_PY_VER} via uv"
uv python install "${REQ_PY_VER}"
echo "UV_PYTHON=${REQ_PY_VER}" >> "${GITHUB_ENV:-/dev/null}" || true

echo "[setup] Syncing Python dependencies (dev)..."
uv sync --dev --no-progress

echo "[setup] Installing external tools (hadolint, prettier, ruff, yamllint, darglint)..."
./scripts/utils/install-tools.sh --local

# Ensure local bin is persisted in PATH for downstream steps in GitHub Actions
if [ -n "$GITHUB_PATH" ] && [ -d "$HOME/.local/bin" ]; then
  echo "$HOME/.local/bin" >> "$GITHUB_PATH"
fi

echo "[setup] Environment bootstrap complete."


