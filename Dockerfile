# =============================================================================
# Stage 1: Tools - Pre-built external tools (updated weekly)
# =============================================================================
# Use the pre-built tools image to avoid rebuilding tools on every CI run.
# TOOLS_IMAGE can be overridden at build time (e.g., for PR testing with new tools)
# yamllint disable-line rule:line-length
ARG TOOLS_IMAGE=ghcr.io/lgtm-hq/lintro-tools:latest@sha256:e145d4f4942fd3165c4406fabbe34d98edbe02aabb4d99cd71e8db79b0116c8f
# hadolint ignore=DL3006
FROM ${TOOLS_IMAGE} AS tools

# =============================================================================
# Stage 2: Builder - Add Python dependencies to tools image
# =============================================================================
FROM tools AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock package.json /app/

# Copy full source
COPY lintro/ /app/lintro/

# Install Python dependencies
RUN uv sync --dev --extra tools --no-progress && (uv cache clean || true)

# Ensure clippy shims are in /usr/local/bin (needed until tools image is rebuilt)
# Copy the rustup proxy shims which delegate to the actual toolchain binaries
RUN if [ ! -f /usr/local/bin/clippy-driver ]; then \
        rustup component add clippy && \
        for bin in clippy-driver cargo-clippy; do \
            if [ -f "/root/.cargo/bin/$bin" ]; then \
                cp -p "/root/.cargo/bin/$bin" "/usr/local/bin/$bin" && \
                chmod +x "/usr/local/bin/$bin"; \
            fi; \
        done; \
    fi

# =============================================================================
# Stage 3: Runtime - Minimal image with only what's needed to run
# =============================================================================
FROM python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18 AS runtime

# Add Docker labels
LABEL maintainer="lgtm-hq"
LABEL org.opencontainers.image.source="https://github.com/lgtm-hq/py-lintro"
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

# Copy installed tools from builder (which got them from tools image)
COPY --from=builder /usr/local/bin/hadolint /usr/local/bin/
COPY --from=builder /usr/local/bin/actionlint /usr/local/bin/
COPY --from=builder /usr/local/bin/shellcheck /usr/local/bin/
COPY --from=builder /usr/local/bin/shfmt /usr/local/bin/
COPY --from=builder /usr/local/bin/taplo /usr/local/bin/
COPY --from=builder /usr/local/bin/gitleaks /usr/local/bin/
COPY --from=builder /usr/local/bin/cargo /usr/local/bin/
COPY --from=builder /usr/local/bin/rustc /usr/local/bin/
COPY --from=builder /usr/local/bin/rustfmt /usr/local/bin/
COPY --from=builder /usr/local/bin/clippy-driver /usr/local/bin/
COPY --from=builder /usr/local/bin/cargo-clippy /usr/local/bin/
COPY --from=builder /usr/local/bin/uv /usr/local/bin/
COPY --from=builder /usr/local/bin/bun /usr/local/bin/
COPY --from=builder /root/.bun/install/global /opt/bun/install/global
COPY --chown=lintro:lintro --from=builder /root/.cargo /home/lintro/.cargo
COPY --chown=lintro:lintro --from=builder /root/.rustup /home/lintro/.rustup

# Set Rust environment for lintro user and bun global install location
# RUFF_CACHE_DIR set to /tmp to avoid permission issues with mounted volumes
ENV CARGO_HOME=/home/lintro/.cargo \
    RUSTUP_HOME=/home/lintro/.rustup \
    BUN_INSTALL=/opt/bun \
    RUFF_CACHE_DIR=/tmp/.ruff_cache

# Create bunx symlink (bun acts as bunx when called by that name)
RUN ln -sf /usr/local/bin/bun /usr/local/bin/bunx

# Create wrapper scripts for Node.js tools (uses bun as runtime)
# Only create wrappers for tools that are actually installed in the tools image
RUN printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/prettier/bin/prettier.cjs "$@"\n' > /usr/local/bin/prettier && \
    chmod +x /usr/local/bin/prettier && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs "$@"\n' > /usr/local/bin/markdownlint-cli2 && \
    chmod +x /usr/local/bin/markdownlint-cli2 && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/typescript/bin/tsc "$@"\n' > /usr/local/bin/tsc && \
    chmod +x /usr/local/bin/tsc && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/oxlint/bin/oxlint "$@"\n' > /usr/local/bin/oxlint && \
    chmod +x /usr/local/bin/oxlint && \
    printf '#!/bin/sh\nexec bun /opt/bun/install/global/node_modules/oxfmt/bin/oxfmt "$@"\n' > /usr/local/bin/oxfmt && \
    chmod +x /usr/local/bin/oxfmt

# Copy Python virtual environment and application from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/lintro /app/lintro
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/package.json /app/package.json

# Copy entrypoint scripts
COPY scripts/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/docker/fix-permissions.sh /usr/local/bin/fix-permissions.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/fix-permissions.sh

# Create /code directory for volume mounts and set ownership
RUN mkdir -p /code && chown -R lintro:lintro /app /code

# Health check to verify lintro is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/.venv/bin/python -m lintro --version || exit 1

# Default to lintro user for security
USER lintro

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
