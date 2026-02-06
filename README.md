# Lintro

<!-- markdownlint-disable MD033 MD013 -->
<p align="center">
<img src="https://raw.githubusercontent.com/lgtm-hq/py-lintro/main/assets/images/lintro.png" alt="Lintro Logo" style="width:100%;max-width:800px;height:auto;">
</p>

<p align="center">
A comprehensive CLI tool that unifies various code formatting, linting, and quality
assurance tools under a single command-line interface.
</p>

<!-- Badges: Build & Quality -->
<p align="center">
<a href="https://github.com/lgtm-hq/py-lintro/actions/workflows/test-and-coverage.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/lgtm-hq/py-lintro/test-and-coverage.yml?label=tests&branch=main&logo=githubactions&logoColor=white" alt="Tests"></a>
<a href="https://github.com/lgtm-hq/py-lintro/actions/workflows/ci-lintro-analysis.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/lgtm-hq/py-lintro/ci-lintro-analysis.yml?label=ci&branch=main&logo=githubactions&logoColor=white" alt="CI"></a>
<a href="https://github.com/lgtm-hq/py-lintro/actions/workflows/docker-build-publish.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/lgtm-hq/py-lintro/docker-build-publish.yml?label=docker&logo=docker&branch=main" alt="Docker"></a>
<a href="https://codecov.io/gh/lgtm-hq/py-lintro"><img src="https://codecov.io/gh/lgtm-hq/py-lintro/branch/main/graph/badge.svg" alt="Coverage"></a>
</p>

<!-- Badges: Releases -->
<p align="center">
<a href="https://github.com/lgtm-hq/py-lintro/releases/latest"><img src="https://img.shields.io/github/v/release/lgtm-hq/py-lintro?label=release" alt="Release"></a>
<a href="https://pypi.org/project/lintro/"><img src="https://img.shields.io/pypi/v/lintro?label=pypi" alt="PyPI"></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
</p>

<!-- Badges: Security & Supply Chain -->
<p align="center">
<a href="https://github.com/lgtm-hq/py-lintro/actions/workflows/codeql.yml?query=branch%3Amain"><img src="https://github.com/lgtm-hq/py-lintro/actions/workflows/codeql.yml/badge.svg?branch=main" alt="CodeQL"></a>
<a href="https://scorecard.dev/viewer/?uri=github.com/lgtm-hq/py-lintro"><img src="https://img.shields.io/ossf-scorecard/github.com/lgtm-hq/py-lintro?label=openssf%20scorecard" alt="OpenSSF Scorecard"></a>
<a href="https://www.bestpractices.dev/projects/11142"><img src="https://www.bestpractices.dev/projects/11142/badge" alt="OpenSSF Best Practices"></a>
<a href="docs/security/assurance.md"><img src="https://img.shields.io/badge/SBOM-CycloneDX-brightgreen" alt="SBOM"></a>
<a href="https://github.com/lgtm-hq/py-lintro/actions/workflows/sbom-on-main.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/lgtm-hq/py-lintro/sbom-on-main.yml?label=sbom&branch=main" alt="SBOM Status"></a>
</p>
<!-- markdownlint-enable MD033 MD013 -->

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

