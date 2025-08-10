# GitHub Integration Guide

This guide explains how to set up Lintro with GitHub Actions for automated code quality checks, coverage reporting, and CI/CD integration.

## Quick Setup

The repository includes pre-configured GitHub Actions workflows. To activate them:

1. **Enable GitHub Pages** in repository settings (for coverage badges)
2. **Push to main branch** to trigger workflows
3. **Add badges** to your README.md (optional)

## Available Workflows

### 1. Quality Check Workflow

**File:** `.github/workflows/ci-lintro-analysis.yml`

**Features:**

- 🔍 **Comprehensive analysis** across all file types
- 🛠️ **Auto-fixing** with `lintro format` where possible
- 📊 **Detailed reporting** in GitHub Actions summaries
- 🚀 **Multi-tool analysis:**
  - Python: Ruff + Darglint
  - YAML: Yamllint
  - JSON: Prettier
  - Docker: Hadolint

**Triggers:**

- Pull requests
- Pushes to main branch
- Manual workflow dispatch

### 2. Coverage Badge Workflow

**File:** `.github/workflows/test-and-coverage.yml`

**Features:**

- 🧪 **Test coverage reporting** with badges
- 📈 **GitHub Pages deployment** for coverage badges
- 🔄 **Auto-updating** on each push to main

### 3. Lintro Report Workflow

**File:** `.github/workflows/lintro-report-scheduled.yml`

**Features:**

- 📊 **Comprehensive codebase analysis** with Lintro
- 📈 **Report generation** in multiple formats (Grid, Markdown)
- 📋 **GitHub Actions summary** with detailed results
- 📦 **Artifact upload** for report retention
- 🌐 **Optional GitHub Pages deployment** for report hosting

**GitHub Pages Deployment:**

The workflow includes optional GitHub Pages deployment steps that are commented out by default. To enable GitHub Pages deployment for your Lintro reports:

1. **Enable GitHub Pages** in your repository settings
2. **Uncomment the following steps** in `.github/workflows/lintro-report.yml`:

```yaml
- name: Setup Pages
  uses: actions/configure-pages@v3

- name: Upload artifact for Pages
  uses: actions/upload-pages-artifact@v2
  with:
    path: lintro-report/

- name: Deploy to GitHub Pages
  id: deployment
  uses: actions/deploy-pages@v3
```

3. **Add required permissions** to the workflow:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

**Note:** GitHub Pages deployment requires either a public repository or GitHub Pages enabled for private repositories.

### 4. Complete CI Pipeline

**File:** `.github/workflows/ci-lintro-analysis.yml`

**Features:**

- 🎯 **Quality-first approach** - Lintro runs before tests
- 📋 **Combined reporting** - Quality + testing results
- 🚀 **Showcase integration** - Demonstrates Lintro capabilities

### 5. Docker Image Publishing

**File:** `.github/workflows/docker-build-publish.yml`

**Features:**

- 🐳 **Automated Docker image building** and publishing to GHCR
- 🏷️ **Smart tagging** - Latest, main branch, and semantic versions
- 🔄 **Release integration** - Images published on releases
- 📦 **GHCR integration** - Images available at `ghcr.io/turbocoder13/py-lintro`

**Usage in CI/CD:**

You can use the published Docker image in your own CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Lintro with Docker
  run: |
    docker run --rm -v ${{ github.workspace }}:/code \
      ghcr.io/turbocoder13/py-lintro:latest check --output-format grid

# GitLab CI example
lintro:
  image: ghcr.io/turbocoder13/py-lintro:latest
  script:
    - lintro check --output-format grid
