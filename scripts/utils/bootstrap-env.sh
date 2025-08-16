#!/bin/bash
set -e

# bootstrap-env.sh - Ensure Python env tools and project deps are installed
# - Installs uv if missing (official installer)
# - Syncs Python dependencies (dev)
# - Installs external tools used by Lintro
# - Ensures ~/.local/bin is on PATH for the current workflow

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Bootstraps CI environment with Python, uv, and external tools.

Usage:
  scripts/utils/bootstrap-env.sh [--help|-h]

Actions:
  - Install uv if missing and add ~/.local/bin to PATH
  - uv sync --dev --no-progress
  - ./scripts/utils/install-tools.sh --local
  - Persist ~/.local/bin to GITHUB_PATH when available
EOF
  exit 0
fi

echo "[setup] Bootstrapping environment..."

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Add default uv install location to PATH for this session
  if [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

echo "[setup] Syncing Python dependencies (dev)..."
uv sync --dev --no-progress

echo "[setup] Installing external tools (hadolint, prettier, ruff, yamllint, darglint)..."
./scripts/utils/install-tools.sh --local

# Ensure local bin is persisted in PATH for downstream steps in GitHub Actions
if [ -n "$GITHUB_PATH" ] && [ -d "$HOME/.local/bin" ]; then
  echo "$HOME/.local/bin" >> "$GITHUB_PATH"
fi

echo "[setup] Environment bootstrap complete."


