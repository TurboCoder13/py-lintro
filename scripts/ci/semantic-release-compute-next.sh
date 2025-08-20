#!/usr/bin/env bash
set -euo pipefail

# semantic-release-compute-next.sh
# Run semantic-release (via uvx) in noop mode to compute next version and write to GITHUB_OUTPUT.
# Requires: uv.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Compute next version using python-semantic-release (noop/dry run).

Usage:
  scripts/ci/semantic-release-compute-next.sh

Writes next_version= to $GITHUB_OUTPUT.
EOF
  exit 0
fi

NO_COLOR=1 FORCE_COLOR=0 OUTPUT=$(uvx --from python-semantic-release \
  semantic-release --noop version --print 2>&1 || true)
echo "$OUTPUT"
# Extract the last full semver-looking line from output, strip optional leading 'v'.
NEXT_VERSION=$(printf "%s\n" "$OUTPUT" \
  | sed -e 's/\r//g' \
  | grep -E '^[vV]?[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.]+)?$' \
  | tail -n 1 \
  | sed -E 's/^[vV]//' || true)
echo "Detected NEXT_VERSION=${NEXT_VERSION:-<empty>}"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "next_version=${NEXT_VERSION}" >> "$GITHUB_OUTPUT"
else
  echo "next_version=${NEXT_VERSION}"
fi

