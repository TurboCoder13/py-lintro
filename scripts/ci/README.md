# CI Scripts Directory

This directory contains scripts used by the CI/CD pipeline and local development.

## Directory Structure

```bash
scripts/ci/
├── deployment/          # Deployment and release scripts
│   ├── guard-release-commit.sh
│   ├── pypi-version-exists.sh
│   ├── pypi-verify-published.sh
│   ├── sbom-attest-artifacts.sh
│   ├── sbom-fetch-github-api.sh
│   ├── sbom-generate-safe.sh
│   ├── sbom-generate.sh
│   ├── sbom-install-binary-gh.sh
│   └── sbom-rename-artifacts.sh
├── docker/              # Docker-related scripts
│   ├── docker-build-test.sh
│   ├── docker-lintro.sh
│   └── docker-test.sh
├── github/              # GitHub integration scripts
│   ├── ci-post-pr-comment.sh
│   ├── ci-pr-comment.sh
│   ├── coverage-pr-comment.sh
│   ├── post-pr-delete-previous.sh
│   ├── semantic-pr-title-check.sh
│   └── semantic-release-helpers.sh
├── maintenance/         # System maintenance and automation
│   ├── auto-tag-unified.sh
│   ├── bomctl-help-test.sh
│   ├── codecov-upload.sh
│   ├── configure-git-user.sh
│   ├── egress-audit-lite.sh
│   ├── ensure-tag-on-main.sh
│   ├── fail-if-semantic-invalid.sh
│   ├── fail-on-lint.sh
│   ├── ghcr_prune_untagged.py
│   ├── security-audit.sh
│   ├── semantic_release_compute_next.py
│   └── validate-action-pinning.sh
└── testing/             # Test execution and reporting
    ├── ci-extract-coverage.sh
    ├── ci-lintro.sh
    ├── coverage-badge-update.sh
    ├── enforce-coverage-threshold.sh
    ├── lintro-report-generate.sh
    └── reusable-quality-entry.sh
```

## Usage

These scripts are primarily called by GitHub Actions workflows but can also be used for
local development:

- **Deployment scripts**: Handle package publishing, SBOM generation, and release
  validation
- **Docker scripts**: Build and test Docker images
- **GitHub scripts**: Manage PR comments, semantic versioning, and GitHub API
  interactions
- **Maintenance scripts**: Automate tagging, security checks, and system maintenance
- **Testing scripts**: Run tests, generate coverage reports, and update badges

## Local Development

Many scripts can be run locally for development and testing. Check individual script
headers for usage instructions.

## Adding New Scripts

When adding new scripts:

1. Place them in the appropriate subdirectory based on their primary function
2. Include a header comment explaining usage and parameters
3. Make scripts executable (`chmod +x`)
4. Update this README if adding new subdirectories
