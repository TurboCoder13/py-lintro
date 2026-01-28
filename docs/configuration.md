# Configuration Guide

This guide covers all configuration options for Lintro and the underlying tools it
integrates. Learn how to customize behavior, set tool-specific options, and optimize
Lintro for your project.

> **TL;DR**: Lintro uses your existing tool configs (`.prettierrc`, `pyproject.toml`,
> etc.) automatically. It only provides fallback defaults when no native config exists.
> Use `enforce.line_length` to ensure consistent settings across all tools via CLI
> injection.

## Configuration Model: 4-Tier System

Lintro uses a clear 4-tier configuration model that separates concerns:

| Tier          | Purpose                                             | When Applied               |
| ------------- | --------------------------------------------------- | -------------------------- |
| **execution** | What tools run and how                              | Always                     |
| **enforce**   | Cross-cutting settings (line_length, target_python) | Always (via CLI flags)     |
| **defaults**  | Fallback config when no native config exists        | Only when no native config |
| **tools**     | Per-tool enable/disable and config source           | Always                     |

### Key Principles

1. **Native configs are respected by default** - Tools use their own `.prettierrc`,
   `pyproject.toml [tool.ruff]`, etc.
2. **`enforce` settings override via CLI flags** - Line length and target Python are
   injected as CLI arguments to ensure consistency
3. **`defaults` provide fallbacks** - Only used when a tool has no native config file
4. **Simple and transparent** - Users know exactly which config is used

### Tiered Configuration Flow

The configuration system works in a specific order:

1. **Execution Tier** - Determines which tools run and in what order
   - `enabled_tools`: Empty list means all enabled tools run
   - `tool_order`: Controls execution order (priority, alphabetical, or custom)
   - `fail_fast`: Whether to stop on first tool failure
   - `parallel`: Whether to run tools in parallel (default: `true`)
   - `max_workers`: Maximum parallel workers, 1-32 (default: CPU count)

2. **Enforce Tier** - Cross-cutting settings injected as CLI flags
   - These settings override native configs via CLI arguments
   - Example: `line_length: 88` becomes `--line-length 88` for ruff/black
   - Applied to all tools that support the setting

3. **Defaults Tier** - Fallback configuration when no native config exists
   - Only used if tool's native config file is not found
   - Example: If `.prettierrc` doesn't exist, use `defaults.prettier`
   - Generated as temporary config files when needed

4. **Tools Tier** - Per-tool enable/disable and config source tracking
   - `enabled`: Whether the tool is enabled
   - `config_source`: Optional explicit path to native config file

### Configuration Resolution Example

For a tool like Prettier:

1. Check if tool is enabled (`tools.prettier.enabled`)
2. Check for native config (`.prettierrc`, `.prettierrc.json`, etc.)
3. If native config found:
   - Use native config
   - Inject `enforce.line_length` as `--print-width` CLI flag
   - Ignore `defaults.prettier`
4. If no native config found:
   - Generate temp config from `defaults.prettier`
   - Inject `enforce.line_length` as `--print-width` CLI flag
   - Use generated config

This ensures consistent behavior while respecting tool-specific configurations.

## Lintro Configuration

### Configuration File: `.lintro-config.yaml`

Create a `.lintro-config.yaml` in your project root:

```yaml
# Tier 1: EXECUTION - What tools run and how
execution:
  enabled_tools: [] # Empty = all enabled tools run
  tool_order: priority # priority | alphabetical | [custom list]
  fail_fast: false
  parallel: true # Run tools in parallel (default: true)
  max_workers: 10 # Max parallel workers, 1-32 (default: CPU count)

# Tier 2: ENFORCE - Cross-cutting settings injected via CLI flags
# These OVERRIDE native configs for consistency
enforce:
  line_length: 88 # Injected as --line-length, --print-width, etc.
  target_python: py313 # Injected as --target-version

# Tier 3: DEFAULTS - Fallback config when NO native config exists
# Only used if tool's native config file is not found
defaults:
  prettier:
    semi: true
    singleQuote: true
  yamllint:
    extends: default

# Tier 4: TOOLS - Per-tool enable/disable and config source
tools:
  ruff:
    enabled: true
  prettier:
    enabled: true
    config_source: ".prettierrc" # Optional: explicit native config path
```

