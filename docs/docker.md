# Docker Usage Guide

This guide explains how to use Lintro with Docker for containerized development and CI environments.

## Quick Start

### Setup

```bash
# Clone the repository
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro

# Make the Docker script executable
chmod +x docker-lintro.sh

# Run Lintro with Docker
./docker-lintro.sh check --table-format
```

### Basic Commands

```bash
# Check code for issues
./docker-lintro.sh check

# Auto-fix issues where possible
./docker-lintro.sh fmt

# Use table formatting (recommended)
./docker-lintro.sh check --table-format --group-by code

# List available tools
./docker-lintro.sh list-tools
```

## Building the Image

```bash
# Build the Docker image
docker build -t lintro:latest .

# Or use docker compose
docker compose build
```

## Running Commands

### Using the Shell Script (Recommended)

The `docker-lintro.sh` script provides the easiest way to run Lintro in Docker:

```bash
# Basic usage
./docker-lintro.sh check --table-format

# Specific tools
./docker-lintro.sh check --tools ruff,prettier

# Format code
./docker-lintro.sh fmt --tools ruff

# Export results
./docker-lintro.sh check --table-format --output results.txt
```

### Using Docker Directly

```bash
# Basic check
docker run --rm -v "$(pwd):/code" lintro:latest check

# With table formatting
docker run --rm -v "$(pwd):/code" lintro:latest check --table-format

# Format code
docker run --rm -v "$(pwd):/code" lintro:latest fmt --tools ruff
```

### Using Docker Compose

```bash
# Check code
docker compose run --rm lintro check --table-format

# Format code
docker compose run --rm lintro fmt --tools ruff

# Specific tools
docker compose run --rm lintro check --tools ruff,prettier
```

## Command Options

### Check Command

```bash
./docker-lintro.sh check [OPTIONS] [PATHS]...
```

**Options:**

- `--tools TEXT` - Comma-separated list of tools (default: all)
- `--table-format` - Format output as a table
- `--group-by [file|code|none|auto]` - How to group issues
- `--output FILE` - Save output to file
- `--exclude TEXT` - Patterns to exclude
- `--include-venv` - Include virtual environment directories

**Tool-specific options:**

- `--darglint-timeout INTEGER` - Darglint timeout in seconds
- `--prettier-timeout INTEGER` - Prettier timeout in seconds

### Format Command

```bash
./docker-lintro.sh fmt [OPTIONS] [PATHS]...
```

Same options as check command, but only runs tools that can auto-fix issues.

### List Tools Command

```bash
./docker-lintro.sh list-tools [OPTIONS]
```

**Options:**

- `--show-conflicts` - Show potential conflicts between tools
- `--output FILE` - Save tool list to file

## Output to Files

When using the `--output` option, files are created in your current directory:

```bash
# Save check results
./docker-lintro.sh check --table-format --output results.txt

# Save to subdirectory (make sure it exists)
./docker-lintro.sh check --table-format --output reports/results.txt

# Save tool list
./docker-lintro.sh list-tools --output tools.txt
```

## Common Use Cases

### Code Quality Checks

```bash
# Basic quality check
./docker-lintro.sh check --table-format

# Group by error type for easier fixing
./docker-lintro.sh check --table-format --group-by code

# Check specific files or directories
./docker-lintro.sh check src/ tests/ --table-format

# Use only specific tools
./docker-lintro.sh check --tools ruff,darglint --table-format
```

### Code Formatting

```bash
# Format with all available tools
./docker-lintro.sh fmt

# Format with specific tools
./docker-lintro.sh fmt --tools ruff,prettier

# Format specific directories
./docker-lintro.sh fmt src/ --tools ruff
```

### CI/CD Integration

```bash
# CI-friendly output (no table formatting)
./docker-lintro.sh check --output ci-results.txt

# Exit with error code if issues found
./docker-lintro.sh check && echo "No issues found" || echo "Issues detected"
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
./docker-lintro.sh check --table-format

# Fix auto-fixable issues
./docker-lintro.sh fmt

# Run tests
./docker-test.sh

# Check again to ensure everything is clean
./docker-lintro.sh check --table-format
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with output files:

```bash
# Run with your user ID
docker run --rm -v "$(pwd):/code" --user "$(id -u):$(id -g)" lintro:latest check
```

### Volume Mounting Issues

Ensure you're using the absolute path for volume mounting:

```bash
# Use absolute path
docker run --rm -v "$(pwd):/code" lintro:latest check

# Check current directory
pwd
```

### Docker Script Issues

If the `docker-lintro.sh` script isn't working:

1. **Check permissions:** `chmod +x docker-lintro.sh`
2. **Verify Docker is running:** `docker --version`
3. **Ensure you're in the correct directory:** Should contain `Dockerfile`

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
./docker-lintro.sh check --tools ruff --table-format

# Exclude unnecessary patterns
./docker-lintro.sh check --exclude "*.pyc,venv,node_modules" --table-format

# Process specific directories
./docker-lintro.sh check src/ --table-format
```

## Integration with Other Tools

### Makefile Integration

```makefile
lint:
	./docker-lintro.sh check --table-format

fix:
	./docker-lintro.sh fmt

lint-ci:
	./docker-lintro.sh check --output lint-results.txt
```

### GitHub Actions

```yaml
- name: Run Lintro
  run: |
    chmod +x docker-lintro.sh
    ./docker-lintro.sh check --table-format --output lintro-results.txt
```

## Best Practices

1. **Use table formatting** for better readability: `--table-format`
2. **Group by error type** for systematic fixing: `--group-by code`
3. **Save results to files** for CI integration: `--output results.txt`
4. **Use specific tools** for faster checks: `--tools ruff,prettier`
5. **Exclude irrelevant files** to reduce noise: `--exclude "venv,node_modules"`
