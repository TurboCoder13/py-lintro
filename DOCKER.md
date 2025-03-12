# Lintro Docker Usage

This document explains how to use Lintro with Docker, which allows you to run Lintro without installing all the dependencies directly on your system.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for using the docker-compose.yml file)

## Running Lintro with Docker

There are two main ways to run Lintro with Docker:

1. Using the provided shell script (`lintro-docker.sh`)
2. Using Docker commands directly

### Option 1: Using the Shell Script (Recommended)

The easiest way to use Lintro with Docker is to use the provided shell script:

```bash
# Make the script executable (first time only)
chmod +x lintro-docker.sh

# Run lintro commands
./lintro-docker.sh check --table-format
./lintro-docker.sh fmt --tools black,isort
./lintro-docker.sh list-tools
```

The script will automatically build the Docker image if it doesn't exist and run Lintro with your specified arguments.

### Option 2: Using Docker Commands Directly

If you prefer to use Docker commands directly:

```bash
# Build the Docker image
docker build -t lintro:latest .

# Run lintro with Docker
docker run --rm -v "$(pwd):/code" lintro:latest check --table-format
docker run --rm -v "$(pwd):/code" lintro:latest fmt --tools black,isort
```

### Option 3: Using Docker Compose

You can also use Docker Compose:

```bash
# Build the image
docker-compose build

# Run lintro with Docker Compose
docker-compose run --rm lintro check --table-format
docker-compose run --rm lintro fmt --tools black,isort
```

## Available Commands and Options

Lintro provides three main commands:

1. `check` - Check code for issues without making changes
2. `fmt` - Format code by fixing issues
3. `list-tools` - List all available tools

### Common Options for All Commands

- `--output FILE` - Write output to a file (the file will be created in your current directory)
- `--table-format` - Format output as a table (recommended for readability)

### Check Command Options

```bash
./lintro-docker.sh check [OPTIONS] [PATHS]...
```

Options:
- `--tools TEXT` - Comma-separated list of tools to run (default: all tools that can check)
- `--exclude TEXT` - Comma-separated list of patterns to exclude (e.g., '*.pyc,venv')
- `--include-venv` - Include virtual environment directories
- `--group-by [file|code|none|auto]` - How to group issues in the output (default: auto)
- `--ignore-conflicts` - Ignore tool conflicts

Tool-specific options:
- `--darglint-timeout INTEGER` - Timeout for darglint in seconds
- `--hadolint-timeout INTEGER` - Timeout for hadolint in seconds
- `--pydocstyle-timeout INTEGER` - Timeout for pydocstyle in seconds
- `--pydocstyle-convention TEXT` - Convention for pydocstyle (e.g., 'numpy', 'google')
- `--prettier-timeout INTEGER` - Timeout for prettier in seconds
- `--pylint-rcfile TEXT` - Path to pylint configuration file
- `--semgrep-config TEXT` - Semgrep configuration option (default: auto)
- `--terraform-recursive` - Recursively check Terraform directories
- `--yamllint-config TEXT` - Path to yamllint configuration file
- `--yamllint-strict` - Use strict mode for yamllint
- `--mypy-config TEXT` - Path to mypy configuration file
- `--mypy-python-version TEXT` - Python version to use for mypy type checking
- `--mypy-disallow-untyped-defs` - Disallow untyped function definitions in mypy
- `--mypy-disallow-incomplete-defs` - Disallow incomplete function definitions in mypy
- `--verbose` - Show verbose output

### Format Command Options

```bash
./lintro-docker.sh fmt [OPTIONS] [PATHS]...
```

Options:
- `--tools TEXT` - Comma-separated list of tools to run (default: all tools that can fix)
- `--exclude TEXT` - Comma-separated list of patterns to exclude
- `--include-venv` - Include virtual environment directories
- `--group-by [file|code|none|auto]` - How to group issues in the output (default: auto)
- `--ignore-conflicts` - Ignore tool conflicts

Tool-specific options:
- Same as for the `check` command

### List Tools Command Options

```bash
./lintro-docker.sh list-tools [OPTIONS]
```

Options:
- `--show-conflicts` - Show potential conflicts between tools

### Saving Output to a File

To save the output to a file, use the `--output` option:

```bash
# Save check results to a file
./lintro-docker.sh check --table-format --output results.txt

# Save formatted output to a file
./lintro-docker.sh fmt --table-format --output changes.txt

# Save tool list to a file
./lintro-docker.sh list-tools --output tools.txt
```

The output file will be created in your current directory on the host machine because Docker mounts your current directory as a volume inside the container. You can specify any path relative to your current directory:

```bash
# Save to a subdirectory
./lintro-docker.sh check --table-format --output reports/results.txt
```

Just make sure the directory exists before running the command.

## Common Use Cases

### Check Code Quality

```bash
# Basic check with table formatting
./lintro-docker.sh check --table-format

# Group issues by error code
./lintro-docker.sh check --table-format --group-by code

# Save output to a file
./lintro-docker.sh check --table-format --group-by code --output result.txt

# Check specific files or directories
./lintro-docker.sh check path/to/file.py path/to/directory

# Use specific tools only
./lintro-docker.sh check --tools black,flake8,pylint
```

### Format Code

```bash
# Format with all available formatting tools
./lintro-docker.sh fmt

# Format with specific tools
./lintro-docker.sh fmt --tools black,isort

# Format specific files or directories
./lintro-docker.sh fmt path/to/file.py path/to/directory
```

### List Available Tools

```bash
# List all tools
./lintro-docker.sh list-tools

# Show potential conflicts between tools
./lintro-docker.sh list-tools --show-conflicts
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with the output files, you may need to adjust the user in the Docker container:

```bash
docker run --rm -v "$(pwd):/code" --user "$(id -u):$(id -g)" lintro:latest check
```

### Volume Mounting Issues

If you're having trouble with volume mounting, ensure you're using the absolute path:

```bash
docker run --rm -v "$(pwd):/code" lintro:latest check
```

### Docker Script Not Working

If the `lintro-docker.sh` script isn't working, check that:

1. The script has execute permissions: `chmod +x lintro-docker.sh`
2. Docker is installed and running: `docker --version`
3. You're in the directory containing the Dockerfile

## Building Custom Images

You can modify the Dockerfile to include additional tools or configurations. After making changes, rebuild the image:

```bash
docker build -t lintro:custom .
docker run --rm -v "$(pwd):/code" lintro:custom check
```