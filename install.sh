#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Create the parent directory for virtual environments if it doesn't exist
VENV_DIR=$(eval echo ${UV_VENV_PYTHON_PATH:-".venv"})
VENV_PARENT_DIR=$(dirname "$VENV_DIR")
if [ ! -d "$VENV_PARENT_DIR" ]; then
    echo "Creating directory for virtual environments: $VENV_PARENT_DIR"
    mkdir -p "$VENV_PARENT_DIR"
fi

# Create a virtual environment using uv with the PATH argument
echo "Creating virtual environment at: $VENV_DIR"
uv venv "$VENV_DIR"

# Activate the virtual environment
echo "Activating virtual environment..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment activation script not found at $VENV_DIR/bin/activate"
    echo "Using default .venv directory instead"
    source .venv/bin/activate
fi

# Install Lintro in development mode using uv
echo "Installing Lintro in development mode..."
uv pip install -e .

# Test the installation
echo "Testing Lintro installation..."
lintro --version

echo "Installation complete! Try running:"
echo "  lintro list-tools"
echo "  lintro check sample.py"
echo "  lintro fmt sample.py"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source $VENV_DIR/bin/activate" 