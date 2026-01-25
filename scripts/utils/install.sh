#!/usr/bin/env bash
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
	echo "Loading environment variables from .env file..."
	# SC2046: word splitting is intentional for env var export
	# shellcheck disable=SC2046
	export $(grep -v '^#' .env | xargs)
fi

# Install Lintro using uv
echo "Installing Lintro with dependencies..."
if ! uv sync --dev; then
	echo "Error: Failed to install Lintro dependencies"
	exit 1
fi

# Test the installation
echo "Testing Lintro installation..."
if uv run lintro --version; then
	echo "✓ Installation successful!"
else
	echo "✗ Installation test failed"
	exit 1
fi

echo ""
echo "Installation complete! Try running:"
echo "  uv run lintro list-tools"
echo "  uv run lintro check sample.py"
echo "  uv run lintro format sample.py"
echo ""
echo "Or use the convenience scripts:"
echo "  ./scripts/local/local-lintro.sh list-tools"
echo "  ./scripts/local/local-lintro.sh check sample.py"
