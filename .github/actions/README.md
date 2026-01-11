# Composite Actions

Centralized, reusable steps to keep workflows small and DRY. Each action exposes clear
inputs in its action.yml.

## Versioning Strategy

Internal actions use **semantic version tags** with the `actions-` prefix (e.g.,
`actions-v1.0.0`, `actions-v1.0.1`) instead of commit SHAs. Workflows reference actions
using explicit version tags like `@actions-v1.0.10`. This approach:

- Provides explicit, reproducible builds
- Provides clear versioning for action stability
- Separates action versions from lintro PyPI release versions
- Follows industry best practices for monorepos

### Automatic Versioning

The `auto-version-actions.yml` workflow automatically creates new patch version tags
when actions or reusable workflows are modified.

**How it works:**

1. Modify an action file (e.g., `.github/actions/setup-env/action.yml`)
2. Commit and push to main
3. Workflow automatically creates `actions-v1.0.0` (first run) or the next patch version
   (e.g., `actions-v1.0.11`)
4. Update workflow references to use the new version tag

### Updating Workflow References

After a new action version is created, update workflow references:

1. Check the latest tag: `git tag -l 'actions-v1.*' | sort -V | tail -1`
2. Update all workflow files referencing `@actions-v1.x.x` to the new version
3. Commit and push the updated workflows

### Manual Versioning (Breaking Changes Only)

For major version changes (breaking changes), manually create a new major version tag:

1. **Make your breaking changes** to the action files
2. **Create and push the tag**:

   ```bash
   git tag actions-v2.0.0 -m "Major version: breaking changes"
   git push origin actions-v2.0.0
   ```

3. **Update workflow references** to use `@actions-v2.0.0`

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

## .github/actions/extract-version

- Purpose: Extract version from git tag reference, stripping the 'v' prefix
- Inputs:
  - strip-prefix (string, default 'true'): whether to strip the 'v' prefix
- Outputs:
  - version: the extracted version (without 'v' prefix if strip-prefix is true)
  - tag: the original tag name

Example:

```yaml
- name: Extract version from tag
  id: version
  uses: ./.github/actions/extract-version

- name: Use version
  run: echo "Version is ${{ steps.version.outputs.version }}"
```

## .github/actions/harden-runner-preset

- Purpose: Apply step-security/harden-runner with predefined endpoint presets
- Note: This action requires checkout first, so it cannot be the first step. For maximum
  security, use direct harden-runner calls as the first step.
- Inputs:
  - preset (string, required): endpoint preset to use
    - python: PyPI and GitHub
    - docker: Python + container registries
    - codecov: Python + Codecov
    - sigstore: Python + Sigstore services
    - homebrew: Python + Homebrew tap
    - full: All common endpoints
  - policy (string, default 'block'): egress policy (block or audit)
  - extra-endpoints (string, optional): additional endpoints to allow

Example:

```yaml
- name: Checkout
  uses: actions/checkout@v4

- name: Harden Runner
  uses: ./.github/actions/harden-runner-preset
  with:
    preset: python
    extra-endpoints: 'custom.example.com:443'
```

Notes:

- Workflows must remain in .github/workflows/ (no subdirectories supported).
- Prefer scripts under scripts/ for any logic beyond orchestration.
