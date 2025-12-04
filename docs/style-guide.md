# Lintro Style Guide

This document outlines the coding standards and best practices for the Lintro project.

## Python Code Style

### General Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style
- Use [Darglint](https://github.com/terrencepreilly/darglint) for docstring argument
  checking
- Use [Prettier](https://prettier.io/) for frontend code formatting

### Type Hints

- All functions and methods must include type hints
- All classes must include type hints for attributes
- Prefer using pipe operator (`|`) over `Optional` for optional types
- Avoid importing from `typing` for built-in types like `list`, `dict`, etc.
- Use `Any` sparingly and only when absolutely necessary

```python
# ❌ Bad
from typing import Dict, List, Optional

def process_data(data: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
    pass

# ✅ Good
def process_data(data: list[dict[str, str]] | None = None) -> dict[str, str] | None:
    pass
```

### Docstrings

- All modules, classes, functions, and methods must have docstrings
- Use Google-style docstrings
- Include parameter descriptions, return value descriptions, and raised exceptions

```python
def calculate_total(items: list[dict[str, float]]) -> float:
    """
    Calculate the total value of all items.

    Args:
        items: List of items with their prices

    Returns:
        Total value of all items

    Raises:
        ValueError: If any item has a negative price
    """
    pass
```

### Function and Method Definitions

- For function/method declarations with more than 1 parameter, use trailing commas and
  format with Ruff
- Same applies to function/method calls with multiple arguments

```python
# Function definition with multiple parameters
def complex_function(
    param1: str,
    param2: int,
    param3: bool = False,
) -> str:
    pass

# Function call with multiple arguments
result = complex_function(
    "value1",
    42,
    True,
)
```

### Imports

- Use `ruff` to automatically sort imports
- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use absolute imports
- Use explicit imports
- Use `from __future__ import annotations` in Python files

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import click
from tabulate import tabulate

# Local imports
from lintro.tools import Tool
from lintro.utils import format_output
```

### Error Handling

- Use specific exception types rather than catching all exceptions
- Include meaningful error messages
- Use context managers (`with` statements) for resource management

```python
# ❌ Bad
try:
    process_file(filename)
except Exception as e:
    print(f"Error: {e}")

# ✅ Good
try:
    process_file(filename)
except FileNotFoundError:
    print(f"File {filename} not found")
except PermissionError:
    print(f"Permission denied when accessing {filename}")
```

### Variable Naming

- Use descriptive variable names
- Use `snake_case` for variables, functions, and methods
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants

```python
# Constants
MAX_RETRY_COUNT = 5
DEFAULT_TIMEOUT = 30

# Variables
user_input = input("Enter your name: ")
file_path = "/path/to/file.txt"

# Functions
def calculate_total(items):
    pass

# Classes
class FileProcessor:
    pass
```

## Project Structure

### Directory Layout

- Keep related files together
- Use meaningful directory names
- Separate code, tests, and documentation

```text
lintro/
├── __init__.py
├── cli.py
├── tools/
│   ├── __init__.py
│   ├── darglint.py
│   ├── flake8.py
│   ├── hadolint.py
│   ├── pydocstyle.py
│   └── ruff.py
└── utils/
    ├── __init__.py
    └── formatting.py
tests/
├── __init__.py
├── test_cli.py
└── tools/
    ├── test_flake8.py
    └── test_isort.py
```

### File Organization

- Each module should have a single, well-defined responsibility
- Keep files to a reasonable size (< 500 lines if possible)
- Use meaningful file names that reflect their contents

## Commit Messages

- Use the imperative mood in commit messages
- Start with a prefix indicating the type of change
- Include a brief summary of changes in the first line
- Optionally include a more detailed description in subsequent lines

Prefixes:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration

```text
feat: add support for mypy integration

- Add MyPyTool class
- Update CLI to include mypy in available tools
- Add tests for mypy integration
```

## Testing

- Write tests for all new features and bug fixes
- Aim for high test coverage (>= 90%)
- Use pytest for testing
- Use fixtures to reduce test code duplication
- Use meaningful test names that describe what is being tested

```python
def test_darglint_tool_checks_docstrings_correctly():
    # Test implementation
    pass

def test_prettier_tool_formats_code_correctly():
    # Test implementation
    pass
```

## Documentation

- Keep documentation up-to-date with code changes
- Document all public APIs
- Include examples in documentation
- Use Markdown for documentation files

## Tool Configuration

When adding new tools to Lintro, ensure they follow these guidelines:

1. Implement the `Tool` interface
2. Configure tool conflicts and priorities
3. Include comprehensive docstrings
4. Add appropriate tests
5. Update documentation

Example tool configuration:

```python
class ExampleTool(Tool):
  """Example tool integration."""

  name = "example"
  description = "Example tool for demonstration"
  can_fix = False

  config = ToolConfig(
      priority=60,
      conflicts_with=[],
      file_patterns=["*.py"],
  )
```

## Code Review

When reviewing code, check for:

1. Adherence to this style guide
2. Correctness and completeness
3. Test coverage
4. Documentation
5. Performance considerations
6. Security considerations

## Continuous Integration

All code should pass the following checks before being merged:

1. All tests pass
2. Code is checked with Lintro
3. Test coverage meets minimum threshold

## Code Formatting

We use the Lintro tool for code formatting and linting:

### Python Code Formatting

1. Use Lintro for checking:

   ```bash
   lintro check [PATH]
   ```

2. Use Lintro for formatting:

   ```bash
   lintro format [PATH]
   ```

3. Format specific files:

   ```bash
   lintro format file1.py file2.py
   ```

4. Format with custom options:

   ```bash
   lintro format --tools ruff --core-options "ruff:--line-length=100" [PATH]
   ```

### Style Guide Project Structure

```text
lintro/
├── lintro/
│   ├── __init__.py
│   ├── cli.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ruff.py
│   │   ├── flake8.py
│   │   ├── pydocstyle.py
│   │   └── darglint.py
│   └── utils/
│       ├── __init__.py
│       └── output.py
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_cli_commands.py
    ├── test_cli_commands_extended.py
    ├── test_cli_commands_advanced.py
    ├── test_cli_utils.py
    └── test_cli_output.py
```

<!-- markdownlint-disable MD025 -->

# Formatter and Output Style Architecture

## Overview

Lintro supports flexible, extensible output formatting for all tools. This is achieved
by separating:

- **Table structure** (columns, extraction) per tool
- **Output style** (plain, markdown, etc.)

This allows:

- Each tool to define its own columns and row extraction logic
- Easy addition of new output styles (Markdown, HTML, JSON, etc.)
- Consistent, DRY, and testable formatting logic

---

## Key Components

### 1. TableDescriptor (per tool)

- Describes the columns and how to extract them from an issue object.
- Each tool provides its own TableDescriptor if needed.

```python
from lintro.formatters.base_formatter import TableDescriptor
from typing import List


class DarglintTableDescriptor(TableDescriptor):
  def get_columns(self) -> List[str]:
    return ["File", "Line", "Code", "Message"]

  def get_row(self, issue) -> List[str]:
    return [issue.file, str(issue.line), issue.code, issue.message]
```

### 2. OutputStyle (per output format)

- Defines how to render a table (columns + rows) as a string.
- Implemented in `lintro/formatters/styles/`.

```python

from lintro.formatters.core.output_style import OutputStyle
from typing import List, Any


class MarkdownStyle(OutputStyle):
  def format(self, columns: List[str], rows: List[List[Any]]) -> str:
# ...
```

### 3. Tool Formatter

- Wires up the descriptor, issues, and style.
- Example for darglint:

```python
from lintro.formatters.tools.darglint_formatter import DarglintTableDescriptor, STYLE_MAP


def format_darglint_issues(issues, style="plain"):
  descriptor = DarglintTableDescriptor()
  columns = descriptor.get_columns()
  rows = [descriptor.get_row(issue) for issue in issues]
  formatter = STYLE_MAP.get(style, PlainStyle())
  return formatter.format(columns, rows)
```

---

## How to Add a New Output Style

1. Create a new class in `lintro/formatters/styles/` inheriting from `OutputStyle`.
2. Implement the `format(columns, rows)` method.
3. Register the new style in the tool's `STYLE_MAP`.

---

## How to Add/Change a Tool's Table Structure

1. Create a new `TableDescriptor` for the tool if needed.
2. Implement `get_columns()` and `get_row(issue)`.
3. Use this descriptor in the tool's formatter.

---

## CLI Integration

- The CLI can expose a `--output-style` flag to let users select the output style (e.g.,
  `plain`, `markdown`).
- The selected style is passed to the tool formatter, which uses the appropriate
  OutputStyle.

---

## Example Usage

```python
issues = parse_darglint_output(raw_output)
print(format_darglint_issues(issues, style="markdown"))
```

---

## Benefits

- Extensible: Add new styles or tool structures easily
- Consistent: All tools use the same formatting pipeline
- Testable: Each style and descriptor can be unit tested
- Flexible: Tools with different columns or special needs are supported