### Configuration Report Command

Use `lintro config` to view the current configuration status for all tools:

```bash
# View configuration report
lintro config

# Show detailed output including native configs
lintro config --verbose

# Output as JSON for scripting
lintro config --json
```

The config command shows:

- **Enforce settings**: Central `line_length`, `target_python`
- **Tool execution order**: Based on configured strategy (priority, alphabetical, or
  custom)
- **Per-tool configuration**: Whether enabled, native config found
- **Defaults applied**: Which tools are using fallback defaults

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

Lintro respects each tool's native configuration files, allowing you to leverage
existing setups.

### Enforce Settings (Cross-Cutting Concerns)

The `enforce` tier contains settings that MUST be consistent across tools. These are
injected directly as CLI flags to each tool, overriding their native configs.

```yaml
enforce:
  line_length: 88 # Injected as --line-length (ruff, black) or --print-width (prettier)
  target_python: py313 # Injected as --target-version (ruff, black)
```

**How CLI injection works:**

| Tool     | CLI Flag for `line_length` | CLI Flag for `target_python` |
| -------- | -------------------------- | ---------------------------- |
| Ruff     | `--line-length 88`         | `--target-version py313`     |
| Black    | `--line-length 88`         | `--target-version py313`     |
| Prettier | `--print-width 88`         | N/A                          |

**Tools without CLI support:**

Some tools (Yamllint, Markdownlint) don't have CLI flags for line length. For these:

- Use the `defaults` tier to provide fallback config
- Or configure their native config files manually

### Defaults Tier (Fallback Config)

The `defaults` tier provides fallback configuration for tools that have no native config
file. This is useful for ensuring consistent settings without creating multiple config
files.

```yaml
defaults:
  prettier:
    semi: true
    singleQuote: true
    tabWidth: 2
    trailingComma: es5

  yamllint:
    extends: default
    rules:
      line-length:
        max: 88

  markdownlint:
    MD013:
      line_length: 88
      code_blocks: false
      tables: false
```

**When defaults are applied:**

1. Lintro checks if the tool has a native config file (e.g., `.prettierrc`)
2. If NO native config exists, Lintro generates a temp file from `defaults`
3. If native config EXISTS, `defaults` are ignored (native config is used)

### Tool Ordering Configuration

Lintro supports configurable tool execution order. By default, tools run in priority
order (formatters before linters), but you can change this behavior.

```toml
[tool.lintro]
# Tool order strategy: "priority" (default), "alphabetical", or "custom"
tool_order = "priority"

# For "custom" strategy, specify the order explicitly
tool_order_custom = ["prettier", "black", "ruff", "markdownlint", "yamllint"]

# Override individual tool priorities (lower = runs first)
tool_priorities = { ruff = 5, black = 10, prettier = 1 }
```

**Tool Order Strategies:**

| Strategy       | Description                                                      |
| -------------- | ---------------------------------------------------------------- |
| `priority`     | Formatters run before linters based on priority values (default) |
| `alphabetical` | Tools run in alphabetical order by name                          |
| `custom`       | Tools run in order specified by `tool_order_custom`              |

**Default Tool Priorities:**

| Tool         | Priority | Type             |
| ------------ | -------- | ---------------- |
| prettier     | 10       | Formatter        |
| black        | 15       | Formatter        |
| ruff         | 20       | Linter/Formatter |
| markdownlint | 30       | Linter           |
| yamllint     | 35       | Linter           |
| pydoclint    | 40       | Linter           |
| bandit       | 45       | Security         |
| hadolint     | 50       | Infrastructure   |
| actionlint   | 55       | Infrastructure   |
| pytest       | 100      | Test Runner      |

Lower priority values run first. This ensures formatters run before linters, avoiding
false positives from linters detecting issues that formatters would fix.

### Post-checks Configuration

Black is integrated as a post-check tool by default. Post-checks run after the main
tools complete and can be configured to enforce failure if issues are found. This avoids
double-formatting with Ruff and keeps formatting decisions explicit.

