# Workflows overview

This repository uses GitHub Actions for quality gates, release automation, and
publishing. Quick reference by file name:

- ci-lintro-analysis.yml: Run Lintro on PRs/pushes; Docker build; PR comment.
- test-and-coverage.yml: Full test suite in Docker, upload coverage artifacts,
  comment coverage on PRs.
- pages-deploy-coverage.yml: Deploy coverage HTML to GitHub Pages after a
  successful test-and-coverage run.
- lintro-report-scheduled.yml: Scheduled/manual Lintro run that uploads a
  markdown report.
- docker-build-publish.yml: Build/test Docker image; publish to GHCR on
  main/release.
- lintro-renovate.yml: Renovate bot.
- reusable-quality.yml: Reusable quality gate (Lintro format/check) exporting
  the project version.
- reusable-build.yml: Reusable build (uv sync, build sdist/wheel, twine check),
  uploads `dist/`.
- publish-pypi-on-tag.yml: Publish to PyPI on tag push (OIDC). Verifies pushed
  tag matches `pyproject.toml` version.
- publish-pypi-on-release.yml: [Removed] superseded by tag-based publishing.
- publish-testpypi.yml: Manual dispatch to publish to TestPyPI (OIDC), reusing
  quality and build workflows.
- release-create.yml: Build artifacts and create a GitHub Release with assets.
- auto-tag-on-main.yml: On push to `main` affecting `pyproject.toml`, if the
  version changed and the tag doesn’t exist, create and push the tag.
- semantic-release.yml: Runs python-semantic-release to auto-bump version and
  create a tag based on conventional commits (main branch).
- semantic-pr-title.yml: Validates PR title follows Conventional Commits and
  comments/fails if not, preventing merges until corrected.
