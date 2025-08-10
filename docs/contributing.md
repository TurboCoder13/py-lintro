# Contributing to Lintro

Thank you for your interest in contributing to Lintro! This document provides guidelines and information for contributors.

## Conventional Commits (required)

We use Conventional Commits (Angular style) to drive automated versioning and releases.

- Format: `type(scope): subject` (scope optional)
- Types: feat, fix, docs, refactor, perf, test, chore, ci, style, revert
- Use imperative mood (e.g., "add", not "added").

Examples:

```
feat: add new configuration option

- support for custom tool paths
- update documentation
- add integration tests
```

PR titles must also follow Conventional Commits. A PR check enforces this and
will comment with guidance if invalid.

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

Release automation:

- Merges to `main` run semantic-release to determine the next version from commits and tag the repo.
- Tag push publishes to PyPI (OIDC) and creates a GitHub Release with artifacts.

For detailed contribution guidelines, see the project documentation or contact a maintainer.
