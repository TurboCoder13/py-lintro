#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Determine the virtual environment directory
VENV_DIR=$(eval echo ${UV_VENV_PYTHON_PATH:-".venv"})

# Create the parent directory if it doesn't exist
VENV_PARENT_DIR=$(dirname "$VENV_DIR")
if [ ! -d "$VENV_PARENT_DIR" ]; then
    echo "Creating directory for virtual environments: $VENV_PARENT_DIR"
    mkdir -p "$VENV_PARENT_DIR"
fi

# Create a virtual environment using uv with the PATH argument
echo "Creating virtual environment at: $VENV_DIR"
uv venv "$VENV_DIR"

echo "Virtual environment created at: $VENV_DIR"
echo "To activate, run: source $VENV_DIR/bin/activate" 