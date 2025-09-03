# Configuration Guide

This guide covers all configuration options for Lintro and the underlying tools it integrates. Learn how to customize behavior, set tool-specific options, and optimize Lintro for your project.

## Lintro Configuration

### Command-Line Options

#### Global Options

```bash
# Output options
lintro check                  # Use grid formatting
lintro check --output results.txt            # Save output to file
lintro check --group-by [file|code|none|auto] # Group issues

# Tool selection
lintro check --tools ruff,prettier           # Run specific tools only
lintro check --all                           # Run all available tools

# File filtering
lintro check --exclude "*.pyc,venv"          # Exclude patterns
lintro check --include-venv                  # Include virtual environments
lintro check path/to/files                   # Check specific paths
```

#### Tool-Specific Options

```bash
# Tool-specific options (key=value; lists use |)
lintro check --tool-options "ruff:line_length=88,prettier:print_width=80"

# Example with lists and booleans
lintro check --tool-options "ruff:select=E|F|W,ruff:preview=True"

# Exclude patterns
lintro check --exclude "*.pyc,venv,node_modules"
```

### Environment Variables

```bash
# Override default settings
export LINTRO_DEFAULT_TIMEOUT=60
export LINTRO_VERBOSE=1

# Default exclude patterns
export LINTRO_EXCLUDE="*.pyc,venv,node_modules"

# Default output format
export LINTRO_DEFAULT_FORMAT="grid"
```

## Tool Configuration

Lintro respects each tool's native configuration files, allowing you to leverage existing setups.

### Lintro Project Config

You can set Lintro-level defaults in `pyproject.toml` under `[tool.lintro]`.
CLI `--tool-options` override file-based config.

Example enabling Ruff formatter by default and controlling fix stages during
`lintro format`:

```toml
[tool.lintro.ruff]
format = true      # run `ruff format` during fmt (default true)
lint_fix = true    # run `ruff check --fix` during fmt (default true)
```

### Post-checks Configuration

Black is integrated as a post-check tool by default. Post-checks run after the
main tools complete and can be configured to enforce failure if issues are
found. This avoids double-formatting with Ruff and keeps formatting decisions
explicit.

```toml
[tool.lintro.post_checks]
enabled = true
tools = ["black"]        # Black runs after core tools
enforce_failure = true   # Fail the run if Black finds issues in check mode
```

Notes:

- With post-checks enabled for Black, Ruff’s `format`/`format_check` stages can
  be disabled or overridden via CLI when desired.
- In `lintro check`, Black runs with `--check` and contributes to failure when
  `enforce_failure` is true. In `lintro format`, Black formats files in the
  post-check phase.

### Python Tools

#### Ruff Configuration

**File:** `pyproject.toml`

```toml
[tool.ruff]
# Basic configuration
line-length = 88
target-version = "py313"
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pypackages__",
    "migrations",
]

# Rule selection
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "D",   # pydocstyle
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

ignore = [
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
]

# Per-file ignores
[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["D100", "D103"]
"__init__.py" = ["F401"]

# Import sorting
[tool.ruff.isort]
known-first-party = ["lintro"]
force-single-line = true

# Docstring configuration
[tool.ruff.pydocstyle]
convention = "google"
```

**Alternative:** `setup.cfg`

```ini
[tool:ruff]
line-length = 88
select = E,W,F,I,N,D
exclude = .git,__pycache__,.venv
```

#### Bandit Configuration

**File:** `pyproject.toml`

```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".git"]
tests = ["B101,B102,B103"]  # Specific test IDs to run
skips = ["B101"]            # Test IDs to skip
confidence = "MEDIUM"       # Minimum confidence level
severity = "LOW"           # Minimum severity level

[tool.bandit.assert_used]
exclude = ["test_*.py"]     # Files to exclude from assert_used test
```

**File:** `.bandit`

```ini
[bandit]
exclude = tests,venv,.git
tests = B101,B102,B103
skips = B101
confidence = MEDIUM
severity = LOW

[[tool.bandit.assert_used]]
exclude = test_*.py
```

**Available Options:**

- `tests`: Comma-separated list of test IDs to run
- `skips`: Comma-separated list of test IDs to skip
- `exclude`: Comma-separated list of paths to exclude
- `exclude_dirs`: List of directories to exclude (pyproject.toml only)
- `severity`: Minimum severity level (`LOW`, `MEDIUM`, `HIGH`)
- `confidence`: Minimum confidence level (`LOW`, `MEDIUM`, `HIGH`)
- `baseline`: Path to baseline report for comparison

#### Darglint Configuration

