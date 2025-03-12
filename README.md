# Lintro

A comprehensive CLI tool that unifies various code formatting, linting, and quality assurance tools under a single command-line interface.

[![Test and Coverage](https://github.com/yourusername/lintro/actions/workflows/test-coverage.yml/badge.svg)](https://github.com/yourusername/lintro/actions/workflows/test-coverage.yml)
[![Coverage](https://raw.githubusercontent.com/yourusername/lintro/main/coverage-badge.svg)](https://github.com/yourusername/lintro/actions/workflows/test-coverage.yml)

## Features

- Run multiple linting and formatting tools with a single command
- Standardized configuration and output formatting
- Consistent error handling
- Extensible architecture for adding new tools
- Intelligent conflict resolution between tools
- Configurable tool priorities and execution order

## Supported Tools

- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- darglint (docstring linting)
- hadolint (Dockerfile linting)
- mypy (static type checking)
- prettier (code formatting for multiple languages)
- pydocstyle (docstring style checking)
- pylint (Python linting)
- semgrep (semantic code pattern matching)
- terraform (Terraform formatting)
- yamllint (YAML linting)

## Dependency Management

This project uses [Renovate](https://github.com/renovatebot/renovate) for automated dependency updates. Renovate will automatically create pull requests when updates are available for:

- Python dependencies in requirements.txt and requirements-dev.txt
- GitHub Actions in workflow files
- Docker base images in Dockerfile

The Renovate configuration is defined in `renovate.json` in the root of the repository. Updates are scheduled to run daily at 10:00 PM UTC.

### Renovate Features

- Automatic merging of patch updates for seamless minor fixes
- Automatic grouping of minor and patch updates to reduce PR noise
- Separate PRs for major updates that might include breaking changes
- Special grouping for related packages (e.g., pytest and its plugins)
- Dependency dashboard for monitoring update status
- Configurable schedule and rate limiting

## Installation

### Standard Installation

```bash
pip install lintro
```

### Docker Installation

You can also use Lintro with Docker, which allows you to run it without installing all the dependencies directly on your system:

```bash
# Clone the repository
git clone https://github.com/yourusername/lintro.git
cd lintro

# Make the Docker script executable
chmod +x lintro-docker.sh

# Run lintro with Docker
./lintro-docker.sh check --table-format
```

For detailed instructions on using Lintro with Docker, including all available options and common use cases, see the [Docker documentation](DOCKER.md).

## Usage

### List available tools

```bash
lintro list-tools
```

### Format code (auto-fix where possible)

```bash
lintro fmt [PATH]
```

### Check code for issues without fixing

```bash
lintro check [PATH]
```

### Run specific tools

```bash
lintro fmt --tools black,isort [PATH]
lintro check --tools flake8,pylint,mypy [PATH]
```

### Exclude specific patterns

By default, Lintro excludes virtual environment directories. You can specify additional patterns to exclude:

```bash
lintro check --exclude "migrations,node_modules,dist" [PATH]
lintro fmt --exclude "migrations,node_modules,dist" [PATH]
```

### Include virtual environment directories

If you want to include virtual environment directories (which are excluded by default):

```bash
lintro check --include-venv [PATH]
lintro fmt --include-venv [PATH]
```

### Export output to a file

You can export the output to a file using the `--output` option:

```bash
lintro check --output report.txt [PATH]
lintro fmt --output changes.txt [PATH]
lintro list-tools --output tools.txt
```

When using the `--output` option, the detailed output will be displayed in both the console and written to the specified file.

### Use table formatting for output

You can use a nicely formatted table for the output using the `--table-format` option:

```bash
lintro check --table-format [PATH]
lintro fmt --table-format [PATH]
```

This option requires the `tabulate` package to be installed. If it's not installed, Lintro will fall back to the standard formatting.

To install tabulate:

```bash
pip install tabulate
```

You can combine the table format with the output file option:

```bash
lintro check --table-format --output report.txt [PATH]
```

### Group issues in the output

When using table formatting, you can choose how to group the issues in the output using the `--group-by` option:

```bash
# Group by file (default for check command)
lintro check --table-format --group-by file [PATH]

# Group by error code
lintro check --table-format --group-by code [PATH]

# No grouping (flat list)
lintro check --table-format --group-by none [PATH]

# Auto-grouping (default for fmt command) - intelligently chooses the best grouping method
lintro check --table-format --group-by auto [PATH]
lintro fmt --table-format --group-by auto [PATH]
```

The auto-grouping option intelligently chooses between file and code grouping based on the output:
- If there are more unique files than error codes (and few error code types), it groups by error code
- Otherwise, it groups by file

Grouping by file is useful when you want to fix issues file by file, while grouping by error code is helpful when you want to fix similar issues across multiple files.

## Tool-Specific Options

Lintro supports various tool-specific options that can be passed directly to the underlying tools:

### darglint

```bash
lintro check --darglint-timeout 20 [PATH]
```

### hadolint

```bash
lintro check --hadolint-timeout 20 [PATH]
```

### mypy

```bash
lintro check --mypy-config mypy.ini [PATH]
lintro check --mypy-python-version 3.9 [PATH]
lintro check --mypy-disallow-untyped-defs [PATH]
lintro check --mypy-disallow-incomplete-defs [PATH]
```

### pydocstyle

```bash
lintro check --pydocstyle-timeout 20 [PATH]
lintro check --pydocstyle-convention numpy [PATH]  # Options: pep257, numpy, google
```

### prettier

```bash
lintro check --prettier-timeout 60 [PATH]
```

### pylint

```bash
lintro check --pylint-rcfile .pylintrc [PATH]
```