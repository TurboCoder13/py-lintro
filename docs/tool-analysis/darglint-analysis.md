# Darglint Tool Analysis

## Overview

Darglint is a Python docstring linter that checks docstring style and completeness
against function signatures. This analysis compares Lintro's wrapper implementation with
the core Darglint tool.

## Core Tool Capabilities

Darglint provides comprehensive docstring analysis including:

- **Style checking**: Google, Sphinx, NumPy docstring formats
- **Completeness validation**: Missing parameters, return types, raises clauses
- **Type checking**: Parameter and return type consistency
- **Configuration options**: `--docstring-style`, `--strictness`, `--ignore-regex`
- **Output formats**: Default, JSON, custom formatters
- **Error codes**: Specific codes for different violation types (D100-D417)

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Docstring validation**: Full preservation of docstring checking capabilities
- ✅ **Style enforcement**: Supports all docstring styles (Google, Sphinx, NumPy)
- ✅ **Completeness checking**: Detects missing parameters, returns, raises
- ✅ **Error categorization**: Preserves Darglint's error code system
- ✅ **File targeting**: Supports Python file analysis

**Command Execution:**

```python
# From tool_darglint.py
cmd = ["darglint"] + self.files
result = subprocess.run(cmd, capture_output=True, text=True)
```

**Error Code Preservation:**

- ✅ **D100-D107**: Missing docstrings (module, class, method, function, etc.)
- ✅ **D200-D214**: Whitespace and formatting issues
- ✅ **D300-D302**: Triple quotes usage
- ✅ **D400-D417**: Content requirements (summary, parameters, returns, etc.)

### ⚠️ Limited/Missing Features

**Configuration Control:**

- ⚠️ **Runtime docstring style**: Prefer config; proposed pass-through
  `darglint:docstring_style=google`.
- ⚠️ **Strictness levels**: Already exposed (default `full`); can be overridden;
  document CLI mapping.
- ⚠️ **Ignore patterns**: `ignore_regex` is exposed; emphasize usage via
  `--tool-options`.
- ❌ **Custom error selection**: No runtime control over which errors to check

**Output Customization:**

- ❌ **JSON output**: No access to `--output-format json`
- ❌ **Custom formatters**: Cannot use custom output formatters
- ❌ **Verbose mode**: No access to detailed error explanations

**Advanced Features:**

- ❌ **Line length control**: Cannot set docstring line length limits
- ❌ **Type annotation integration**: Limited type checking configuration
- ❌ **Recursive directory**: Basic file listing vs Darglint's built-in recursion

**Performance Options:**

- ❌ **Parallel processing**: No access to Darglint's built-in parallelization
- ❌ **Caching**: No access to incremental checking features

### 🚀 Enhancements

**Unified Interface:**

- ✅ **Consistent API**: Same interface as other linting tools (`check()`,
  `set_options()`)
- ✅ **Structured output**: Issues formatted as standardized `Issue` objects
- ✅ **Python integration**: Native Python object handling vs CLI parsing
- ✅ **Pipeline integration**: Seamless integration with other tools

**Enhanced Error Processing:**

- ✅ **Issue normalization**: Converts Darglint output to standard Issue format:

  ```python
  Issue(
      file_path=match.group(1),
      line_number=int(match.group(2)),
      column_number=int(match.group(3)) if match.group(3) else None,
      error_code=match.group(4),
      message=match.group(5).strip(),
      severity="error"
  )
  ```

**Error Parsing:**

### 🔧 Proposed runtime pass-throughs

- `--tool-options darglint:docstring_style=google`
- `--tool-options darglint:strictness=short`
- `--tool-options darglint:verbosity=1`

- ✅ **Regex-based parsing**: Robust parsing of Darglint's output format
- ✅ **Multi-line support**: Handles complex error messages
- ✅ **Position tracking**: Accurate line and column number extraction

**File Management:**

- ✅ **Extension filtering**: Automatic Python file detection
- ✅ **Batch processing**: Efficient handling of multiple files
- ✅ **Error aggregation**: Collects all issues across files

## Usage Comparison

### Core Darglint

```bash
# Basic checking
darglint src/module.py

# With style specification
darglint --docstring-style google src/

# Strict mode with custom ignores
darglint --strictness full --ignore-regex "^test_" src/

# JSON output
darglint --output-format json src/module.py
```

### Lintro Wrapper

```python
# Basic checking
darglint_tool = DarglintTool()
darglint_tool.set_files(["src/module.py"])
issues = darglint_tool.check()

# Process results
for issue in issues:
    print(f"{issue.file_path}:{issue.line_number} {issue.error_code}: {issue.message}")
```

## Configuration Strategy

### Core Tool Configuration

Darglint uses configuration files:

- `.darglint`
- `setup.cfg` `[darglint]` section
- `pyproject.toml` `[tool.darglint]` section

### Lintro Approach

The wrapper relies on Darglint's configuration files for:

- Docstring style selection
- Strictness levels
- Ignore patterns
- Error code selection

## Error Code Mapping

Lintro preserves all Darglint error codes:

| Category               | Codes     | Description                                |
| ---------------------- | --------- | ------------------------------------------ |
| **Missing Docstrings** | D100-D107 | Module, class, method, function docstrings |
| **Whitespace**         | D200-D214 | Formatting and whitespace issues           |
| **Quotes**             | D300-D302 | Triple quote usage                         |
| **Content**            | D400-D417 | Summary, parameters, returns, raises       |

## Recommendations

### When to Use Core Darglint

- Need runtime configuration changes
- Require JSON output for tooling integration
- Want parallel processing for large codebases
- Need custom ignore patterns per run
- Require specific strictness levels per execution

### When to Use Lintro Wrapper

- Part of multi-tool linting pipeline
- Need consistent issue reporting across tools
- Want Python object integration
- Require aggregated results across multiple tools
- Need standardized error handling

## Limitations and Workarounds

### Missing Runtime Configuration

**Problem**: Cannot change docstring style at runtime **Workaround**: Use configuration
files (`.darglint`, `setup.cfg`, `pyproject.toml`)

### No JSON Output

**Problem**: Cannot get structured output from core tool **Workaround**: Lintro provides
structured `Issue` objects

### Limited Ignore Capabilities

**Problem**: Cannot use runtime ignore patterns **Workaround**: Configure ignore
patterns in Darglint config files

## Future Enhancement Opportunities

1. **Configuration Pass-through**: Allow runtime options via `set_options()`
2. **Advanced Filtering**: Post-processing filters for issue selection
3. **Custom Formatters**: Plugin system for output formatting
4. **Performance**: Leverage Darglint's parallel processing capabilities
5. **Type Integration**: Enhanced type annotation checking
