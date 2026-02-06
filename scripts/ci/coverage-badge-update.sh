#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper for coverage badge updates.
# The implementation lives in scripts/ci/testing/coverage-badge-update.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/testing/coverage-badge-update.sh" "$@"
