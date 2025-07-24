# Lintro Self-Use: Eating Our Own Dog Food 🐕

This document explains how the Lintro project uses Lintro itself for code quality assurance. This demonstrates the tool's capabilities and ensures we maintain high code standards.

## 🎯 Philosophy

We believe in **"eating our own dog food"** - using Lintro on the Lintro codebase to:

- Validate the tool works correctly in real-world scenarios
- Maintain consistent code quality across the project
- Showcase Lintro's capabilities to users
- Catch issues early in development

## 🔧 Tools Used on This Project

Lintro runs multiple specialized tools on different file types:

### 🐍 Python Files (`lintro/`, `tests/`)

- **Ruff**: Fast Python linter and formatter
  - Checks import order, unused variables, code style
  - Auto-fixes many issues when possible
- **Darglint**: Validates Python docstring completeness
  - Ensures all functions have proper documentation
  - Checks docstring format consistency

### 📄 YAML Files (`.github/`, configs)

- **Yamllint**: YAML syntax and style validation
  - Ensures proper indentation and structure
  - Catches common YAML errors

### 🟨 JavaScript/JSON Files

- **Prettier**: Code formatting for JS/JSON
  - Formats `package.json`, `renovate.json`
  - Ensures consistent JSON structure

### 🐳 Docker Files (when present)

- **Hadolint**: Dockerfile best practices
  - Security and optimization recommendations
  - Multi-stage build validation

## 🚀 GitHub Actions Integration

### 1. Quality-First Pipeline

Our CI pipeline runs Lintro **before** tests to catch quality issues early:

```yaml
jobs:
  quality-check: # 🔍 Lintro runs first
    name: 🔍 Code Quality (Lintro)
    steps:
      - run: uv run lintro check lintro/ tests/ --tools ruff,darglint

  test-coverage: # 🧪 Tests run after quality passes
    needs: quality-check
    name: 🧪 Tests & Coverage
```

### 2. Multi-Tool Analysis

Different tools for different file types:

```bash
# Python code quality
uv run lintro check lintro/ tests/ --tools ruff,darglint

# YAML validation
uv run lintro check .github/ --tools yamllint

# JSON formatting
uv run lintro check *.json --tools prettier
```

### 3. Auto-fixing

Lintro can automatically fix many issues:

```bash
# Auto-fix Python formatting issues
uv run lintro fmt lintro/ tests/ --tools ruff
```

## 📊 Current Quality Status

As of the latest run:

- **31 Python issues** detected by Ruff (mostly unused imports)
- **Auto-fixable**: Most issues can be resolved automatically
- **Docstring coverage**: Validated by Darglint
- **YAML/JSON**: Well-formatted and valid

## 🔍 Local Development

Run the same checks locally during development:

```bash
# Check all Python files
uv run lintro check lintro/ tests/ --tools ruff,darglint

# Auto-fix issues
uv run lintro fmt lintro/ tests/ --tools ruff

# Check specific file types
uv run lintro check .github/ --tools yamllint
uv run lintro check package.json --tools prettier

# List all available tools
uv run lintro list-tools
```

## 🎨 Output Formats

Lintro provides multiple output formats for different use cases:

```bash
# Grid format (default) - nice tables
uv run lintro check lintro/

# Plain format - CI-friendly
uv run lintro check lintro/ --output-format plain

# JSON format - for tooling integration
uv run lintro check lintro/ --output-format json

# Markdown format - for documentation
uv run lintro check lintro/ --output-format markdown
```
