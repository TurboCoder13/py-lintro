## Commit Summary (Conventional Commits)

- Title (required, present tense):

  ```
  <type>(optional-scope)!: concise summary
  ```

  Examples: `feat(cli): add --group-by`, `fix(parser): handle empty config`, `refactor(core)!: rewrite engine`

- Type:
  - [ ] feat (minor)
  - [ ] fix / perf (patch)
  - [ ] docs
  - [ ] refactor
  - [ ] test
  - [ ] chore / ci / style

- Breaking change:
  - [ ] `!` in title or `BREAKING CHANGE:` footer included

## What’s Changing

Describe the changes and why.

## Checklist

- [ ] Title follows Conventional Commits
- [ ] Tests added/updated
- [ ] Docs updated if user-facing
- [ ] Local CI passed (`./scripts/local/run-tests.sh`)

## Related Issues

Closes #
Fixes #
Related #

## Details

Implementation notes, migration/breaking notes, and testing strategy.
