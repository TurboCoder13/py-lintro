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
  semantic-release -v --noop version 2>&1 || true)
echo "$OUTPUT"

# If tool reports no release, leave NEXT_VERSION empty
if printf "%s\n" "$OUTPUT" | grep -qiE 'type[^\n]*no_release|no[_ ]release|no release will be made'; then
  NEXT_VERSION=""
else
  # Prefer explicit phrasing from semantic-release logs
  NEXT_VERSION=$(printf "%s\n" "$OUTPUT" \
    | sed -n 's/.*The next version is[: ]*\(v\?[0-9][0-9.]*[0-9][0-9A-Za-z.-]*\).*/\1/p' \
    | head -1 \
    | sed -E 's/^[vV]//' || true)

  # Fallback: standalone semver line (strip leading v)
  if [[ -z "$NEXT_VERSION" ]]; then
    NEXT_VERSION=$(printf "%s\n" "$OUTPUT" \
      | sed -e 's/\r//g' \
      | grep -E '^[vV]?[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.]+)?$' \
      | tail -n 1 \
      | sed -E 's/^[vV]//' || true)
  fi
fi
echo "Detected NEXT_VERSION=${NEXT_VERSION:-<empty>}"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "next_version=${NEXT_VERSION}" >> "$GITHUB_OUTPUT"
else
  echo "next_version=${NEXT_VERSION}"
fi

