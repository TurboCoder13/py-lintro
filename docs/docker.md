# Docker Usage Guide

This guide explains how to use Lintro with Docker for containerized development and CI environments.

## Quick Start

### Using Published Image (Recommended)

The easiest way to use Lintro is with the pre-built image from GitHub Container Registry:

```bash
# Basic usage
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check

# With grid formatting
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# Run specific tools
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --tools ruff,prettier

# Format code
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest format
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro

# Make the Docker script executable
chmod +x scripts/**/*.sh

# Run Lintro with Docker
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --output-format grid
```

### Basic Commands

```bash
# Check code for issues
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check

# Auto-fix issues where possible
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest format

# Use grid formatting (recommended)
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --output-format grid --group-by code

# List available tools
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest list-tools
```

## Published Docker Image

Lintro provides a pre-built Docker image available on GitHub Container Registry (GHCR):

### Image Details

- **Registry**: `ghcr.io/turbocoder13/py-lintro`
- **Tags**:
  - `latest` - Latest development version
  - `main` - Main branch version
  - `v1.0.0` - Specific release versions (when available)

### Using the Published Image

```bash
# Pull the latest image
docker pull ghcr.io/turbocoder13/py-lintro:latest

# Run with the published image
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check

# Use a specific version
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:main check
```

### CI/CD Integration

Use the published image in your CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Lintro
  run: |
    docker run --rm -v ${{ github.workspace }}:/code \
      ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# GitLab CI example
lintro:
  image: ghcr.io/turbocoder13/py-lintro:latest
  script:
    - lintro check --output-format grid
```

## Building the Image Locally

```bash
# Build the Docker image
docker build -t lintro:latest .

# Or use docker compose
docker compose build
```

## Running Commands

### Using Docker Directly

```bash
# Basic check
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check

# With grid formatting
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# Format code
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format --tools ruff
```

### Using Docker Compose

```bash
# Check code
docker compose run --rm lintro check

# Format code
docker compose run --rm lintro format --tools ruff

# Specific tools
docker compose run --rm lintro check --tools ruff,prettier
```

## Command Options

### Check Command

```bash
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check [OPTIONS] [PATHS]...
```

**Options:**

- `--tools TEXT` - Comma-separated list of tools (default: all)
- `--output-format grid` - Format output as a grid table
- `--group-by [file|code|none|auto]` - How to group issues
- `--output FILE` - Save output to file
- `--exclude TEXT` - Patterns to exclude
- `--include-venv` - Include virtual environment directories

**Tool-specific options:**

- `--tool-options TEXT` - Tool-specific options in format tool:option=value

### Format Command

```bash
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format [OPTIONS] [PATHS]...
```

Same options as check command, but only runs tools that can auto-fix issues.

### List Tools Command

```bash
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest list-tools [OPTIONS]
```

**Options:**

- `--show-conflicts` - Show potential conflicts between tools
- `--output FILE` - Save tool list to file

## Output to Files

When using the `--output` option, files are created in your current directory:

```bash
# Save check results
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid --output results.txt

# Save to subdirectory (make sure it exists)
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid --output reports/results.txt

# Save tool list
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest list-tools --output tools.txt
```

## Common Use Cases

### Code Quality Checks

```bash
# Basic quality check
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# Group by error type for easier fixing
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid --group-by code

# Check specific files or directories
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check src/ tests/ --output-format grid

# Use only specific tools
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --tools ruff,darglint --output-format grid
```

### Code Formatting

```bash
# Format with all available tools
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format

# Format with specific tools
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format --tools ruff,prettier

# Format specific directories
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format src/ --tools ruff
```

### CI/CD Integration

```bash
# CI-friendly output (no grid formatting)
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output ci-results.txt

# Exit with error code if issues found
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check && echo "No issues found" || echo "Issues detected"
```

## Testing

### Run Tests in Docker

```bash
# Run all integration tests (including Docker-only tests)
./docker-test.sh

# Run local tests only
./run-tests.sh
```

### Development Workflow

```bash
# Check your changes
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# Fix auto-fixable issues
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format

# Run tests
./docker-test.sh

# Check again to ensure everything is clean
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with output files:

```bash
# Run with your user ID
docker run --rm -v "$(pwd):/code" --user "$(id -u):$(id -g)" ghcr.io/turbocoder13/py-lintro:latest check
```

### Volume Mounting Issues

Ensure you're using the absolute path for volume mounting:

```bash
# Use absolute path
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check

# Check current directory
pwd
```

### Docker Command Issues

If Docker commands aren't working:

1. **Verify Docker is running:** `docker --version`
2. **Ensure you're in the correct directory:** Should contain code to lint
3. **Check volume permissions:** You may need to add `--user "$(id -u):$(id -g)"` to the docker run command

### Build Issues

If Docker build fails:

```bash
# Clean build (no cache)
docker build --no-cache -t lintro:latest .

# Check Docker logs
docker build -t lintro:latest . 2>&1 | tee build.log
```

## Advanced Usage

### Custom Configuration

Build a custom image with your own configuration:

```bash
# Copy your config files to the container
docker build -t lintro:custom .

# Run with custom config
docker run --rm -v "$(pwd):/code" lintro:custom check
```

### Performance Optimization

For large codebases:

```bash
# Use specific tools only
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --tools ruff --output-format grid

# Exclude unnecessary patterns
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --exclude "*.pyc,venv,node_modules" --output-format grid

# Process specific directories
docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check src/ --output-format grid
```

## Integration with Other Tools

### Makefile Integration

```makefile
lint:
	docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

fix:
	docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest format

lint-ci:
	docker run --rm -v "$(pwd):/code" ghcr.io/turbocoder13/py-lintro:latest check --output lint-results.txt
```

### GitHub Actions

```yaml
- name: Run Lintro
  run: |
    docker run --rm -v ${{ github.workspace }}:/code \
      ghcr.io/turbocoder13/py-lintro:latest check --output-format grid --output lintro-results.txt
```

## Best Practices

1. **Use grid formatting** for better readability: `--output-format grid`
2. **Group by error type** for systematic fixing: `--group-by code`
3. **Save results to files** for CI integration: `--output results.txt`
4. **Use specific tools** for faster checks: `--tools ruff,prettier`
5. **Exclude irrelevant files** to reduce noise: `--exclude "venv,node_modules"`
