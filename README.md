# Lintro

A comprehensive CLI tool that unifies various code formatting, linting, and quality assurance tools under a single command-line interface.

[![Test and Coverage](https://github.com/TurboCoder13/py-lintro/actions/workflows/test-coverage.yml/badge.svg)](https://github.com/TurboCoder13/py-lintro/actions/workflows/test-coverage.yml)
[![Coverage](https://raw.githubusercontent.com/TurboCoder13/py-lintro/main/coverage-badge.svg)](https://github.com/TurboCoder13/py-lintro/actions/workflows/test-coverage.yml)
[![Lintro Report](https://github.com/TurboCoder13/py-lintro/actions/workflows/lintro-report.yml/badge.svg)](https://github.com/TurboCoder13/py-lintro/actions/workflows/lintro-report.yml)

## Features

- **Unified CLI** for multiple code quality tools
- **Multi-language support** - Python, JavaScript, YAML, Docker, and more
- **Auto-fixing** capabilities where possible
- **Beautiful output formatting** with table views
- **Docker support** for containerized environments
- **CI/CD integration** with GitHub Actions

## Supported Tools

| Tool         | Language/Format | Purpose              | Auto-fix |
| ------------ | --------------- | -------------------- | -------- |
| **Ruff**     | Python          | Linting & Formatting | ✅       |
| **Darglint** | Python          | Docstring Validation | ❌       |
| **Prettier** | JS/TS/JSON      | Code Formatting      | ✅       |
| **Yamllint** | YAML            | Syntax & Style       | ❌       |
| **Hadolint** | Dockerfile      | Best Practices       | ❌       |

## Quick Start

### Installation

```bash
pip install lintro
```

### Basic Usage

```bash
# Check all files for issues
lintro check

# Auto-fix issues where possible
lintro fmt

# Use table formatting for better readability
lintro check --table-format

# Run specific tools only
lintro check --tools ruff,prettier

# List all available tools
lintro list-tools
```

## Docker Usage

```bash
# Clone and setup
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro
chmod +x scripts/*.sh

# Run with Docker
./scripts/docker-lintro.sh check --table-format
```

See [Docker Documentation](docs/docker.md) for detailed usage.

## Advanced Usage

### Output Formatting

```bash
# Table format (recommended)
lintro check --table-format --group-by code

# Export to file
lintro check --output report.txt

# Different grouping options
lintro check --table-format --group-by file  # Group by file
lintro check --table-format --group-by code  # Group by error type
```

### Tool-Specific Options

```bash
# Darglint timeout
lintro check --darglint-timeout 20

# Prettier timeout
lintro check --prettier-timeout 60

# Exclude patterns
lintro check --exclude "migrations,node_modules,dist"
```

### CI/CD Integration

Lintro includes pre-built GitHub Actions workflows:

- **Automated code quality checks** on pull requests
- **Coverage reporting** with badges
- **Multi-tool analysis** across your entire codebase

See [GitHub Integration Guide](docs/github-integration.md) for setup instructions.

## Documentation

- **[Getting Started](docs/getting-started.md)** - Installation and basic usage
- **[Docker Usage](docs/docker.md)** - Containerized development
- **[GitHub Integration](docs/github-integration.md)** - CI/CD setup
- **[Configuration](docs/configuration.md)** - Tool configuration options
- **[Contributing](docs/contributing.md)** - Developer guide
- **[Tool Analysis](docs/tool-analysis/)** - Detailed tool comparisons

## Development

```bash
# Run tests
./scripts/run-tests.sh

# Run Lintro on itself
./scripts/local-lintro.sh check --table-format

# Docker development
./scripts/docker-test.sh
./scripts/docker-lintro.sh check --table-format
```

## Dependencies

- **Renovate** for automated dependency updates
- **Python 3.13+** with UV package manager
- **Optional**: Docker for containerized usage

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for details on:

- Adding new tools
- Reporting bugs
- Submitting features
- Code style guidelines
