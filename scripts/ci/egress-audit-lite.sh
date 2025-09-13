#!/usr/bin/env bash
set -euo pipefail

# egress-audit-lite.sh
# Usage: scripts/ci/egress-audit-lite.sh <fail-on-missing:true|false>
#
# Show help
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: scripts/ci/egress-audit-lite.sh [--help|-h] <fail-on-missing:true|false>

Reads a newline-separated list of host:port entries from STDIN and performs
HTTPS HEAD checks to validate reachability. When fail-on-missing is 'true',
the script exits non-zero if any endpoint is unreachable.
USAGE
  exit 0
fi
# Reads a newline-separated list of host:port entries from STDIN.

FAIL_ON_MISSING=${1:-false}

echo "[egress-audit-lite] Starting"
missing=0
while IFS= read -r line; do
  ep="${line//[$'\t\r']*/}"
  [[ -z "$ep" ]] && continue
  host="${ep%%:*}"
  port="${ep##*:}"
  if [[ -z "$host" || -z "$port" ]]; then
    continue
  fi
  url="https://$host/"
  printf '[egress-audit-lite] Testing %s:%s ... ' "$host" "$port"
  if curl -sI --max-time 5 "$url" >/dev/null; then
    echo OK
  else
    echo FAIL
    missing=$((missing+1))
  fi
done

if [[ "$FAIL_ON_MISSING" == "true" && $missing -gt 0 ]]; then
  echo "[egress-audit-lite] $missing endpoint(s) unreachable" >&2
  exit 1
fi
echo "[egress-audit-lite] Done"


