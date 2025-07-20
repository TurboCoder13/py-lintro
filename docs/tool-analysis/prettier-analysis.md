# Prettier Tool Analysis

## Overview

Prettier is a code formatter that supports JavaScript, TypeScript, CSS, HTML, and many other languages. This analysis compares Lintro's wrapper implementation with the core Prettier tool.

## Core Tool Capabilities

Prettier provides extensive CLI options including:

- **Formatting options**: `--tab-width`, `--use-tabs`, `--semi`, `--single-quote`, `--quote-props`, `--trailing-comma`
- **File handling**: `--write`, `--check`, `--config`, `--ignore-path`, `--stdin-filepath`
- **Parser options**: `--parser` (auto-detect or specify: babel, typescript, css, html, etc.)
- **Output control**: `--list-different`, `--require-pragma`, `--insert-pragma`
- **Debug options**: `--debug-check`, `--debug-print-doc`

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Formatting capability**: Full preservation through `--write` flag
- ✅ **Check mode**: Preserved through `--check` flag
- ✅ **File targeting**: Supports file patterns and paths
- ✅ **Configuration files**: Respects `.prettierrc` and `prettier.config.js`
- ✅ **Error detection**: Captures formatting violations as issues
- ✅ **Auto-fixing**: Can automatically format files when `fix()` is called

**Command Execution:**

```python
# From tool_prettier.py
cmd = ["prettier", "--check"] + self.files
# For fixing:
cmd = ["prettier", "--write"] + self.files
```

### ⚠️ Limited/Missing Features

**Granular Configuration:**

- ❌ **Runtime formatting options**: No access to `--tab-width`, `--use-tabs`, `--semi`, etc.
- ❌ **Parser specification**: Cannot override parser selection
- ❌ **Output format control**: Limited to check/write modes
- ❌ **Debug capabilities**: No access to `--debug-check` or `--debug-print-doc`
- ❌ **Pragma handling**: No `--require-pragma` or `--insert-pragma` support

**Advanced Features:**

- ❌ **Stdin processing**: No `--stdin-filepath` support
- ❌ **List different**: Cannot use `--list-different` mode
- ❌ **Custom ignore paths**: No runtime `--ignore-path` specification

**Error Handling:**

- ⚠️ **Limited error context**: Basic error reporting without detailed formatting suggestions
- ⚠️ **No syntax validation**: Doesn't expose Prettier's syntax error detection

### 🚀 Enhancements

**Unified Interface:**

- ✅ **Consistent API**: Same interface as other linting tools (`check()`, `fix()`, `set_options()`)
- ✅ **Structured output**: Issues formatted as standardized `Issue` objects
- ✅ **File filtering**: Built-in file extension filtering and ignore patterns
- ✅ **Integration ready**: Seamless integration with other tools in linting pipeline

**Error Processing:**

- ✅ **Issue normalization**: Converts Prettier output to standard Issue format:
  ```python
  Issue(
      file_path=file_path,
      line_number=None,  # Prettier doesn't provide line-specific info
      column_number=None,
      error_code="formatting",
      message=f"File is not formatted correctly: {file_path}",
      severity="error"
  )
  ```

**Workflow Integration:**

- ✅ **Batch processing**: Can process multiple files in single operation
- ✅ **Conditional execution**: Only runs when relevant file types are present
- ✅ **Status tracking**: Clear success/failure reporting

## Usage Comparison

### Core Prettier

```bash
# Check formatting
prettier --check "src/**/*.{js,ts,css}"

# Format files
prettier --write "src/**/*.{js,ts,css}" --tab-width 2 --single-quote

# Custom config
prettier --write --config custom-prettier.json src/
```

### Lintro Wrapper

```python
# Check formatting
prettier_tool = PrettierTool()
prettier_tool.set_files(["src/main.js", "src/style.css"])
issues = prettier_tool.check()

# Format files
prettier_tool.fix()
```

## Recommendations

### When to Use Core Prettier

- Need specific formatting options at runtime
- Require debug output or syntax validation
- Working with non-standard file patterns
- Need pragma-based formatting control

### When to Use Lintro Wrapper

- Part of multi-tool linting pipeline
- Need consistent issue reporting across tools
- Want simplified configuration management
- Require programmatic integration with Python workflows

## Configuration Strategy

The Lintro wrapper relies entirely on Prettier's configuration files:

- `.prettierrc`
- `.prettierrc.json`
- `prettier.config.js`
- `package.json` "prettier" field

For runtime customization, users should modify these config files rather than passing CLI options.
