# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-12-19

### Fixed

- **PyPI Publication Workflow**: Fixed test failures in PyPI publish workflow by adding missing tool installation step
  - Added tool installation step (`./scripts/utils/install-tools.sh --local`) to PyPI workflow
  - Added PATH setup to ensure tools are available during test execution
  - Now matches the tool setup used in the main CI workflow
- **Tool Installation Script**: Improved compatibility with uv-based Python environments
  - Updated `install-tools.sh` to use `uv pip install` for Python packages when uv is available
  - Added detection for GitHub Actions environment and uv availability
  - Maintains fallback to pip for environments without uv
- **Package Distribution**: Fixed MANIFEST.in file patterns to eliminate build warnings
  - Updated Dockerfile pattern to match actual file names (`Dockerfile.*`)
  - Removed unnecessary `.rst` and `.txt` patterns for docs directory
  - Clean build process with no warnings during package creation

### Technical Details

- **Files Modified**:
  - `.github/workflows/publish-pypi.yml` - Added tool installation and PATH setup
  - `scripts/utils/install-tools.sh` - Improved uv compatibility for Python package installation
  - `MANIFEST.in` - Fixed file inclusion patterns

- **Root Cause**: PyPI publish workflow was missing external tool dependencies (ruff, darglint, prettier, yamllint, hadolint) that integration tests require
- **Impact**: All tests now pass in PyPI publication workflow, enabling successful package distribution

## [Unreleased]

### Added

- Initial release preparation
- PyPI package configuration
- MANIFEST.in file for asset inclusion
- CHANGELOG.md for version tracking

### Fixed

- CI script path references for coverage comments
- Package metadata and classifiers
- Logo display in README for PyPI compatibility

## [0.1.0] - 2024-07-26

### Added

- Initial release of Lintro
- Unified CLI interface for multiple code quality tools
- Support for Ruff, Darglint, Prettier, Yamllint, and Hadolint
- Multiple output formats (grid, JSON, HTML, CSV, Markdown)
- Auto-fixing capabilities where supported
- Docker support and containerized environments
- Comprehensive test suite with 85% coverage
- CI/CD integration with GitHub Actions
- Documentation and usage examples

### Features

- **Unified CLI**: Single command interface for all tools
- **Multi-language support**: Python, JavaScript, YAML, Docker
- **Rich output formatting**: Beautiful table views and multiple formats
- **Auto-fixing**: Automatic issue resolution where possible
- **Docker ready**: Containerized execution for consistency
- **CI/CD integration**: GitHub Actions workflows for automation

### Supported Tools

- **Ruff**: Python linting and formatting
- **Darglint**: Python docstring validation
- **Prettier**: JavaScript/TypeScript/JSON formatting
- **Yamllint**: YAML syntax and style checking
- **Hadolint**: Dockerfile best practices

### Technical Details

- Python 3.13+ compatibility
- MIT License
- Comprehensive type hints
- Google-style docstrings
- Ruff and MyPy linting
- 85% test coverage
- Docker containerization
