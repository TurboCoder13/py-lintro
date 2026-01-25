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

pydoclint outputs issues in a simple text format:

```
path/file.py:line:col: DOCxxx: message
```

Example output:

```
src/module.py:10:5: DOC101: Function `calculate` has 2 argument(s) in signature: ['a', 'b']. Arguments 1 to 2 are not documented.
src/module.py:25:1: DOC201: Function `process` does not have a return section in docstring.
src/module.py:40:5: DOC301: Function `validate` does not have a Raises section in docstring.
```

## Common Error Codes

| Code   | Description                                      |
| ------ | ------------------------------------------------ |
| DOC101 | Missing argument in docstring                    |
| DOC102 | Extra argument in docstring                      |
| DOC103 | Argument in docstring doesn't exist in signature |
| DOC104 | Argument type mismatch                           |
| DOC105 | Argument order mismatch                          |
| DOC201 | Missing return section                           |
| DOC202 | Return type specified but no return section      |
| DOC203 | Return type mismatch                             |
| DOC301 | Missing Raises section                           |
| DOC302 | Raises documented but not raised                 |
| DOC401 | Class attribute documentation issues             |
| DOC501 | Raises section but no raises in body             |
| DOC502 | Raises not documented                            |

## Configuration Options

### Style

pydoclint supports three docstring styles:

- `google` (default) - Google-style docstrings
- `numpy` - NumPy-style docstrings
- `sphinx` - Sphinx-style docstrings

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

| Feature              | pydoclint             | darglint             |
| -------------------- | --------------------- | -------------------- |
| Actively maintained  | Yes                   | No (deprecated)      |
| Python 3.11+ support | Full                  | Limited              |
| Speed                | Fast                  | Slower               |
| Output format        | Simple text           | Multiple formats     |
| Configuration        | pyproject.toml        | .darglint, setup.cfg |
| Style support        | Google, NumPy, Sphinx | Google, Sphinx       |

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
