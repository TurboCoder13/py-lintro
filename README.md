# Lintro

<!-- markdownlint-disable MD033 MD013 -->
<img src="https://raw.githubusercontent.com/TurboCoder13/py-lintro/main/assets/images/lintro.png" alt="Lintro Logo" style="width:100%;max-width:800px;height:auto;display:block;margin:0 auto 24px auto;">
<!-- markdownlint-enable MD033 MD013 -->

A comprehensive CLI tool that unifies various code formatting, linting, and quality
assurance tools under a single command-line interface.

<!-- Badges: Build & Quality -->

[![Tests](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/test-and-coverage.yml?label=tests&branch=main&logo=githubactions&logoColor=white)](https://github.com/TurboCoder13/py-lintro/actions/workflows/test-and-coverage.yml?query=branch%3Amain)
[![CI](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/ci-lintro-analysis.yml?label=ci&branch=main&logo=githubactions&logoColor=white)](https://github.com/TurboCoder13/py-lintro/actions/workflows/ci-lintro-analysis.yml?query=branch%3Amain)
[![Docker](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/docker-build-publish.yml?label=docker&logo=docker&branch=main)](https://github.com/TurboCoder13/py-lintro/actions/workflows/docker-build-publish.yml?query=branch%3Amain)
[![Coverage](https://codecov.io/gh/TurboCoder13/py-lintro/branch/main/graph/badge.svg)](https://codecov.io/gh/TurboCoder13/py-lintro)

<!-- Badges: Releases -->

[![Release](https://img.shields.io/github/v/release/TurboCoder13/py-lintro?label=release)](https://github.com/TurboCoder13/py-lintro/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/lintro?label=pypi)](https://pypi.org/project/lintro/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<!-- Badges: Security & Supply Chain -->

[![CodeQL](https://github.com/TurboCoder13/py-lintro/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/TurboCoder13/py-lintro/actions/workflows/codeql.yml?query=branch%3Amain)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/TurboCoder13/py-lintro/badge)](https://scorecard.dev/viewer/?uri=github.com/TurboCoder13/py-lintro)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/11142/badge)](https://www.bestpractices.dev/projects/11142)
[![SBOM](https://img.shields.io/badge/SBOM-CycloneDX-brightgreen)](docs/security/assurance.md)
[![SBOM Status](https://img.shields.io/github/actions/workflow/status/TurboCoder13/py-lintro/sbom-on-main.yml?label=sbom&branch=main)](https://github.com/TurboCoder13/py-lintro/actions/workflows/sbom-on-main.yml?query=branch%3Amain)

## 🚀 Quick Start

```bash
pip install lintro          # Install
lintro check .              # Find issues
lintro format .             # Fix issues
lintro check --output-format grid   # Beautiful output
```

<!-- TODO: Add screenshot of grid output -->

## ✨ Why Lintro?

- **🎯 Unified Interface** - One command for all your linting and formatting tools
- **📊 Consistent Output** - Beautiful, standardized output formats across all tools
- **🔧 Auto-fixing** - Automatically fix issues where possible
- **🐳 Docker Ready** - Run in isolated containers for consistent environments
- **📈 Rich Reporting** - Multiple formats: grid, JSON, HTML, CSV, Markdown
- **⚡ Fast** - Optimized parallel execution

## 🔌 Works With Your Existing Configs

Lintro respects your native tool configurations. If you have a `.prettierrc`,
`pyproject.toml [tool.ruff]`, or `.yamllint`, Lintro uses them automatically - no
migration required.

- **Native configs are detected** - Your existing `.prettierrc`, `.eslintrc`, etc. work
  as-is
- **Enforce settings override consistently** - Set `line_length: 88` once, applied
  everywhere
- **Fallback defaults when needed** - Tools without native configs use sensible defaults

See the [Configuration Guide](docs/configuration.md) for details on the 4-tier config
system.

## 🛠️ Supported Tools

<!-- markdownlint-disable MD013 MD060 -->

| Tool                                                                                                                                                          | Language               | Auto-fix |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------- |
| [![Ruff](https://img.shields.io/badge/Ruff-lint%2Bformat-000?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)                                   | 🐍 Python              | ✅       |
| [![Black](https://img.shields.io/badge/Black-format-000000?logo=python&logoColor=white)](https://github.com/psf/black)                                        | 🐍 Python              | ✅       |
| [![Mypy](https://img.shields.io/badge/Mypy-type%20checking-2d50a5?logo=python&logoColor=white)](https://mypy-lang.org/)                                       | 🐍 Python              | -        |
| [![Bandit](https://img.shields.io/badge/Bandit-security-yellow?logo=python&logoColor=white)](https://github.com/PyCQA/bandit)                                 | 🐍 Python              | -        |
| [![Semgrep](https://img.shields.io/badge/Semgrep-security-5b21b6?logo=semgrep&logoColor=white)](https://semgrep.dev/)                                         | 🔒 Multi-language      | -        |
| [![Gitleaks](https://img.shields.io/badge/Gitleaks-secrets-dc2626?logo=git&logoColor=white)](https://gitleaks.io/)                                            | 🔐 Secret Detection    | -        |
| [![Prettier](https://img.shields.io/badge/Prettier-format-1a2b34?logo=prettier&logoColor=white)](https://prettier.io/)                                        | 🟨 JS/TS · 🧾 JSON     | ✅       |
| [![Biome](https://img.shields.io/badge/Biome-lint-60A5FA?logo=biome&logoColor=white)](https://biomejs.dev/)                                                   | 🟨 JS/TS · 🧾 JSON/CSS | ✅       |
| [![Yamllint](https://img.shields.io/badge/Yamllint-lint-cb171e?logo=yaml&logoColor=white)](https://github.com/adrienverge/yamllint)                           | 🧾 YAML                | -        |
| [![Hadolint](https://img.shields.io/badge/Hadolint-lint-2496ED?logo=docker&logoColor=white)](https://github.com/hadolint/hadolint)                            | 🐳 Dockerfile          | -        |
| [![Actionlint](https://img.shields.io/badge/Actionlint-lint-24292e?logo=github&logoColor=white)](https://github.com/rhysd/actionlint)                         | ⚙️ GitHub Actions      | -        |
| [![ShellCheck](https://img.shields.io/badge/ShellCheck-lint-4EAA25?logo=gnubash&logoColor=white)](https://www.shellcheck.net/)                                | 🐚 Shell Scripts       | -        |
| [![shfmt](https://img.shields.io/badge/shfmt-format-4EAA25?logo=gnubash&logoColor=white)](https://github.com/mvdan/sh)                                        | 🐚 Shell Scripts       | ✅       |
| [![SQLFluff](https://img.shields.io/badge/SQLFluff-lint%2Bformat-4b5563?logo=database&logoColor=white)](https://sqlfluff.com/)                                | 🗃️ SQL                 | ✅       |
| [![Taplo](https://img.shields.io/badge/Taplo-lint%2Bformat-9b4dca?logo=toml&logoColor=white)](https://taplo.tamasfe.dev/)                                     | 🧾 TOML                | ✅       |
| [![Markdownlint](https://img.shields.io/badge/Markdownlint--cli2-lint-000000?logo=markdown&logoColor=white)](https://github.com/DavidAnson/markdownlint-cli2) | 📝 Markdown            | -        |
| [![Clippy](https://img.shields.io/badge/Clippy-lint-000000?logo=rust&logoColor=white)](https://github.com/rust-lang/rust-clippy)                              | 🦀 Rust                | ✅       |
| [![pydoclint](https://img.shields.io/badge/pydoclint-docstrings-3776AB?logo=python&logoColor=white)](https://github.com/jsh9/pydoclint)               | 🐍 Python              | -        |

<!-- markdownlint-enable MD013 MD060 -->

## 📋 Requirements

### Python Version

**Python 3.11+** is required. Lintro uses modern Python features not available in older
versions.

### Bundled Tools

These Python tools are automatically installed with Lintro:

- **Ruff** - Fast Python linter and formatter
- **Black** - Python code formatter
- **Bandit** - Python security linter
- **Mypy** - Python static type checker
- **Yamllint** - YAML linter
- **pydoclint** - Python docstring linter

### Optional External Tools

For full functionality, install these additional tools:

- **Prettier** - `npm install -g prettier`
- **Markdownlint-cli2** - `npm install -g markdownlint-cli2`
- **Hadolint** - [GitHub Releases](https://github.com/hadolint/hadolint/releases)
- **Actionlint** - [GitHub Releases](https://github.com/rhysd/actionlint/releases)
- **Semgrep** - `pipx install semgrep`, `pip install semgrep`, or `brew install semgrep`
- **Gitleaks** - `brew install gitleaks` or
  [GitHub Releases](https://github.com/gitleaks/gitleaks/releases)
- **ShellCheck** - `brew install shellcheck` or
  [GitHub Releases](https://github.com/koalaman/shellcheck/releases)
- **shfmt** - `brew install shfmt` or
  [GitHub Releases](https://github.com/mvdan/sh/releases)
- **SQLFluff** - `pip install sqlfluff`
- **Taplo** - `brew install taplo` or
  [GitHub Releases](https://github.com/tamasfe/taplo/releases)

Check all tool versions with: `lintro list-tools`

## 📦 Installation

```bash
# PyPI (recommended)
pip install lintro

# Homebrew (macOS binary)
brew tap TurboCoder13/tap && brew install lintro-bin

# Docker (includes all tools)
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check
```

See [Getting Started](docs/getting-started.md) for detailed installation options.

## 💻 Usage

```bash
# Check all files
lintro check .

# Auto-fix issues
lintro format .

# Grid output with grouping
lintro check --output-format grid --group-by file

# Run specific tools
lintro check --tools ruff,prettier,mypy

# Exclude directories
lintro check --exclude "node_modules,dist,venv"

# List available tools
lintro list-tools
```

### 🐳 Docker

```bash
# Run from GHCR
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check

# With formatting
docker run --rm -v $(pwd):/code ghcr.io/turbocoder13/py-lintro:latest check --output-format grid
```

## 📚 Documentation

| Guide                                            | Description                             |
| ------------------------------------------------ | --------------------------------------- |
| [Getting Started](docs/getting-started.md)       | Installation, first steps, requirements |
| [Configuration](docs/configuration.md)           | Tool configuration, options, presets    |
| [Docker Usage](docs/docker.md)                   | Containerized development               |
| [GitHub Integration](docs/github-integration.md) | CI/CD setup, workflows                  |
| [Contributing](docs/contributing.md)             | Development guide, adding tools         |
| [Troubleshooting](docs/troubleshooting.md)       | Common issues and solutions             |

**Advanced:** [Tool Analysis](docs/tool-analysis/) | [Architecture](docs/architecture/)
| [Security](docs/security/)

## 🔨 Development

```bash
# Clone and install
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro
uv sync --dev

# Run tests
./scripts/local/run-tests.sh

# Run lintro on itself
./scripts/local/local-lintro.sh check --output-format grid
```

## 🤝 Community

- 🐛
  [Bug Reports](https://github.com/TurboCoder13/py-lintro/issues/new?template=bug_report.md)
- 💡
  [Feature Requests](https://github.com/TurboCoder13/py-lintro/issues/new?template=feature_request.md)
- ❓
  [Questions](https://github.com/TurboCoder13/py-lintro/issues/new?template=question.md)
- 📖 [Contributing Guide](docs/contributing.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
