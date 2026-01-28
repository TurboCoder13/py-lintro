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
    """Extract <details> blocks and remaining content from a string.

    Args:
        content: The content to parse.

    Returns:
        Tuple of (content outside details blocks, list of details blocks).
    """
    # Pattern to match <details>...</details> blocks (non-greedy, assumes no nesting)
    # This simple approach works for flat history blocks without nested details
    details_pattern = re.compile(
        r"<details>\s*\n.*?</details>",
        re.DOTALL,
    )

    details_blocks: list[str] = details_pattern.findall(content)
    remaining_content: str = details_pattern.sub("", content).strip()

    return remaining_content, details_blocks


# Reserved for future use in parsing details blocks for deduplication or sorting.
# Currently covered only by unit tests; may be used when history management evolves.
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
            f"<summary>\U0001f4dc Previous run ({now_utc})</summary>\n\n"
            f"{prev_current_content.strip()}\n"
            f"</details>"
        )
        history_blocks.append(new_history_block)

    # Add existing historical blocks (already in order from previous merge)
    history_blocks.extend(existing_history)

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
