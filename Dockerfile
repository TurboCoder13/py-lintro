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

# Install system dependencies and uv first
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv \
    && rm -rf /var/lib/apt/lists/*

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
RUN cat > /usr/local/bin/fix-permissions.sh << 'EOF'
#!/bin/bash
# Fix permissions for mounted volumes
if [ -d "/code" ]; then
    # Ensure current user can write to /code
    chown -R $(whoami):$(whoami) /code 2>/dev/null || true
    chmod -R 755 /code 2>/dev/null || true
fi
exec "$@"
EOF
RUN chmod +x /usr/local/bin/fix-permissions.sh

# Create a script to handle both root and non-root execution
RUN cat > /usr/local/bin/entrypoint.sh << 'EOF'
#!/bin/bash
# Handle both root and non-root execution
if [ "$(whoami)" = "root" ]; then
    # Running as root - use uv run directly
    exec uv run "$@"
else
    # Running as lintro user - use uv run
    exec uv run "$@"
fi
EOF
RUN chmod +x /usr/local/bin/entrypoint.sh

# Default to lintro user for security, but allow override
USER lintro

# Use the flexible entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["lintro", "--help"] 