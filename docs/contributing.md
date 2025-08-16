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

### PR titles and version bumps

Semantic versioning is determined from the PR title (we squash-merge so the PR title becomes the merge commit):

- **minor**: `feat(...)`
- **patch**: `fix(...)`, `perf(...)`
- **major**: add `!` after type or include a `BREAKING CHANGE:` footer
- **no bump**: `docs`, `chore`, `refactor`, `style`, `test`, `ci`, `build` (unless marked breaking)

Examples:

```text
feat(cli): add --group-by option            # minor
fix(parser): handle empty config            # patch
perf(ruff): speed up large file handling    # patch
refactor(core)!: rewrite execution model    # major (breaking)
chore: update dependencies                  # no bump

# Footer form for breaking change
refactor(core): unify plugin interfaces

BREAKING CHANGE: plugins must implement run() and report()
```

Notes:

- Use imperative mood (e.g., "add", not "added").
- If work is ambiguous (e.g., a large refactor), explicitly signal with `!` or a `BREAKING CHANGE:` footer.
- The PR title validator (`.github/workflows/semantic-pr-title.yml`) enforces the format before merge.

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
