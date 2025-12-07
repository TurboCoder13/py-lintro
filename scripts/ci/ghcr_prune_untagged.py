# mypy: ignore-errors
"""Prune untagged GHCR image versions for this repository.

Google-style docstring.

This script lists container package versions for the current repo on GHCR and
deletes those that have no tags. Requires GITHUB_TOKEN with packages:write scope in
Actions (GITHUB_TOKEN is sufficient for deleting own repo packages).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger


@dataclass
class GhcrVersion:
    """Container version metadata minimal subset.

    Attributes:
        id: Numeric version id.
        tags: List of tags bound to this version.
    """

    id: int
    tags: list[str]
    created_at: str = ""


def get_repo_owner_repo() -> tuple[str, str]:
    """Return (owner, repo) from GITHUB_REPOSITORY env.

    Returns:
        tuple[str, str]: owner and repo.
    """
    repo = os.environ.get("GITHUB_REPOSITORY", "TurboCoder13/py-lintro")
    owner, name = repo.split("/", 1)
    return owner, name


def list_container_versions(client: httpx.Client, owner: str) -> list[GhcrVersion]:
    """List container versions for this user-owned package.

    Args:
        client: Authenticated HTTP client.
        owner: Repository owner (user/org).

    Returns:
        list[GhcrVersion]: Version entries.
    """
    # User package API path
    url = (
        f"https://api.github.com/users/{owner}/packages/container/py-lintro/versions"
        "?per_page=100"
    )
    resp = client.get(url, headers={"Accept": "application/vnd.github+json"})
    resp.raise_for_status()
    data: list[dict[str, Any]] = resp.json()
    versions: list[GhcrVersion] = []
    for item in data:
        vid = int(item.get("id"))
        tags = list(item.get("metadata", {}).get("container", {}).get("tags", []))
        created_at = str(item.get("created_at", ""))
        versions.append(GhcrVersion(id=vid, tags=tags, created_at=created_at))
    return versions


def delete_version(client: httpx.Client, owner: str, version_id: int) -> None:
    """Delete a container version by id.

    Args:
        client: Authenticated HTTP client.
        owner: Repository owner (user/org).
        version_id: GHCR version id to delete.
    """
    url = (
        f"https://api.github.com/users/{owner}/packages/container/py-lintro/versions/"
        f"{version_id}"
    )
    resp = client.delete(url, headers={"Accept": "application/vnd.github+json"})
    # 204 no content on success
    if resp.status_code not in (204, 404):
        resp.raise_for_status()


def main() -> int:
    """Entry point.

    Returns:
        int: Process exit code.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN is required")
        return 2

    owner, _ = get_repo_owner_repo()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "py-lintro-ghcr-cleanup",
    }
    deleted = 0
    dry_run = os.environ.get("GHCR_PRUNE_DRY_RUN", "0") == "1"
    keep_n_env = os.environ.get("GHCR_PRUNE_KEEP_UNTAGGED_N", "0")
    try:
        keep_n = int(keep_n_env)
    except ValueError:
        keep_n = 0
    with httpx.Client(headers=headers, timeout=30) as client:
        versions = list_container_versions(client=client, owner=owner)
        untagged = [v for v in versions if len(v.tags) == 0]
        # Keep the N most recent untagged by created_at (descending)
        if keep_n > 0:
            untagged.sort(key=lambda v: v.created_at, reverse=True)
            to_delete = untagged[keep_n:]
        else:
            to_delete = untagged
        for v in to_delete:
            if dry_run:
                logger.info(
                    "[dry-run] Would delete version id={} created_at={}",
                    v.id,
                    v.created_at,
                )
                continue
            delete_version(client=client, owner=owner, version_id=v.id)
            deleted += 1
    action = "Would delete" if dry_run else "Deleted"
    logger.info("{} {} untagged GHCR versions", action, deleted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
