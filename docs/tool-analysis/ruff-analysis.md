# Ruff Tool Analysis

## Overview

Ruff is an extremely fast Python linter and code formatter written in Rust that can replace multiple Python tools like flake8, black, isort, and more. This analysis compares Lintro's wrapper implementation with the core Ruff tool.

## Core Tool Capabilities

Ruff provides extensive linting and formatting capabilities including:

- **Linting**: 700+ rules covering PEP 8, flake8, isort, pyupgrade, and more
- **Formatting**: Black-compatible code formatting with customization options
- **Performance**: Extremely fast execution due to Rust implementation
- **Configuration**: `pyproject.toml`, `ruff.toml`, or command-line options
- **Rule selection**: `--select`, `--ignore`, `--extend-select`, `--extend-ignore`
- **Formatting options**: `--line-length`, `--target-version`, `--skip-magic-trailing-comma`
- **Fix capabilities**: `--fix`, `--unsafe-fixes`, `--fix-only`, `--show-fixes`
- **Output formats**: Default, JSON, SARIF, JUnit XML

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Linting capability**: Full preservation through `ruff check` command
- ✅ **Formatting capability**: Full preservation through `ruff format` command
- ✅ **Auto-fixing**: Supports `--fix` with safe and unsafe fix options
- ✅ **Rule selection**: Supports `--select`, `--ignore`, `--extend-select`, `--extend-ignore`
- ✅ **Configuration files**: Respects `pyproject.toml` and `ruff.toml`
- ✅ **File targeting**: Supports Python file patterns (`*.py`, `*.pyi`)
- ✅ **Error detection**: Captures both linting and formatting violations

**Command Execution:**

```python
# From tool_ruff.py
cmd = self._get_executable_command("ruff") + ["check"]
# For fixing:
cmd = self._get_executable_command("ruff") + ["check", "--fix"]
# For formatting:
cmd = self._get_executable_command("ruff") + ["format"]
```

**Configuration Options:**

- ✅ **Rule selection**: `select`, `ignore`, `extend_select`, `extend_ignore`
- ✅ **Line length**: `line_length` parameter
- ✅ **Target version**: `target_version` parameter
- ✅ **Fix options**: `fix_only`, `unsafe_fixes`, `show_fixes`
- ✅ **Formatting control**: `format` boolean to enable/disable formatting

### ⚠️ Limited/Missing Features

**Advanced Configuration:**

- ❌ **Runtime rule customization**: Limited to predefined rule sets
- ❌ **Custom rule definitions**: No support for custom rule creation
- ❌ **Per-file configuration**: No support for `# ruff: noqa` comments
- ❌ **Output format selection**: Limited to JSON output for parsing

**Formatting Options:**

- ❌ **Detailed formatting options**: No access to `--skip-magic-trailing-comma`, `--preview`
- ❌ **Formatting configuration**: Limited line length and target version control
- ❌ **Format-only mode**: Cannot run formatter without linter

**Advanced Features:**

- ❌ **Watch mode**: No `--watch` functionality for continuous monitoring
- ❌ **Cache control**: No access to `--cache-dir`, `--no-cache`
- ❌ **Statistics**: No access to `--statistics` output
- ❌ **Exit codes**: Limited exit code customization

**Performance Options:**

- ❌ **Parallel processing**: No access to Ruff's built-in parallelization
- ❌ **Memory optimization**: No control over memory usage settings

### 🚀 Enhancements

**Unified Interface:**

- ✅ **Consistent API**: Same interface as other linting tools (`check()`, `fix()`, `set_options()`)
- ✅ **Structured output**: Issues formatted as standardized `Issue` objects
- ✅ **Combined operations**: Runs both linting and formatting in single operation
- ✅ **Integration ready**: Seamless integration with other tools in linting pipeline

**Enhanced Error Processing:**