**File:** `.darglint`

```ini
[darglint]
docstring_style = google
strictness = full
ignore_regex = ^_(.*)|^test_(.*)
ignore = DAR101,DAR201
enable = DAR104
```

**File:** `pyproject.toml`

```toml
[tool.darglint]
docstring_style = "google"
strictness = "full"
enable = "DAR104"
ignore = "DAR101,DAR201"
ignore_regex = "^_(.*)"
```

**File:** `setup.cfg`

```ini
[darglint]
docstring_style = google
strictness = full
```

**Available Options:**

- `docstring_style`: `google`, `sphinx`, `numpy`
- `strictness`: `short`, `long`, `full`
- `ignore`: Comma-separated error codes
- `enable`: Enable specific checks
- `ignore_regex`: Regex pattern for ignoring functions

### Frontend Tools

#### Prettier Configuration

**File:** `.prettierrc`

```json
{
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "quoteProps": "as-needed",
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "printWidth": 80,
  "endOfLine": "lf"
}
```

**File:** `prettier.config.js`

```javascript
module.exports = {
  tabWidth: 2,
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  bracketSpacing: true,
  arrowParens: 'avoid',
  printWidth: 80,

  // Override for specific file types
  overrides: [
    {
      files: '*.json',
      options: {
        tabWidth: 4,
      },
    },
    {
      files: '*.md',
      options: {
        printWidth: 120,
        proseWrap: 'always',
      },
    },
  ],
};
```

**File:** `package.json`

```json
{
  "prettier": {
    "tabWidth": 2,
    "semi": true,
    "singleQuote": true
  }
}
```

**Ignore Files:** `.prettierignore`

```
node_modules/
dist/
build/
coverage/
*.min.js
*.min.css
```

### YAML Tools

#### Yamllint Configuration

**File:** `.yamllint`

```yaml
extends: default

rules:
  # Line length
  line-length:
    max: 120
    level: warning

  # Indentation
  indentation:
    spaces: 2
    indent-sequences: true
    check-multi-line-strings: false

  # Comments
  comments:
    min-spaces-from-content: 2

  # Document start
  document-start:
    present: false

  # Truthy values
  truthy:
    allowed-values: ['true', 'false']
    check-keys: true
```

**File:** `pyproject.toml`

```toml
[tool.yamllint]
extends = "default"

[tool.yamllint.rules.line-length]
max = 120

[tool.yamllint.rules.indentation]
spaces = 2
```

### Infrastructure Tools

#### Hadolint Configuration

**File:** `.hadolint.yaml`

```yaml
ignored:
  - DL3008 # Pin versions in apt-get install
  - DL3009 # Delete apt-get lists
  - DL3015 # Avoid additional packages

trustedRegistries:
  - docker.io
  - gcr.io

allowedRegistries:
  - docker.io
  - gcr.io
  - quay.io
```

**Inline ignoring:**

```dockerfile
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip
```

#### Actionlint Configuration

Actionlint validates GitHub Actions workflows. Lintro discovers workflow files
under `/.github/workflows/` when you run `lintro check .` and invokes the
`actionlint` binary.

- Discovery: YAML files filtered to those in `/.github/workflows/`
- Defaults: Lintro does not pass special flags; native actionlint defaults are used
- Local install: use `scripts/utils/install-tools.sh --local` to place `actionlint` on PATH
- Docker/CI: the Docker image installs `actionlint` during build, so CI tests run it

```bash
# Validate workflows only
lintro check --tools actionlint

# Validate workflows along with other tools
lintro check --tools ruff,actionlint
```

## Project-Specific Configuration

### Multi-Language Projects

For projects with multiple languages, organize configuration by component:

```
project/
├── .lintro.toml              # Lintro-specific config
├── pyproject.toml            # Python tools
├── .prettierrc               # JavaScript/CSS
├── .yamllint                 # YAML files
├── .hadolint.yaml           # Docker files
├── frontend/
│   └── .prettierrc          # Frontend-specific overrides
└── backend/
    └── pyproject.toml       # Backend-specific overrides
```

### Lintro Project Configuration

**File:** `.lintro.toml` (future feature)

```toml
[lintro]
default_tools = ["ruff", "darglint", "prettier", "yamllint"]
table_format = true
group_by = "auto"
exclude_patterns = ["migrations", "node_modules", "dist"]

[lintro.timeouts]
default = 30
darglint = 45
prettier = 60

[lintro.paths]
python = ["src/", "tests/"]
javascript = ["frontend/", "assets/"]
yaml = [".github/", "config/"]
docker = ["Dockerfile*", "docker/"]

[lintro.output]
format = "table"
save_to_file = true
file_prefix = "lintro-report"
```

