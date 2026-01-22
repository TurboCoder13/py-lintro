#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Verify that all required tools are installed in the tools image.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Verify that all required tools are installed in the tools image.

Usage:
  scripts/ci/tools-image-verify.sh

Environment Variables (optional):
  IMAGE   Docker image to verify (default: lintro-tools:test)

The script runs tool version checks inside the specified Docker image
to ensure all linting/formatting tools are properly installed.

Example:
  IMAGE=ghcr.io/turbocoder13/lintro-tools:latest ./scripts/ci/tools-image-verify.sh
EOF
	exit 0
fi

IMAGE="${IMAGE:-lintro-tools:test}"

echo "Verifying installed tools in ${IMAGE}..."

# Run all verifications in a single container for efficiency
docker run --rm "$IMAGE" bash -c '
    set -euo pipefail
    echo "Core infrastructure tools:"
    bun --version
    uv --version
    cargo --version
    rustc --version

    echo ""
    echo "Linting and formatting tools:"
    actionlint --version
    bandit --version
    biome --version
    black --version
    cargo audit --version
    cargo clippy --version
    darglint --version
    gitleaks version
    hadolint --version
    markdownlint-cli2 --version
    mypy --version
    prettier --version
    ruff --version
    semgrep --version
    shellcheck --version
    shfmt --version
    sqlfluff --version
    taplo --version
    rustfmt --version
    yamllint --version
'

echo "All tools verified successfully!"