```

## Setting Up in Your Repository

### 1. Copy Workflow Files

Copy the workflow files from this repository to your project:

```bash
mkdir -p .github/workflows
cp .github/workflows/*.yml your-project/.github/workflows/
```

### 2. Customize for Your Project

Edit the workflow files to match your project structure:

```yaml
# .github/workflows/ci-lintro-analysis.yml
- name: Run Lintro Quality Check
  run: |
    # Adjust paths for your project
    uv run lintro check src/ tests/ --tools ruff,darglint --output-format grid
    uv run lintro check .github/ --tools yamllint --output-format grid
    uv run lintro check *.json --tools prettier --output-format grid
```

### 3. Configure Repository Settings

**Enable GitHub Pages:**

1. Go to repository **Settings** → **Pages**
2. Select **Source:** "GitHub Actions"
3. Your coverage badge will be available at: `https://TurboCoder13.github.io/py-lintro/badges/coverage.svg`

## Example Workflows

### Basic Quality Check

```yaml
name: Code Quality

on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install UV
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run Lintro
        run: |
          uv run lintro check --output-format grid --output lintro-results.txt
          cat lintro-results.txt

      - name: Upload results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: lintro-results
          path: lintro-results.txt
```

### Auto-fix Pull Request

```yaml
name: Auto-fix Code Issues

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  autofix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install UV and dependencies
        run: |
          pip install uv
          uv sync

      - name: Run Lintro auto-fix
        run: uv run lintro format --output-format grid

      - name: Check for changes
        id: verify-changed-files
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
          fi

      - name: Commit changes
        if: steps.verify-changed-files.outputs.changed == 'true'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git commit -m "style: auto-fix code issues with Lintro"
          git push
```

### Quality Gate

```yaml
name: Quality Gate

on:
  pull_request:

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install UV and dependencies
        run: |
          pip install uv
          uv sync

      - name: Run quality checks
        run: |
          # Try to auto-fix first
          uv run lintro format --output-format grid

          # Then check for remaining issues
          uv run lintro check --output-format grid --output quality-report.txt

          # Fail if critical issues remain
          if grep -q "error" quality-report.txt; then
            echo "❌ Critical quality issues found"
            cat quality-report.txt
            exit 1
          else
            echo "✅ Quality gate passed"
          fi
```

## Badge Integration

### Coverage Badge

Add to your README.md:

```markdown
![Coverage](https://TurboCoder13.github.io/py-lintro/badges/coverage.svg)
```

### Quality Badge

```markdown
![Code Quality](https://github.com/TurboCoder13/py-lintro/workflows/Code%20Quality/badge.svg)
```

### Custom Lintro Badge

```markdown
![Lintro](https://img.shields.io/badge/code%20quality-lintro-blue)
```

## Advanced Configuration

### Tool-Specific Workflows

```yaml
# Python-only quality check
- name: Python Quality
  run: uv run lintro check src/ tests/ --tools ruff,darglint --output-format grid

# Frontend-only quality check
- name: Frontend Quality
  run: uv run lintro check assets/ --tools prettier --output-format grid

# Infrastructure quality check
- name: Infrastructure Quality
  run: uv run lintro check Dockerfile* --tools hadolint --output-format grid
```

### Matrix Builds

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']
    tool: ['ruff', 'darglint', 'prettier']
```

### Conditional Execution

```yaml
- name: Run Lintro on changed files
  run: |
    # Get changed files
    git diff --name-only HEAD^ HEAD > changed-files.txt

    # Run Lintro only on changed files
    if [ -s changed-files.txt ]; then
      uv run lintro check $(cat changed-files.txt) --output-format grid
    else
      echo "No files changed"
    fi
```

## Troubleshooting

### Common Issues

**1. Workflow not triggering:**

- Check workflow file syntax
- Ensure proper indentation (YAML)
- Verify trigger conditions

**2. Permission denied:**

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

**3. Dependencies not installed:**

```yaml
- name: Install dependencies
  run: |
    pip install uv
    uv sync --dev
```

**4. Tool not found:**

```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y hadolint
```

### Debug Workflow

```yaml
- name: Debug Lintro
  run: |
    echo "=== Environment ==="
    python --version
    uv --version

    echo "=== Available tools ==="
    uv run lintro list-tools

    echo "=== File structure ==="
    find . -name "*.py" | head -10

    echo "=== Running Lintro ==="
    uv run lintro check --output-format grid || true
```

## Integration Benefits

Using Lintro in GitHub Actions provides:

1. **Early Issue Detection** - Catch problems before they reach production
2. **Consistent Quality** - Enforce coding standards across all contributors
3. **Automated Fixes** - Reduce manual work with auto-fixing
4. **Comprehensive Reporting** - Multi-tool analysis in one place
5. **Quality Gates** - Block problematic code from merging
6. **Coverage Tracking** - Monitor test coverage over time

## Best Practices

1. **Run Lintro early** in your CI pipeline (before tests)
2. **Use auto-fix first**, then check for remaining issues
3. **Separate workflows** for different file types when needed
4. **Cache dependencies** to speed up workflows
5. **Use artifacts** to preserve reports
6. **Set up quality gates** to maintain code standards
7. **Monitor coverage trends** over time

This integration transforms your repository into a high-quality, maintainable codebase with automated quality assurance! 🚀
