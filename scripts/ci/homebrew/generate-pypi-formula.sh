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
  - Python 3.x with pip
  - homebrew-pypi-poet (pip install homebrew-pypi-poet)

Examples:
  generate-pypi-formula.sh 1.0.0 Formula/lintro.rb
EOF
    exit 0
fi

VERSION="${1:?Version is required}"
OUTPUT_FILE="${2:?Output file is required}"

log_info "Generating lintro formula for version ${VERSION}"

# Packages that require special handling (can't build from source in Homebrew)
# darglint: requires poetry to build
# pydantic_core: requires Rust/maturin to build
WHEEL_PACKAGES=("darglint" "pydantic_core")

# Packages available as Homebrew formulae (use depends_on instead of bundling)
HOMEBREW_PACKAGES=("bandit" "black" "mypy" "ruff" "yamllint")

# Fetch package info from PyPI
PYPI_URL="https://pypi.org/pypi/lintro/${VERSION}/json"
log_info "Fetching package info from: ${PYPI_URL}"

PYPI_JSON=$(curl -sf "$PYPI_URL")
if [[ -z "$PYPI_JSON" ]]; then
    log_error "Failed to fetch package info from PyPI"
    exit 1
fi

# Extract tarball URL and SHA256 using Python
read -r TARBALL_URL TARBALL_SHA < <(echo "$PYPI_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for url in data['urls']:
    if url['packagetype'] == 'sdist':
        print(url['url'], url['digests']['sha256'])
        break
")

if [[ -z "$TARBALL_URL" ]] || [[ -z "$TARBALL_SHA" ]]; then
    log_error "Failed to extract tarball URL or SHA256"
    exit 1
fi

log_info "Tarball URL: ${TARBALL_URL}"
log_info "Tarball SHA256: ${TARBALL_SHA}"

# Generate resources with poet
if ! command -v poet &> /dev/null; then
    log_error "poet not found. Install with: pip install homebrew-pypi-poet"
    exit 1
fi

log_info "Installing lintro==${VERSION} for poet dependency analysis..."
pip install "lintro==${VERSION}" --quiet

log_info "Generating resources with poet..."
POET_OUTPUT=$(poet lintro 2>/dev/null)

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

# Generate wheel resources for packages that can't build from source
log_info "Generating wheel resources for special packages..."

DARGLINT_RESOURCE=$(python3 "${SCRIPT_DIR}/fetch_wheel_info.py" darglint \
    --type universal \
    --comment "darglint requires poetry to build - use wheel") || {
    log_error "Failed to fetch darglint wheel info"
    exit 1
}

PYDANTIC_CORE_RESOURCE=$(python3 "${SCRIPT_DIR}/fetch_wheel_info.py" pydantic_core \
    --type platform \
    --comment "pydantic_core requires Rust to build - use platform-specific wheels") || {
    log_error "Failed to fetch pydantic_core wheel info"
    exit 1
}

log_info "Writing formula to ${OUTPUT_FILE}..."

# Generate the formula
cat > "$OUTPUT_FILE" << EOF
# typed: strict
# frozen_string_literal: true

# Homebrew formula for lintro
# CLI tools (ruff, black, mypy, bandit) are installed as Homebrew dependencies
# Python libraries are bundled as resources
class Lintro < Formula
  include Language::Python::Virtualenv

  desc "Unified CLI tool for code formatting, linting, and quality assurance"
  homepage "https://github.com/TurboCoder13/py-lintro"
  url "${TARBALL_URL}"
  sha256 "${TARBALL_SHA}"
  license "MIT"

  livecheck do
    url :stable
    strategy :pypi
  end

  # CLI tools installed via Homebrew
  depends_on "actionlint"
  depends_on "bandit"
  depends_on "black"
  depends_on "hadolint"
  depends_on "mypy"
  depends_on "prettier"
  depends_on "python@3.13"
  depends_on "ruff"
  depends_on "yamllint"

  # Pure Python library dependencies
${RESOURCES}
${DARGLINT_RESOURCE}

${PYDANTIC_CORE_RESOURCE}

  def install
    venv = virtualenv_create(libexec, "python3.13")

    # Install other resources first (this sets up pip in the venv)
    other_resources = resources.reject { |r| r.name == "pydantic_core" }
    venv.pip_install other_resources

    # Install pydantic_core wheel (requires special handling due to Rust build)
    resource("pydantic_core").stage do
      wheel = Pathname.pwd.children.find { |f| f.extname == ".whl" }
      system "python3.13", "-m", "pip", "--python=#{libexec}/bin/python",
             "install", "--no-deps", "--ignore-installed", wheel.to_s
    end

    # Install lintro itself
    venv.pip_install_and_link buildpath
  end

  def caveats
    <<~EOS
      Lintro is now installed!

      Included tools (installed via Homebrew):
        - ruff - Python linter and formatter
        - black - Python code formatter
        - mypy - Python type checker
        - bandit - Python security linter
        - hadolint - Dockerfile linter
        - actionlint - GitHub Actions workflow linter
        - prettier - Code formatter
        - yamllint - YAML linter

      Bundled tools:
        - darglint - Python docstring linter

      Get started:
        lintro check          # Check files for issues
        lintro format         # Auto-fix issues
        lintro list-tools     # View available tools

      Documentation: https://github.com/TurboCoder13/py-lintro/tree/main/docs
    EOS
  end

  test do
    assert_match version.to_s, shell_output("\#{bin}/lintro --version")
  end
end
EOF

log_success "Formula written to ${OUTPUT_FILE}"
