#!/usr/bin/env python3
"""Utilities to merge PR comment bodies while preserving history.

This module exposes a function to combine a previous PR comment body with
new content. Historical runs are displayed in separate collapsed <details>
blocks below the current content.

The marker line (e.g., "<!-- coverage-report -->") is ensured at the very top
of the merged body so future runs can reliably find and update the same
comment.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

# Maximum number of historical runs to keep in comments
# Prevents comment bloat on long-running PRs
MAX_HISTORY_RUNS: int = 5


def _normalize_newline(value: str) -> str:
    """Normalize newlines to Unix style.

    Args:
        value: The text to normalize.

    Returns:
        str: Normalized text with Unix newlines.
    """
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _extract_details_blocks(content: str) -> tuple[str, list[str]]:
    """Extract history <details> blocks and remaining content from a string.

    Only extracts <details> blocks that are history entries (identified by
    summary text containing "Previous run" or "Run #"). Other <details>
    blocks (e.g., user-created collapsibles) are left intact in the remaining
    content.

    Args:
        content: The content to parse.

    Returns:
        Tuple of (content outside history details blocks, list of history blocks).
    """
    # Pattern to match <details>...</details> blocks that are history entries
    # History blocks have summaries containing "Previous run" or "Run #" patterns
    # Uses non-greedy match to handle multiple blocks; assumes no nesting
    history_pattern = re.compile(
        r"<details>\s*<summary>[^<]*(Previous run|Run #)[^<]*</summary>.*?</details>",
        re.DOTALL,
    )

    # findall returns the captured group, not the full match; use finditer instead
    details_blocks: list[str] = [m.group(0) for m in history_pattern.finditer(content)]
    remaining_content: str = history_pattern.sub("", content).strip()

    return remaining_content, details_blocks


def _extract_timestamp_from_details(details_block: str) -> str | None:
    """Extract timestamp from a details block summary.

    Args:
        details_block: A <details>...</details> block.

    Returns:
        The timestamp string if found, None otherwise.
    """
    # Match patterns like "Run #N (2026-01-25 19:00:00 UTC)" or
    # "Previous run (updated 2026-01-25 19:00:00 UTC)"
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \w+")
    match = timestamp_pattern.search(details_block)
    return match.group(0) if match else None


def _sort_history_by_timestamp(history_blocks: list[str]) -> list[str]:
    """Sort history blocks by timestamp, newest first.

    Blocks without timestamps are placed at the end to preserve order
    for malformed or legacy entries.

    Args:
        history_blocks: List of <details>...</details> blocks to sort.

    Returns:
        List of blocks sorted by timestamp (newest first).
    """

    def sort_key(block: str) -> tuple[int, str]:
        timestamp = _extract_timestamp_from_details(block)
        if timestamp:
            # (0, x) sorts before (1, "") so dated blocks come first.
            # Invert chars so newer timestamps sort first (descending).
            inverted = "".join(chr(126 - ord(c)) for c in timestamp)
            return (0, inverted)
        # Blocks without timestamps go last, maintain relative order
        return (1, "")

    # Sort ascending: (0, inverted_timestamp) < (1, "") puts dated first, newest first
    return sorted(history_blocks, key=sort_key)


def merge_comment_bodies(
    *,
    marker: str,
    previous_body: str | None,
    new_body: str,
    place_new_above: bool = True,
) -> str:
    """Merge previous and new PR comment bodies with history in flat sections.

    Ensures the marker appears at the top of the merged body exactly once.

    The current run content is displayed at the top (not collapsed). Historical
    runs are displayed in separate <details> blocks below, each with its own
    timestamp. History is limited to the most recent MAX_HISTORY_RUNS.

    Args:
        marker: Marker string used to identify the comment.
        previous_body: Existing comment body to preserve, if any.
        new_body: Freshly generated body for the current run.
        place_new_above: If True, place new_body above the historical
            sections; otherwise, place it below. Defaults to True.
            Use ``place_new_above=False`` for chronological log-style display
            where the latest entry appears at the bottom (e.g., deployment logs
            or audit trails where older entries should be visible first).

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

    if not previous_body:
        return f"{marker_line}\n\n{normalized_new}\n"

    normalized_prev: str = _normalize_newline(previous_body).strip()

    # Remove any leading marker line from previous to avoid duplication
    if normalized_prev.startswith(marker_line):
        normalized_prev = normalized_prev[len(marker_line) :].lstrip("\n")

    # Extract existing details blocks and the current content from previous
    prev_current_content, existing_history = _extract_details_blocks(normalized_prev)

    # Build the list of historical runs (newest first)
    history_blocks: list[str] = []

    # The previous "current" content becomes the newest historical entry
    if prev_current_content.strip():
        new_history_block: str = (
            f"<details>\n"
            f"<summary>📜 Previous run ({now_utc})</summary>\n\n"
            f"{prev_current_content.strip()}\n"
            f"</details>"
        )
        history_blocks.append(new_history_block)

    # Add existing historical blocks and sort by timestamp to ensure newest-first order
    history_blocks.extend(existing_history)
    history_blocks = _sort_history_by_timestamp(history_blocks)

    # Limit history to MAX_HISTORY_RUNS
    history_blocks = history_blocks[:MAX_HISTORY_RUNS]

    # Build final merged content
    history_section: str = "\n\n".join(history_blocks) if history_blocks else ""

    if place_new_above:
        if history_section:
            merged = f"{marker_line}\n\n{normalized_new}\n\n{history_section}\n"
        else:
            merged = f"{marker_line}\n\n{normalized_new}\n"
    else:
        if history_section:
            merged = f"{marker_line}\n\n{history_section}\n\n{normalized_new}\n"
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
