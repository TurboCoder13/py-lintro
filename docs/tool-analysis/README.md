# Tool Analysis Documentation

This directory contains comprehensive analyses comparing Lintro's wrapper
implementations with the core tools themselves.

## Available Analyses

### [Ruff Analysis](./ruff-analysis.md)

<!-- markdownlint-disable MD036 -->

**Comprehensive Python Static Code Analyzer**

- ✅ **Preserved**: Linting, formatting, auto-fixing, rule selection, configuration
  files
- ⚠️ **Limited**: Runtime rule customization, watch mode, cache control, statistics
- 🚀 **Enhanced**: Combined linting/formatting, smart fix handling, unified API

### [pydoclint Analysis](./pydoclint-analysis.md)

**Python Docstring Linter**

- ✅ **Preserved**: Docstring validation, style enforcement, error codes
- ⚠️ **Limited**: Runtime configuration, JSON output, parallel processing
- 🚀 **Enhanced**: Issue normalization, Python integration, error parsing

### [Prettier Analysis](./prettier-analysis.md)

**Code Formatter for JavaScript, TypeScript, CSS, HTML**

- ✅ **Preserved**: Core formatting, configuration files, auto-fixing
- ⚠️ **Limited**: Runtime options, parser specification, debug capabilities
- 🚀 **Enhanced**: Unified API, structured output, pipeline integration

### [Oxc Analysis](./oxc-analysis.md)

**Fast Rust-based JavaScript/TypeScript Linter and Formatter**

- ✅ **Preserved**: Linting, formatting, auto-fix, native config discovery, JSON output
- ⚠️ **Limited**: Plugin control, stdin piping, type-aware linting
- 🚀 **Enhanced**: Normalized issues, unified API, much faster than traditional tools

### [Yamllint Analysis](./yamllint-analysis.md)

**YAML Linter for Syntax and Style**

- ✅ **Preserved**: Syntax validation, style checking, configuration files, error codes
- ⚠️ **Limited**: Runtime rule customization, schema validation, auto-fixing
- 🚀 **Enhanced**: Issue normalization, Python integration, error parsing

### [Markdownlint Analysis](./markdownlint-analysis.md)

**Markdown Style Linter (markdownlint-cli2)**

- ✅ **Preserved**: Markdown rule enforcement, native config and ignore support
- ⚠️ **Limited**: No auto-fix, limited CLI pass-through, single-process execution
- 🚀 **Enhanced**: Central line-length injection, normalized issues, safe version checks

### [Hadolint Analysis](./hadolint-analysis.md)

### [Bandit Analysis](./bandit-analysis.md)

**Python Security Linter**

- ✅ **Preserved**: Recursive scanning, severity/confidence gates, config/baseline
- ⚠️ **Defaults**: JSON output and quiet logs for stable parsing
- 🚀 **Notes**: Robust JSON extraction; normalized reporting

### [Actionlint Analysis](./actionlint-analysis.md)

**GitHub Actions Workflow Linter**

- ✅ **Preserved**: Default output, rule detection, workflow path targeting
- ⚠️ **Defaults**: No flags; filtered to `/.github/workflows/`
- 🚀 **Notes**: Normalized parsing and formatting

**Dockerfile Linter for Best Practices**

- ✅ **Preserved**: Dockerfile analysis, shell script linting, best practices, security
  scanning
- ⚠️ **Limited**: Runtime rule customization, Docker Compose support, auto-fixing
- 🚀 **Enhanced**: Issue normalization, Python integration, error parsing
<!-- markdownlint-enable MD036 -->

### [Black Analysis](./black-analysis.md)

### Python Code Formatter

- ✅ **Preserved**: Core formatting, pyproject config, check and write flows
- ⚙️ **Pass-throughs**: `line_length`, `target_version`, `fast`, `preview`, `diff`
- 🚀 **Notes**: Cooperates with Ruff via Lintro post-check policy

### [Mypy Analysis](./mypy-analysis.md)

### Python Static Type Checker

- ✅ **Preserved**: Strict checking, config discovery, JSON output with codes/columns
- ⚠️ **Limited**: No plugin flag pass-through, incremental/cache tuning, warn-\* toggles
- 🚀 **Enhanced**: Strict-by-default, timeout handling, normalized results, default
  excludes

### [Pytest Analysis](./pytest-analysis.md)

### Python Test Runner

- ✅ **Preserved**: Test discovery/execution, JSON/JUnit/plain outputs, config respect
- ⚠️ **Limited**: No impact analysis or mutation testing; plugin install not managed
- 🚀 **Enhanced**: Coverage helpers, parallel presets, plugin/marker/fixture listings

## Analysis Framework

Each analysis follows a consistent structure:

1. **Overview**: Tool purpose and comparison scope
2. **Core Tool Capabilities**: Full feature set of the original tool
3. **Lintro Implementation Analysis**:
   - ✅ **Preserved Features**: What's maintained from the core tool
   - ⚠️ **Limited/Missing Features**: What's not available in the wrapper
   - 🚀 **Enhancements**: What Lintro adds beyond the core tool
4. **Usage Comparison**: Side-by-side examples
5. **Configuration Strategy**: How configuration is handled
6. **Recommendations**: When to use each approach

## Key Findings

### Common Patterns

**Preserved Across All Tools:**

- Core functionality and error detection
- Configuration file respect
- Essential CLI capabilities
- Error code systems

**Common Limitations:**

- Runtime configuration options
- Advanced output formats
- Performance optimizations
- Tool-specific advanced features

**Common Enhancements:**

- Unified API across all tools
- Structured `Issue` objects
- Python-native integration
- Pipeline-friendly design

### Trade-offs Summary

| Aspect          | Core Tools                    | Lintro Wrappers                     |
| --------------- | ----------------------------- | ----------------------------------- |
| **Flexibility** | High (all CLI options)        | Limited (config files only)         |
| **Performance** | Optimized (parallel, caching) | Sequential processing (no parallel) |
| **Integration** | CLI-based                     | Python-native                       |
| **Consistency** | Tool-specific APIs            | Unified interface                   |
| **Output**      | Various formats               | Standardized objects                |

## Use Case Recommendations

<!-- markdownlint-disable MD026 -->

### Use Core Tools When:

- Need maximum configuration flexibility
- Require advanced performance features
- Want tool-specific output formats
- Working with large codebases
- Need specialized tool features

### Use Lintro Wrappers When:

- Building multi-tool pipelines
- Need consistent issue reporting
- Want Python-native integration
- Prefer simplified configuration
- Require aggregated results

<!-- markdownlint-enable MD026 -->

## Future Enhancement Opportunities

1. **Configuration Pass-through**: Runtime option support for all tools
2. **Performance**: Parallel processing capabilities (currently sequential)
3. **Output Formats**: JSON and custom formatter support
4. **Plugin Systems**: Custom checker integration
5. **Metrics**: Code quality scoring and reporting
6. **Auto-fixing**: Enhanced auto-fixing for tools that support it
7. **Schema Validation**: Built-in schema validation for YAML and other formats
