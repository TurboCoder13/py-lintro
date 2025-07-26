# Contributing to Lintro

Thank you for your interest in contributing to Lintro! This document provides guidelines and information for contributors.

## New Section: How to Write High-Quality Commit Messages

Writing clear and descriptive commit messages helps everyone understand the history and intent of changes. Please follow these guidelines:

- **Use the imperative mood** (e.g., "add feature" not "added feature").
- **Start with a type prefix**: `feature`, `bug-fix`, `docs`, `style`, `refactor`, `opt`, `tests`, `build`, `ci`.
- **Provide a concise summary** on the first line.
- **Add bullet points** for details if needed.

**Example:**

```
feature: add new configuration option

- support for custom tool paths
- update documentation
- add integration tests
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/TurboCoder13/py-lintro.git
   cd py-lintro
   ```
2. Install dependencies:
   ```bash
   uv sync --dev
   ```
3. Run tests:
   ```bash
   ./scripts/local/run-tests.sh
   ```
4. Run Lintro on the codebase:
   ```bash
   ./scripts/local/local-lintro.sh check --output-format grid
   ```

## More Information

For detailed contribution guidelines, see the project documentation or contact a maintainer.
