# Lintro

<img src="https://raw.githubusercontent.com/TurboCoder13/py-lintro/main/assets/images/lintro.png" alt="Lintro Logo" style="width:100%;max-width:800px;height:auto;display:block;margin:0 auto 24px auto;">

A comprehensive CLI tool that unifies various code formatting, linting, and quality assurance tools under a single command-line interface.

## What is Lintro?

Lintro is a unified command-line interface that brings together multiple code quality tools into a single, easy-to-use package. Instead of managing separate tools like Ruff, Prettier, Yamllint, and others individually, Lintro provides a consistent interface for all your code quality needs.

[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/downloads/)
[![Coverage](https://codecov.io/gh/TurboCoder13/py-lintro/branch/main/graph/badge.svg)](https://codecov.io/gh/TurboCoder13/py-lintro)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/test-and-coverage.yml?label=tests&branch=main&logo=githubactions&logoColor=white)](https://github.com/TurboCoder13/py-lintro/actions/workflows/test-and-coverage.yml?query=branch%3Amain)
[![CI](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/ci-lintro-analysis.yml?label=ci&branch=main&logo=githubactions&logoColor=white)](https://github.com/TurboCoder13/py-lintro/actions/workflows/ci-lintro-analysis.yml?query=branch%3Amain)
[![Docker](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/docker-build-publish.yml?label=docker&logo=docker&branch=main)](https://github.com/TurboCoder13/py-lintro/actions/workflows/docker-build-publish.yml?query=branch%3Amain)
[![PyPI](https://img.shields.io/pypi/v/lintro?label=pypi)](https://pypi.org/project/lintro/)

[![CodeQL](https://github.com/TurboCoder13/py-lintro/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/TurboCoder13/py-lintro/actions/workflows/codeql.yml?query=branch%3Amain)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/turbocoder13/py-lintro/badge)](https://scorecard.dev/viewer/?uri=github.com/turbocoder13/py-lintro)

### Why Lintro?

- **🚀 Unified Interface**: One command to run all your linting and formatting tools
- **🎯 Consistent Output**: Beautiful, standardized output formats across all tools
- **🔧 Auto-fixing**: Automatically fix issues where possible
- **🐳 Docker Ready**: Run in isolated containers for consistent environments
- **📊 Rich Reporting**: Multiple output formats (grid, JSON, HTML, CSV, Markdown)
- **⚡ Fast**: Optimized execution with efficient tool management
- **🔒 Reliable**: Comprehensive test suite with 84% coverage

## Features

- **Unified CLI** for multiple code quality tools
- **Multi-language support** - Python, JavaScript, YAML, Docker, and more
- **Auto-fixing** capabilities where possible
- **Beautiful output formatting** with table views
- **Docker support** for containerized environments
- **CI/CD integration** with GitHub Actions

## Supported Tools

| Tool                                                                                                                                                | Language            | Auto-fix |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------- |
| [![Actionlint](https://img.shields.io/badge/Actionlint-GitHub%20Workflows-24292e?logo=github&logoColor=white)](https://github.com/rhysd/actionlint) | ⚙️ GitHub Workflows | -        |
| [![Bandit](https://img.shields.io/badge/Bandit-security-yellow?logo=python&logoColor=white)](https://github.com/PyCQA/bandit)                       | 🐍 Python           | -        |
| [![Darglint](https://img.shields.io/badge/Darglint-docstrings-3776AB?logo=python&logoColor=white)](https://github.com/terrencepreilly/darglint)     | 🐍 Python           | -        |
| [![Hadolint](https://img.shields.io/badge/Hadolint-lint-2496ED?logo=docker&logoColor=white)](https://github.com/hadolint/hadolint)                  | 🐳 Dockerfile       | -        |
| [![Prettier](https://img.shields.io/badge/Prettier-format-1a2b34?logo=prettier&logoColor=white)](https://prettier.io/)                              | 🟨 JS/TS · 🧾 JSON  | ✅       |
| [![Ruff](https://img.shields.io/badge/Ruff-lint%2Bformat-000?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)                         | 🐍 Python           | ✅       |
| [![Yamllint](https://img.shields.io/badge/Yamllint-lint-cb171e?logo=yaml&logoColor=white)](https://github.com/adrienverge/yamllint)                 | 🧾 YAML             | -        |

## Quick Start

### Installation

#### From PyPI (Recommended)

```bash
pip install lintro
```

#### Development Installation

```bash
# Clone and install in development mode
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro
pip install -e .
```

### Basic Usage

```bash
# Check all files for issues
lintro check

# Auto-fix issues where possible
lintro format

# Use grid formatting for better readability
lintro check --output-format grid

# Run specific tools only
lintro check --tools ruff,prettier,actionlint

# List all available tools
lintro list-tools
```

## Docker Usage

### Quick Start with Published Image

```bash
# Run Lintro directly from GitHub Container Registry
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check

# With specific formatting
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# Run specific tools only
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --tools ruff,prettier
```

### Development Setup

```bash
# Clone and setup
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro
chmod +x scripts/**/*.sh

# Run with local Docker build
./scripts/docker/docker-lintro.sh check --output-format grid
```

See [Docker Documentation](docs/docker.md) for detailed usage.

## Advanced Usage

### Output Formatting

```bash
# Grid format (recommended)
lintro check --output-format grid --group-by code

# Export to file
lintro check --output report.txt

# Different grouping options
lintro check --output-format grid --group-by file  # Group by file
lintro check --output-format grid --group-by code  # Group by error type
```

### Tool-Specific Options

```bash
# Exclude patterns
lintro check --exclude "migrations,node_modules,dist"

# Tool-specific options use key=value (lists with |)
lintro check --tool-options "ruff:line_length=88,prettier:print_width=80"

# Ruff fix configuration (fmt):
# By default, fmt applies both lint fixes and formatting for Ruff.
# Disable either stage as needed:
lintro format --tool-options ruff:lint_fix=False     # format only
lintro format --tool-options ruff:format=False       # lint fixes only
```

### CI/CD Integration

Lintro includes pre-built GitHub Actions workflows:

- **Automated code quality checks** on pull requests
- **Coverage reporting** with badges
- **Multi-tool analysis** across your entire codebase

See [GitHub Integration Guide](docs/github-integration.md) for setup instructions.

## Documentation

For comprehensive documentation, see our **[Documentation Hub](docs/README.md)** which includes:

- **[Getting Started](docs/getting-started.md)** - Installation and basic usage
- **[Docker Usage](docs/docker.md)** - Containerized development
- **[GitHub Integration](docs/github-integration.md)** - CI/CD setup
- **[Configuration](docs/configuration.md)** - Tool configuration options
- **[Contributing](docs/contributing.md)** - Developer guide
- **[Tool Analysis](docs/tool-analysis/)** - Detailed tool comparisons

## Development

```bash
# Run tests
./scripts/local/run-tests.sh

# Run Lintro on itself
./scripts/local/local-lintro.sh check --output-format grid

# Docker development
./scripts/docker/docker-test.sh
./scripts/docker/docker-lintro.sh check --output-format grid
```

For detailed information about all available scripts, see [Scripts Documentation](scripts/README.md).

## Dependencies

- **Renovate** for automated dependency updates
- **Python 3.13+** with UV package manager
- **Optional**: Docker for containerized usage

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

#### "Command not found: lintro"

**Solution**: Ensure Lintro is installed correctly:

```bash
pip install lintro
# or for development
pip install -e .
```

#### "Tool not found" errors

**Solution**: Install the required tools or use Docker:

```bash
# Install tools individually
pip install ruff darglint
npm install -g prettier
pip install yamllint
# or use Docker (recommended)
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check
```

#### Permission errors on Windows

**Solution**: Run as administrator or use WSL:

```bash
# Use WSL for better compatibility
wsl
pip install lintro
```

#### Docker permission issues

**Solution**: Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

#### Slow performance

**Solution**: Use exclude patterns and specific tools:

```bash
# Exclude large directories
lintro check --exclude "node_modules,venv,.git"

# Run specific tools only
lintro check --tools ruff,prettier
```

### Getting Help

- 📖 **Documentation**: Check the [docs/](docs/) directory
- 🐛 **Bug Reports**: Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 **Questions**: Use the [question template](.github/ISSUE_TEMPLATE/question.md)
- 🚀 **Feature Requests**: Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)

## Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for details on:

- Adding new tools
- Reporting bugs
- Submitting features
- Code style guidelines
