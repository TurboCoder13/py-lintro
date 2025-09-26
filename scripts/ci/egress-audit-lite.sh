#!/usr/bin/env bash
set -euo pipefail

# egress-audit-lite.sh
# Usage:
#   scripts/ci/egress-audit-lite.sh [--help|-h] [--check-ip] [true|false]
# Updated for comprehensive egress policy testing
# Added critical container endpoints to main allowlist
# Removed duplicates from container allowlist to avoid parsing conflicts
# Testing with IP addresses to see if domain resolution is the issue
#
# Behavior:
# - Reads endpoints from STDIN if piped; otherwise from EGRESS_ALLOWED_ENDPOINTS
#   (newline or comma separated). If EGRESS_ENDPOINTS_FILE is set, its contents
#   are used when STDIN is not provided and the env var is empty.
# - Each endpoint entry must be host:port.
# - By default, IP literals are skipped to avoid TLS SNI/cert pitfalls.
#   Pass --check-ip to include IPs.
# - When final positional arg is 'true', fail on any unreachable endpoint.
#
# Show help
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: scripts/ci/egress-audit-lite.sh [--help|-h] [--check-ip] [true|false]

Reads allowed egress endpoints and performs HTTPS HEAD checks to validate
reachability. Endpoints should be provided as host:port pairs.

Input priority:
  1) STDIN (newline-separated)
  2) EGRESS_ALLOWED_ENDPOINTS env (newline or comma-separated)
  3) EGRESS_ENDPOINTS_FILE env (path to file with newline-separated entries)

Options:
  --check-ip     Include IP literals (IPv4/IPv6). Default skips IPs.

Exit policy:
  If the final positional arg is 'true', the script exits non-zero when any
  endpoint is unreachable.
USAGE
  exit 0
fi

CHECK_IP=false
FAIL_ON_MISSING=false

# Parse flags and optional fail-on-missing boolean positional
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --check-ip)
      CHECK_IP=true
      ;;
    true|false)
      FAIL_ON_MISSING="$arg"
      ;;
    *)
      ARGS+=("$arg")
      ;;
  esac
done

echo "[egress-audit-lite] Starting"

# Load endpoints from STDIN when data is actually piped; otherwise env or file
endpoints_input=""
if [ -p /dev/stdin ] || [ -s /dev/stdin ]; then
  endpoints_input="$(cat)"
else
  if [[ -n "${EGRESS_ALLOWED_ENDPOINTS:-}" ]]; then
    endpoints_input="${EGRESS_ALLOWED_ENDPOINTS//$','/$'\n'}"
  elif [[ -n "${EGRESS_ENDPOINTS_FILE:-}" && -f "${EGRESS_ENDPOINTS_FILE}" ]]; then
    endpoints_input="$(cat "${EGRESS_ENDPOINTS_FILE}")"
  else
    echo "[egress-audit-lite] No endpoints provided via STDIN, env, or file" >&2
    echo "[egress-audit-lite] Set EGRESS_ALLOWED_ENDPOINTS or EGRESS_ENDPOINTS_FILE" >&2
    exit 2
  fi
fi

missing=0

process_line() {
  local line="$1"
  local ep="${line//[$'\t\r']*/}"
  [[ -z "$ep" ]] && return 0
  local host="${ep%%:*}"
  local port="${ep##*:}"
  if [[ -z "$host" || -z "$port" ]]; then
    return 0
  fi

  # Detect IPv4 or IPv6 literal
  local is_ip=false
  if [[ "$host" =~ ^[0-9]+(\.[0-9]+){3}$ ]]; then
    is_ip=true
  elif [[ "$host" =~ ^[0-9a-fA-F:]+$ || "$host" =~ ^\[[0-9a-fA-F:]+\]$ ]]; then
    is_ip=true
  fi

  if [[ "$is_ip" == true && "$CHECK_IP" != true ]]; then
    echo "[egress-audit-lite] Skipping IP literal ${host}:${port}"
    return 0
  fi

  local url="https://${host}:${port}/"
  printf '[egress-audit-lite] Testing %s:%s ... ' "$host" "$port"
  if curl -sI --max-time 5 "$url" >/dev/null; then
    echo OK
  else
    echo FAIL
    missing=$((missing+1))
  fi
}

while IFS= read -r line; do
  process_line "$line"
done <<< "$endpoints_input"

if [[ "$FAIL_ON_MISSING" == "true" && $missing -gt 0 ]]; then
  echo "[egress-audit-lite] $missing endpoint(s) unreachable" >&2
  exit 1
fi
echo "[egress-audit-lite] Done"