```toml
[tool.lintro.post_checks]
enabled = true
tools = ["black"]        # Black runs after core tools
enforce_failure = true   # Fail the run if Black finds issues in check mode
```

Notes:

- With post-checks enabled for Black, Ruff’s `format`/`format_check` stages can be
  disabled or overridden via CLI when desired.
- In `lintro check`, Black runs with `--check` and contributes to failure when
  `enforce_failure` is true. In `lintro format`, Black formats files in the post-check
  phase.

#### Black Options via `--tool-options`

You can override Black behavior on the CLI. Supported options include `line_length`,
`target_version`, `fast`, `preview`, and `diff`.

```bash
# Increase line length and target a specific Python version
lintro check --tool-options "black:line_length=100,black:target_version=py313"

# Enable fast and preview modes
lintro format --tool-options "black:fast=True,black:preview=True"

# Show diffs during formatting (in addition to applying changes)
lintro format --tool-options "black:diff=True"
```

These options can also be set in `pyproject.toml` under `[tool.lintro.black]`:

```toml
[tool.lintro.black]
line_length = 100
target_version = "py313"
fast = false
preview = false
diff = false
```

### Ruff vs Black Policy (Python)

Lintro enforces Ruff-first linting and Black-first formatting when Black is configured
as a post-check.

- Ruff: primary linter (keep strict rules like `COM812` trailing commas and `E501` line
  length enabled for checks)
- Black: primary formatter (applies formatting during post-checks; performs safe line
  breaking where Ruff’s auto-format may be limited)

Runtime behavior with Black as post-check:

- lintro format
  - Ruff fixes lint issues only (Ruff `format=False`) unless explicitly overridden
  - Black performs formatting in the post-check phase

- lintro check
  - Ruff runs lint checks (Ruff `format_check=False`) unless explicitly overridden
  - Black runs `--check` as a post-check to enforce formatting

Overrides when needed:

```bash
# Force Ruff to format during fmt
lintro format --tool-options ruff:format=True

# Force Ruff to include format check during check
lintro check --tool-options ruff:format_check=True
```

Rationale:

- Avoids double-formatting churn (Ruff format followed by Black format) while preserving
  Ruff’s stricter lint rules (e.g., `COM812`, `E501`).
- Black’s safe wrapping is preferred for long lines; Ruff continues to enforce lint
  limits during checks.

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

#### Mypy Configuration

- Default run mode: `--strict` with `--ignore-missing-imports` enabled to avoid
  third-party stub noise (applied unless you override via `set_options()` or
  `--tool-options`).
- Config discovery: mypy auto-discovers `pyproject.toml [tool.mypy]`, `mypy.ini`, or
  `setup.cfg [mypy]` and the discovered config is passed via `--config-file`. When a
  native config provides `exclude`, Lintro does **not** add its default
  test/test_samples excludes; otherwise, it applies the defaults plus `.lintro-ignore`.
- Recommended overrides when needed:

```bash
# Disable strict mode temporarily
lintro check --tools mypy --tool-options mypy:strict=False

# Surface missing-import errors (no ignore)
lintro check --tools mypy --tool-options mypy:ignore_missing_imports=False

# Pin target Python version
lintro check --tools mypy --tool-options mypy:python_version=3.13
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

#### Semgrep Configuration

Semgrep is a fast, open-source static analysis tool for security scanning and code
quality enforcement across 30+ languages.

**File:** `.semgrep.yaml` or `.semgrep.yml`

```yaml
rules:
  - id: custom-security-rule
    pattern: eval(...)
    message: "Avoid using eval() - potential code injection"
    languages: [python]
    severity: ERROR
```

**Available Options via `--tool-options`:**

| Option              | Type   | Description                                              |
| ------------------- | ------ | -------------------------------------------------------- |
| `config`            | string | Rule config: `auto`, `p/python`, `p/javascript`, or path |
| `exclude`           | list   | Patterns to exclude from scanning                        |
| `include`           | list   | Patterns to include in scanning                          |
| `severity`          | string | Minimum severity: `INFO`, `WARNING`, `ERROR`             |
| `timeout_threshold` | int    | Per-file timeout in seconds                              |
| `jobs`              | int    | Number of parallel jobs                                  |

**Example Usage:**

```bash
# Use Python security rules
lintro check --tools semgrep --tool-options "semgrep:config=p/python"

