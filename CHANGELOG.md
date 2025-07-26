# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project setup with comprehensive CLI tool
- Support for multiple linting tools: Ruff, Darglint, Prettier, Yamllint, Hadolint
- Docker containerization support
- GitHub Actions CI/CD workflows
- Comprehensive test suite with 84% coverage
- Multiple output formats (grid, CSV, JSON, HTML, Markdown, plain)
- Auto-fixing capabilities for supported tools
- Tool-specific configuration options
- Exclude pattern support
- Coverage reporting and badge generation

### Changed

- Organized assets into proper directory structure (`assets/images/`)

### Fixed

- Docker test execution issues
- Makefile docker-test script path
- Docker file copying for test accessibility

## [0.1.0] - 2024-07-25

### Added

- Initial release of Lintro
- Core CLI functionality with check, format, and list-tools commands
- Integration with Ruff for Python linting and formatting
- Integration with Darglint for Python docstring validation
- Integration with Prettier for JavaScript/TypeScript/JSON formatting
- Integration with Yamllint for YAML syntax and style checking
- Integration with Hadolint for Dockerfile best practices
- Comprehensive documentation
- Docker support for containerized environments
- GitHub Actions workflows for CI/CD
- Test suite with integration and unit tests

[Unreleased]: https://github.com/TurboCoder13/py-lintro/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/TurboCoder13/py-lintro/releases/tag/v0.1.0
