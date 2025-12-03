#!/usr/bin/env bash
set -euo pipefail

# ci-log.sh
# Generic CI logging utility for workflow status messages.
#
# Usage:
#   scripts/ci/ci-log.sh <message>
#   scripts/ci/ci-log.sh --help|-h
#
# This script provides a standardized way to output status messages
# in CI workflows, keeping workflow YAML files shell-free.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
CI logging utility for workflow status messages.

Usage:
  scripts/ci/ci-log.sh <message>

Arguments:
  message  The message to log to stdout

Examples:
  scripts/ci/ci-log.sh "Build completed successfully"
  scripts/ci/ci-log.sh "Skipping step: condition not met"
EOF
  exit 0
fi

if [[ $# -eq 0 ]]; then
  echo "Error: No message provided" >&2
  echo "Usage: scripts/ci/ci-log.sh <message>" >&2
  exit 1
fi

echo "$*"

