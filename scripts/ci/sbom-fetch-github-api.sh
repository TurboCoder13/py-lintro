#!/usr/bin/env bash
set -euo pipefail

# sbom-fetch-github-api.sh
# Fetch repository SBOM using GitHub REST API instead of bomctl fetch.
# This approach uses GitHub's native dependency graph SBOM export.
#
# Features:
# - Fetches GitHub dependency graph SBOM via REST API
# - Validates JSON structure before import
# - Merges with local SBOM and exports to CycloneDX 1.6 and SPDX 2.3
# - Strict mode in CI: fails on errors; graceful mode in dev: continues with local SBOM
# - Graceful mode exports local SBOM even if GitHub fetch/merge fails
# - Comprehensive logging and validation

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fetch repository SBOM via GitHub REST API and import via bomctl

Usage:
  scripts/ci/sbom-fetch-github-api.sh

Environment:
  GITHUB_REPOSITORY  Repository in owner/repo format (required)
  GITHUB_TOKEN       GitHub API token (required)
  CI                 When set to 'true', enables strict mode (fails on errors)

Notes:
  - Requires gh CLI and bomctl on PATH
  - Requires jq for JSON validation
  - Requires 'project' alias in bomctl cache (from sbom-generate-safe.sh)
  - In CI mode (strict): fails if GitHub SBOM fetch/merge/export fails
  - In dev mode (graceful): warns on GitHub SBOM failures, exports local SBOM only
  - Graceful mode continues to export step even if GitHub fetch/merge fails
  - Exports: dist/sbom/py-lintro-sbom.cyclonedx-1.6.json
  - Exports: dist/sbom/py-lintro-sbom.spdx-2.3.json

Exit Codes:
  0  Success
  1  Critical failure (in CI mode) or validation error
  2  Prerequisites not met
EOF
  exit 0
fi

# Configuration
STRICT_MODE="${CI:-false}"
OUTPUT_DIR="dist/sbom"
SBOM_NAME="py-lintro-sbom"
PROJECT_ALIAS="project"
GITHUB_DEPS_ALIAS="github-deps"

# Validate required environment variables
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN not set}"

# Setup temporary directory with cleanup
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Logging helpers
log_info() {
  echo "[sbom-fetch] INFO: $*" >&2
}

log_success() {
  echo "[sbom-fetch] SUCCESS: $*" >&2
}

log_warn() {
  echo "[sbom-fetch] WARNING: $*" >&2
}

log_error() {
  echo "[sbom-fetch] ERROR: $*" >&2
}

# Error handler: fail in CI, warn in dev
handle_error() {
  local message="$1"
  if [[ "${STRICT_MODE}" == "true" ]]; then
    log_error "${message}"
    log_error "Strict mode enabled (CI=true), exiting with failure"
    exit 1
  else
    log_warn "${message}"
    log_warn "Development mode, continuing with local SBOM only"
  fi
}

# Validate prerequisites
validate_prerequisites() {
  local missing=0
  
  if ! command -v gh >/dev/null 2>&1; then
    log_error "gh CLI not found on PATH"
    missing=1
  fi
  
  if ! command -v bomctl >/dev/null 2>&1; then
    log_error "bomctl not found on PATH"
    missing=1
  fi
  
  if ! command -v jq >/dev/null 2>&1; then
    log_error "jq not found on PATH (required for JSON validation)"
    missing=1
  fi
  
  if [ ${missing} -eq 1 ]; then
    log_error "Prerequisites not met. Install required tools before running."
    exit 2
  fi
  
  log_info "Prerequisites validated: gh, bomctl, jq"
}

# Validate JSON structure and unwrap GitHub format if needed
validate_json() {
  local file="$1"
  
  if ! jq empty "${file}" 2>"${tmpdir}/jq-error.log"; then
    log_error "Invalid JSON in ${file}"
    cat "${tmpdir}/jq-error.log" >&2
    return 1
  fi
  
  # Validate SPDX/CycloneDX structure and unwrap GitHub format
  if jq -e '.sbom' "${file}" >/dev/null 2>&1; then
    log_info "Detected GitHub SBOM format (SPDX wrapper)"
    # Extract the actual SBOM from the wrapper
    log_info "Extracting SBOM from GitHub wrapper..."
    jq '.sbom' "${file}" > "${file}.unwrapped"
    mv "${file}.unwrapped" "${file}"
    log_success "Extracted SBOM from wrapper"
    return 0
  elif jq -e '.spdxVersion' "${file}" >/dev/null 2>&1; then
    log_info "Detected SPDX format"
    return 0
  elif jq -e '.bomFormat' "${file}" >/dev/null 2>&1; then
    log_info "Detected CycloneDX format"
    return 0
  else
    log_warn "Unknown SBOM format, proceeding anyway"
    return 0
  fi
}

