#!/usr/bin/env bash
set -euo pipefail

# sbom-generate.sh
# Generate and export SBOMs using bomctl with optional merge and formats.
#
# Features:
# - Fetch SBOM from GitHub dependency graph (public repos) via bomctl
# - Import local SBOM files and optionally merge them
# - Output CycloneDX and/or SPDX variants to an output directory
# - Dry-run mode to preview planned actions
#
# Usage:
#   scripts/ci/sbom-generate.sh [options]
#
# Options:
#   --help               Show this help and exit
#   --dry-run            Print actions without executing bomctl
#   --output-dir DIR     Directory for exported files (default: dist/sbom)
#   --name NAME          Logical document name (default: py-lintro-sbom)
#   --alias ALIAS        Alias for merged/output document (default: project)
#   --format CHOICE      Output format (repeatable). Supported values:
#                        cyclonedx-1.5, cyclonedx-1.6, spdx-2.3 (default: cyclonedx-1.5)
#   --encoding CHOICE    Output encoding for CycloneDX (json|xml; default: json)
#   --repo-url URL       GitHub repo URL to fetch (default inferred from GITHUB_REPOSITORY)
#   --skip-fetch         Skip bomctl fetch step
#   --import FILE        Import a local SBOM file (repeat to include multiple)
#   --netrc              Pass --netrc to bomctl for authenticated fetch/push
#
# Notes:
# - For fetch from private repos, configure credentials via --netrc and .netrc.
# - When importing multiple files, a merged document will be created and exported.
# - By default this script writes artifacts only to the filesystem; remote push
#   destinations can be added later if desired.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# Source shared utilities if available (optional)
if [ -f "${REPO_ROOT}/scripts/utils/utils.sh" ]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/utils/utils.sh"
  log_info "SBOM generation script starting"
else
  log_info() { echo "[info] $*"; }
  log_success() { echo "[ok] $*"; }
  log_warning() { echo "[warn] $*"; }
  log_error() { echo "[err] $*"; }
fi

show_help() {
  sed -n '1,80p' "$0"
}

# Defaults
DRY_RUN=0
OUTPUT_DIR="dist/sbom"
DOC_NAME="py-lintro-sbom"
DOC_ALIAS="project"
FORMATS=("cyclonedx-1.5")
ENCODING="json"
REPO_URL=""
SKIP_FETCH=0
PASSTHROUGH_NETRC=0
IMPORT_FILES=()

## Container execution is no longer supported.
## This script now requires the bomctl binary to be installed on PATH.

# Ensure bomctl cache directory exists and is used (improves fetch/push --tree)
if [ -z "${XDG_CACHE_HOME:-}" ]; then
  export XDG_CACHE_HOME="${PWD}/.bomctl-cache"
fi
mkdir -p "${XDG_CACHE_HOME}"

while (( "$#" )); do
  case "$1" in
    --help|-h)
      show_help; exit 0 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"; shift 2 ;;
    --name)
      DOC_NAME="${2:-}"; shift 2 ;;
    --alias)
      DOC_ALIAS="${2:-}"; shift 2 ;;
    --format)
      FORMATS+=("${2:-}"); shift 2 ;;
    --encoding)
      ENCODING="${2:-}"; shift 2 ;;
    --repo-url)
      REPO_URL="${2:-}"; shift 2 ;;
    --skip-fetch)
      SKIP_FETCH=1; shift ;;
    --import)
      IMPORT_FILES+=("${2:-}"); shift 2 ;;
    --netrc)
      PASSTHROUGH_NETRC=1; shift ;;
    *)
      log_error "Unknown argument: $1"; exit 2 ;;
  esac
done

