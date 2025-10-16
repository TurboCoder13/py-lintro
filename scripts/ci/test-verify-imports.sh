#!/usr/bin/env bash
set -euo pipefail

# test-verify-imports.sh - Verify critical package imports in installed lintro
# Tests that the installed package can be imported and key submodules are accessible

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Verify critical imports from installed lintro package.

Usage:
  scripts/ci/test-verify-imports.sh [--help|-h] [PYTHON_BIN] [DISTRIBUTION_TYPE]

Arguments:
  PYTHON_BIN        Python executable in venv (default: test_venv/bin/python)
  DISTRIBUTION_TYPE 'wheel', 'sdist', or 'both' (default: wheel)

Environment Variables:
  TEST_VENV_PYTHON  Python executable path (overrides PYTHON_BIN arg)

Verifies:
  - Basic package import: lintro
  - Parsers module: lintro.parsers
  - Specific parser: lintro.parsers.bandit
  - Tool implementations (wheel only): lintro.tools.implementations
  - CLI module: lintro.cli
EOF
  exit 0
fi

PYTHON_BIN="${TEST_VENV_PYTHON:-${1:-test_venv/bin/python}}"
DISTRIBUTION_TYPE="${2:-wheel}"

log_info() {
  echo "[test-verify-imports] $*"
}

log_info "Verifying imports with: $PYTHON_BIN"

# Verify Python executable exists
if [ ! -f "$PYTHON_BIN" ]; then
  echo "[test-verify-imports] ERROR: Python executable not found at $PYTHON_BIN" >&2
  exit 1
fi

# Test 1: Basic package import and version
log_info "Test 1: Basic package import"
if ! "$PYTHON_BIN" -c "import lintro; print(f'lintro {lintro.__version__}')"; then
  echo "[test-verify-imports] ERROR: Failed to import lintro" >&2
  exit 1
fi

# Test 2: Parsers module
log_info "Test 2: Parsers module import"
if ! "$PYTHON_BIN" -c "import lintro.parsers"; then
  echo "[test-verify-imports] ERROR: Failed to import lintro.parsers" >&2
  exit 1
fi

# Test 3: Specific parser (bandit)
log_info "Test 3: Bandit parser import"
if ! "$PYTHON_BIN" -c "from lintro.parsers import bandit"; then
  echo "[test-verify-imports] ERROR: Failed to import lintro.parsers.bandit" >&2
  exit 1
fi

# Test 4: Wheel-only tests (actionlint parser and tool)
if [ "$DISTRIBUTION_TYPE" = "wheel" ] || [ "$DISTRIBUTION_TYPE" = "both" ]; then
  log_info "Test 4: Actionlint parser import (wheel distribution)"
  if ! "$PYTHON_BIN" -c "from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output"; then
    echo "[test-verify-imports] ERROR: Failed to import actionlint_parser" >&2
    exit 1
  fi

  log_info "Test 5: Actionlint tool import (wheel distribution)"
  if ! "$PYTHON_BIN" -c "from lintro.tools.implementations.tool_actionlint import ActionlintTool"; then
    echo "[test-verify-imports] ERROR: Failed to import ActionlintTool" >&2
    exit 1
  fi
fi

# Test 5/6: CLI module
log_info "Test $([ "$DISTRIBUTION_TYPE" = "wheel" ] && echo 6 || echo 4): CLI module import"
if ! "$PYTHON_BIN" -c "from lintro.cli import cli"; then
  echo "[test-verify-imports] ERROR: Failed to import lintro.cli" >&2
  exit 1
fi

log_info "All import tests passed ✅"
