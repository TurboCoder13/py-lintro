#!/usr/bin/env python3
"""Utilities to merge PR comment bodies while preserving history.

This module exposes a function to combine a previous PR comment body with
new content. The previous content is wrapped in a collapsed <details> block
to keep the comment concise while maintaining history.

The marker line (e.g., "<!-- coverage-report -->") is ensured at the very top
of the merged body so future runs can reliably find and update the same
comment.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

from datetime import UTC, datetime


def _normalize_newline(value: str) -> str:
    """Normalize newlines to Unix style.

    Args:
        value: The text to normalize.

    Returns:
        str: Normalized text with Unix newlines.
    """
    return value.replace("\r\n", "\n").replace("\r", "\n")


def merge_comment_bodies(
    *,
    marker: str,
    previous_body: str | None,
    new_body: str,
    place_new_above: bool = True,
) -> str:
    """Merge previous and new PR comment bodies with history collapsed.

    Ensures the marker appears at the top of the merged body exactly once.

    The previous body (if any) is wrapped in a collapsed <details> block with a
    timestamp label. The new body is placed above or below per `place_new_above`.

    Args:
        marker: Marker string used to identify the comment.
        previous_body: Existing comment body to preserve, if any.
        new_body: Freshly generated body for the current run.
        place_new_above: If True, place new_body above the collapsed
            previous section; otherwise, place it below.

    Returns:
        str: The merged comment body ready to send to the GitHub API.
    """
    marker_line: str = marker.strip()
    normalized_new: str = _normalize_newline(new_body).strip()
    # Ensure the marker only appears once at the very top by removing any
    # occurrences from the newly generated body.
    if marker_line in normalized_new:
        normalized_new = normalized_new.replace(marker_line, "").strip()

    now_utc: str = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S %Z")

    if previous_body:
        normalized_prev: str = _normalize_newline(previous_body).strip()
        # Remove any leading marker line from previous to avoid duplication
        if normalized_prev.startswith(marker_line):
            normalized_prev = normalized_prev[len(marker_line) :].lstrip("\n")

        collapsed_prev: str = (
            f"<details>\n"
            f"<summary>Previous run (updated {now_utc})</summary>\n\n"
            f"{normalized_prev}\n"
            f"</details>\n"
        )

        if place_new_above:
            merged = f"{marker_line}\n\n{normalized_new}\n\n{collapsed_prev}\n"
        else:
            merged = f"{marker_line}\n\n{collapsed_prev}\n{normalized_new}\n"
    else:
        merged = f"{marker_line}\n\n{normalized_new}\n"

    return merged


if __name__ == "__main__":  # pragma: no cover - simple CLI aid
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Merge PR comment bodies")
    parser.add_argument("marker", help="Marker line, e.g., <!-- coverage-report -->")
    parser.add_argument("new_file", help="Path to file with new body content")
    parser.add_argument(
        "--previous-file",
        help="Path to file with previous body content",
        default=None,
    )
    parser.add_argument(
        "--place-new-below",
        help="Place new content below previous details",
        action="store_true",
    )
    args = parser.parse_args()

    prev_text: str | None = None
    if args.previous_file:
        try:
            with open(args.previous_file, encoding="utf-8") as f:
                prev_text = f.read()
        except FileNotFoundError:
            prev_text = None

    with open(args.new_file, encoding="utf-8") as f:
        new_text = f.read()

    merged_out = merge_comment_bodies(
        marker=args.marker,
        previous_body=prev_text,
        new_body=new_text,
        place_new_above=not args.place_new_below,
    )
    sys.stdout.write(merged_out)
