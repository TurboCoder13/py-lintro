#!/usr/bin/env bash
# entrypoint.sh - Flexible Docker entrypoint for lintro
#
# This entrypoint supports multiple invocation styles:
#   - `lintro ...` - runs lintro with arguments
#   - `python ...` - runs Python with arguments
#   - `<any other command>` - treated as lintro arguments
#
# The venv interpreter is always used for consistency.

set -e

# Handle --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	cat <<'EOF'
entrypoint.sh - Docker entrypoint for lintro container

USAGE:
    docker run lintro [COMMAND] [ARGS...]

COMMANDS:
    lintro [ARGS]     Run lintro with specified arguments
    python [ARGS]     Run Python interpreter with arguments
    <any>             Treated as lintro arguments

EXAMPLES:
    docker run lintro check --tools ruff
    docker run lintro lintro list-tools
    docker run lintro python -c "print('hello')"

The virtual environment Python interpreter (/app/.venv/bin/python)
is always used for consistency.
EOF
	exit 0
fi

VENV_PYTHON="/app/.venv/bin/python"

# Change to /code if it exists and has content (user's mounted project)
# This ensures lintro scans the user's code, not /app (lintro's installation)
if [ -d "/code" ] && [ "$(ls -A /code 2>/dev/null)" ]; then
	cd /code
fi

# Auto-install Node.js dependencies if explicitly enabled via environment variable
# This enables seamless tsc support in Docker without manual intervention
# Security: Requires explicit opt-in via LINTRO_AUTO_INSTALL_DEPS=1
# Security: Uses --ignore-scripts to prevent lifecycle script execution
if [ "${LINTRO_AUTO_INSTALL_DEPS:-0}" = "1" ] && [ -f "package.json" ] && [ ! -d "node_modules" ]; then
	echo "[lintro] Installing Node.js dependencies (LINTRO_AUTO_INSTALL_DEPS=1)..."
	install_success=false
	if command -v bun &>/dev/null; then
		# Use --frozen-lockfile for reproducibility, --ignore-scripts for security
		if bun install --frozen-lockfile --ignore-scripts 2>/dev/null || bun install --ignore-scripts 2>/dev/null; then
			install_success=true
		fi
	elif command -v npm &>/dev/null; then
		# Use npm ci for reproducibility (requires package-lock.json), --ignore-scripts for security
		if npm ci --ignore-scripts 2>/dev/null || npm install --ignore-scripts 2>/dev/null; then
			install_success=true
		fi
	else
		echo "[lintro] Warning: No package manager (bun/npm) found"
	fi
	if [ "$install_success" = true ]; then
		echo "[lintro] Node.js dependencies installed."
	else
		echo "[lintro] Warning: Failed to install Node.js dependencies (may be read-only mount)"
	fi
fi

if [ "$1" = "lintro" ]; then
	shift
	exec "$VENV_PYTHON" -m lintro "$@"
elif [ "$1" = "python" ]; then
	shift
	exec "$VENV_PYTHON" "$@"
else
	# Default: treat all arguments as lintro arguments
	exec "$VENV_PYTHON" -m lintro "$@"
fi
