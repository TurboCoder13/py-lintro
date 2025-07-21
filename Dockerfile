FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set shell options for pipefail before using pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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

# Copy scripts directory and install tools
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && \
    /app/scripts/install-tools.sh --docker

# Copy the entire project and install dependencies
COPY . .
RUN uv sync --dev --no-progress && \
    uv cache clean

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

# Create a script to handle both root and non-root execution
RUN echo '#!/bin/bash' > /usr/local/bin/entrypoint.sh && \
    echo '# Handle both root and non-root execution' >> /usr/local/bin/entrypoint.sh && \
    echo "if [ \"\$(whoami)\" = \"root\" ]; then" >> /usr/local/bin/entrypoint.sh && \
    echo '    # Running as root - use uv run directly' >> /usr/local/bin/entrypoint.sh && \
    echo "    exec uv run \"\$@\"" >> /usr/local/bin/entrypoint.sh && \
    echo 'else' >> /usr/local/bin/entrypoint.sh && \
    echo '    # Running as lintro user - use uv run' >> /usr/local/bin/entrypoint.sh && \
    echo "    exec uv run \"\$@\"" >> /usr/local/bin/entrypoint.sh && \
    echo 'fi' >> /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Default to lintro user for security, but allow override
USER lintro

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["lintro", "--help"] 