- ✅ **Issue normalization**: Converts Ruff output to standard Issue format:
  ```python
  Issue(
      file_path=issue.file,
      line_number=issue.line,
      column_number=issue.column,
      error_code=issue.code,
      message=issue.message,
      severity="error"
  )
  ```

**Smart Fix Handling:**

- ✅ **Fix reporting**: Shows number of issues fixed vs remaining
- ✅ **Unsafe fix detection**: Warns about issues that could be fixed with unsafe fixes
- ✅ **Fix-only mode**: Option to only apply fixes without reporting remaining issues
- ✅ **Format integration**: Automatic formatting when enabled

**File Management:**

- ✅ **Extension filtering**: Automatic Python file detection
- ✅ **Batch processing**: Efficient handling of multiple files
- ✅ **Error aggregation**: Collects all issues across files

## Usage Comparison

### Core Ruff

```bash
# Basic linting
ruff check src/

# With specific rules
ruff check --select E501,W503 src/

# Auto-fixing
ruff check --fix src/

# Formatting
ruff format src/

# Combined lint and format
ruff check --fix src/ && ruff format src/
```

### Lintro Wrapper

```python
# Basic checking (lint + format)
ruff_tool = RuffTool()
ruff_tool.set_files(["src/main.py"])
issues = ruff_tool.check()

# Auto-fixing
ruff_tool.fix()

# With specific options
ruff_tool.set_options(
    select=["E501", "W503"],
    line_length=88,
    unsafe_fixes=True
)
```

## Configuration Strategy

### Core Tool Configuration

Ruff uses configuration files:

- `pyproject.toml` `[tool.ruff]` section
- `ruff.toml`
- `.ruff.toml`

### Lintro Approach

The wrapper supports both configuration files and runtime options:

- **Configuration files**: Primary configuration method
- **Runtime options**: Override specific settings via `set_options()`
- **Combined approach**: Configuration files provide defaults, runtime options override

## Rule Categories

Lintro preserves all Ruff rule categories:

| Category                  | Prefix | Description                        |
| ------------------------- | ------ | ---------------------------------- |
| **Pyflakes**              | F      | Logical errors and undefined names |
| **pycodestyle**           | E, W   | PEP 8 style violations             |
| **isort**                 | I      | Import sorting issues              |
| **pydocstyle**            | D      | Docstring style violations         |
| **pyupgrade**             | UP     | Python upgrade suggestions         |
| **flake8-bugbear**        | B      | Bug detection and complexity       |
| **flake8-comprehensions** | C4     | Comprehension improvements         |
| **flake8-simplify**       | SIM    | Code simplification suggestions    |

## Recommendations

### When to Use Core Ruff

- Need maximum configuration flexibility
- Require specific output formats (SARIF, JUnit XML)
- Want watch mode for continuous monitoring
- Need custom rule definitions
- Require detailed statistics and caching control

### When to Use Lintro Wrapper

- Part of multi-tool linting pipeline
- Need consistent issue reporting across tools
- Want Python object integration
- Require combined linting and formatting
- Need standardized error handling

## Limitations and Workarounds

### Limited Runtime Configuration

**Problem**: Cannot customize all Ruff options at runtime
**Workaround**: Use configuration files for complex setups, runtime options for overrides

### No Custom Rules

**Problem**: Cannot define custom linting rules
**Workaround**: Use Ruff's extensive built-in rule set (700+ rules)

### Limited Output Formats

**Problem**: Limited to JSON output for parsing
**Workaround**: Lintro provides structured `Issue` objects and multiple output formats

## Future Enhancement Opportunities

1. **Configuration Pass-through**: Support for all Ruff CLI options
2. **Custom Rules**: Integration with Ruff's rule system
3. **Watch Mode**: Continuous monitoring capabilities
4. **Performance**: Leverage Ruff's parallel processing
5. **Statistics**: Detailed performance and issue statistics
6. **Cache Integration**: Intelligent caching for faster subsequent runs
