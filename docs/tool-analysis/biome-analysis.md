# Biome Tool Analysis

## Overview

Biome is a fast linter for JavaScript, TypeScript, JSON, and CSS that provides detailed
diagnostics and safe fixes. This analysis compares Lintro's wrapper implementation with
the core Biome tool.

## Core Tool Capabilities

Biome provides extensive CLI options including:

- **Linting options**: `--write`, `--unsafe`, `--suppress`, `--reporter`
- **File handling**: `--files-max-size`, `--files-ignore-unknown`
- **Configuration**: `--config-path`, `--no-config`
- **Output control**: `--reporter json`, `--reporter json-pretty`, `--max-diagnostics`
- **Rule control**: `--only`, `--skip`, `--diagnostic-level`
- **Cache**: VCS integration with `--vcs-enabled`

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Linting capability**: Full preservation through standard Biome execution
- ✅ **Check mode**: Preserved through `biome lint --reporter=json` (no --write flag)
- ✅ **File targeting**: Supports file patterns (`*.js`, `*.jsx`, `*.ts`, `*.tsx`,
  `*.json`, `*.css`)
- ✅ **Auto-fixing**: Can automatically fix issues when `fix()` is called with `--write`
  flag
- ✅ **Configuration files**: Respects `biome.json` and `biome.jsonc` configs
- ✅ **Error detection**: Captures linting violations as issues with rule categories,
  severity, and messages
- ✅ **JSON output**: Uses `--reporter json` for reliable parsing

**Command Execution:**

```python
# From tool_biome.py
cmd = self._get_executable_command(tool_name="biome") + [
    "lint", "--reporter", "json"
] + rel_files
# For fixing:
cmd = self._get_executable_command(tool_name="biome") + [
    "lint", "--write"
] + rel_files

# Where _get_executable_command returns: ["npx", "--yes", "@biomejs/biome"]
```

### ⚠️ Limited/Missing Features

**Granular Configuration:**

- ⚠️ **Runtime rule configuration**: Prefer config files; proposed pass-throughs include
  `only`, `skip`, `diagnostic_level`, etc.
- ⚠️ **Format specification**: Currently hardcoded to JSON; could support other
  reporters
- ⚠️ **Discovery controls**: Proposed `biome:config=.config/biome.json`,
  `biome:no_config=True`, `biome:vcs_enabled=False`.
- ⚠️ **Cache options**: Optional `biome:vcs_enabled=True`, `biome:vcs_client_kind=git`,
  `biome:vcs_use_ignore_file=True`.
- ⚠️ **Diagnostic limits**: Optional `biome:max_diagnostics=N`.

**Advanced Features:**

- ❌ **Unsafe fixes**: No `--unsafe` support for potentially unsafe fixes
- ❌ **Rule suppression**: No `--suppress` support for comment-based suppressions
- ❌ **Custom reporters**: No support for custom Biome reporters
- ❌ **Inline rule configuration**: No runtime `--only`/`--skip` specification
- ❌ **VCS integration**: No runtime VCS configuration

**Error Handling:**

- ⚠️ **Limited error context**: Basic error reporting without detailed rule
  documentation links
- ⚠️ **Severity handling**: Distinguishes errors, warnings, and info levels but treats
  all as issues

### 🚀 Enhancements

**Unified Interface:**

- ✅ **Consistent API**: Same interface as other linting tools (`check()`, `fix()`,
  `set_options()`)
- ✅ **Structured output**: Issues formatted as standardized `BiomeIssue` objects with:
  - File path
  - Line and column numbers
  - Rule category (e.g., 'lint/suspicious/noDoubleEquals')
  - Severity (error/warning/info)
  - Message
  - Fixable flag
- ✅ **File filtering**: Built-in file extension filtering and ignore patterns
- ✅ **Integration ready**: Seamless integration with other tools in linting pipeline

**Error Processing:**

- ✅ **Issue normalization**: Converts Biome JSON output to standard Issue format:

  ```python
  BiomeIssue(
      file=file_path,
      line=line_number,
      column=column_number,
      code=rule_category,
      message=message_text,
      severity=severity,  # error/warning/info
      fixable=has_fix
  )
  ```

**Workflow Integration:**

- ✅ **Batch processing**: Can process multiple files in single operation
- ✅ **Conditional execution**: Only runs when relevant file types are present
- ✅ **Status tracking**: Clear success/failure reporting
- ✅ **Fix tracking**: Tracks initial issues, fixed issues, and remaining issues

### 🔧 Proposed runtime pass-throughs

- `--tool-options biome:config=.config/biome.json,biome:no_config=True`
- `--tool-options biome:max_diagnostics=20,biome:diagnostic_level=warn`
- `--tool-options biome:only=lint/suspicious,biome:skip=lint/style/useConst`
- `--tool-options biome:vcs_enabled=False,biome:files_max_size=1MB`

## Usage Comparison

### Core Biome

```bash
# Check linting
biome lint --reporter=json "src/**/*.{js,ts,json,css}"

# Fix issues
biome lint --write "src/**/*.{js,ts,json,css}"

# Custom config
biome lint --config custom-biome.json src/
```

### Lintro Wrapper

```python
# Check linting
biome_tool = BiomeTool()
biome_tool.set_options()
result = biome_tool.check(["src/main.js", "src/utils.ts"])

# Fix issues
fix_result = biome_tool.fix(["src/main.js", "src/utils.ts"])
```

## Recommendations

### When to Use Core Biome

- Need specific rule configuration at runtime
- Require custom reporters or output formats
- Working with non-standard file patterns
- Need advanced VCS integration or caching
- Require unsafe fixes or rule suppressions

### When to Use Lintro Wrapper

- Part of multi-tool linting pipeline
- Need consistent issue reporting across tools
- Want simplified configuration management
- Require programmatic integration with Python workflows
- Need unified fix tracking across multiple tools

## Configuration Strategy

The Lintro wrapper relies on Biome's configuration files:

- `biome.json`
- `biome.jsonc`

For runtime customization, users should modify these config files rather than passing
CLI options. Biome also respects `.biomeignore` files natively.

## Priority and Conflicts

Biome is configured with:

- **Priority**: 50
- **Tool Type**: LINTER
- **Conflicts**: None (can run alongside formatters)
- **Execution Order**: Runs after formatters like Prettier (priority 80) due to lower
  priority value

Biome has priority 50 and Prettier has priority 80, meaning Prettier runs before Biome
since higher numeric priority values execute first. This ensures that formatting happens
before linting, which is the recommended workflow.

## Migration from ESLint

Biome provides excellent ESLint compatibility:

- **Rule Coverage**: 340+ rules covering most ESLint use cases
- **Performance**: Significantly faster than ESLint due to Rust implementation
- **Language Support**: Adds JSON and CSS linting not available in ESLint
- **Configuration**: Biome can migrate ESLint configs with
  `biome migrate eslint --write`

For projects migrating from ESLint to Biome:

1. Run `biome migrate eslint --write` to convert config
2. Test Biome on your codebase
3. Gradually replace ESLint usage with Biome
4. Remove ESLint dependencies once migration is complete
