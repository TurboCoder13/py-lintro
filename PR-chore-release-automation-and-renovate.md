## Commit Summary (Conventional Commits)

- Title (required, present tense):

  ```
  ci: automate release flow and adjust renovate settings
  ```

- Type:
  - [x] chore / ci / style

- Breaking change:
  - [ ] `!` in title or `BREAKING CHANGE:` footer included

### Release Trigger Rules (exact)

- A merged PR will bump the version based on its title (squash merge required):
  - `feat(...)` or `feat:` → MINOR bump
  - `fix(...)` / `fix:` or `perf(...)` / `perf:` → PATCH bump
  - Any title with `!` after the type (e.g. `feat!:` or `feat(scope)!:`) or a body
    containing `BREAKING CHANGE:` → MAJOR bump
- Use squash merge so the PR title becomes the merge commit title.
- Valid examples:
  - `feat(cli): add --group-by`
  - `fix(parser): handle empty config`
  - `perf: optimize grouping performance`
  - `feat(api)!: remove deprecated flags`

## What’s Changing

End-to-end automation for releases and PyPI publish, plus Renovate policy fixes:

- Clarify exact Conventional Commit rules in PR template and require squash merge
- Make semantic-release version detection deterministic (no fuzzy fallbacks)
- Ensure publish workflows allow modern wheel metadata (Metadata-Version 2.4)
- Prevent Renovate from pinning digest for `amannn/action-semantic-pull-request`
  while keeping other actions pinned

## Checklist

- [x] Title follows Conventional Commits
- [x] Tests added/updated (N/A)
- [x] Docs updated if user-facing (PR template updated)
- [x] Local CI passed (`./scripts/local/run-tests.sh`) and `actionlint` clean

## Related Issues

- refs: pypi/warehouse#15611
- refs: astral-sh/rye#1446

## Details

- `.github/pull_request_template.md`: adds explicit release trigger rules
- `.github/workflows/semantic-release.yml`: rely only on computed next version
- `.github/workflows/publish-pypi-on-tag.yml`: `verify-metadata: false`
- `.github/workflows/publish-testpypi.yml`: `verify-metadata: false`
- `renovate.json`: disable digest pinning for `amannn/action-semantic-pull-request`

Flow after merge to `main`:

- PR with compliant title → squash merge → semantic release PR/tag → tag-based
  publish to PyPI → GitHub Release with assets
