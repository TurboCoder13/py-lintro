# Workflows overview

This repository uses GitHub Actions for quality gates, release automation, and
publishing. Quick reference by file name:

- ci-lintro-analysis.yml: Run Lintro on PRs/pushes via turbo-ci reusable workflow.
- test-and-coverage.yml: Full test suite & coverage via turbo-ci reusable workflow;
  uploads artifacts and comments coverage on PRs.
- pages-deploy-coverage.yml: Deploy coverage HTML to GitHub Pages after a
  successful test-and-coverage run.
- lintro-report-scheduled.yml: Scheduled/manual Lintro run using turbo-ci; uploads
  a markdown report.
- docker-build-publish.yml: Build/test Docker image; publish to GHCR on
  main/release.
- lintro-renovate.yml: Renovate bot.
- reusable-quality.yml: Provided by turbo-ci. Quality gate (format/check) exporting
  the project version.
- reusable-build.yml: Provided by turbo-ci. Build (uv sync, sdist/wheel, twine check),
  uploads `dist/`.
- publish-pypi-on-tag.yml: Publish to PyPI on tag push (OIDC). Uses turbo-ci
  composites to ensure tag-on-main and version match.
- publish-pypi-on-release.yml: [Removed] superseded by tag-based publishing.
- publish-testpypi.yml: Manual dispatch to publish to TestPyPI (OIDC), reusing
  quality and build workflows.
- release-create.yml: [Removed] replaced by Release PR → tag flow.
- auto-tag-on-main.yml: On push to `main` affecting `pyproject.toml`, guarded by
  a release-commit check, if the version changed and the tag doesn’t exist, create
  and push the tag.
- semantic-release.yml: Computes next version and opens a Release PR via uvx
  python-semantic-release (no direct push to main).
- semantic-pr-title.yml: Validates PR titles using turbo-ci composite; fails when
  invalid to block merges until corrected.

## Pinning policy

All references to `TurboCoder13/turbo-ci` are pinned to a full commit SHA for
supply-chain safety. Update pins in a single sweep when bumping turbo-ci.

## Egress policy

Egress allowlisting and runner hardening are centralized in `turbo-ci` via
`TurboCoder13/turbo-ci/.github/actions/harden-runner@<sha>`. This repository
inherits that policy; do not duplicate endpoint lists here.
