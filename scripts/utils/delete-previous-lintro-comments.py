#!/usr/bin/env python3
"""Delete previous lintro bot comments from a GitHub pull request.

This script deletes all comments containing the marker '<!-- lintro-report -->'
from a specified pull request.

Uses httpx for HTTP requests.

Environment Variables:
    GITHUB_TOKEN (str): GitHub API token with repo permissions.
    GITHUB_REPOSITORY (str): Repository in 'owner/repo' format.
    PR_NUMBER (str or int): Pull request number.

Usage:
    python3 scripts/delete-previous-lintro-comments.py

Intended for use in CI workflows to keep PRs clean of duplicate bot comments.
"""

import os
import sys
from typing import Any

import httpx


def get_marker() -> str:
    """Get the marker/tag from command-line arguments or use default.

    Returns:
        str: The marker/tag to use.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return "<!-- lintro-report -->"


def get_env_var(name: str) -> str:
    """Get an environment variable or exit with error.

    Args:
        name (str): Name of the environment variable.

    Returns:
        str: Value of the environment variable.
    """
    value = os.environ.get(name)
    if not value:
        print(f"Error: Environment variable {name} is required.", file=sys.stderr)
        sys.exit(1)
    return value


def get_pr_comments(repo: str, pr_number: str, token: str) -> list[dict[str, Any]]:
    """Fetch all comments for a pull request.

    Args:
        repo (str): Repository in 'owner/repo' format.
        pr_number (str): Pull request number.
        token (str): GitHub API token.

    Returns:
        list[dict[str, Any]]: List of comment objects.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    with httpx.Client(timeout=10) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def delete_comment(repo: str, comment_id: int, token: str) -> None:
    """Delete a comment by ID.

    Args:
        repo (str): Repository in 'owner/repo' format.
        comment_id (int): Comment ID.
        token (str): GitHub API token.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    with httpx.Client(timeout=10) as client:
        response = client.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"Deleted comment {comment_id}")
        else:
            print(
                f"Failed to delete comment {comment_id}: "
                f"{response.status_code} {response.text}",
                file=sys.stderr,
            )


def main() -> None:
    """Main entry point for the script."""
    repo = get_env_var("GITHUB_REPOSITORY")
    pr_number = get_env_var("PR_NUMBER")
    token = get_env_var("GITHUB_TOKEN")
    marker = get_marker()

    try:
        comments = get_pr_comments(repo=repo, pr_number=pr_number, token=token)
    except Exception as e:
        print(f"Error fetching comments: {e}", file=sys.stderr)
        sys.exit(1)

    deleted_any = False
    for comment in comments:
        if marker in comment.get("body", ""):
            delete_comment(repo=repo, comment_id=comment["id"], token=token)
            deleted_any = True

    if not deleted_any:
        print(f"No previous comments found to delete for marker: {marker}")


if __name__ == "__main__":
    main()
