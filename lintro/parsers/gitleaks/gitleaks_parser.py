"""Gitleaks output parser for secret detection findings."""

from __future__ import annotations

import json

from loguru import logger

from lintro.parsers.base_parser import validate_int_field, validate_str_field
from lintro.parsers.gitleaks.gitleaks_issue import GitleaksIssue


def parse_gitleaks_output(output: str | None) -> list[GitleaksIssue]:
    """Parse Gitleaks JSON output into GitleaksIssue objects.

    Gitleaks outputs a JSON array at the root level. Each element represents
    a detected secret with fields like File, StartLine, RuleID, etc.

    Args:
        output: Raw JSON output string from gitleaks, or None.

    Returns:
        List of parsed secret detection findings. Returns empty list if the
        output is invalid or cannot be parsed.
    """
    if not output or not output.strip():
        return []

    text = output.strip()

    # Gitleaks outputs an empty array [] when no secrets found
    if text == "[]":
        return []

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse gitleaks JSON output: {e}")
        return []

    # Gitleaks outputs a JSON array at root level
    if not isinstance(data, list):
        logger.warning(
            "Gitleaks output is not a JSON array, got %s",
            type(data).__name__,
        )
        return []

    issues: list[GitleaksIssue] = []

    for item in data:
        if not isinstance(item, dict):
            logger.debug("Skipping non-dict item in gitleaks output")
            continue

        try:
            issue = _parse_single_finding(item)
            if issue is not None:
                issues.append(issue)
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Failed to parse gitleaks finding: {e}")
            continue

    return issues


def _parse_single_finding(item: dict[str, object]) -> GitleaksIssue | None:
    """Parse a single gitleaks finding into a GitleaksIssue.

    Args:
        item: Dictionary representing a single finding from gitleaks JSON.

    Returns:
        GitleaksIssue if parsing succeeds, None otherwise.
    """
    # Required fields
    file_path = validate_str_field(
        value=item.get("File"),
        field_name="File",
        log_warning=True,
    )
    if not file_path:
        logger.warning("Skipping gitleaks finding with empty File")
        return None

    start_line = validate_int_field(
        value=item.get("StartLine"),
        field_name="StartLine",
    )

    # Optional fields
    start_column = validate_int_field(
        value=item.get("StartColumn"),
        field_name="StartColumn",
    )
    end_line = validate_int_field(
        value=item.get("EndLine"),
        field_name="EndLine",
    )
    end_column = validate_int_field(
        value=item.get("EndColumn"),
        field_name="EndColumn",
    )

    rule_id = validate_str_field(
        value=item.get("RuleID"),
        field_name="RuleID",
    )
    description = validate_str_field(
        value=item.get("Description"),
        field_name="Description",
    )
    secret = validate_str_field(
        value=item.get("Secret"),
        field_name="Secret",
    )
    match = validate_str_field(
        value=item.get("Match"),
        field_name="Match",
    )
    fingerprint = validate_str_field(
        value=item.get("Fingerprint"),
        field_name="Fingerprint",
    )

    # Git-related fields (populated when scanning git history)
    commit = validate_str_field(
        value=item.get("Commit"),
        field_name="Commit",
    )
    author = validate_str_field(
        value=item.get("Author"),
        field_name="Author",
    )
    email = validate_str_field(
        value=item.get("Email"),
        field_name="Email",
    )
    date = validate_str_field(
        value=item.get("Date"),
        field_name="Date",
    )
    commit_message = validate_str_field(
        value=item.get("Message"),
        field_name="Message",
    )

    # Entropy field (float)
    entropy_raw = item.get("Entropy")
    entropy: float = 0.0
    if isinstance(entropy_raw, (int, float)) and not isinstance(entropy_raw, bool):
        entropy = float(entropy_raw)

    # Tags field (list of strings)
    tags_raw = item.get("Tags")
    tags: list[str] = []
    if isinstance(tags_raw, list):
        tags = [t for t in tags_raw if isinstance(t, str)]

    return GitleaksIssue(
        file=file_path,
        line=start_line,
        column=start_column,
        end_line=end_line,
        end_column=end_column,
        rule_id=rule_id,
        description=description,
        secret=secret,
        entropy=entropy,
        tags=tags,
        fingerprint=fingerprint,
        match=match,
        commit=commit,
        author=author,
        email=email,
        date=date,
        commit_message=commit_message,
    )