# Verify bomctl cache has required alias
verify_bomctl_cache() {
  local alias="$1"
  
  log_info "Verifying bomctl cache contains '${alias}' alias..."
  
  if ! bomctl list 2>"${tmpdir}/bomctl-list-error.log" | grep -q "${alias}"; then
    log_error "'${alias}' alias not found in bomctl cache"
    log_error "Ensure sbom-generate-safe.sh ran successfully first"
    cat "${tmpdir}/bomctl-list-error.log" >&2
    return 1
  fi
  
  log_success "'${alias}' alias found in bomctl cache"
  return 0
}

# Main execution
main() {
  log_info "Starting GitHub SBOM fetch and merge"
  log_info "Mode: $([ "${STRICT_MODE}" == "true" ] && echo "STRICT (CI)" || echo "GRACEFUL (dev)")"
  
  validate_prerequisites
  
  # Parse repository owner and name
  owner="${GITHUB_REPOSITORY%/*}"
  repo="${GITHUB_REPOSITORY#*/}"
  log_info "Repository: ${owner}/${repo}"
  
  # Flag to track if GitHub SBOM was successfully merged
  github_merged=false
  
  # Fetch SBOM from GitHub REST API
  log_info "Fetching SBOM from GitHub Dependency Graph API..."
  
  if ! gh api "/repos/${owner}/${repo}/dependency-graph/sbom" > "${tmpdir}/github-sbom.json" 2>"${tmpdir}/gh-api-error.log"; then
    log_warn "Failed to fetch SBOM from GitHub API"
    cat "${tmpdir}/gh-api-error.log" >&2
    handle_error "GitHub API SBOM fetch failed (may not be available for this repository)"
  else
    log_success "Fetched SBOM from GitHub API"
    
    # Validate JSON structure
    log_info "Validating SBOM JSON structure..."
    if ! validate_json "${tmpdir}/github-sbom.json"; then
      handle_error "SBOM validation failed: invalid JSON structure"
    else
      log_success "SBOM JSON structure validated"
      
      # Import into bomctl
      log_info "Importing GitHub SBOM into bomctl with alias '${GITHUB_DEPS_ALIAS}'..."
      if ! bomctl import --alias "${GITHUB_DEPS_ALIAS}" "${tmpdir}/github-sbom.json" 2>"${tmpdir}/bomctl-import-error.log"; then
        log_error "Failed to import GitHub SBOM into bomctl"
        cat "${tmpdir}/bomctl-import-error.log" >&2
        handle_error "bomctl import failed"
      else
        log_success "Imported GitHub SBOM into bomctl"
        
        # Check if local SBOM exists before attempting merge
        if bomctl list 2>/dev/null | grep -q "${PROJECT_ALIAS}"; then
          # Merge GitHub SBOM with local SBOM
          log_info "Merging GitHub SBOM ('${GITHUB_DEPS_ALIAS}') with local SBOM ('${PROJECT_ALIAS}')..."
          if ! bomctl merge --alias "${PROJECT_ALIAS}" --name "${SBOM_NAME}" "${GITHUB_DEPS_ALIAS}" "${PROJECT_ALIAS}" 2>"${tmpdir}/bomctl-merge-error.log"; then
            log_error "Failed to merge SBOMs"
            cat "${tmpdir}/bomctl-merge-error.log" >&2
            handle_error "bomctl merge failed"
          else
            log_success "Merged GitHub and local SBOMs into '${PROJECT_ALIAS}' alias"
            github_merged=true
          fi
        else
          # No local SBOM, use GitHub SBOM only
          log_info "No local SBOM found ('${PROJECT_ALIAS}' alias missing), using GitHub SBOM only"
          log_info "Creating '${PROJECT_ALIAS}' alias from GitHub SBOM..."
          if ! bomctl merge --alias "${PROJECT_ALIAS}" --name "${SBOM_NAME}" "${GITHUB_DEPS_ALIAS}" 2>"${tmpdir}/bomctl-merge-error.log"; then
            log_error "Failed to create project alias from GitHub SBOM"
            cat "${tmpdir}/bomctl-merge-error.log" >&2
            handle_error "bomctl merge failed"
          else
            log_success "Created '${PROJECT_ALIAS}' alias from GitHub SBOM"
            github_merged=true
          fi
        fi
      fi
    fi
  fi
  
  # If GitHub merge failed in graceful mode, continue with local SBOM only
  if [ "${github_merged}" = false ]; then
    if [ "${STRICT_MODE}" = "true" ]; then
      log_error "GitHub SBOM processing failed in strict mode"
      exit 1
    fi
    
    # Check if local SBOM exists for fallback
    if bomctl list 2>/dev/null | grep -q "${PROJECT_ALIAS}"; then
      log_info "Continuing with local SBOM only (from '${PROJECT_ALIAS}' alias)"
    else
      log_error "No SBOM data available: GitHub fetch failed and no local SBOM exists"
      log_error "Cannot export SBOM without any source data"
      exit 1
    fi
  fi
  
  # Prepare output directory
  mkdir -p "${OUTPUT_DIR}"
  log_info "Output directory: ${OUTPUT_DIR}"
  
  # Export CycloneDX 1.6 JSON
  log_info "Exporting CycloneDX 1.6 JSON format..."
  cyclonedx_file="${OUTPUT_DIR}/${SBOM_NAME}.cyclonedx-1.6.json"
  cyclonedx_success=false
  
  if ! bomctl push "${PROJECT_ALIAS}" "${cyclonedx_file}" -f "cyclonedx-1.6" -e "json" --tree 2>"${tmpdir}/bomctl-push-cdx-error.log"; then
    log_error "Failed to export CycloneDX 1.6 format"
    cat "${tmpdir}/bomctl-push-cdx-error.log" >&2
    handle_error "CycloneDX export failed"
  elif [ ! -f "${cyclonedx_file}" ]; then
    handle_error "CycloneDX file was not created: ${cyclonedx_file}"
  else
    log_success "Exported CycloneDX 1.6: ${cyclonedx_file}"
    cyclonedx_success=true
  fi
  
  # Export SPDX 2.3 JSON
  log_info "Exporting SPDX 2.3 JSON format..."
  spdx_file="${OUTPUT_DIR}/${SBOM_NAME}.spdx-2.3.json"
  spdx_success=false
  
  if ! bomctl push "${PROJECT_ALIAS}" "${spdx_file}" -f "spdx-2.3" --tree 2>"${tmpdir}/bomctl-push-spdx-error.log"; then
    log_error "Failed to export SPDX 2.3 format"
    cat "${tmpdir}/bomctl-push-spdx-error.log" >&2
    handle_error "SPDX export failed"
  elif [ ! -f "${spdx_file}" ]; then
    handle_error "SPDX file was not created: ${spdx_file}"
  else
    log_success "Exported SPDX 2.3: ${spdx_file}"
    spdx_success=true
  fi
  
  # Check if at least one export succeeded
  if [ "${cyclonedx_success}" = false ] && [ "${spdx_success}" = false ]; then
    log_error "Both SBOM exports failed"
    if [ "${STRICT_MODE}" = "true" ]; then
      exit 1
    else
      log_warn "No SBOM files were successfully exported"
      return 1
    fi
  fi
  
  # Validate exported files
  log_info "Validating exported SBOM files..."
  validation_failed=false
  
  for file in "${cyclonedx_file}" "${spdx_file}"; do
    # Skip validation if file doesn't exist (export already failed)
    [ ! -f "${file}" ] && continue
    
    if ! validate_json "${file}"; then
      handle_error "Exported file validation failed: ${file}"
      validation_failed=true
      continue
    fi
    
    local size
    # Try macOS/BSD stat format first, then Linux format
    if ! size=$(stat -f %z "${file}" 2>/dev/null || stat -c %s "${file}" 2>/dev/null); then
      handle_error "Failed to get file size for: ${file}"
      validation_failed=true
      continue
    fi
    if [ "${size}" -lt 100 ]; then
      handle_error "Exported file suspiciously small (${size} bytes): ${file}"
      validation_failed=true
      continue
    fi
    log_info "Validated: ${file} (${size} bytes)"
  done
  
  if [ "${validation_failed}" = true ]; then
    log_warn "Some SBOM files failed validation"
    if [ "${STRICT_MODE}" = "true" ]; then
      exit 1
    fi
  fi
  
  if [ "${cyclonedx_success}" = true ] || [ "${spdx_success}" = true ]; then
    log_success "SBOM export(s) completed successfully"
  fi
  
  if [ "${github_merged}" = true ]; then
    log_success "GitHub SBOM fetch, merge, and export complete"
  else
    log_success "Local SBOM export complete (GitHub SBOM not available)"
  fi
  
  return 0
}

# Execute main function
main "$@"

