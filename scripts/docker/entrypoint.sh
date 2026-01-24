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
