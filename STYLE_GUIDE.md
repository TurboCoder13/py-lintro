# Lintro Style Guide

This document outlines the coding standards and best practices for the Lintro project.

## Python Code Style

### General Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use [MyPy](https://mypy.readthedocs.io/) for static type checking
- Use [Pylint](https://pylint.pycqa.org/) for additional linting
- Use [pydocstyle](https://www.pydocstyle.org/) for docstring style checking
- Use [darglint](https://github.com/terrencepreilly/darglint) for docstring correctness

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

- For function/method declarations with more than 1 parameter, use trailing commas and format with Black
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

- Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- Use absolute imports rather than relative imports
- Use `isort` to automatically sort imports

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

```
lintro/
├── __init__.py
├── cli.py
├── tools/
│   ├── __init__.py
│   ├── black.py
│   ├── darglint.py
│   ├── flake8.py
│   ├── hadolint.py
│   ├── isort.py
│   ├── mypy.py
│   ├── prettier.py
│   ├── pydocstyle.py
│   ├── pylint.py
│   ├── semgrep.py
│   ├── terraform.py
│   └── yamllint.py
└── utils/
    ├── __init__.py
    └── formatting.py
tests/
├── __init__.py
├── test_cli.py
└── tools/
    ├── test_black.py
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

```
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
def test_black_tool_formats_code_correctly():
    # Test implementation
    pass

def test_black_tool_handles_syntax_errors_gracefully():
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
class MyPyTool(Tool):
    """MyPy static type checker integration."""

    name = "mypy"
    description = "Static type checker for Python"
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
2. Code is formatted with Black
3. Imports are sorted with isort
4. No Flake8 warnings
5. Type checking with MyPy passes
6. Test coverage meets minimum threshold 
7. No Pylint warnings 