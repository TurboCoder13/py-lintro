#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    # Use while read loop for safe parsing (handles spaces in values)
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # Remove surrounding quotes from value if present
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        export "$key=$value"
    done < .env
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