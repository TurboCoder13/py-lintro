#!/usr/bin/env bash
set -euo pipefail

# test-install-package.sh - Install and verify built package in isolated venv
# Handles both wheel (.whl) and source distribution (.tar.gz) files

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	cat <<'EOF'
Install a built package distribution into an isolated virtual environment.

Usage:
  scripts/ci/test-install-package.sh [--help|-h] [PACKAGE_TYPE] [PYTHON_BIN]

Arguments:
  PACKAGE_TYPE  Type of package: 'wheel' or 'sdist' (default: wheel)
  PYTHON_BIN    Python executable in venv (default: test_venv/bin/python)

Environment Variables:
  TEST_VENV_PYTHON  Python executable path (overrides PYTHON_BIN arg)

Requirements:
  - Virtual environment must be set up at specified path
  - Built packages must exist in dist/ directory
  - For wheel: dist/*.whl file must exist
  - For sdist: dist/*.tar.gz file must exist
EOF
	exit 0
fi

PACKAGE_TYPE="${1:-wheel}"
PYTHON_BIN="${TEST_VENV_PYTHON:-${2:-test_venv/bin/python}}"

log_info() {
	echo "[test-install-package] $*"
}

# Validate package type
if [ "$PACKAGE_TYPE" != "wheel" ] && [ "$PACKAGE_TYPE" != "sdist" ]; then
	echo "[test-install-package] ERROR: PACKAGE_TYPE must be 'wheel' or 'sdist'" >&2
	exit 1
fi

# Find package file
if [ "$PACKAGE_TYPE" = "wheel" ]; then
	PACKAGE_FILE=$(find dist/ -name '*.whl' -type f | head -n 1)
	if [ -z "$PACKAGE_FILE" ]; then
		echo "[test-install-package] ERROR: No wheel file found in dist/" >&2
		exit 1
	fi
else
	PACKAGE_FILE=$(find dist/ -name '*.tar.gz' -type f | head -n 1)
	if [ -z "$PACKAGE_FILE" ]; then
		echo "[test-install-package] ERROR: No sdist file found in dist/" >&2
		exit 1
	fi
fi

log_info "Installing $PACKAGE_TYPE: $PACKAGE_FILE"

# Verify Python executable exists
if [ ! -f "$PYTHON_BIN" ]; then
	echo "[test-install-package] ERROR: Python executable not found at $PYTHON_BIN" >&2
	exit 1
fi

# Install package
if ! "$PYTHON_BIN" -m pip install "$PACKAGE_FILE"; then
	echo "[test-install-package] ERROR: Failed to install package" >&2
	exit 1
fi

log_info "Package installation successful ✅"
