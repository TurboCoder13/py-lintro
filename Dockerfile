# =============================================================================
# Stage 1: Builder - Install all tools and dependencies
# =============================================================================
FROM python:3.13-slim@sha256:05b118ecc93ea09e30569706568fb251c71b77d2a3908d338b77be033e162b59 AS builder

# Tool versions as build args for easy updates
ARG HADOLINT_VERSION=2.12.0
ARG ACTIONLINT_VERSION=1.7.5

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:/root/.cargo/bin:${PATH}"

# Set shell options for pipefail before using pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /app

# Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    git \
    unzip \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install bun (JavaScript runtime and package manager)
RUN curl -fsSL https://bun.sh/install | bash && \
    mv /root/.bun/bin/bun /usr/local/bin/bun && \
    chmod +x /usr/local/bin/bun

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

# Copy only _tool_versions.py first (needed for tool version info in install-tools.sh)
# This preserves Docker layer cache - tool install won't rebuild on source changes
COPY pyproject.toml /app/
COPY lintro/_tool_versions.py /app/lintro/_tool_versions.py

# Copy scripts and package.json for tool installation
COPY scripts/ /app/scripts/
COPY package.json /app/package.json

# Install external tools and copy Rust tools to system-wide location
RUN find /app/scripts -type f -name "*.sh" -exec chmod +x {} \; && \
    /app/scripts/utils/install-tools.sh --docker && \
    if [ -d "/root/.cargo/bin" ]; then \
        cp -p /root/.cargo/bin/cargo /usr/local/bin/cargo 2>/dev/null || true; \
        cp -p /root/.cargo/bin/rustc /usr/local/bin/rustc 2>/dev/null || true; \
        cp -p /root/.cargo/bin/rustup /usr/local/bin/rustup 2>/dev/null || true; \
        cp -p /root/.cargo/bin/rustfmt /usr/local/bin/rustfmt 2>/dev/null || true; \
        chmod +x /usr/local/bin/cargo /usr/local/bin/rustc /usr/local/bin/rustup /usr/local/bin/rustfmt 2>/dev/null || true; \
    fi

# Copy full source before installing Python dependencies
COPY lintro/ /app/lintro/

# Install Python dependencies
RUN uv sync --dev --extra tools --no-progress && (uv cache clean || true)

# =============================================================================
# Stage 2: Runtime - Minimal image with only what's needed to run
# =============================================================================
FROM python:3.13-slim@sha256:05b118ecc93ea09e30569706568fb251c71b77d2a3908d338b77be033e162b59 AS runtime

# Add Docker labels
LABEL maintainer="turbocoder13"
LABEL org.opencontainers.image.source="https://github.com/turbocoder13/py-lintro"
LABEL org.opencontainers.image.description="Making Linters Play Nice... Mostly."
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:/app/.venv/bin:${PATH}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install minimal runtime dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m lintro

WORKDIR /app

# Copy installed tools from builder
COPY --from=builder /usr/local/bin/hadolint /usr/local/bin/
COPY --from=builder /usr/local/bin/actionlint /usr/local/bin/
COPY --from=builder /usr/local/bin/shellcheck /usr/local/bin/
COPY --from=builder /usr/local/bin/shfmt /usr/local/bin/
COPY --from=builder /usr/local/bin/taplo /usr/local/bin/
COPY --from=builder /usr/local/bin/gitleaks /usr/local/bin/
COPY --from=builder /usr/local/bin/cargo /usr/local/bin/
COPY --from=builder /usr/local/bin/rustc /usr/local/bin/
COPY --from=builder /usr/local/bin/rustup /usr/local/bin/
COPY --from=builder /usr/local/bin/rustfmt /usr/local/bin/
COPY --from=builder /usr/local/bin/uv /usr/local/bin/
COPY --from=builder /usr/local/bin/bun /usr/local/bin/
COPY --from=builder /root/.bun/install/global /opt/bun/install/global
COPY --from=builder /root/.cargo /home/lintro/.cargo
COPY --from=builder /root/.rustup /home/lintro/.rustup

# Set Rust environment for lintro user and bun global install location
# RUFF_CACHE_DIR set to /tmp to avoid permission issues with mounted volumes
ENV CARGO_HOME=/home/lintro/.cargo \
    RUSTUP_HOME=/home/lintro/.rustup \
    BUN_INSTALL=/opt/bun \
    RUFF_CACHE_DIR=/tmp/.ruff_cache

# Create bunx symlink (bun acts as bunx when called by that name)
RUN ln -sf /usr/local/bin/bun /usr/local/bin/bunx

# Create wrapper scripts for Node.js tools (uses bun as runtime)
RUN printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/prettier/bin/prettier.cjs "$@"\n' > /usr/local/bin/prettier && \
    chmod +x /usr/local/bin/prettier && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs "$@"\n' > /usr/local/bin/markdownlint-cli2 && \
    chmod +x /usr/local/bin/markdownlint-cli2 && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/@biomejs/biome/bin/biome "$@"\n' > /usr/local/bin/biome && \
    chmod +x /usr/local/bin/biome

# Copy Python virtual environment and application from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/lintro /app/lintro
COPY --from=builder /app/pyproject.toml /app/

# Copy entrypoint scripts
COPY scripts/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/docker/fix-permissions.sh /usr/local/bin/fix-permissions.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/fix-permissions.sh

# Create /code directory for volume mounts and fix Rust directory ownership
RUN mkdir -p /code && chown -R lintro:lintro /app /code /home/lintro/.cargo /home/lintro/.rustup

# Health check to verify lintro is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/.venv/bin/python -m lintro --version || exit 1

# Default to lintro user for security
USER lintro

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
