#!/usr/bin/env python3
"""Extract comment body from GitHub API JSON response by comment ID.

This utility parses GitHub API JSON responses to extract the body text
of a specific comment identified by its ID.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

import json
import sys


def extract_comment_body(json_payload: str, comment_id: str) -> str:
    """Extract the body of a comment with the given ID.

    Args:
        json_payload (str): JSON response from GitHub API comments endpoint.
        comment_id (str): The ID of the comment to extract.

    Returns:
        str: The comment body text, or empty string if not found.
    """
    try:
        data = json.loads(json_payload)
    except json.JSONDecodeError:
        return ""

    # Handle both paginated (items) and direct array responses
    items = data.get("items") if isinstance(data, dict) else data
    if not items:
        return ""

    for item in items:
        if str(item.get("id")) == comment_id:
            return item.get("body") or ""

    return ""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: extract_comment_body.py JSON_PAYLOAD COMMENT_ID", file=sys.stderr)
        sys.exit(1)

    json_payload = sys.argv[1]
    comment_id = sys.argv[2]

    body = extract_comment_body(json_payload, comment_id)
    sys.stdout.write(body)