| Tool                                                                                                                                                          | Language            | Auto-fix |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------- |
| [![Actionlint](https://img.shields.io/badge/Actionlint-lint-24292e?logo=github&logoColor=white)](https://github.com/rhysd/actionlint)                         | ⚙️ GitHub Actions   | -        |
| [![Astro](https://img.shields.io/badge/Astro-type%20check-ff5d01?logo=astro&logoColor=white)](https://astro.build/)                                           | 🚀 Astro            | -        |
| [![Svelte](https://img.shields.io/badge/Svelte-type%20check-ff3e00?logo=svelte&logoColor=white)](https://svelte.dev/)                                         | 🔥 Svelte           | -        |
| [![Bandit](https://img.shields.io/badge/Bandit-security-yellow?logo=python&logoColor=white)](https://github.com/PyCQA/bandit)                                 | 🐍 Python           | -        |
| [![Black](https://img.shields.io/badge/Black-format-000000?logo=python&logoColor=white)](https://github.com/psf/black)                                        | 🐍 Python           | ✅       |
| [![Clippy](https://img.shields.io/badge/Clippy-lint-000000?logo=rust&logoColor=white)](https://github.com/rust-lang/rust-clippy)                              | 🦀 Rust             | ✅       |
| [![Gitleaks](https://img.shields.io/badge/Gitleaks-secrets-dc2626?logo=git&logoColor=white)](https://gitleaks.io/)                                            | 🔐 Secret Detection | -        |
| [![Hadolint](https://img.shields.io/badge/Hadolint-lint-2496ED?logo=docker&logoColor=white)](https://github.com/hadolint/hadolint)                            | 🐳 Dockerfile       | -        |
| [![Markdownlint](https://img.shields.io/badge/Markdownlint--cli2-lint-000000?logo=markdown&logoColor=white)](https://github.com/DavidAnson/markdownlint-cli2) | 📝 Markdown         | -        |
| [![Mypy](https://img.shields.io/badge/Mypy-type%20checking-2d50a5?logo=python&logoColor=white)](https://mypy-lang.org/)                                       | 🐍 Python           | -        |
| [![Oxfmt](https://img.shields.io/badge/Oxfmt-format-e05d44?logo=javascript&logoColor=white)](https://oxc.rs/)                                                 | 🟨 JS/TS            | ✅       |
| [![Oxlint](https://img.shields.io/badge/Oxlint-lint-e05d44?logo=javascript&logoColor=white)](https://oxc.rs/)                                                 | 🟨 JS/TS            | ✅       |
| [![Prettier](https://img.shields.io/badge/Prettier-format-1a2b34?logo=prettier&logoColor=white)](https://prettier.io/)                                        | 🟨 JS/TS · 🧾 JSON  | ✅       |
| [![pydoclint](https://img.shields.io/badge/pydoclint-docstrings-3776AB?logo=python&logoColor=white)](https://github.com/jsh9/pydoclint)                       | 🐍 Python           | -        |
| [![Ruff](https://img.shields.io/badge/Ruff-lint%2Bformat-000?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)                                   | 🐍 Python           | ✅       |
| [![Semgrep](https://img.shields.io/badge/Semgrep-security-5b21b6?logo=semgrep&logoColor=white)](https://semgrep.dev/)                                         | 🔒 Multi-language   | -        |
| [![ShellCheck](https://img.shields.io/badge/ShellCheck-lint-4EAA25?logo=gnubash&logoColor=white)](https://www.shellcheck.net/)                                | 🐚 Shell Scripts    | -        |
| [![shfmt](https://img.shields.io/badge/shfmt-format-4EAA25?logo=gnubash&logoColor=white)](https://github.com/mvdan/sh)                                        | 🐚 Shell Scripts    | ✅       |
| [![SQLFluff](https://img.shields.io/badge/SQLFluff-lint%2Bformat-4b5563?logo=database&logoColor=white)](https://sqlfluff.com/)                                | 🗃️ SQL              | ✅       |
| [![Taplo](https://img.shields.io/badge/Taplo-lint%2Bformat-9b4dca?logo=toml&logoColor=white)](https://taplo.tamasfe.dev/)                                     | 🧾 TOML             | ✅       |
| [![TypeScript](https://img.shields.io/badge/TypeScript-type%20check-3178c6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)                 | 🟨 JS/TS            | -        |
| [![Vue-tsc](https://img.shields.io/badge/Vue--tsc-type%20check-42b883?logo=vuedotjs&logoColor=white)](https://github.com/vuejs/language-tools)                | 💚 Vue              | -        |
| [![Yamllint](https://img.shields.io/badge/Yamllint-lint-cb171e?logo=yaml&logoColor=white)](https://github.com/adrienverge/yamllint)                           | 🧾 YAML             | -        |

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
- **Oxlint** - `bun add -g oxlint` or `npm install -g oxlint`
- **Oxfmt** - `bun add -g oxfmt` or `npm install -g oxfmt`
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
- **TypeScript** - `brew install typescript`, `bun add -g typescript`, or
  `npm install -g typescript`
- **Astro** - `bun add astro` or `npm install astro`
- **Svelte Check** - `bun add -D svelte-check` or `npm install -D svelte-check`
- **Vue-tsc** - `bun add -D vue-tsc` or `npm install -D vue-tsc`

Check all tool versions with: `lintro list-tools`

## 📦 Installation

```bash
# PyPI (recommended)
pip install lintro

# Homebrew (macOS binary)
brew tap lgtm-hq/tap && brew install lintro-bin

# Docker (tools image - includes all external tools)
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:latest check

# Docker (base image - minimal, no external tools)
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:base check
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

# Auto-install Node.js dependencies (useful for TypeScript projects)
lintro check --tools tsc --auto-install

# Exclude directories
lintro check --exclude "node_modules,dist,venv"

# List available tools
lintro list-tools
```

### 🐳 Docker

```bash
# Run from GHCR (tools image - recommended)
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:latest check

# With formatting
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:latest check --output-format grid

# Base image (minimal, no external tools)
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:base check
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
git clone https://github.com/lgtm-hq/py-lintro.git
cd py-lintro
uv sync --dev

# Run tests
./scripts/local/run-tests.sh

# Run lintro on itself
./scripts/local/local-lintro.sh check --output-format grid
```

## 🤝 Community

- 🐛
  [Bug Reports](https://github.com/lgtm-hq/py-lintro/issues/new?template=bug_report.md)
- 💡
  [Feature Requests](https://github.com/lgtm-hq/py-lintro/issues/new?template=feature_request.md)
- ❓ [Questions](https://github.com/lgtm-hq/py-lintro/issues/new?template=question.md)
- 📖 [Contributing Guide](docs/contributing.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
