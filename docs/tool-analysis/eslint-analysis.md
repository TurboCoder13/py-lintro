# ESLint Tool Analysis

## Overview

ESLint is a linter for JavaScript and TypeScript that identifies and reports on patterns
in code. This analysis compares Lintro's wrapper implementation with the core ESLint
tool.

## Core Tool Capabilities

ESLint provides extensive CLI options including:

- **Linting options**: `--fix`, `--fix-dry-run`, `--format`, `--max-warnings`
- **File handling**: `--ext`, `--ignore-path`, `--ignore-pattern`, `--no-ignore`
- **Configuration**: `--config`, `--env`, `--parser`, `--parser-options`
- **Output control**: `--format json`, `--format compact`, `--format stylish`
- **Rule control**: `--rule`, `--no-eslintrc`, `--config-file`
- **Cache**: `--cache`, `--cache-location`, `--cache-strategy`

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Linting capability**: Full preservation through standard ESLint execution
- ✅ **Check mode**: Preserved through standard ESLint check (no --fix flag)
- ✅ **File targeting**: Supports file patterns (`*.js`, `*.jsx`, `*.ts`, `*.tsx`,
  `*.mjs`, `*.cjs`)
- ✅ **Auto-fixing**: Can automatically fix issues when `fix()` is called with `--fix`
  flag
- ✅ **Configuration files**: Respects `.eslintrc.*`, `eslint.config.*`, and
  `package.json` configs
- ✅ **Error detection**: Captures linting violations as issues with rule IDs, severity,
  and messages
- ✅ **JSON output**: Uses `--format json` for reliable parsing

**Command Execution:**

```python
# From tool_eslint.py
cmd = ["eslint", "--format", "json"] + self.files
# For fixing:
cmd = ["eslint", "--fix"] + self.files
```

### ⚠️ Limited/Missing Features

**Granular Configuration:**

- ⚠️ **Runtime rule configuration**: Prefer config files; proposed pass-throughs include
  `rule`, `env`, `parser`, `parser_options`, etc.
- ⚠️ **Format specification**: Currently hardcoded to JSON; could support other formats
- ⚠️ **Discovery controls**: Proposed `eslint:config=...`, `eslint:no_eslintrc=True`,
  `eslint:ignore_path=.eslintignore`.
- ⚠️ **Cache options**: Optional `eslint:cache=True`, `eslint:cache_location=...`,
  `eslint:cache_strategy=...`.
- ⚠️ **Warning limits**: Optional `eslint:max_warnings=N`.

**Advanced Features:**

- ❌ **Dry-run fixes**: No `--fix-dry-run` support
- ❌ **Custom formatters**: No support for custom ESLint formatters
- ❌ **Inline rule configuration**: No runtime `--rule` specification
- ❌ **Parser options**: No runtime `--parser-options` specification

**Error Handling:**

- ⚠️ **Limited error context**: Basic error reporting without detailed rule
  documentation links
- ⚠️ **Severity handling**: Distinguishes warnings (severity 1) from errors (severity 2)
  but treats both as issues

### 🚀 Enhancements

**Unified Interface:**

- ✅ **Consistent API**: Same interface as other linting tools (`check()`, `fix()`,
  `set_options()`)
- ✅ **Structured output**: Issues formatted as standardized `EslintIssue` objects with:
  - File path
  - Line and column numbers
  - Rule ID (e.g., 'no-unused-vars')
  - Severity (1=warning, 2=error)
  - Message
  - Fixable flag
- ✅ **File filtering**: Built-in file extension filtering and ignore patterns
- ✅ **Integration ready**: Seamless integration with other tools in linting pipeline

**Error Processing:**

- ✅ **Issue normalization**: Converts ESLint JSON output to standard Issue format:

  ```python
  EslintIssue(
      file=file_path,
      line=line_number,
      column=column_number,
      code=rule_id,
      message=message_text,
      severity=severity,  # 1=warning, 2=error
      fixable=has_fix
  )
  ```

**Workflow Integration:**

- ✅ **Batch processing**: Can process multiple files in single operation
- ✅ **Conditional execution**: Only runs when relevant file types are present
- ✅ **Status tracking**: Clear success/failure reporting
- ✅ **Fix tracking**: Tracks initial issues, fixed issues, and remaining issues

### 🔧 Proposed runtime pass-throughs

- `--tool-options eslint:config=.config/eslint.json,eslint:ignore_path=.eslintignore`
- `--tool-options eslint:max_warnings=10,eslint:env=node,browser`
- `--tool-options eslint:cache=True,eslint:cache_location=.cache/eslint`
- `--tool-options eslint:rule=no-console:error,eslint:rule=no-unused-vars:warn`

## Usage Comparison

### Core ESLint

```bash
# Check linting
eslint --format json "src/**/*.{js,ts}"

# Fix issues
eslint --fix "src/**/*.{js,ts}"

# Custom config
eslint --config custom-eslint.json src/
```

### Lintro Wrapper

```python
# Check linting
eslint_tool = EslintTool()
eslint_tool.set_options()
result = eslint_tool.check(["src/main.js", "src/utils.ts"])

# Fix issues
fix_result = eslint_tool.fix(["src/main.js", "src/utils.ts"])
```

## Recommendations

### When to Use Core ESLint

- Need specific rule configuration at runtime
- Require custom formatters or output formats
- Working with non-standard file patterns
- Need advanced cache strategies
- Require dry-run fix preview

### When to Use Lintro Wrapper

- Part of multi-tool linting pipeline
- Need consistent issue reporting across tools
- Want simplified configuration management
- Require programmatic integration with Python workflows
- Need unified fix tracking across multiple tools

## Configuration Strategy

The Lintro wrapper relies on ESLint's configuration files:

- `.eslintrc.js`
- `.eslintrc.json`
- `.eslintrc.yaml` / `.eslintrc.yml`
- `eslint.config.js` (flat config)
- `package.json` "eslintConfig" field

For runtime customization, users should modify these config files rather than passing
CLI options. The wrapper also respects `.eslintignore` files natively.

## Priority and Conflicts

ESLint is configured with:

- **Priority**: 50 (lower than formatters like Prettier, which have priority 80)
- **Tool Type**: LINTER
- **Conflicts**: None (can run alongside formatters)
- **Execution Order**: Runs after formatters due to lower priority

This ensures that formatting happens before linting, which is the recommended workflow.
