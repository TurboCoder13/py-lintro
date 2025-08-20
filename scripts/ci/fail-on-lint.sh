#!/usr/bin/env bash
set -euo pipefail

# fail-on-lint.sh
# Fail the CI job with a clear message when lint checks did not pass.
#
# Usage:
#   CHK_EXIT_CODE=<code> scripts/ci/fail-on-lint.sh

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fail the step when lint checks failed.

Usage:
  CHK_EXIT_CODE=<code> scripts/ci/fail-on-lint.sh

Environment:
  CHK_EXIT_CODE  Exit code from previous lint step (non-zero means failure)
EOF
  exit 0
fi

code="${CHK_EXIT_CODE:-}"
if [[ -z "${code}" ]]; then
  echo "CHK_EXIT_CODE is required" >&2
  exit 2
fi

echo "❌ Linting checks failed"
echo "Please fix the issues identified by lintro and try again."
exit 1


