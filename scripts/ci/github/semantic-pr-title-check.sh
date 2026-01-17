#!/usr/bin/env bash
set -euo pipefail

# Validate PR title against Conventional Commits.
#
# Inputs via env:
#   TYPES_INPUT       Newline- or comma-separated allowed types (default set)
#   REQUIRE_SCOPE     'true' to require scope like type(scope): subject
#   COMMENT_ON_FAIL   'true' to post a guidance comment on PR if invalid
#   PR_NUMBER         Pull request number
#   GITHUB_TOKEN      Token (only for commenting)
#   GITHUB_REPOSITORY owner/repo (for commenting)
#   GITHUB_EVENT_PATH Path to event JSON (fallback to read title)
#
# Outputs:
#   ok=true|false written to $GITHUB_OUTPUT (if set)

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Validate PR title against Conventional Commits.

Environment variables:
  TYPES_INPUT       Allowed types (newline- or comma-separated)
  REQUIRE_SCOPE     'true' to require a scope
  COMMENT_ON_FAIL   'true' to comment when invalid
  PR_NUMBER         PR number (for commenting)
  GITHUB_TOKEN      Token (only for commenting)
  GITHUB_REPOSITORY owner/repo (for commenting)
EOF
	exit 0
fi

TYPES_INPUT=${TYPES_INPUT:-$'chore\nci\ndocs\nfeat\nfix\nperf\nrefactor\nrevert\nstyle\ntest'}
REQUIRE_SCOPE=${REQUIRE_SCOPE:-false}
COMMENT_ON_FAIL=${COMMENT_ON_FAIL:-true}

# Obtain title via gh if available, else from event payload
TITLE=""
if command -v gh >/dev/null 2>&1 && [[ -n "${PR_NUMBER:-}" ]]; then
	TITLE=$(gh pr view "$PR_NUMBER" --json title -q .title 2>/dev/null || echo "")
fi
if [[ -z "$TITLE" && -n "${GITHUB_EVENT_PATH:-}" && -f "$GITHUB_EVENT_PATH" ]]; then
	TITLE=$(
		python3 - <<'PY'
import json, os
path=os.environ.get('GITHUB_EVENT_PATH')
try:
    with open(path,'r',encoding='utf-8') as f:
        ev=json.load(f)
    print(ev.get('pull_request',{}).get('title',''))
except Exception:
    print('')
PY
	)
fi

# Build regex from types
types_pipe=$(printf "%s" "$TYPES_INPUT" | tr ', ' '\n' | sed '/^$/d' | paste -sd'|' -)
if [[ -z "$types_pipe" ]]; then
	[[ -n "${GITHUB_OUTPUT:-}" ]] && echo "ok=false" >>"$GITHUB_OUTPUT"
	exit 0
fi
if [[ "$REQUIRE_SCOPE" == "true" ]]; then
	regex="^(${types_pipe})\([^)]+\):[[:space:]].+"
else
	regex="^(${types_pipe})(\([^)]+\))?:[[:space:]].+"
fi

if printf "%s" "$TITLE" | grep -Eq "$regex"; then
	[[ -n "${GITHUB_OUTPUT:-}" ]] && echo "ok=true" >>"$GITHUB_OUTPUT"
	exit 0
fi

[[ -n "${GITHUB_OUTPUT:-}" ]] && echo "ok=false" >>"$GITHUB_OUTPUT"

# Optional comment
if [[ "$COMMENT_ON_FAIL" == "true" && -n "${PR_NUMBER:-}" ]]; then
	body='🚫 Conventional Commits required for release automation.

Please format the PR title like:
- feat: add amazing thing
- fix(scope): handle edge case

Scopes are optional (unless required). Use present tense, imperative mood.

Once updated, this check will pass automatically.'
	if command -v gh >/dev/null 2>&1; then
		gh pr comment "$PR_NUMBER" --body "$body" >/dev/null 2>&1 || true
	elif [[ -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" ]]; then
		JSON_BODY=$(
			python3 - <<'PY'
import json, os
print(json.dumps({"body": os.environ.get("BODY","")}))
PY
		)
		curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
			-H "Accept: application/vnd.github+json" \
			-H "X-GitHub-Api-Version: 2022-11-28" \
			-X POST \
			-d "$JSON_BODY" \
			"https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" >/dev/null 2>&1 || true
	fi
fi

exit 0
