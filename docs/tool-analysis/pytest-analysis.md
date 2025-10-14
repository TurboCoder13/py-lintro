# Pytest Tool Analysis

## Overview

Pytest is a mature full-featured Python testing tool that helps you write better programs. This analysis compares Lintro's wrapper implementation with the core pytest tool.

## Core Tool Capabilities

Pytest provides extensive testing capabilities including:

- **Test Discovery**: Automatic discovery of test files and functions
- **Assertions**: Simple assert statements with detailed failure reporting
- **Fixtures**: Dependency injection system for test setup and teardown
- **Parametrization**: Run the same test with different data sets
- **Markers**: Categorize and selectively run tests
- **Plugins**: Extensive plugin ecosystem for additional functionality
- **Output Formats**: Multiple output formats including JSON, JUnit XML, and plain text
- **Configuration**: Support for `pyproject.toml`, `pytest.ini`, and command-line options
- **Coverage Integration**: Works with coverage.py for test coverage reporting
- **Parallel Execution**: Support for parallel test execution with pytest-xdist

## Lintro Implementation Analysis

### ✅ Preserved Features

**Core Functionality:**

- ✅ **Test Execution**: Full preservation through `pytest` command
- ✅ **Output Formats**: Supports JSON, JUnit XML, and plain text output
- ✅ **Configuration**: Respects `pyproject.toml` and `pytest.ini`
- ✅ **File Targeting**: Supports Python test file patterns (`test_*.py`, `*_test.py`)
- ✅ **Failure Detection**: Captures test failures and errors
- ✅ **Verbose Output**: Configurable verbosity levels
- ✅ **Traceback Format**: Configurable traceback display
- ✅ **Max Failures**: Configurable maximum number of failures before stopping

**Command Execution:**

```python
# From tool_pytest.py
cmd = self._get_executable_command("pytest") + ["-v", "--tb", "short", "--maxfail", "1"]
# For JSON output:
cmd = self._get_executable_command("pytest") + ["--json-report", "--json-report-file=pytest-report.json"]
# For JUnit XML output:
cmd = self._get_executable_command("pytest") + ["--junitxml", "report.xml"]
```

**Configuration Options:**

- ✅ **Verbosity**: `verbose` parameter
- ✅ **Traceback Format**: `tb` parameter (short, long, auto, line, native)
- ✅ **Max Failures**: `maxfail` parameter
- ✅ **Header Control**: `no_header` parameter
- ✅ **Warnings**: `disable_warnings` parameter
- ✅ **JSON Report**: `json_report` parameter
- ✅ **JUnit XML**: `junitxml` parameter

### 🔄 Enhanced Features

**Lintro-Specific Enhancements:**

- 🔄 **Test Mode Isolation**: Adds `--strict-markers` and `--strict-config` in test mode
- 🔄 **Timeout Management**: Configurable timeout (default 300 seconds)
- 🔄 **Priority System**: High priority (90) for test execution
- 🔄 **File Pattern Matching**: Automatic discovery of test files
- 🔄 **Output Parsing**: Multiple output format parsing with fallback

### ❌ Limitations

**Not Implemented:**

- ❌ **Plugin Support**: No direct plugin management
- ❌ **Coverage Integration**: No built-in coverage reporting
- ❌ **Parallel Execution**: No parallel test execution support
- ❌ **Custom Markers**: No custom marker definition
- ❌ **Fixture Management**: No fixture creation or management
- ❌ **Parametrization**: No parametrized test creation
- ❌ **Test Collection**: No test collection without execution

## Implementation Details

### Parser Support

The pytest parser supports multiple output formats:

1. **JSON Format**: Parses pytest-json-report output
2. **JUnit XML**: Parses JUnit XML output
3. **Plain Text**: Parses standard pytest text output

### Issue Model

```python
@dataclass
class PytestIssue:
    file: str
    line: int
    test_name: str
    message: str
    test_status: str
    duration: float | None = None
    node_id: str | None = None
```

### Formatter Support

The pytest formatter provides table-based output with columns:
- File: Test file path
- Line: Line number of failure
- Test Name: Name of the failing test
- Status: Test status (FAILED, ERROR, etc.)
- Message: Error message or failure description

## Usage Examples

### Basic Test Execution

```bash
# Run all tests
lintro check --tool pytest

# Run specific test files
lintro check --tool pytest test_example.py

# Run with custom options
lintro check --tool pytest --verbose --tb long --maxfail 5
```

### Configuration File Support

```toml
# pyproject.toml
[tool.pytest]
addopts = "-v --tb=short --maxfail=1"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
```

### Output Formats

```bash
# JSON output
lintro check --tool pytest --json-report

# JUnit XML output
lintro check --tool pytest --junitxml report.xml

# Plain text output (default)
lintro check --tool pytest
```

## Integration with Lintro

### Tool Type

- **Type**: LINTER
- **Priority**: 90 (high priority for test execution)
- **Timeout**: 300 seconds (5 minutes)
- **Can Fix**: False (pytest doesn't fix code, it runs tests)

### File Patterns

- `test_*.py`: Standard pytest test file pattern
- `*_test.py`: Alternative test file pattern

### Dependencies

- Requires pytest to be installed
- Optional: pytest-json-report for JSON output
- Optional: pytest-xdist for parallel execution

## Best Practices

1. **Test Organization**: Use consistent test file naming conventions
2. **Configuration**: Use `pyproject.toml` for pytest configuration
3. **Output Format**: Choose appropriate output format for your CI/CD pipeline
4. **Timeout**: Set appropriate timeout for your test suite
5. **Max Failures**: Use `maxfail=1` for fast feedback in development

## Future Enhancements

Potential improvements for the pytest integration:

1. **Plugin Support**: Add support for popular pytest plugins
2. **Coverage Integration**: Integrate with coverage.py
3. **Parallel Execution**: Add support for parallel test execution
4. **Test Discovery**: Add test collection without execution
5. **Fixture Management**: Add fixture creation and management
6. **Parametrization**: Add parametrized test creation
7. **Custom Markers**: Add custom marker definition
8. **Performance Metrics**: Add test execution time tracking
9. **Test Results**: Add test result summary and statistics
10. **CI Integration**: Add CI-specific configurations and optimizations