### Output System: Auto-Generated Reports

Lintro now generates all output formats for every run in a timestamped directory under `.lintro/` (e.g., `.lintro/run-20240722-153000/`).

You do not need to specify output format or file options. Each run produces:

- `console.log`: The full console output
- `results.json`: Machine-readable results
- `report.md`: Human-readable Markdown report
- `report.html`: Web-viewable HTML report
- `summary.csv`: Spreadsheet-friendly summary

This ensures you always have every format available for your workflow, CI, or reporting needs.

## Advanced Configuration

### Tool Conflicts and Priorities

Some tools may conflict with each other. Lintro handles this by:

1. **Priority system** - Higher priority tools run first
2. **Conflict detection** - Warns about conflicting tools
3. **Auto-resolution** - Chooses the best tool for each task

```bash
# Check for conflicts
lintro list-tools --show-conflicts

# Force conflicting tools to run
lintro check --tools ruff,black --ignore-conflicts
```

### Performance Optimization

#### Large Codebases

```bash
# Use specific tools for faster checks
lintro check --tools ruff

# Process directories separately
lintro check src/ --tools ruff,darglint
lintro check tests/ --tools ruff

# Exclude heavy directories
lintro check --exclude "venv,node_modules,migrations"
```

#### CI/CD Optimization

```bash
# Fast checks for PR validation
lintro check --tools ruff

# Full analysis for main branch
lintro check --all --output full-report.txt
```

### Custom Output Formats

#### JSON Output (planned)

```bash
lintro check --output-format json --output results.json
```

```json
{
  "summary": {
    "total_issues": 15,
    "tools_run": ["ruff", "darglint"],
    "files_checked": 42
  },
  "issues": [
    {
      "file": "src/main.py",
      "line": 12,
      "column": 5,
      "tool": "ruff",
      "code": "F401",
      "message": "'os' imported but unused",
      "severity": "error"
    }
  ]
}
```

#### Markdown Output (planned)

```bash
lintro check --output-format markdown --output QUALITY_REPORT.md
```

## Integration Patterns

### Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: lintro-check
        name: Lintro Quality Check
        entry: lintro check --output-format grid
        language: system
        pass_filenames: false
        stages: [commit]

      - id: lintro-fix
        name: Lintro Auto-fix
        entry: lintro format --output-format grid
        language: system
        pass_filenames: false
        stages: [commit]
```

### Makefile Integration

```makefile
.PHONY: lint fix check quality install-tools

# Quality checks
lint:
	lintro check

fix:
	lintro format

check: lint
	@echo "Quality check completed"

# Comprehensive quality report
quality:
	lintro check --all --output quality-report.txt
	@echo "Full quality report saved to quality-report.txt"

# Tool installation
install-tools:
	pip install ruff darglint
	npm install -g prettier
```

### IDE Integration

#### VS Code Settings

**File:** `.vscode/settings.json`

```json
{
  "python.linting.enabled": false,
  "python.formatting.provider": "none",
  "editor.formatOnSave": false,
  "editor.codeActionsOnSave": {
    "source.organizeImports": false
  },
  "files.associations": {
    ".lintro.toml": "toml"
  }
}
```

**File:** `.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Lintro Check",
      "type": "shell",
      "command": "lintro",
      "args": ["check", "--output-format grid"],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      },
      "problemMatcher": []
    },
    {
      "label": "Lintro Fix",
      "type": "shell",
      "command": "lintro",
      "args": ["format", "--output-format grid"],
      "group": "build"
    }
  ]
}
```

## Troubleshooting Configuration

### Common Issues

**1. Tool not respecting configuration:**

```bash
# Check if config file is found
lintro check --tools ruff --verbose

# Verify config file syntax
ruff check --show-settings
```

**2. Conflicting configurations:**

```bash
# Check for multiple config files
find . -name "*.toml" -o -name ".ruff*" -o -name "setup.cfg"

# Use specific config
ruff check --config custom-ruff.toml
```

**3. Performance issues:**

```bash
# Profile tool execution
time lintro check --tools ruff --output-format grid

# Use more specific file patterns
lintro check "src/**/*.py" --tools ruff --output-format grid
```

### Debug Configuration

```bash
# Enable verbose output
lintro check --verbose --output-format grid

# Check tool availability
lintro list-tools

# Test individual tools
ruff check src/
darglint src/main.py
prettier --check package.json
```

This comprehensive configuration guide should help you customize Lintro to fit your project's specific needs and integrate seamlessly into your development workflow!
