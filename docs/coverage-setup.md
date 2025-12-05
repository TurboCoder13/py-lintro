# Coverage Setup Reference

> **Note:** This document is preserved for reference. For comprehensive CI/CD setup
> including coverage, see the [GitHub Integration Guide](github-integration.md).

## Quick Setup

The repository includes pre-configured GitHub Actions for coverage badges:

1. **Enable GitHub Pages** in repository settings
2. **Push to main branch** to trigger workflows
3. **Add badge** to README:
   `![Coverage](https://TurboCoder13.github.io/py-lintro/badges/coverage.svg)`

## Coverage Options

### Local Development

```bash
# Generate coverage report
uv run pytest --cov=lintro --cov-report=html
open htmlcov/index.html
```

### CI/CD Integration

```bash
# Set coverage thresholds
uv run pytest --cov=lintro --cov-fail-under=80
```

### External Services

- **Codecov:** Free for open source, detailed reporting
- **Coveralls:** Alternative coverage service

## Badge Examples

```markdown
![Coverage](https://TurboCoder13.github.io/py-lintro/badges/coverage.svg)
[![codecov](https://codecov.io/gh/TurboCoder13/py-lintro/branch/main/graph/badge.svg)](https://codecov.io/gh/TurboCoder13/py-lintro)
```

For detailed setup instructions, see the
[GitHub Integration Guide](github-integration.md).
