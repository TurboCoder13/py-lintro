#!/usr/bin/env bash
set -euo pipefail

# test-built-package-integration.sh
# Run integration tests for the built package in an isolated virtual environment.
#
# Usage:
#   scripts/ci/test-built-package-integration.sh [--help|-h]
#
# Prerequisites:
#   - test_venv must exist (created by test-venv-setup.sh)
#   - Package must be installed in test_venv (via test-install-package.sh)

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Run integration tests for the built package.

Usage:
  scripts/ci/test-built-package-integration.sh

Prerequisites:
  - test_venv virtual environment must exist
  - Package must be installed in test_venv

This script:
  1. Activates the test_venv virtual environment
  2. Installs pytest and test dependencies
  3. Runs the built package integration tests
EOF
  exit 0
fi

# Verify test_venv exists
if [[ ! -d "test_venv" ]]; then
  echo "Error: test_venv not found. Run test-venv-setup.sh first." >&2
  exit 1
fi

# Activate and run tests
# shellcheck source=/dev/null
source test_venv/bin/activate

pip install pytest pytest-cov assertpy

pytest tests/integration/test_built_package.py -v

