# Getting Started with Lintro

This guide will help you get up and running with Lintro quickly. Whether you're a new user or looking to integrate Lintro into your project, this guide covers everything you need to know.

## What is Lintro?

Lintro is a unified CLI tool that brings together multiple code quality tools under a single interface. Instead of learning and configuring dozens of different linting and formatting tools, Lintro provides:

- **One command** to rule them all
- **Consistent interface** across all tools
- **Beautiful output** with table formatting
- **Auto-fixing** capabilities where possible
- **Multi-language support** for modern development stacks

## Installation

### Standard Installation

```bash
pip install lintro
```

### Development Installation

If you want to contribute or use the latest features:

```bash
# Clone the repository
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro

# Install with UV (recommended)
uv sync

# Or with pip
pip install -e .
```

### Docker Installation

For containerized environments or if you prefer not to install dependencies locally:

```bash
# Clone and setup
git clone https://github.com/TurboCoder13/py-lintro.git
cd py-lintro
chmod +x docker-lintro.sh

# Use Lintro via Docker
./docker-lintro.sh check --table-format
```

## First Steps

### 1. Verify Installation

```bash
# Check if Lintro is installed
lintro --help

# List available tools
lintro list-tools
```

### 2. Basic Usage

Start with checking your code:

```bash
# Check current directory
lintro check

# Check with better formatting
lintro check --table-format

# Auto-fix issues where possible
lintro fmt --table-format
```

### 3. Understanding the Output

Lintro provides clear, structured output:

```
┌─────────────────────┬──────┬───────┬─────────────────────────────────────┐
│ File                │ Line │ Code  │ Message                             │
├─────────────────────┼──────┼───────┼─────────────────────────────────────┤
│ src/main.py         │   12 │ F401  │ 'os' imported but unused           │
│ src/utils.py        │   25 │ E302  │ expected 2 blank lines             │
│ tests/test_main.py  │    8 │ D100  │ Missing docstring in public module │
└─────────────────────┴──────┴───────┴─────────────────────────────────────┘
```

## Supported Languages and Tools

### Python Projects

```bash
# Check Python files
lintro check src/ tests/ --tools ruff,darglint

# Format Python code
lintro fmt src/ --tools ruff
```

**Tools:**

- **Ruff** - Fast Python linter and formatter
- **Darglint** - Docstring validation

### JavaScript/TypeScript Projects

```bash
# Check and format JS/TS files
lintro check src/ --tools prettier
lintro fmt src/ --tools prettier
```

**Tools:**

- **Prettier** - Code formatter for JS, TS, JSON, CSS, HTML

### YAML Files

```bash
# Check YAML configuration files
lintro check .github/ config/ --tools yamllint
```

**Tools:**

- **Yamllint** - YAML syntax and style validation

### Docker Files

```bash
# Check Dockerfiles
lintro check Dockerfile* --tools hadolint
```

**Tools:**

- **Hadolint** - Dockerfile best practices

### Mixed Projects

```bash
# Check everything at once
lintro check --table-format

# Or be more specific
lintro check src/ --tools ruff,prettier --table-format
```

## Common Workflows

### Daily Development

```bash
# Check your changes before committing
lintro check --table-format

# Auto-fix what can be fixed
lintro fmt --table-format

# Check again to see remaining issues
lintro check --table-format
```

### Project Setup

```bash
# Initial project scan
lintro check --table-format --output initial-scan.txt

# Fix auto-fixable issues
lintro fmt --table-format

# Generate final report
lintro check --table-format --output final-report.txt
```

### CI/CD Integration

```bash
# CI-friendly check (no table formatting)
lintro check --output ci-results.txt

# Exit with error if issues found
lintro check || exit 1
```

## Configuration

### Using Tool Configuration Files

Lintro respects each tool's native configuration:

**Python (Ruff):**

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]
```

**YAML (Yamllint):**

```yaml
# .yamllint
extends: default
rules:
  line-length:
    max: 120
```

**Prettier:**

```json
{
  "tabWidth": 2,
  "semi": true,
  "singleQuote": true
}
```

### Lintro-Specific Options

```bash
# Tool timeouts
lintro check --darglint-timeout 30 --prettier-timeout 60

# Exclude patterns
lintro check --exclude "migrations,node_modules,dist"

# Include virtual environments (not recommended)
lintro check --include-venv

# Group output by error type
lintro check --table-format --group-by code
```

## Tips and Tricks

### 1. Use Table Formatting

Always use `--table-format` for better readability:

```bash
lintro check --table-format
```

### 2. Group by Error Type

When fixing multiple similar issues:

```bash
lintro check --table-format --group-by code
```

### 3. Focus on Specific Tools

For faster checks in large codebases:

```bash
# Only check Python formatting
lintro check --tools ruff --table-format

# Only check documentation
lintro check --tools darglint --table-format
```

### 4. Save Results for Analysis

```bash
# Save detailed report
lintro check --table-format --output quality-report.txt

# Review offline
cat quality-report.txt
```

### 5. Incremental Fixing

Fix issues incrementally by tool type:

```bash
# Fix formatting issues first (auto-fixable)
lintro fmt --tools ruff,prettier --table-format

# Then address linting issues
lintro check --tools darglint,yamllint --table-format
```

## Integration Examples

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: lintro
        name: Lintro Quality Check
        entry: lintro check --table-format
        language: system
        pass_filenames: false
```

### Makefile Integration

```makefile
.PHONY: lint fix check

lint:
	lintro check --table-format

fix:
	lintro fmt --table-format

check: lint
	@echo "Quality check completed"
```

### VS Code Integration

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Lintro Check",
      "type": "shell",
      "command": "lintro",
      "args": ["check", "--table-format"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

**1. Tool not found:**

```bash
# Check which tools are available
lintro list-tools

# Install missing tools
pip install ruff darglint
```

**2. No files to check:**

```bash
# Check file patterns
lintro check --table-format .

# Include specific file types
lintro check --table-format "**/*.py"
```

**3. Too many issues:**

```bash
# Focus on specific tools
lintro check --tools ruff --table-format

# Exclude problematic directories
lintro check --exclude "legacy,migrations" --table-format
```

**4. Permission errors:**

```bash
# Check file permissions
ls -la

# Use sudo if needed (not recommended)
sudo lintro check --table-format
```

### Getting Help

- **Command help:** `lintro --help` or `lintro check --help`
- **List tools:** `lintro list-tools --show-conflicts`
- **GitHub Issues:** Report bugs or request features
- **Documentation:** Check other guides in the `docs/` directory

## Next Steps

Now that you're familiar with the basics:

1. **Explore advanced features** - Check out the [Configuration Guide](configuration.md)
2. **Set up CI/CD** - See the [GitHub Integration Guide](github-integration.md)
3. **Use Docker** - Read the [Docker Usage Guide](docker.md)
4. **Contribute** - Check the [Contributing Guide](contributing.md)
5. **Analyze tools** - Dive into [Tool Analysis](tool-analysis/) for detailed comparisons

Welcome to the Lintro community! 🚀
