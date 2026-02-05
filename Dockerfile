# =============================================================================
# Lintro Docker Image
# =============================================================================
# Built on top of the pre-built tools image which contains all linting tools.
# This image adds the Python application layer.
#
# The tools image is rebuilt weekly and contains:
# - Rust toolchain (rustfmt, clippy, cargo-audit)
# - Node.js tools via bun (prettier, markdownlint-cli2, tsc, oxlint, oxfmt)
# - Python tools (ruff, black, bandit, mypy, semgrep, etc.)
# - Standalone binaries (hadolint, actionlint, shellcheck, shfmt, taplo, gitleaks)
# =============================================================================

# TOOLS_IMAGE can be overridden at build time (e.g., for PR testing with new tools)
# yamllint disable-line rule:line-length
ARG TOOLS_IMAGE=ghcr.io/lgtm-hq/lintro-tools:latest@sha256:e9f648af442ec5ae7e2539386487c124096746c216790c0b88c77001f8cce651
# checkov:skip=CKV_DOCKER_7: Tools image is pinned by digest; tag is for readability.
# hadolint ignore=DL3006
FROM ${TOOLS_IMAGE}

# Add Docker labels
LABEL maintainer="lgtm-hq"
LABEL org.opencontainers.image.source="https://github.com/lgtm-hq/py-lintro"
LABEL org.opencontainers.image.description="Making Linters Play Nice... Mostly."
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
# Explicitly include tool paths to ensure they're available for non-root user
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    RUFF_CACHE_DIR=/tmp/.ruff_cache \
    PATH="/usr/local/bin:/opt/cargo/bin:/opt/bun/bin:${PATH}"

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock package.json /app/

# Copy full source
COPY lintro/ /app/lintro/

# Install Python dependencies
RUN uv sync --dev --extra tools --no-progress && (uv cache clean || true)

# Copy entrypoint scripts
COPY scripts/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/docker/fix-permissions.sh /usr/local/bin/fix-permissions.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/fix-permissions.sh

# Create non-root user and directories
RUN getent group tools >/dev/null || groupadd -r tools && \
    id -u lintro >/dev/null 2>&1 || useradd -m -G tools lintro && \
    mkdir -p /code && \
    chown -R lintro:lintro /app /code

# Verify all tools are working (fail the build if any tool is broken)
RUN echo "Verifying tools..." && \
    rustfmt --version && \
    cargo clippy --version && \
    cargo audit --version && \
    semgrep --version && \
    ruff --version && \
    black --version && \
    hadolint --version && \
    actionlint --version && \
    shellcheck --version && \
    shfmt --version && \
    taplo --version && \
    gitleaks version && \
    prettier --version && \
    markdownlint-cli2 --version && \
    tsc --version && \
    oxlint --version && \
    oxfmt --version && \
    bandit --version && \
    mypy --version && \
    pydoclint --version && \
    yamllint --version && \
    sqlfluff --version && \
    echo "All tools verified!"

# Health check to verify lintro is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/.venv/bin/python -m lintro --version || exit 1

# Default to lintro user for security
USER lintro

# Verify tools work as non-root user (catches permission issues early)
RUN echo "Verifying tools as non-root user..." && \
    prettier --version && \
    markdownlint-cli2 --version && \
    tsc --version && \
    oxlint --version && \
    oxfmt --version && \
    rustfmt --version && \
    cargo clippy --version && \
    cargo audit --version && \
    semgrep --version && \
    echo "All tools verified for non-root user!"

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
