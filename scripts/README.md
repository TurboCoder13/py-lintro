# Scripts Directory

This directory contains utility scripts for development, CI/CD, Docker operations, and local testing. All scripts are organized into logical subdirectories for easy navigation.

## 📁 Directory Structure

```
scripts/
├── ci/           # CI/CD and GitHub Actions scripts (8 files)
├── docker/       # Docker-related scripts (3 files)
├── local/        # Local development scripts (3 files)
└── utils/        # Utility scripts and shared functions (7 files)
```

## 🚀 Quick Start

### For New Contributors

1. **Install dependencies:**

```bash
./scripts/utils/install.sh
```

2. **Run tests:**

```bash
./scripts/local/run-tests.sh
```

3. **Use Lintro locally:**

```bash
./scripts/local/local-lintro.sh check --output-format grid
```

### For Docker Users

```bash
# Build and test Docker image
./scripts/docker/docker-test.sh

# Run Lintro in Docker
./scripts/docker/docker-lintro.sh check --output-format grid
```

## 📋 Script Categories

### 🔧 CI/CD Scripts (`ci/`)

Scripts for GitHub Actions workflows and continuous integration.

| Script                        | Purpose                                       | Usage                                                     |
| ----------------------------- | --------------------------------------------- | --------------------------------------------------------- |
| `ci-extract-coverage.sh`      | Extract coverage percentage from coverage.xml | `./scripts/ci/ci-extract-coverage.sh`                     |
| `ci-lintro.sh`                | Run Lintro analysis in Docker for CI          | `./scripts/ci/ci-lintro.sh`                               |
| `ci-post-pr-comment.sh`       | Post comments to PRs using GitHub API         | `./scripts/ci/ci-post-pr-comment.sh [file]`               |
| `ci-pr-comment.sh`            | Generate PR comments with Lintro results      | `./scripts/ci/ci-pr-comment.sh`                           |
| `coverage-badge-update.sh`    | Generate and update coverage badge            | `./scripts/ci/coverage-badge-update.sh`                   |
| `coverage-pr-comment.sh`      | Generate PR comments with coverage info       | `./scripts/ci/coverage-pr-comment.sh`                     |
| `lintro-report-generate.sh`   | Generate comprehensive Lintro reports         | `./scripts/ci/lintro-report-generate.sh`                  |
| `pages-deploy.sh`             | Deploy coverage reports to GitHub Pages       | `./scripts/ci/pages-deploy.sh`                            |
| `auto-tag-read-version.sh`    | Read version from pyproject to GITHUB_OUTPUT  | `./scripts/ci/auto-tag-read-version.sh`                   |
| `auto-tag-detect-previous.sh` | Get previous version from HEAD^ pyproject     | `./scripts/ci/auto-tag-detect-previous.sh`                |
| `auto-tag-create-push-tag.sh` | Create and push annotated git tag             | `./scripts/ci/auto-tag-create-push-tag.sh`                |
| `ci-auto-fix.sh`              | Auto-format via Docker and push changes       | `./scripts/ci/ci-auto-fix.sh`                             |
| `pypi-version-exists.sh`      | Check if version exists on PyPI               | `./scripts/ci/pypi-version-exists.sh <project> <version>` |

### 🐳 Docker Scripts (`docker/`)

Scripts for containerized development and testing.

| Script                   | Purpose                         | Usage                                     |
| ------------------------ | ------------------------------- | ----------------------------------------- |
| `docker-build-test.sh`   | Build and test Docker image     | `./scripts/docker/docker-build-test.sh`   |
| `docker-lintro.sh`       | Run Lintro in Docker container  | `./scripts/docker/docker-lintro.sh check` |
| `docker-simple-tests.sh` | Run simplified Docker tests     | `./scripts/docker/docker-test.sh`         |
| `docker-test.sh`         | Run integration tests in Docker | `./scripts/docker/docker-test.sh`         |

### 💻 Local Development Scripts (`local/`)

Scripts for local development and testing.

