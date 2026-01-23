"""Parser for Oxlint JSON output.

Handles Oxlint JSON format output from --format json flag.
"""

import json
from typing import Any

from loguru import logger

from lintro.parsers.oxlint.oxlint_issue import OxlintIssue


def parse_oxlint_output(output: str) -> list[OxlintIssue]:
    """Parse Oxlint JSON output into a list of OxlintIssue objects.

    Args:
        output: The raw JSON output from Oxlint.

    Returns:
        List of OxlintIssue objects.
    """
    issues: list[OxlintIssue] = []

    if not output:
        return issues

    try:
        # Oxlint JSON format is a single object with diagnostics array
        # Extract JSON from output (Oxlint may add extra text after JSON)
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            return issues
        json_content = output[json_start:json_end]
        oxlint_data: dict[str, Any] = json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse Oxlint JSON output: {e}")
        return issues
    except (ValueError, TypeError) as e:
        logger.debug(f"Error processing Oxlint output: {e}")
        return issues

    if not isinstance(oxlint_data, dict):
        logger.debug("Oxlint output is not a dictionary")
        return issues

    diagnostics = oxlint_data.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        logger.debug("Oxlint diagnostics is not a list")
        return issues

    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            continue
        try:
            issue = _parse_diagnostic(diagnostic)
            if issue is not None:
                issues.append(issue)
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"Failed to parse Oxlint diagnostic: {e}")
            continue

    return issues


def _parse_diagnostic(diagnostic: dict[str, Any]) -> OxlintIssue | None:
    """Parse a single Oxlint diagnostic into an OxlintIssue.

    Args:
        diagnostic: A single diagnostic dictionary from Oxlint output.

    Returns:
        OxlintIssue if parsing succeeds, None otherwise.
    """
    # Extract filename
    file_path = diagnostic.get("filename", "")
    if not file_path:
        return None

    # Extract message and code
    message = diagnostic.get("message", "")
    code = diagnostic.get("code", "")
    severity = diagnostic.get("severity", "warning")
    help_text = diagnostic.get("help")

    # Extract line and column from labels array
    # labels[0].span contains {offset, length, line, column}
    line = 0
    column = 0
    labels = diagnostic.get("labels", [])
    if isinstance(labels, list) and len(labels) > 0:
        first_label = labels[0]
        if isinstance(first_label, dict):
            span = first_label.get("span", {})
            if isinstance(span, dict):
                line = span.get("line", 0)
                column = span.get("column", 0)

    # Oxlint does not currently indicate fixable issues in JSON output
    # Default to False
    fixable = False

    return OxlintIssue(
        file=file_path,
        line=line,
        column=column,
        message=message,
        code=code,
        severity=severity,
        fixable=fixable,
        help=help_text,
    )
