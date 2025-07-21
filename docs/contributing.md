# Contributing to Lintro

Thank you for your interest in contributing to Lintro! This document provides guidelines and information for contributors.

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/TurboCoder13/py-lintro.git
   cd py-lintro
   ```

2. **Install dependencies:**

   ```bash
   uv sync --dev
   ```

3. **Run tests:**

   ```bash
   ./scripts/run-tests.sh
   ```

4. **Run Lintro on the codebase:**
   ```bash
   ./scripts/local-lintro.sh check --table-format
   ```

### Docker Development

For consistent development environment:

```bash
# Run tests in Docker
./scripts/docker-test.sh

# Run Lintro in Docker
./scripts/docker-lintro.sh check --table-format
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards and make your changes.

### 3. Test Your Changes

```bash
# Run the full test suite
./scripts/run-tests.sh

# Run specific tests
uv run pytest tests/test_ruff_integration.py

# Run Lintro on your changes
./scripts/local-lintro.sh check --format grid
```

### 4. Commit Your Changes

Follow the commit message format:

```
type: brief description

- detailed point 1
- detailed point 2
- detailed point 3
```

Types: `feature`, `bug-fix`, `docs`, `style`, `refactor`, `opt`, `tests`, `build`, `ci`

### 5. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python Code

- **Python Version:** 3.13+
- **Package Manager:** uv
- **Type Hints:** Required for all functions and methods
- **Docstrings:** Google Style Guide format
- **Formatting:** ruff
- **Linting:** ruff + darglint

### Code Style

```python
from typing import Optional

def example_function(
    param1: str,
    param2: Optional[int] = None,
) -> bool:
    """Example function with proper type hints and docstring.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")

    return True
```

### File Organization

- **Dataclasses:** Each in a separate file
- **String Enums:** Use `StrEnum` and `auto()`
- **Imports:** No unnecessary typing imports for modules

## Testing

### Running Tests

```bash
# Full test suite
./scripts/run-tests.sh

# Specific test file
uv run pytest tests/test_ruff_integration.py

# With verbose output
./scripts/run-tests.sh --verbose

# Docker tests
./scripts/docker-test.sh
```

### Test Coverage

Tests should maintain good coverage:

```bash
# Run with coverage
uv run pytest --cov=lintro --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

Integration tests verify that Lintro works correctly with external tools:

- `test_ruff_integration.py` - Python linting and formatting
- `test_darglint_integration.py` - Docstring validation
- `test_prettier_integration.py` - JavaScript/JSON formatting
- `test_yamllint_integration.py` - YAML linting
- `test_hadolint_integration.py` - Dockerfile linting

## Tool Integration

### Adding a New Tool

1. **Create the tool implementation:**

   - Add to `lintro/tools/implementations/`
   - Inherit from `ToolBase`
   - Implement required methods

2. **Create the parser:**

   - Add to `lintro/parsers/`
   - Create issue model and parser

3. **Create the formatter:**

   - Add to `lintro/formatters/tools/`
   - Handle tool-specific output formatting

4. **Add tests:**

   - Create integration test file
   - Test direct tool execution
   - Test through Lintro

5. **Update tool registry:**
   - Add to `ToolEnum`
   - Update tool manager

### Example Tool Structure

```
lintro/
├── tools/implementations/
│   └── tool_example.py
├── parsers/example/
│   ├── example_issue.py
│   └── example_parser.py
└── formatters/tools/
    └── example_formatter.py
```

## Documentation

### Updating Documentation

- **README.md:** Main project documentation
- **docs/:** Detailed documentation
- **Docstrings:** Code documentation
- **Comments:** Complex logic explanation

### Documentation Standards

- Use clear, concise language
- Include examples
- Keep up-to-date with code changes
- Use proper markdown formatting

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally (`./scripts/run-tests.sh`)
- [ ] All tests pass in Docker (`./scripts/docker-test.sh`)
- [ ] Documentation is updated
- [ ] Type hints are added
- [ ] Docstrings are updated

### PR Description

Include:

- **Summary:** Brief description of changes
- **Motivation:** Why the change is needed
- **Changes:** Detailed list of changes
- **Testing:** How to test the changes
- **Screenshots:** If UI changes are involved

## Code Review Process

1. **Automated Checks:** CI/CD pipeline runs tests and linting
2. **Review:** At least one maintainer reviews the PR
3. **Feedback:** Address any review comments
4. **Merge:** PR is merged after approval

## Getting Help

- **Issues:** Use GitHub issues for bugs and feature requests
- **Discussions:** Use GitHub discussions for questions
- **Documentation:** Check the docs/ directory

## Release Process

### Versioning

Follow semantic versioning (SemVer):

- **Major:** Breaking changes
- **Minor:** New features (backward compatible)
- **Patch:** Bug fixes (backward compatible)

### Release Steps

1. Update version in `pyproject.toml`
2. Update changelog
3. Create release tag
4. Publish to PyPI

## License

By contributing to Lintro, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Lintro! 🎉
