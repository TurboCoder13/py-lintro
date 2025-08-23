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
  # Prefer explicit phrasing from semantic-release logs (several variants)
  NEXT_VERSION=$(printf "%s\n" "$OUTPUT" \
    | sed -n 's/.*The next version is[: ]*\(v\?[0-9][0-9.]*[0-9][0-9A-Za-z.-]*\).*/\1/p' \
    | head -1 \
    | sed -E 's/^[vV]//' || true)

  # Variant: "Bump from X to Y"
  if [[ -z "$NEXT_VERSION" ]]; then
    NEXT_VERSION=$(printf "%s\n" "$OUTPUT" \
      | sed -n 's/.*[Bb]ump from[[:space:]]*v\?[0-9][0-9.]*[0-9][0-9A-Za-z.-]*[[:space:]]*to[[:space:]]*\(v\?[0-9][0-9.]*[0-9][0-9A-Za-z.-]*\).*/\1/p' \
      | head -1 \
      | sed -E 's/^[vV]//' || true)
  fi

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

# Determine eligibility from commits since last baseline (tag or prepare commit)
LAST_TAG=$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)
BASE_REF=""
BASE_VERSION=""

if [[ -n "$LAST_TAG" ]]; then
  BASE_REF="$LAST_TAG"
  BASE_VERSION="${LAST_TAG#v}"
else
  # Fallback: find last prepare commit and derive base version from it
  PREP_SHA=$(git log --grep='^chore(release): prepare ' --pretty=format:'%h' -n 1 --no-merges 2>/dev/null || true)
  if [[ -n "$PREP_SHA" ]]; then
    BASE_REF="$PREP_SHA"
    BASE_VERSION=$(git log -1 --pretty=format:'%s' "$PREP_SHA" | sed -E 's/.*prepare ([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
  else
    # Last resort: read current version from pyproject.toml
    if [[ -f pyproject.toml ]]; then
      BASE_VERSION=$(sed -nE "s/^version\s*=\s*\"([0-9]+\.[0-9]+\.[0-9]+)\"/\1/p" pyproject.toml | head -1)
    fi
    BASE_REF="HEAD"
  fi
fi

LOG_RANGE="${BASE_REF}..HEAD"
COMMITS_SUBJECTS=$(git log ${LOG_RANGE} --pretty=%s 2>/dev/null || true)
COMMITS_BODIES=$(git log ${LOG_RANGE} --pretty=%B 2>/dev/null || true)

HAS_BREAKING=$( { printf "%s\n" "$COMMITS_SUBJECTS" | grep -Eq '^[a-z]+[^:!]*!:'; } || { printf "%s\n" "$COMMITS_BODIES" | grep -Eq '^BREAKING CHANGE:'; } && echo yes || echo no)
HAS_FEAT=$(printf "%s\n" "$COMMITS_SUBJECTS" | grep -Eq '^feat(\(|:)|^feat!' && echo yes || echo no)
HAS_FIX_OR_PERF=$(printf "%s\n" "$COMMITS_SUBJECTS" | grep -Eq '^(fix|perf)(\(|:)|^(fix|perf)!' && echo yes || echo no)

# If semantic-release did not produce a next version, compute a fallback
if [[ -z "${NEXT_VERSION}" ]]; then
  if [[ -z "$BASE_VERSION" ]]; then
    echo "No base version found; cannot compute fallback next version." >&2
  else
    IFS='.' read -r MAJOR MINOR PATCH <<< "$BASE_VERSION"
    if [[ "$HAS_BREAKING" == yes ]]; then
      MAJOR=$((MAJOR + 1))
      MINOR=0
      PATCH=0
    elif [[ "$HAS_FEAT" == yes ]]; then
      MINOR=$((MINOR + 1))
      PATCH=0
    elif [[ "$HAS_FIX_OR_PERF" == yes ]]; then
      PATCH=$((PATCH + 1))
    else
      # No eligible commits; leave NEXT_VERSION empty
      :
    fi
    if [[ -z "${NEXT_VERSION}" ]] && { [[ "$HAS_BREAKING" == yes ]] || [[ "$HAS_FEAT" == yes ]] || [[ "$HAS_FIX_OR_PERF" == yes ]]; }; then
      NEXT_VERSION="${MAJOR}.${MINOR}.${PATCH}"
      echo "Fallback computed NEXT_VERSION=$NEXT_VERSION (base=$BASE_VERSION, tag=$LAST_TAG)"
      if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
        echo "next_version=${NEXT_VERSION}" >> "$GITHUB_OUTPUT"
      else
        echo "next_version=${NEXT_VERSION}"
      fi
    fi
  fi
fi

# Optionally clamp bump to at most minor when MAX_BUMP=minor
if [[ -n "$BASE_VERSION" && -n "$NEXT_VERSION" && "${MAX_BUMP:-}" == "minor" ]]; then
  IFS='.' read -r BASE_MAJ BASE_MIN BASE_PAT <<< "$BASE_VERSION"
  IFS='.' read -r NEXT_MAJ NEXT_MIN NEXT_PAT <<< "$NEXT_VERSION"
  if (( NEXT_MAJ > BASE_MAJ )); then
    # Clamp major bump down to minor
    CLAMPED_MIN=$((BASE_MIN + 1))
    CLAMPED_VER="${BASE_MAJ}.${CLAMPED_MIN}.0"
    echo "Clamping major bump to minor: ${NEXT_VERSION} -> ${CLAMPED_VER}" >&2
    NEXT_VERSION="$CLAMPED_VER"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
      # Rewrite output
      # Shellcheck disable intentionally: append new value (consumers read last occurrence)
      echo "next_version=${NEXT_VERSION}" >> "$GITHUB_OUTPUT"
    else
      echo "next_version=${NEXT_VERSION}"
    fi
  fi
fi

# If still no version but eligible commits are present, warn
if [[ -z "${NEXT_VERSION}" ]] && { [[ "$HAS_FEAT" == yes ]] || [[ "$HAS_FIX_OR_PERF" == yes ]] || [[ "$HAS_BREAKING" == yes ]]; }; then
  echo "Warning: eligible commits detected since ${BASE_REF:-<none>}, but next_version is empty. Inspect commit messages and configuration." >&2
fi

