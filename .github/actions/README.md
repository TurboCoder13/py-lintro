# Composite Actions

Centralized, reusable steps to keep workflows small and DRY. Each action exposes clear
inputs in its action.yml.

## Versioning Strategy

Internal actions use **semantic version tags** (e.g., `@v1.0.0`) instead of commit SHAs.
This approach:

- Eliminates dependency update loops
- Provides clear versioning for action stability
- Follows industry best practices (used by GitHub and major organizations)

### Creating New Versions

When updating an internal action:

1. **Make your changes** to the action files
2. **Decide on version bump**:
   - **Major** (`v2.0.0`): Breaking changes (input/output changes, behavior changes)
   - **Minor** (`v1.1.0`): New features (new inputs, new functionality)
   - **Patch** (`v1.0.1`): Bug fixes (fixes without changing behavior)
3. **Create and push the tag**:

   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. **Update workflow references** if it's a breaking change (major version), otherwise
   workflows can continue using the major version tag (e.g., `@v1` will auto-update to
   latest `v1.x.x`)

### Current Action Versions

All actions are currently at `v1.0.0`. When you update an action, create a new tag
following semantic versioning principles.

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
