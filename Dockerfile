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
    npm \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

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
        chmod +x /usr/local/bin/cargo /usr/local/bin/rustc /usr/local/bin/rustup 2>/dev/null || true; \
    fi

# Copy project files and install Python dependencies
COPY pyproject.toml /app/
COPY lintro/ /app/lintro/
RUN uv sync --dev --no-progress && (uv cache clean || true)

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
    git \
    npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m lintro

WORKDIR /app

# Copy installed tools from builder
COPY --from=builder /usr/local/bin/hadolint /usr/local/bin/
COPY --from=builder /usr/local/bin/actionlint /usr/local/bin/
COPY --from=builder /usr/local/bin/cargo /usr/local/bin/
COPY --from=builder /usr/local/bin/rustc /usr/local/bin/
COPY --from=builder /usr/local/bin/rustup /usr/local/bin/
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /root/.cargo /home/lintro/.cargo
COPY --from=builder /root/.rustup /home/lintro/.rustup

# Set Rust environment for lintro user
ENV CARGO_HOME=/home/lintro/.cargo \
    RUSTUP_HOME=/home/lintro/.rustup

# Create symlinks for npm global packages
RUN ln -sf /usr/local/lib/node_modules/prettier/bin/prettier.cjs /usr/local/bin/prettier && \
    ln -sf /usr/local/lib/node_modules/markdownlint-cli2/markdownlint-cli2.mjs /usr/local/bin/markdownlint-cli2 || true

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