# Filter by severity
lintro check --tools semgrep --tool-options "semgrep:severity=ERROR"

# Exclude test files
lintro check --tools semgrep --tool-options "semgrep:exclude=tests/*|vendor/*"
```

#### Gitleaks Configuration

**File:** `.gitleaks.toml`

```toml
# Custom rule example
[[rules]]
id = "custom-api-key"
description = "Custom API Key Pattern"
regex = '''custom_api_key_[a-zA-Z0-9]{32}'''
tags = ["key", "custom"]

# Allowlist to ignore false positives
[allowlist]
paths = [
    '''test_samples/''',
    '''\.git/''',
]
regexes = [
    '''EXAMPLE''',
    '''test_''',
]
```

**Available Options:**

| Option                 | Type    | Description                                  |
| ---------------------- | ------- | -------------------------------------------- |
| `no_git`               | boolean | Scan without git history (files only)        |
| `config`               | string  | Path to custom gitleaks config file          |
| `baseline_path`        | string  | Path to baseline file (ignore known secrets) |
| `redact`               | boolean | Redact secrets in output (default: true)     |
| `max_target_megabytes` | integer | Skip files larger than this size in MB       |

**Usage Examples:**

```bash
# Basic scan with default config
lintro check --tools gitleaks

# Scan with git history (not just files)
lintro check --tools gitleaks --tool-options gitleaks:no_git=False

# Use custom config file
lintro check --tools gitleaks --tool-options gitleaks:config=.gitleaks.toml

# Use baseline to ignore known secrets
lintro check --tools gitleaks --tool-options gitleaks:baseline_path=gitleaks-baseline.json

# Limit file size to scan
lintro check --tools gitleaks --tool-options gitleaks:max_target_megabytes=10
```

#### pydoclint Configuration

**File:** `pyproject.toml`

```toml
[tool.pydoclint]
style = "google"
arg-type-hints-in-docstring = false
arg-type-hints-in-signature = true
check-return-types = false
check-arg-order = true
skip-checking-short-docstrings = true
```

**Available Options:**

- `style`: `google`, `numpy`, `sphinx`
- `arg-type-hints-in-docstring`: Require types in docstring (default: true)
- `arg-type-hints-in-signature`: Require type annotations (default: true)
- `check-return-types`: Validate return types match (default: true)
- `check-arg-order`: Verify argument order matches signature
- `skip-checking-short-docstrings`: Skip single-line docstrings

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
  trailingComma: "es5",
  bracketSpacing: true,
  arrowParens: "avoid",
  printWidth: 80,

  // Override for specific file types
  overrides: [
    {
      files: "*.json",
      options: {
        tabWidth: 4,
      },
    },
    {
      files: "*.md",
      options: {
        printWidth: 120,
        proseWrap: "always",
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

```text
node_modules/
dist/
build/
coverage/
*.min.js
*.min.css
```

#### Biome Configuration

**File:** `biome.json`

```json
{
  "$schema": "https://biomejs.dev/schemas/2.3.9/schema.json",
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "suspicious": {
        "noConsole": "warn"
      }
    }
  },
  "formatter": {
    "enabled": false
  }
}
```

**Ignore Files:** `.biomeignore`

```text
node_modules/
dist/
build/
coverage/
```

**Lintro options:** use `--tool-options "biome:timeout=60"` or set `exclude_patterns`
via CLI to adjust discovery; native configs remain primary.

#### Oxlint Configuration

Oxlint is a fast JavaScript/TypeScript linter (50-100x faster than ESLint) with 655+
built-in rules from ESLint, TypeScript, React, JSX-a11y, Unicorn, and more.

**Native Config Detection:**

Lintro detects these oxlint config files:

- `.oxlintrc.json`
- `oxlint.json`

When a native config exists, Lintro uses it automatically and skips generating defaults.

**Installation:**

```bash
# npm/bun
npm install -g oxlint
bun add -g oxlint

