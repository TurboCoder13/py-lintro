# pydoclint Tool Analysis

## Overview

pydoclint is a Python docstring linter that validates docstrings match function
signatures. It checks for missing, extra, or incorrectly documented parameters, return
values, and raised exceptions.

## Installation

```bash
pip install pydoclint
```

Or with uv:

```bash
uv pip install pydoclint
```

## Output Format

pydoclint outputs issues with the file path on its own line, followed by indented issue
lines:

```
path/file.py
    line: DOCxxx: message
```

Example output:

```
src/module.py
    10: DOC101: Function `calculate` has 2 argument(s) in signature: ['a', 'b']. Arguments 1 to 2 are not documented.
    25: DOC201: Function `process` does not have a return section in docstring.
    40: DOC301: `__init__` has a docstring but the class doesn't.
```

## Common Error Codes

### Function/Method Arguments (DOC1xx)

| Code   | Description                                      |
| ------ | ------------------------------------------------ |
| DOC101 | Docstring has fewer arguments than signature     |
| DOC102 | Docstring has more arguments than signature      |
| DOC103 | Docstring arguments differ from signature        |
| DOC104 | Arguments in different order                     |
| DOC105 | Argument type hints don't match                  |
| DOC106 | Duplicate argument in docstring                  |
| DOC107 | No type hints in signature, not required in docs |
| DOC108 | Type hints in signature but not in docstring     |
| DOC109 | `--arg-type-hints-in-docstring` but none in docs |
| DOC110 | Not all args have type hints in docstring        |
| DOC111 | Missing `**kwargs` in docstring                  |

### Return Values (DOC2xx)

| Code   | Description                              |
| ------ | ---------------------------------------- |
| DOC201 | Missing return section in docstring      |
| DOC202 | Return section but no return in function |
| DOC203 | Return type mismatch                     |

### Class Docstrings (DOC3xx)

| Code   | Description                                       |
| ------ | ------------------------------------------------- |
| DOC301 | `__init__` has docstring but class doesn't        |
| DOC302 | Class and `__init__` both have docstring          |
| DOC303 | `__init__` should have args in its own docstring  |
| DOC304 | Class docstring has `Args` but not for `__init__` |
| DOC305 | Class docstring missing `Args` for `__init__`     |
| DOC306 | `__init__` `Args` don't belong in class docstring |

### Raises Documentation (DOC5xx)

| Code   | Description                                |
| ------ | ------------------------------------------ |
| DOC501 | Raises section but no raises in body       |
| DOC502 | Raises in body but not documented          |
| DOC503 | Raises in docstring don't match body       |
| DOC504 | Raises `AssertionError` but not documented |

### Class Attributes (DOC6xx)

| Code   | Description                             |
| ------ | --------------------------------------- |
| DOC601 | Class has fewer attributes in docstring |
| DOC602 | Class has more attributes in docstring  |
| DOC603 | Class attributes differ from docstring  |
| DOC604 | Class attributes in different order     |
| DOC605 | Class attribute type hints don't match  |

## Configuration Options

### Style

pydoclint supports three docstring styles:

- `numpy` - NumPy-style docstrings (pydoclint's native default)
- `google` - Google-style docstrings (lintro's default)
- `sphinx` - Sphinx-style docstrings

Note: While pydoclint defaults to `numpy`, lintro defaults to `google` to match common
project conventions.

### Boolean Options

- `check_return_types` - Check return type documentation (default: True)
- `check_arg_order` - Check argument order matches signature (default: True)
- `skip_checking_short_docstrings` - Skip short docstrings (default: True)
- `quiet` - Suppress non-error output (default: True)

## Lintro Configuration

In `pyproject.toml`:

```toml
[tool.lintro.pydoclint]
style = "google"
timeout = 30
```

Or via command line:

```bash
lintro chk --tools pydoclint --tool-options pydoclint:style=numpy
```

## Comparison with darglint

pydoclint is the recommended replacement for darglint:

| Feature              | pydoclint             | darglint              |
| -------------------- | --------------------- | --------------------- |
| Actively maintained  | Yes                   | Maintenance mode      |
| Python 3.11+ support | Full                  | Limited               |
| Speed                | Fast                  | Slower                |
| Output format        | Simple text           | Multiple formats      |
| Configuration        | pyproject.toml        | .darglint, setup.cfg  |
| Style support        | Google, NumPy, Sphinx | Google, Sphinx, NumPy |

## Migration from darglint

1. Install pydoclint: `pip install pydoclint`
2. Update your configuration:

**Before (darglint):**

```toml
[tool.darglint]
strictness = "full"
```

**After (pydoclint):**

```toml
[tool.pydoclint]
style = "google"
```

3. Run with lintro:

```bash
lintro chk --tools pydoclint
```

## Integration Notes

- pydoclint conflicts with darglint (both check docstrings)
- Priority: 45 (runs before formatters)
- Does not support auto-fix (documentation must be fixed manually)
- Works well with ruff's D (pydocstyle) rules for complementary coverage

## Best Practices

1. **Use with ruff D rules**: pydoclint validates content, ruff D validates format
2. **Set consistent style**: Match your project's docstring convention
3. **Enable check_arg_order**: Catches documentation that doesn't match signature order
4. **Skip short docstrings**: Single-line docstrings often don't need full documentation

## Example Usage

```bash
# Check with default settings
lintro chk --tools pydoclint .

# Check with NumPy style
lintro chk --tools pydoclint --tool-options pydoclint:style=numpy .

# Check specific files
lintro chk --tools pydoclint src/module.py
```
