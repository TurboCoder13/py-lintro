.PHONY: setup install test test-integration lint format clean help

# Include .env file if it exists
-include .env

# Default target
all: setup test

# Setup development environment
setup:
	@echo "Setting up development environment with uv..."
	uv sync --dev
	uv pip install -e .
	@echo "Setup complete! Try 'make test' or 'make lintro-check'"

# Install the package
install:
	@echo "Installing package with uv..."
	uv sync --dev
	uv pip install -e .

# Run all tests
test:
	@echo "Running tests with coverage..."
	uv run pytest --cov=lintro --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "Coverage reports generated:"
	@echo "  - Terminal: displayed above"
	@echo "  - HTML: htmlcov/index.html"
	@echo "  - XML: coverage.xml"

# Run integration tests using our local-test.sh script
test-integration:
	@echo "Running integration tests..."
	./scripts/local-test.sh

# Run linting using lintro itself
lint:
	@echo "Running lintro check..."
	uv run lintro check .

# Format code using lintro itself
format:
	@echo "Running lintro format..."
	uv run lintro fmt .

# Run lintro check (alias for lint)
lintro-check: lint

# Run lintro format (alias for format)
lintro-fmt: format

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t py-lintro:latest .

# Run tests in Docker
docker-test:
	@echo "Running tests in Docker..."
	./scripts/docker-test.sh

# Run type checking
mypy:
	@echo "Running mypy type checking..."
	uv run mypy lintro/

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
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

# Show help
help:
	@echo "Available targets:"
	@echo "  setup           - Set up development environment"
	@echo "  install         - Install package only"
	@echo "  test            - Run unit tests with coverage"
	@echo "  test-integration- Run integration tests"
	@echo "  lint            - Run lintro check"
	@echo "  format          - Run lintro format"
	@echo "  mypy            - Run type checking"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-test     - Run tests in Docker"
	@echo "  clean           - Clean up build artifacts"
	@echo "  help            - Show this help message" 