# Homebrew (macOS)
brew install oxlint
```

**File:** `.oxlintrc.json`

```json
{
  "rules": {
    "no-debugger": "error",
    "no-console": "warn",
    "eqeqeq": "error"
  },
  "plugins": ["react", "unicorn"],
  "ignorePatterns": ["dist/**", "node_modules/**"]
}
```

**Available Options via `--tool-options`:**

| Option     | Type        | Description                                     |
| ---------- | ----------- | ----------------------------------------------- |
| `config`   | string      | Path to config file (--config)                  |
| `tsconfig` | string      | Path to tsconfig.json (--tsconfig)              |
| `allow`    | list\[str\] | Rules to allow (turn off)                       |
| `deny`     | list\[str\] | Rules to deny (report as errors)                |
| `warn`     | list\[str\] | Rules to warn on (report as warnings)           |
| `quiet`    | boolean     | Suppress warnings, only report errors (--quiet) |
| `timeout`  | integer     | Execution timeout in seconds (default: 30)      |

**Usage Examples:**

```bash
# Basic check
lintro check --tools oxlint

# Auto-fix issues
lintro format --tools oxlint

# Suppress warnings (errors only)
lintro check --tools oxlint --tool-options "oxlint:quiet=True"

# Deny specific rules (report as errors)
lintro check --tools oxlint --tool-options "oxlint:deny=no-debugger|no-console"

# Allow specific rules (ignore them)
lintro check --tools oxlint --tool-options "oxlint:allow=no-unused-vars"

# Use custom config file
lintro check --tools oxlint --tool-options "oxlint:config=.oxlintrc.custom.json"

# Specify tsconfig for TypeScript projects
lintro check --tools oxlint --tool-options "oxlint:tsconfig=tsconfig.app.json"
```

#### Oxfmt Configuration

Oxfmt is a fast JavaScript/TypeScript formatter (30x faster than Prettier) that
provides Prettier-compatible formatting with minimal configuration.

**Native Config Detection:**

Lintro detects these oxfmt config files:

- `.oxfmtrc.json`
- `.oxfmtrc.jsonc` (supports comments)

When a native config exists, Lintro uses it automatically and skips generating defaults.

**Installation:**

```bash
# npm/bun
npm install -g oxfmt
bun add -g oxfmt

# Homebrew (macOS)
brew install oxfmt
```

**File:** `.oxfmtrc.json` or `.oxfmtrc.jsonc`

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
```

**Available Options via `--tool-options`:**

| Option        | Type    | Description                                |
| ------------- | ------- | ------------------------------------------ |
| `config`      | string  | Path to config file (--config)             |
| `ignore_path` | string  | Path to ignore file (--ignore-path)        |
| `timeout`     | integer | Execution timeout in seconds (default: 30) |

> **Note:** Formatting options (`printWidth`, `tabWidth`, `useTabs`, `semi`, `singleQuote`)
> are only supported via config file (`.oxfmtrc.json`), not CLI flags.

**Usage Examples:**

```bash
# Basic check
lintro check --tools oxfmt

# Format files
lintro format --tools oxfmt

# Use custom config file
lintro format --tools oxfmt --tool-options "oxfmt:config=.oxfmtrc.custom.json"

# Use custom ignore file
lintro format --tools oxfmt --tool-options "oxfmt:ignore_path=.oxfmtignore"

# Increase timeout
lintro format --tools oxfmt --tool-options "oxfmt:timeout=60"
```

### SQL Tools

#### SQLFluff Configuration

**File:** `.sqlfluff`

```ini
[sqlfluff]
dialect = ansi
templater = jinja
exclude_rules = L016,L031

[sqlfluff:indentation]
indent_unit = space
tab_space_size = 4

[sqlfluff:layout:type:comma]
line_position = trailing

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.identifiers]
extended_capitalisation_policy = lower
```

**File:** `pyproject.toml`