| Script            | Purpose                      | Usage                                   |
| ----------------- | ---------------------------- | --------------------------------------- |
| `local-lintro.sh` | Enhanced local Lintro runner | `./scripts/local/local-lintro.sh check` |

Notes:

- Most scripts support `--help` for usage.
- `local-lintro.sh` supports `--install` to install missing tools and `--yes` for non-interactive acceptance.
- Set `COVERAGE_DEBUG=1` to enable verbose output in `extract-coverage.py`.
  | `local-test.sh` | Local test runner stub | `./scripts/local/local-test.sh --help` |
  | `run-tests.sh` | Universal test runner (local + Docker) | `./scripts/local/run-tests.sh` |
  | `normalize-ascii-art.sh` | Normalize ASCII art to fixed size | `./scripts/local/normalize-ascii-art.sh` |
  | `update-coverage-badge.sh` | Update coverage badge from coverage.xml | `./scripts/local/update-coverage-badge.sh` |

### 🛠️ Utility Scripts (`utils/`)

Shared utilities and helper scripts.

| Script                               | Purpose                                           | Usage                                                     |
| ------------------------------------ | ------------------------------------------------- | --------------------------------------------------------- |
| `check-pypi-version.py`              | Check if version exists on PyPI                   | `python scripts/utils/check-pypi-version.py <version>`    |
| `create-release.py`                  | Create GitHub release with assets                 | `python scripts/utils/create-release.py <version>`        |
| `delete-previous-lintro-comments.py` | Delete old PR comments                            | `python scripts/utils/delete-previous-lintro-comments.py` |
| `determine-release.py`               | Determine next release version from commits       | `python scripts/utils/determine-release.py`               |
| `extract-coverage.py`                | Extract coverage from XML files                   | `python scripts/utils/extract-coverage.py`                |
| `extract-version.py`                 | Print `version=X.Y.Z` from TOML                   | `python scripts/utils/extract-version.py`                 |
| `install-tools.sh`                   | Install external tools (hadolint, prettier, etc.) | `./scripts/utils/install-tools.sh --local`                |
| `install.sh`                         | Install Lintro with dependencies                  | `./scripts/utils/install.sh`                              |
| `update-version.py`                  | Update version in pyproject.toml                  | `python scripts/utils/update-version.py <version>`        |
| `utils.sh`                           | Shared utilities for other scripts                | Sourced by other scripts                                  |
| `bootstrap-env.sh`                   | Bootstrap CI env with uv and tools                | `./scripts/utils/bootstrap-env.sh --help`                 |

## 🔍 Detailed Script Documentation

### CI/CD Scripts

#### `ci-lintro.sh`

Runs Lintro analysis in Docker for CI pipeline.

**Features:**

- Runs Lintro in Docker container
- Excludes test files via `.lintro-ignore`
- Generates GitHub Actions summaries
- Stores exit code for PR comment step

**Usage:**

```bash
./scripts/ci/ci-lintro.sh
```

#### `coverage-badge-update.sh`

Generates and updates the coverage badge with color coding.

**Features:**

- Extracts coverage percentage from coverage.xml
- Generates SVG badge with color coding (green ≥80%, yellow ≥60%, red <60%)
- Commits and pushes badge updates in CI
- Creates default badge if no coverage data

**Usage:**

```bash
./scripts/ci/coverage-badge-update.sh
```

### Docker Scripts

#### `docker-lintro.sh`

Run Lintro in a Docker container without installing dependencies locally.

**Features:**

- Builds Docker image if not exists
- Mounts current directory to container
- Handles permission issues
- Delegates to local-lintro.sh inside container

**Usage:**

```bash
# Basic check
./scripts/docker/docker-lintro.sh check

# With specific tools
./scripts/docker/docker-lintro.sh check --tools ruff,prettier

# Format code
./scripts/docker/docker-lintro.sh format --tools ruff
```

#### `docker-test.sh`

Run integration tests in Docker container with all tools pre-installed.

**Features:**

- Uses Docker Compose for test environment
- All tools pre-installed in container
- Delegates to run-tests.sh inside container
- Provides clear success/failure output

