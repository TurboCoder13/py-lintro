#!/usr/bin/env bash
# generate-pypi-formula.sh
# Generate Homebrew formula for lintro from PyPI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../utils/utils.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Generate Homebrew formula for lintro from PyPI.

Usage: generate-pypi-formula.sh <version> <output-file>

Arguments:
  version      Package version (e.g., 1.0.0)
  output-file  Path to write the formula (e.g., Formula/lintro.rb)

Requirements:
  - Python 3.x with pip and venv

Examples:
  generate-pypi-formula.sh 1.0.0 Formula/lintro.rb
EOF
    exit 0
fi

VERSION="${1:?Version is required}"
OUTPUT_FILE="${2:?Output file is required}"

# Packages that require special handling (can't build from source in Homebrew)
WHEEL_PACKAGES=("darglint" "pydantic_core")

# Packages available as Homebrew formulae (use depends_on instead of bundling)
HOMEBREW_PACKAGES=("bandit" "black" "mypy" "ruff" "yamllint")

log_info "Generating lintro formula for version ${VERSION}"

# Fetch package info using Python helper
log_info "Fetching package info from PyPI..."
read -r TARBALL_URL TARBALL_SHA < <(python3 "$SCRIPT_DIR/fetch_package_info.py" lintro "$VERSION")

if [[ -z "$TARBALL_URL" ]] || [[ -z "$TARBALL_SHA" ]]; then
    log_error "Failed to fetch tarball info from PyPI"
    exit 1
fi

log_info "Tarball URL: ${TARBALL_URL}"
log_info "Tarball SHA256: ${TARBALL_SHA}"

# Create temporary directories (cleaned up on exit)
POET_VENV=$(mktemp -d)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$POET_VENV" "$TMPDIR"' EXIT

log_info "Creating temporary venv for poet analysis..."
python3 -m venv "$POET_VENV"

log_info "Installing lintro==${VERSION} and poet in temporary venv..."
"$POET_VENV/bin/pip" install --quiet "lintro==${VERSION}" homebrew-pypi-poet

log_info "Generating resources with poet..."
POET_OUTPUT=$("$POET_VENV/bin/poet" lintro 2>/dev/null)

# Build exclusion pattern for packages we handle specially
EXCLUDE_PATTERN="lintro"
for pkg in "${WHEEL_PACKAGES[@]}" "${HOMEBREW_PACKAGES[@]}"; do
    EXCLUDE_PATTERN="${EXCLUDE_PATTERN}|${pkg}"
done

# Remove excluded packages and clean up formatting
RESOURCES=$(echo "$POET_OUTPUT" | awk -v pattern="$EXCLUDE_PATTERN" '
    $0 ~ "resource \"(" pattern ")\"" { skip=1; next }
    skip && /^  end$/ { skip=0; getline; next }
    !skip { print }
' | cat -s)

# Validate resources were generated
RESOURCE_COUNT=$(echo "$RESOURCES" | grep -c "^  resource " || echo "0")
if [[ "$RESOURCE_COUNT" -lt 5 ]]; then
    log_error "Expected multiple resource stanzas but only found ${RESOURCE_COUNT}"
    log_error "poet may have failed to analyze dependencies."
    exit 1
fi
log_info "Generated ${RESOURCE_COUNT} resource stanzas from poet"

# Write resources to temp files
echo "$RESOURCES" > "$TMPDIR/poet_resources.txt"

# Generate wheel resources for packages that can't build from source
log_info "Generating wheel resources for special packages..."

python3 "$SCRIPT_DIR/fetch_wheel_info.py" darglint \
    --type universal \
    --comment "darglint requires poetry to build - use wheel" \
    > "$TMPDIR/darglint.txt" || {
    log_error "Failed to fetch darglint wheel info"
    exit 1
}

python3 "$SCRIPT_DIR/fetch_wheel_info.py" pydantic_core \
    --type platform \
    --comment "pydantic_core requires Rust to build - use platform-specific wheels" \
    > "$TMPDIR/pydantic.txt" || {
    log_error "Failed to fetch pydantic_core wheel info"
    exit 1
}

# Render formula from template
log_info "Rendering formula template..."
python3 "$SCRIPT_DIR/render_formula.py" \
    --tarball-url "$TARBALL_URL" \
    --tarball-sha "$TARBALL_SHA" \
    --poet-resources "$TMPDIR/poet_resources.txt" \
    --darglint-resource "$TMPDIR/darglint.txt" \
    --pydantic-resource "$TMPDIR/pydantic.txt" \
    --output "$OUTPUT_FILE"

log_success "Formula written to ${OUTPUT_FILE}"