```toml
[tool.sqlfluff.core]
dialect = "ansi"
templater = "jinja"
exclude_rules = ["L016", "L031"]

[tool.sqlfluff.indentation]
indent_unit = "space"
tab_space_size = 4

[tool.sqlfluff.rules.capitalisation.keywords]
capitalisation_policy = "upper"

[tool.sqlfluff.rules.capitalisation.identifiers]
extended_capitalisation_policy = "lower"
```

**Available Options:**

| Option          | Type   | Description                                         |
| --------------- | ------ | --------------------------------------------------- |
| `dialect`       | string | SQL dialect (ansi, bigquery, postgres, mysql, etc.) |
| `exclude_rules` | list   | List of rules to exclude from checking              |
| `rules`         | list   | List of specific rules to include                   |
| `templater`     | string | Templater to use (raw, jinja, python, placeholder)  |

**Supported Dialects:**

- `ansi` - ANSI SQL standard
- `bigquery` - Google BigQuery
- `clickhouse` - ClickHouse
- `databricks` - Databricks SQL
- `db2` - IBM Db2
- `exasol` - Exasol
- `hive` - Apache Hive
- `mysql` - MySQL
- `oracle` - Oracle Database
- `postgres` - PostgreSQL
- `redshift` - Amazon Redshift
- `snowflake` - Snowflake
- `soql` - Salesforce SOQL
- `sparksql` - Apache Spark SQL
- `sqlite` - SQLite
- `teradata` - Teradata
- `tsql` - T-SQL (Microsoft SQL Server)

**Usage Examples:**

```bash
# Basic SQL check
lintro check --tools sqlfluff

# Format SQL files
lintro format --tools sqlfluff

# Check with specific dialect
lintro check --tools sqlfluff --tool-options sqlfluff:dialect=postgres

# Exclude specific rules
lintro check --tools sqlfluff --tool-options sqlfluff:exclude_rules=L010,L014

# Use jinja templater
lintro check --tools sqlfluff --tool-options sqlfluff:templater=jinja
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
    allowed-values: ["true", "false"]
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

### Markdown Tools

#### Markdownlint-cli2 Configuration {#markdownlint-cli2-configuration}

Markdownlint-cli2 supports configuration via JSON, JSONC, YAML, or TOML files. Lintro
defers to markdownlint-cli2's native configuration discovery, which searches upward from
the file being checked.

**File:** `.markdownlint.json`

```json
{
  "default": true,
  "MD013": {
    "line_length": 120
  },
  "MD041": false
}
```

**File:** `.markdownlint.yaml`

```yaml
default: true
MD013:
  line_length: 120
MD041: false
```

**File:** `.markdownlint-cli2.jsonc`

```jsonc
{
  "config": {
    "default": true,
    "MD013": { "line_length": 120 },
  },
}
```

**Available Options:**

- Configuration files are discovered automatically by markdownlint-cli2
- Rules can be enabled/disabled via configuration files
- Lintro respects markdownlint-cli2's native configuration discovery
- Future versions may expose additional options via `[tool.lintro.markdownlint-cli2]` in
  `pyproject.toml`

### Rust Tools

#### Clippy Configuration

Clippy is Rust's official linter and is configured through Cargo.toml or a separate
clippy.toml file. Lintro automatically discovers and runs clippy on Rust projects by
finding Cargo.toml files.

**File:** `Cargo.toml`

```toml
[package]
name = "my-rust-project"
version = "0.1.0"

[lints.clippy]
# Enable all lints
pedantic = "warn"
# Or be more restrictive
# pedantic = { level = "warn", priority = -1 }

# Disable specific lints
too_many_arguments = "allow"
type_complexity = "allow"

# Configure lint levels
needless_return = "warn"
unused_variables = "error"
```

**File:** `clippy.toml` (alternative)

```toml
# Clippy-specific configuration
too-many-arguments-threshold = 10
type-complexity-threshold = 100
cognitive-complexity-threshold = 15

