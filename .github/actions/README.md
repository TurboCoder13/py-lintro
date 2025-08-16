# Composite Actions

Centralized, reusable steps to keep workflows small and DRY. Each action exposes clear inputs in its action.yml.

## .github/actions/setup-docker

- Purpose: Set up Docker Buildx; optionally log in to a registry (e.g., GHCR)
- Inputs:
  - login (string, default 'false'): set to 'true' to enable login
  - registry (string, default ghcr.io)
  - username (string)
  - password (string)

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

- Purpose: Delete previous PR comments by marker (optional) and post a prepared comment file
- Inputs:
  - file (string, required): path to the comment file
  - marker (string, optional): marker used to delete previous comments

Prerequisites:

- The workflow must set up Python and `uv` and sync project dependencies (the composite invokes repo scripts that use `uv` and Python deps like `httpx`).
- Required env vars are provided by GitHub Actions: `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `github.event.pull_request.number`.

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

- Ensure the directory specified by `path` exists before calling the composite (e.g., generate `_site` first).

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
