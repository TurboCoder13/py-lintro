#!/usr/bin/env bash
set -euo pipefail

# test-venv-setup.sh - Create isolated Python 3.13 virtual environment
# Sets up a venv with pip and exports TEST_VENV_PYTHON path to GitHub Actions env

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Create isolated Python 3.13 virtual environment for package testing.

Usage:
  scripts/ci/test-venv-setup.sh [--help|-h] [VENV_DIR]

Arguments:
  VENV_DIR  Directory for virtual environment (default: test_venv)

Environment Variables:
  GITHUB_ENV  GitHub Actions environment file for exporting TEST_VENV_PYTHON

Output:
  Exports TEST_VENV_PYTHON to $GITHUB_ENV for use in subsequent steps
EOF
  exit 0
fi

VENV_DIR="${1:-test_venv}"

log_info() {
  echo "[test-venv-setup] $*"
}

log_info "Creating isolated Python 3.13 virtual environment at: $VENV_DIR"

# Create venv with Python 3.13
if ! uv venv "$VENV_DIR" --python 3.13; then
  echo "[test-venv-setup] ERROR: Failed to create virtual environment" >&2
  exit 1
fi

log_info "Installing pip into virtual environment"

# Install pip into the venv
if ! uv pip install --python "$VENV_DIR" pip; then
  echo "[test-venv-setup] ERROR: Failed to install pip" >&2
  exit 1
fi

# Activate and upgrade pip
log_info "Upgrading pip"
if ! source "$VENV_DIR/bin/activate" && python -m pip install --upgrade pip; then
  # Continue even if this fails (it's a secondary concern)
  log_info "Warning: pip upgrade may have failed, continuing anyway"
fi

# Export Python path for subsequent steps
PYTHON_PATH="$(pwd)/$VENV_DIR/bin/python"
log_info "Virtual environment ready at: $PYTHON_PATH"

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "TEST_VENV_PYTHON=$PYTHON_PATH" >> "$GITHUB_ENV"
  log_info "Exported TEST_VENV_PYTHON to GitHub Actions environment"
else
  log_info "GITHUB_ENV not set; skipping environment export"
fi

log_info "Setup complete ✅"
