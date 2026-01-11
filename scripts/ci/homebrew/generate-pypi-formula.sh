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

# Fetch package info from PyPI
PYPI_URL="https://pypi.org/pypi/lintro/${VERSION}/json"
log_info "Fetching package info from: ${PYPI_URL}"

PYPI_JSON=$(curl -sf "$PYPI_URL")
if [[ -z "$PYPI_JSON" ]]; then
    log_error "Failed to fetch package info from PyPI"
    exit 1
fi

# Extract tarball URL and SHA256
TARBALL_URL=$(echo "$PYPI_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for url in data['urls']:
    if url['packagetype'] == 'sdist':
        print(url['url'])
        break
")

TARBALL_SHA=$(echo "$PYPI_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for url in data['urls']:
    if url['packagetype'] == 'sdist':
        print(url['digests']['sha256'])
        break
")

if [[ -z "$TARBALL_URL" ]] || [[ -z "$TARBALL_SHA" ]]; then
    log_error "Failed to extract tarball URL or SHA256"
    exit 1
fi

log_info "Tarball URL: ${TARBALL_URL}"
log_info "Tarball SHA256: ${TARBALL_SHA}"

# Generate resources with poet (if available)
RESOURCES=""
if command -v poet &> /dev/null; then
    log_info "Generating resources with poet..."
    RESOURCES=$(poet lintro 2>/dev/null || echo "")
else
    log_warning "poet not found, skipping resource generation"
fi

# Generate the formula
cat > "$OUTPUT_FILE" << EOF
# typed: false
# frozen_string_literal: true

# Homebrew formula for lintro - auto-generated on release
# Manual edits will be overwritten on next release
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

  depends_on "actionlint"
  depends_on "hadolint"
  depends_on "prettier"
  depends_on "python@3.13"
  depends_on "ruff"

${RESOURCES}

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Lintro is now installed!

      Included tools:
        - ruff - Python linter and formatter
        - hadolint - Dockerfile linter
        - actionlint - GitHub Actions workflow linter
        - prettier - Code formatter
        - bandit - Python security linter
        - black - Python code formatter
        - darglint - Python docstring linter
        - yamllint - YAML linter

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
