# Security Assurance (Overview)

This assurance note explains how `py-lintro` meets its documented security requirements and provides pointers to evidence.

## Requirements Coverage

- Governance and Roles — see `GOVERNANCE.md`
- Contribution Integrity — DCO sign-offs required; see `DCO.md` and CI checks
- Responsible Disclosure — see `SECURITY.md`
- Branch Protection — enforced via Allstar (`.allstar/branch_protection.yaml`)
- Dependency Hygiene — Renovate, Dependency Review CI, `uv.lock`
- Static/SAST — Ruff, Bandit, CodeQL; policy checks for workflows (Actionlint)
- Container and Dockerfile — Hadolint
- Documentation and Versioning — `README.md`, `CHANGELOG.md`, semantic releases

## Evidence Pointers

- CI Workflows: `.github/workflows/*.yml`
- Allstar Policy: `.allstar/branch_protection.yaml`
- Scorecard: badge in `README.md`
- Coverage: `coverage.xml` and README badge

## Continuous Improvement

- Periodic updates via Renovate
- Automated analyses (Scorecard, CodeQL)
- Maintainer reviews for all changes
