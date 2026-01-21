#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Verify that all required tools are installed in the tools image.

set -euo pipefail

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