**Usage:**

```bash
./scripts/docker/docker-test.sh
```

### Local Development Scripts

#### `local-lintro.sh`

Enhanced local Lintro runner with automatic tool installation.

**Features:**

- Automatically sets up Python environment with uv
- Checks for missing tools and offers installation
- Works in both local and Docker environments
- Provides helpful error messages and tips

**Usage:**

```bash
# Basic usage
./scripts/local/local-lintro.sh check

# Install missing tools first
./scripts/local/local-lintro.sh --install check

# Format code
./scripts/local/local-lintro.sh format --tools ruff
```

#### `run-tests.sh`

Universal test runner that works both locally and in Docker.

**Features:**

- Automatically sets up Python environment
- Runs all tests with coverage reporting
- Generates HTML, XML, and terminal coverage reports
- Handles Docker environment differences
- Copies coverage files to host directory in Docker

**Usage:**

```bash
# Run tests
./scripts/local/run-tests.sh

# Verbose output
./scripts/local/run-tests.sh --verbose
```

#### `update-coverage-badge.sh`

Updates the coverage badge based on current coverage.xml file.

**Features:**

- Extracts coverage percentage from coverage.xml
- Generates SVG badge with appropriate color coding
- Updates assets/images/coverage-badge.svg file locally
- Provides helpful error messages if coverage.xml missing

**Usage:**

```bash
# Update badge from existing coverage.xml
./scripts/local/update-coverage-badge.sh

# Run tests then update badge
./scripts/local/run-tests.sh && ./scripts/local/update-coverage-badge.sh
```

### Utility Scripts

#### `install-tools.sh`

Installs all external tools required by Lintro.

**Features:**

- Installs hadolint, prettier, ruff, yamllint, darglint
- Supports local and Docker installation modes
- Uses consistent installation methods
- Verifies installations

**Usage:**

```bash
# Local installation
./scripts/utils/install-tools.sh --local

# Docker installation
./scripts/utils/install-tools.sh --docker
```

#### `utils.sh`

Shared utilities used by multiple scripts.

**Features:**

- Common logging functions (log_info, log_success, etc.)
- PR comment generation
- Coverage status determination
- File/directory checking utilities
- Common environment variables

**Usage:**

```bash
# Source in other scripts
source "$(dirname "$0")/utils.sh"
```

## 🔧 Script Dependencies

### System Requirements

- **Bash**: All shell scripts require bash
- **Python 3.13+**: For Python utility scripts
- **Docker**: For Docker-related scripts
- **uv**: Python package manager

### External Tools (installed by `install-tools.sh`)

- **hadolint**: Docker linting
- **prettier**: JavaScript/JSON formatting
- **ruff**: Python linting and formatting
- **yamllint**: YAML linting
- **darglint**: Python docstring validation

### GitHub Actions Requirements

- **GITHUB_TOKEN**: For PR comment scripts
- **GITHUB_REPOSITORY**: Repository information
- **GITHUB_RUN_ID**: Workflow run ID

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**

```bash
chmod +x scripts/**/*.sh
```

2. **Missing Tools**

```bash
./scripts/utils/install-tools.sh --local
```

3. **Docker Not Running**

```bash
# Start Docker Desktop or Docker daemon
docker info
```

4. **Python Environment Issues**

```bash
# Reinstall with uv
uv sync --dev
```

### Getting Help

- **Script Help**: Most scripts support `--help` flag
- **Verbose Output**: Use `--verbose` flag for detailed output
- **Debug Mode**: Set `VERBOSE=1` environment variable

## 📝 Contributing

When adding new scripts:

1. **Place in appropriate subdirectory**
2. **Add help documentation** with `--help` flag
3. **Use shared utilities** from `utils.sh`
4. **Add to this README** with purpose and usage
5. **Test in both local and Docker environments**

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Getting Started](../docs/getting-started.md) - Installation guide
- [Docker Usage](../docs/docker.md) - Docker documentation
- [GitHub Integration](../docs/github-integration.md) - CI/CD setup
