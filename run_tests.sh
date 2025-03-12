#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Determine the virtual environment directory
VENV_DIR=$(eval echo ${UV_VENV_PYTHON_PATH:-".venv"})

# Ensure we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "No virtual environment detected."
    
    # Check if the custom virtual environment exists
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo "Activating existing virtual environment at: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
    else
        echo "Creating a new virtual environment at: $VENV_DIR"
        # Create the parent directory if it doesn't exist
        VENV_PARENT_DIR=$(dirname "$VENV_DIR")
        if [ ! -d "$VENV_PARENT_DIR" ]; then
            mkdir -p "$VENV_PARENT_DIR"
        fi
        
        uv venv "$VENV_DIR"
        
        # Activate the virtual environment
        if [ -f "$VENV_DIR/bin/activate" ]; then
            source "$VENV_DIR/bin/activate"
        else
            echo "Virtual environment activation script not found at $VENV_DIR/bin/activate"
            echo "Using default .venv directory instead"
            source .venv/bin/activate
        fi
        
        uv pip install -e .
        uv pip install -r requirements-dev.txt
    fi
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Run tests
echo "Running tests..."
pytest

# Run linting
echo "Running linting..."
black --check .
isort --check .
flake8 . 