# Disable specific lints
disallowed-names = []
```

**Available Options:**

- **pedantic**: Enable all lints that are typically only enabled in CI
- **nursery**: Enable newer, more experimental lints
- **restriction**: Enable very strict lints that may be overly restrictive for some
  projects
- **cargo**: Enable lints that check Cargo.toml files

**Lintro usage:**

```bash
# Check Rust code with Clippy
lintro check --tools clippy

# Auto-fix Clippy issues where possible
lintro format --tools clippy

# Check specific Rust directories
lintro check src/ --tools clippy
```

### Shell Tools

#### ShellCheck Configuration

ShellCheck is a static analysis tool for shell scripts. It identifies bugs, syntax
issues, and suggests improvements for bash/sh/dash/ksh/zsh scripts. Unlike formatters,
ShellCheck focuses on finding potential bugs and problematic patterns.

**Installation:**

```bash
# macOS
brew install shellcheck

# Debian/Ubuntu
apt-get install shellcheck

# Fedora
dnf install ShellCheck
```

**File:** `.shellcheckrc`

```ini
# Exclude specific codes
disable=SC2086,SC2046

# Set default shell dialect
shell=bash

# Set minimum severity level
severity=warning
```

**Lintro options via `--tool-options`:**

```bash
# Set minimum severity level (error, warning, info, style)
lintro check --tools shellcheck --tool-options "shellcheck:severity=warning"

# Force shell dialect (bash, sh, dash, ksh, zsh)
lintro check --tools shellcheck --tool-options "shellcheck:shell=bash"

# Exclude specific codes
lintro check --tools shellcheck --tool-options "shellcheck:exclude=SC2086|SC2046"
```

**Available Options:**

| Option     | Type        | Description                                     |
| ---------- | ----------- | ----------------------------------------------- |
| `severity` | str         | Minimum severity: error, warning, info, style   |
| `exclude`  | list\[str\] | List of codes to exclude (e.g., SC2086, SC2046) |
| `shell`    | str         | Force shell dialect: bash, sh, dash, ksh, zsh   |

**Common ShellCheck Codes:**

| Code   | Description                                         |
| ------ | --------------------------------------------------- |
| SC2086 | Double quote to prevent globbing and word splitting |
| SC2046 | Quote this to prevent word splitting                |
| SC2002 | Useless use of cat                                  |
| SC2006 | Use $(...) notation instead of backticks            |
| SC2034 | Variable appears unused                             |
| SC2155 | Declare and assign separately                       |

**Inline ignoring:**

```bash
#!/bin/bash

# shellcheck disable=SC2086
echo $unquoted_variable

# Or use a directive that applies to the whole file at the top:
# shellcheck disable=SC2086,SC2046
```

**Lintro usage:**

```bash
# Check shell scripts with ShellCheck
lintro check --tools shellcheck

# Check with warning level (ignores info and style)
lintro check --tools shellcheck --tool-options "shellcheck:severity=warning"

# Check specific shell directories
lintro check scripts/ --tools shellcheck
```

#### Shfmt Configuration

Shfmt is a shell script formatter that supports POSIX, Bash, mksh, and bats shells. It
formats shell scripts to ensure consistent style and can detect formatting issues in
diff mode.

**Installation:**

```bash
# macOS
brew install shfmt

# Linux (via Go)
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Via npm/bun
bun add -g shfmt
```

**File:** `.editorconfig` (shfmt respects EditorConfig)

```ini
[*.sh]
indent_style = tab
indent_size = 4
shell_variant = bash
binary_next_line = true
switch_case_indent = true
space_redirects = false
```

**Lintro options via `--tool-options`:**

```bash
# Set indentation to 4 spaces (0 for tabs)
lintro check --tools shfmt --tool-options "shfmt:indent=4"

# Enable binary operators at start of line
lintro check --tools shfmt --tool-options "shfmt:binary_next_line=True"

# Indent switch cases
lintro check --tools shfmt --tool-options "shfmt:switch_case_indent=True"

# Add space after redirect operators
lintro check --tools shfmt --tool-options "shfmt:space_redirects=True"

# Set language dialect (bash, posix, mksh, bats)
lintro check --tools shfmt --tool-options "shfmt:language_dialect=bash"

