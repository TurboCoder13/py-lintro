#!/usr/bin/env python3
"""JSON encode comment body for GitHub API requests.

This utility safely encodes comment text as JSON for GitHub API requests,
handling proper escaping and encoding.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

import json
import sys


def encode_body_as_json(body: str) -> str:
    """Encode comment body as JSON for GitHub API.

    Args:
        body (str): The comment body text to encode.

    Returns:
        str: JSON-encoded body ready for API request.
    """
    return json.dumps({"body": body})


def encode_file_as_json(file_path: str) -> str:
    """Encode file contents as JSON for GitHub API.

    Args:
        file_path (str): Path to file containing comment body.

    Returns:
        str: JSON-encoded body ready for API request.
    """
    with open(file_path, encoding="utf-8") as f:
        body = f.read()
    return encode_body_as_json(body)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        # File mode: read from file
        file_path = sys.argv[1]
        try:
            json_output = encode_file_as_json(file_path)
            print(json_output)
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Stdin mode: read from stdin
        body = sys.stdin.read()
        json_output = encode_body_as_json(body)
        print(json_output)
