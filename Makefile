.PHONY: setup install test lint format clean mypy

# Include .env file if it exists
-include .env

# Set default virtual environment path if not defined
UV_VENV_PYTHON_PATH ?= .venv

# Default target
all: setup test

# Setup development environment
setup:
	@if [ ! -d "$$(dirname "$(UV_VENV_PYTHON_PATH)")" ]; then \
		mkdir -p "$$(dirname "$(UV_VENV_PYTHON_PATH)")"; \
	fi
	UV_VENV_PYTHON_PATH=$(UV_VENV_PYTHON_PATH) uv venv "$(UV_VENV_PYTHON_PATH)"
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && uv pip install -e . && uv pip install -r requirements-dev.txt; \
	else \
		. .venv/bin/activate && uv pip install -e . && uv pip install -r requirements-dev.txt; \
	fi

# Install the package
install:
	@if [ ! -d "$$(dirname "$(UV_VENV_PYTHON_PATH)")" ]; then \
		mkdir -p "$$(dirname "$(UV_VENV_PYTHON_PATH)")"; \
	fi
	UV_VENV_PYTHON_PATH=$(UV_VENV_PYTHON_PATH) uv venv "$(UV_VENV_PYTHON_PATH)"
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && uv pip install -e .; \
	else \
		. .venv/bin/activate && uv pip install -e .; \
	fi

# Run tests
test:
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && pytest; \
	else \
		. .venv/bin/activate && pytest; \
	fi

# Run linting
lint:
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && black --check . && isort --check . && flake8 . && mypy .; \
	else \
		. .venv/bin/activate && black --check . && isort --check . && flake8 . && mypy .; \
	fi

# Run mypy type checking
mypy:
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && mypy .; \
	else \
		. .venv/bin/activate && mypy .; \
	fi

# Format code
format:
	@if [ -f "$(UV_VENV_PYTHON_PATH)/bin/activate" ]; then \
		. $(UV_VENV_PYTHON_PATH)/bin/activate && black . && isort .; \
	else \
		. .venv/bin/activate && black . && isort .; \
	fi

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} + 