# Enable code simplification
lintro check --tools shfmt --tool-options "shfmt:simplify=True"
```

**Available Options:**

| Option               | Type | Description                                 |
| -------------------- | ---- | ------------------------------------------- |
| `indent`             | int  | Indentation size. 0 for tabs, >0 for spaces |
| `binary_next_line`   | bool | Binary ops like && and \| may start a line  |
| `switch_case_indent` | bool | Indent switch cases                         |
| `space_redirects`    | bool | Redirect operators followed by space        |
| `language_dialect`   | str  | Shell dialect: bash, posix, mksh, bats      |
| `simplify`           | bool | Simplify code where possible                |

**Lintro usage:**

```bash
# Check shell scripts with shfmt
lintro check --tools shfmt

# Auto-format shell scripts
lintro format --tools shfmt

# Check specific shell directories
lintro check scripts/ --tools shfmt
```

### TOML Tools

#### Taplo Configuration

**File:** `taplo.toml` or `.taplo.toml`

```toml
# Taplo configuration
[formatting]
align_entries = false
align_comments = true
array_trailing_comma = true
array_auto_expand = true
array_auto_collapse = true
compact_arrays = true
compact_inline_tables = false
column_width = 80
indent_tables = false
indent_entries = false
indent_string = "  "
trailing_newline = true
reorder_keys = false
allowed_blank_lines = 2
crlf = false

[[rule]]
# Apply to all TOML files
include = ["**/*.toml"]
keys = ["Cargo.toml"]

[rule.formatting]
reorder_keys = true
```

**Available Options:**

| Option                 | Type    | Description                               |
| ---------------------- | ------- | ----------------------------------------- |
| `schema`               | string  | Path or URL to JSON schema for validation |
| `aligned_arrays`       | boolean | Align array entries vertically            |
| `aligned_entries`      | boolean | Align table entries (key = value)         |
| `array_trailing_comma` | boolean | Add trailing comma in multi-line arrays   |
| `indent_string`        | string  | Indentation string (default: 2 spaces)    |
| `reorder_keys`         | boolean | Reorder keys alphabetically               |

**Usage Examples:**

```bash
# Basic TOML check
lintro check --tools taplo

# Format TOML files
lintro format --tools taplo

# Check with aligned entries
lintro check --tools taplo --tool-options taplo:aligned_entries=true

# Format with specific indent
lintro format --tools taplo --tool-options taplo:indent_string="    "

# Use custom schema for validation
lintro check --tools taplo --tool-options taplo:schema=pyproject.schema.json
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

Actionlint validates GitHub Actions workflows. Lintro discovers workflow files under
`/.github/workflows/` when you run `lintro check .` and invokes the `actionlint` binary.

- Discovery: YAML files filtered to those in `/.github/workflows/`
- Defaults: Lintro does not pass special flags; native actionlint defaults are used
- Local install: use `scripts/utils/install-tools.sh --local` to place `actionlint` on
  PATH
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

```text
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
default_tools = ["ruff", "pydoclint", "prettier", "yamllint"]
table_format = true
group_by = "auto"
exclude_patterns = ["migrations", "node_modules", "dist"]

[lintro.timeouts]
default = 30
pydoclint = 45
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

Lintro now generates all output formats for every run in a timestamped directory under
`.lintro/` (e.g., `.lintro/run-20240722-153000/`).

You do not need to specify output format or file options. Each run produces:

- `console.log`: The full console output
- `results.json`: Machine-readable results
- `report.md`: Human-readable Markdown report
- `report.html`: Web-viewable HTML report
- `summary.csv`: Spreadsheet-friendly summary

This ensures you always have every format available for your workflow, CI, or reporting
needs.

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
lintro check src/ --tools ruff,pydoclint
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
    "tools_run": ["ruff", "pydoclint"],
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

<!-- markdownlint-disable MD010 -->

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
	pip install ruff pydoclint
	npm install -g prettier
```

<!-- markdownlint-enable MD010 -->

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
pydoclint src/main.py
prettier --check package.json
```

This comprehensive configuration guide should help you customize Lintro to fit your
project's specific needs and integrate seamlessly into your development workflow!
