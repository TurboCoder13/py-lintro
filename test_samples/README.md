# Test Samples Directory

This directory contains sample files used for testing Lintro's various linting and
formatting tools.

## Directory Structure

```
test_samples/
├── fixtures/                     # Shared test fixtures
│   ├── github/                   # GitHub API response mocks
│   └── pr_comments/              # PR comment templates
└── tools/                        # Tool-specific test samples
    ├── python/                   # Python tool test files
    │   ├── ruff/                 # Ruff-specific samples
    │   ├── bandit/               # Bandit security linter samples
    │   ├── pydoclint/            # pydoclint docstring linter samples
    │   ├── mypy/                 # MyPy type checker samples
    │   └── pytest/               # Pytest test runner samples
    ├── javascript/               # JavaScript/TypeScript tool samples
    │   ├── oxfmt/                # Oxfmt formatter samples
    │   ├── oxlint/               # Oxlint linter samples
    │   └── prettier/             # Prettier formatter samples
    ├── rust/                     # Rust tool samples
    │   ├── clippy/               # Clippy linter samples
    │   └── clippy_violations/    # Clippy violation samples
    └── config/                   # Configuration file tool samples
        ├── yaml/                 # YAML linter samples
        ├── docker/               # Docker linter samples
        ├── github_actions/       # GitHub Actions linter samples
        └── markdown/             # Markdown linter samples
```

## File Naming Conventions

- `{tool}_violations.{ext}` - Files that contain intentional violations for testing
- `{tool}_clean.{ext}` - Files that should pass all checks
- `{tool}_{specific_issue}.{ext}` - Files with specific types of violations
- `*.json` - Mock data files (GitHub API responses, etc.)

## Usage

These files are used by the test suite to:

- Test tool detection and execution
- Verify parsing of tool output
- Validate error reporting and formatting
- Test integration between tools

## Maintenance

When adding new test samples:

1. Follow the directory structure above
2. Use descriptive filenames that indicate what violations they contain
3. Include comments in the files explaining what issues they demonstrate
4. Update this README if adding new tool categories
