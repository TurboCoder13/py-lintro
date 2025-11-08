FROM python:3.13-slim@sha256:8d4ea9d6915221b2d78e39e0dea0c714a4affb73ba74e839dbf6f76c524f78e4

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set shell options for pipefail before using pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Add Docker labels
LABEL maintainer="turbocoder13"
LABEL org.opencontainers.image.source="https://github.com/turbocoder13/py-lintro"
LABEL org.opencontainers.image.description="Making Linters Play Nice... Mostly."
LABEL org.opencontainers.image.licenses="MIT"

# Create a non-root user early
RUN useradd -m lintro

# Set up working directory
WORKDIR /app

# Install system dependencies and external tools
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    git \
    npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

# Copy scripts directory and package.json (needed for prettier version)
COPY scripts/ /app/scripts/
COPY package.json /app/package.json
RUN find /app/scripts -type f -name "*.sh" -print -exec chmod +x {} \; && \
    /app/scripts/utils/install-tools.sh --docker

# Copy pyproject.toml and lintro package first for better caching
COPY pyproject.toml /app/
COPY lintro/ /app/lintro/

# Ensure project files are owned by non-root before creating the venv
RUN chown -R lintro:lintro /app

# Install dependencies as the non-root user so the venv is accessible
USER lintro
RUN uv sync --dev --no-progress
RUN uv cache clean || true
USER root

# Copy the rest of the project
COPY . .

# Set ownership and permissions
RUN chown -R lintro:lintro /app && \
    mkdir -p /code && \
    chown -R lintro:lintro /code

# Create a script to fix permissions on mounted volumes
RUN echo '#!/bin/bash' > /usr/local/bin/fix-permissions.sh && \
    echo '# Fix permissions for mounted volumes' >> /usr/local/bin/fix-permissions.sh && \
    echo 'if [ -d "/code" ]; then' >> /usr/local/bin/fix-permissions.sh && \
    echo '    # Ensure current user can write to /code' >> /usr/local/bin/fix-permissions.sh && \
    echo "    chown -R \$(whoami):\$(whoami) /code 2>/dev/null || true" >> /usr/local/bin/fix-permissions.sh && \
    echo '    chmod -R 755 /code 2>/dev/null || true' >> /usr/local/bin/fix-permissions.sh && \
    echo 'fi' >> /usr/local/bin/fix-permissions.sh && \
    echo "exec \"\$@\"" >> /usr/local/bin/fix-permissions.sh
RUN chmod +x /usr/local/bin/fix-permissions.sh

# Create a flexible entrypoint that supports either `lintro ...` or
# `python -m lintro ...` while ensuring the venv interpreter is used.
# hadolint ignore=SC2016
RUN echo '#!/bin/bash' > /usr/local/bin/entrypoint.sh && \
    echo 'set -e' >> /usr/local/bin/entrypoint.sh && \
    echo 'if [ "$1" = "lintro" ]; then' >> /usr/local/bin/entrypoint.sh && \
    echo '  shift' >> /usr/local/bin/entrypoint.sh && \
    echo '  exec /app/.venv/bin/python -m lintro "$@"' >> /usr/local/bin/entrypoint.sh && \
    echo 'elif [ "$1" = "python" ]; then' >> /usr/local/bin/entrypoint.sh && \
    echo '  shift' >> /usr/local/bin/entrypoint.sh && \
    echo '  exec /app/.venv/bin/python "$@"' >> /usr/local/bin/entrypoint.sh && \
    echo 'else' >> /usr/local/bin/entrypoint.sh && \
    echo '  exec /app/.venv/bin/python -m lintro "$@"' >> /usr/local/bin/entrypoint.sh && \
    echo 'fi' >> /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Default to lintro user for security, but allow override
USER lintro

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["lintro", "--help"] 