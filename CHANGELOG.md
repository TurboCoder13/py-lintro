# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
