#!/usr/bin/env python3
"""Find existing GitHub comment ID that contains a specific marker.

This utility parses GitHub API JSON responses to find the most recent comment
containing a given marker string. Used for updating PR comments in-place.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

import json
import os
import sys


def find_comment_id(json_payload: str, marker: str) -> str | None:
    """Find the ID of the most recent comment containing the marker.

    Args:
        json_payload (str): JSON response from GitHub API comments endpoint.
        marker (str): Marker string to search for in comment bodies.

    Returns:
        str | None: Comment ID if found, None otherwise.
    """
    try:
        data = json.loads(json_payload)
    except json.JSONDecodeError:
        return None

    # Handle both paginated (items) and direct array responses
    items = data.get("items") if isinstance(data, dict) else data
    if not items:
        return None

    # Search from most recent to oldest
    for item in reversed(items):
        body = item.get("body") or ""
        if marker and marker in body:
            return str(item.get("id"))

    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: find_comment_with_marker.py MARKER < JSON_FILE", file=sys.stderr)
        print(
            "   or: find_comment_with_marker.py MARKER (with JSON via stdin)",
            file=sys.stderr,
        )
        sys.exit(1)

    marker = sys.argv[1]

    # Read JSON from stdin to avoid "Argument list too long" error
    json_payload = sys.stdin.read()

    # Also support reading from environment variables for compatibility
    if not json_payload:
        json_payload = os.environ.get("EXISTING_JSON", "[]")
    if not marker:
        marker = os.environ.get("MARKER", "")

    comment_id = find_comment_id(json_payload, marker)
    print(comment_id or "")
