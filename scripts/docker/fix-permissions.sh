#!/usr/bin/env bash
# fix-permissions.sh - Fix permissions for mounted volumes in Docker
#
# This script ensures the current user can write to mounted volumes.
# It's used as a wrapper in Docker containers to handle permission issues
# when volumes are mounted from the host.

set -e

# Handle --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	cat <<'EOF'
fix-permissions.sh - Fix permissions for mounted volumes in Docker

USAGE:
    fix-permissions.sh [COMMAND] [ARGS...]

DESCRIPTION:
    Fixes ownership and permissions for the /code directory in Docker
    containers, then executes the specified command with its arguments.

    This script is typically used as a wrapper to ensure mounted volumes
    are accessible by the container user before running the main command.

EXAMPLES:
    fix-permissions.sh python -m lintro check
    fix-permissions.sh /app/.venv/bin/python -m pytest

NOTE:
    This script requires appropriate permissions to run chown/chmod.
    It silently ignores permission errors to avoid blocking execution.
EOF
	exit 0
fi

# Fix permissions for /code if it exists
if [ -d "/code" ]; then
	# Ensure current user can write to /code
	chown -R "$(id -u):$(id -g)" /code 2>/dev/null || true
	chmod -R 755 /code 2>/dev/null || true
fi

# Execute the command passed as arguments
exec "$@"
