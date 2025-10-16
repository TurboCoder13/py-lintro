#!/usr/bin/env bash
set -euo pipefail

# test-verify-cli.sh - Verify lintro CLI entry points in installed package
# Tests that the installed package CLI is accessible and functional

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Verify CLI entry points from installed lintro package.

Usage:
  scripts/ci/test-verify-cli.sh [--help|-h] [PYTHON_BIN]

Arguments:
  PYTHON_BIN  Python executable in venv (default: test_venv/bin/python)

Environment Variables:
  TEST_VENV_PYTHON  Python executable path (overrides PYTHON_BIN arg)

Verifies:
  - CLI --version: displays version information
  - CLI --help: displays help text
EOF
  exit 0
fi

PYTHON_BIN="${TEST_VENV_PYTHON:-${1:-test_venv/bin/python}}"

log_info() {
  echo "[test-verify-cli] $*"
}

log_info "Verifying CLI with: $PYTHON_BIN"

# Verify Python executable exists
if [ ! -f "$PYTHON_BIN" ]; then
  echo "[test-verify-cli] ERROR: Python executable not found at $PYTHON_BIN" >&2
  exit 1
fi

# Test 1: CLI --version
log_info "Test 1: CLI --version"
if ! "$PYTHON_BIN" -m lintro --version; then
  echo "[test-verify-cli] ERROR: CLI --version failed" >&2
  exit 1
fi

# Test 2: CLI --help
log_info "Test 2: CLI --help"
if ! "$PYTHON_BIN" -m lintro --help; then
  echo "[test-verify-cli] ERROR: CLI --help failed" >&2
  exit 1
fi

log_info "All CLI tests passed ✅"