# Normalize default formats (avoid duplicate default when user provided --format)
if [ ${#FORMATS[@]} -gt 1 ]; then
  # Drop the initial default if additional were specified
  if [ "${FORMATS[0]}" = "cyclonedx-1.5" ]; then
    FORMATS=("${FORMATS[@]:1}")
  fi
fi
if [ ${#FORMATS[@]} -eq 0 ]; then
  FORMATS=("cyclonedx-1.5")
fi

# Resolve repo URL if not provided
infer_repo_url() {
  if [ -n "${REPO_URL}" ]; then
    echo "${REPO_URL}"
    return 0
  fi
  if [ -n "${GITHUB_REPOSITORY:-}" ]; then
    echo "https://github.com/${GITHUB_REPOSITORY}"
    return 0
  fi
  # Try to translate git@github.com:owner/repo.git -> https://github.com/owner/repo
  if git remote get-url origin >/dev/null 2>&1; then
    local raw
    raw=$(git remote get-url origin)
    case "$raw" in
      git@github.com:*)
        local path
        path="${raw#git@github.com:}"
        path="${path%.git}"
        echo "https://github.com/${path}"
        return 0
        ;;
      https://github.com/*)
        echo "${raw%.git}"
        return 0
        ;;
    esac
  fi
  echo ""  # not found
}

run_print_cmd() {
  # Best-effort pretty print for dry-run
  local shown="$*"
  echo "$shown"
}

# Determine bomctl invocation as an array for safe execution
declare -a BOMCTL_ARR
BOMCTL_ARR=()
resolve_bomctl_arr() {
  if command -v bomctl >/dev/null 2>&1; then
    BOMCTL_ARR=("bomctl")
    return 0
  fi
  return 1
}

REPO_URL_RESOLVED="$(infer_repo_url)"
if ! resolve_bomctl_arr; then
  if [ ${DRY_RUN} -eq 0 ]; then
    log_error "bomctl is not available on PATH. Install it via scripts/ci/sbom-install-binary-gh.sh before running this script."
    exit 1
  fi
fi

netrc_flag=""
if [ ${PASSTHROUGH_NETRC} -eq 1 ]; then
  netrc_flag="--netrc"
fi

mkdir -p "${OUTPUT_DIR}"
chmod +x "$0" >/dev/null 2>&1 || true

# Helpers to run bomctl safely via array
run_bomctl() {
  # Usage: run_bomctl <args...>
  if [ ${DRY_RUN} -eq 1 ]; then
    echo "# Dry-run: planned action"
    # Ensure stable placeholder when bomctl is not present
    if [ ${#BOMCTL_ARR[@]} -eq 0 ]; then
      run_print_cmd "bomctl $*"
    else
      run_print_cmd "${BOMCTL_ARR[*]} $*"
    fi
    return 0
  fi
  log_info "Running: ${BOMCTL_ARR[*]} $*"
  "${BOMCTL_ARR[@]}" "$@"
}

HAS_FETCH=0
if [ ${SKIP_FETCH} -eq 0 ] && [ -n "${REPO_URL_RESOLVED}" ]; then
  HAS_FETCH=1
  if [ -n "${netrc_flag}" ]; then
    run_bomctl fetch "${REPO_URL_RESOLVED}" "${netrc_flag}"
  else
    run_bomctl fetch "${REPO_URL_RESOLVED}"
  fi
else
  log_warning "Fetch step skipped or repo URL not resolved; only imports will be processed."
fi

# Import provided local SBOMs
for f in "${IMPORT_FILES[@]:-}"; do
  if [ -n "$f" ]; then
    run_bomctl import --alias "${DOC_ALIAS}" --tag project:py-lintro --tag "run:$(date +%s)" "$f"
  fi
done

# Decide on root document and merging strategy
ROOT_ID=""
IMPORT_COUNT=${#IMPORT_FILES[@]}
MERGE_NEEDED=0
if [ ${HAS_FETCH} -eq 1 ] || [ ${IMPORT_COUNT} -gt 1 ]; then
  MERGE_NEEDED=1
fi

if [ ${MERGE_NEEDED} -eq 1 ]; then
  if [ ${HAS_FETCH} -eq 1 ] && [ ${IMPORT_COUNT} -gt 0 ]; then
    # Merge fetched document with imported alias into a single alias
    run_bomctl merge --alias "${DOC_ALIAS}" --name "${DOC_NAME}" "${REPO_URL_RESOLVED}" "${DOC_ALIAS}"
  elif [ ${HAS_FETCH} -eq 1 ] && [ ${IMPORT_COUNT} -eq 0 ]; then
    # Merge single fetched doc into alias to standardize pushes
    run_bomctl merge --alias "${DOC_ALIAS}" --name "${DOC_NAME}" "${REPO_URL_RESOLVED}"
  else
    # Multiple imports under the same alias; perform merge to consolidate
    run_bomctl merge --alias "${DOC_ALIAS}" --name "${DOC_NAME}" "${DOC_ALIAS}"
  fi
  ROOT_ID="${DOC_ALIAS}"
else
  # Single import only; alias points to the document
  if [ ${IMPORT_COUNT} -eq 1 ]; then
    ROOT_ID="${DOC_ALIAS}"
  else
    # Fetch-only without merge should not happen; default to alias
    ROOT_ID="${DOC_ALIAS}"
  fi
fi

# Export SBOMs (push tree to filesystem)
for fmt in "${FORMATS[@]}"; do
  case "$fmt" in
    cyclonedx-* )
      if [ -n "${netrc_flag}" ]; then
        run_bomctl push "${netrc_flag}" "${ROOT_ID}" "${OUTPUT_DIR}/${DOC_NAME}.${fmt}.${ENCODING}" -f "${fmt}" -e "${ENCODING}" --tree
      else
        run_bomctl push "${ROOT_ID}" "${OUTPUT_DIR}/${DOC_NAME}.${fmt}.${ENCODING}" -f "${fmt}" -e "${ENCODING}" --tree
      fi
      ;;
    spdx-* )
      if [ -n "${netrc_flag}" ]; then
        run_bomctl push "${netrc_flag}" "${ROOT_ID}" "${OUTPUT_DIR}/${DOC_NAME}.${fmt}.json" -f "${fmt}" --tree
      else
        run_bomctl push "${ROOT_ID}" "${OUTPUT_DIR}/${DOC_NAME}.${fmt}.json" -f "${fmt}" --tree
      fi
      ;;
    * )
      log_warning "Unsupported format: $fmt (skipping)" ;;
  esac
done

log_success "SBOM artifacts written to ${OUTPUT_DIR}"


