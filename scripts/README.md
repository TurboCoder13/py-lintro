# Scripts Directory

This directory contains utility scripts for CI/CD testing and validation.

**Note:** Most CI/CD scripts have been migrated to
[turbo-ci](https://github.com/TurboCoder13/turbo-ci) for centralized management
and consistency across TurboCoder13 projects.

## 📁 Directory Structure

```
scripts/
├── ci/           # CI/CD testing and validation scripts
├── docker/       # Removed - Docker scripts migrated to turbo-ci
├── local/        # Removed - Local development scripts migrated to turbo-ci
└── utils/        # Shared utility modules
```

## 🔧 CI Testing Scripts (`ci/`)

Scripts for testing package installation and CLI verification in isolated
environments.

| Script                | Purpose                                     | Usage                                      |
| --------------------- | ------------------------------------------- | ------------------------------------------ |
| `test-venv-setup.sh`  | Create isolated Python 3.13 venv            | `./scripts/ci/test-venv-setup.sh`          |
| `test-install-package.sh` | Install built package in isolated venv  | `./scripts/ci/test-install-package.sh wheel` |
| `test-verify-cli.sh`  | Verify lintro CLI entry points              | `./scripts/ci/test-verify-cli.sh`          |
| `test-verify-imports.sh` | Verify critical package imports         | `./scripts/ci/test-verify-imports.sh wheel` |

## 🔗 CI/CD Infrastructure

For general CI/CD automation, configuration, and reusable workflow steps, see
[turbo-ci](https://github.com/TurboCoder13/turbo-ci).
