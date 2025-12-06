# Composite Actions

Centralized, reusable steps to keep workflows small and DRY. Each action exposes clear
inputs in its action.yml.

## Versioning Strategy

Internal actions use **semantic version tags** with the `actions-` prefix (e.g.,
`@actions-v1.0.0`) instead of commit SHAs. This approach:

- Eliminates dependency update loops
- Provides clear versioning for action stability
- Separates action versions from lintro PyPI release versions
- Follows industry best practices for monorepos

### Automatic Versioning

The `auto-version-actions.yml` workflow automatically creates new patch version tags
when actions or reusable workflows are modified. You don't need to manually create tags.

**How it works:**

1. Modify an action file (e.g., `.github/actions/setup-env/action.yml`)
2. Commit and push to main
3. Workflow automatically creates `actions-v1.0.1` (or next patch version)
4. All workflows using `@actions-v1` automatically use the new version

### Manual Versioning (Breaking Changes Only)

For major version changes (breaking changes), manually create a new major version tag:

1. **Make your breaking changes** to the action files
2. **Create and push the tag**:

   ```bash
   git tag actions-v2.0.0 -m "Major version: breaking changes"
   git push origin actions-v2.0.0
   ```

3. **Update workflow references** from `@actions-v1` to `@actions-v2`

### Current Action Versions

All actions are currently at `actions-v1.0.0`. Patch versions are automatically managed
by the `auto-version-actions` workflow.

## .github/actions/setup-docker

- Purpose: Set up Docker Buildx; optionally log in to a registry (e.g., GHCR)
- **Note**: This action does NOT include hardened runner - use in workflows that already
  have hardening
- Inputs:
  - login (string, default 'false'): set to 'true' to enable login
  - registry (string, default ghcr.io)
  - username (string)
  - password (string)
  - driver (string, default 'docker'): buildx driver

Example:

```yaml
- name: Setup Docker (Buildx + login)
  uses: ./.github/actions/setup-docker
  with:
    login: 'true'
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

## .github/actions/post-pr-comment

- Purpose: Delete previous PR comments by marker (optional) and post a prepared comment
  file
- Inputs:
  - file (string, required): path to the comment file
  - marker (string, optional): marker used to delete previous comments

Prerequisites:

- The workflow must set up Python and `uv` and sync project dependencies (the composite
  invokes repo scripts that use `uv` and Python deps like `httpx`).
- Required env vars are provided by GitHub Actions: `GITHUB_TOKEN`, `GITHUB_REPOSITORY`,
  and `github.event.pull_request.number`.

Example:

```yaml
- name: Comment PR
  uses: ./.github/actions/post-pr-comment
  with:
    file: pr-comment.txt
    marker: '<!-- lintro-report -->'
```

## .github/actions/pages-deploy

- Purpose: Configure Pages, upload an artifact directory, and deploy
- Inputs:
  - path (string, required): directory to upload for Pages

Usage note:

- Ensure the directory specified by `path` exists before calling the composite (e.g.,
  generate `_site` first).

Example:

```yaml
- name: Deploy coverage report to Pages
  uses: ./.github/actions/pages-deploy
  with:
    path: _site
```

Notes:

- Workflows must remain in .github/workflows/ (no subdirectories supported).
- Prefer scripts under scripts/ for any logic beyond orchestration.
