"""Parser for mypy JSON output."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from lintro.parsers.base_parser import extract_int_field, extract_str_field
from lintro.parsers.mypy.mypy_issue import MypyIssue


def _parse_issue(item: dict[str, Any]) -> MypyIssue | None:
    """Convert a mypy JSON error object into a ``MypyIssue``.

    Args:
        item: A single issue payload returned by mypy in JSON form.

    Returns:
        A populated ``MypyIssue`` instance or ``None`` when the payload cannot
        be parsed.
    """
    try:
        file_path = extract_str_field(item, ["path", "filename", "file"])
        if not file_path:
            return None

        line = extract_int_field(item, ["line"], default=0) or 0
        column = extract_int_field(item, ["column"], default=0) or 0
        end_line_int = extract_int_field(item, ["endLine", "end_line"])
        end_column_int = extract_int_field(item, ["endColumn", "end_column"])

        raw_code = item.get("code")
        code: str | None
        if isinstance(raw_code, dict):
            code = (
                raw_code.get("code")
                or raw_code.get("id")
                or raw_code.get("text")
                or None
            )
        else:
            code = str(raw_code) if raw_code is not None else None

        message = str(item.get("message") or "").strip()
        severity = item.get("severity")

        return MypyIssue(
            file=file_path,
            line=line,
            column=column,
            code=code,
            message=message,
            severity=str(severity) if severity is not None else None,
            end_line=end_line_int,
            end_column=end_column_int,
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.debug(f"Failed to parse mypy issue item: {e}")
        return None


def _extract_errors(data: Any) -> list[dict[str, Any]]:
    """Extract error objects from parsed JSON data.

    Args:
        data: The decoded JSON payload emitted by mypy.

    Returns:
        A list of error dictionaries ready for issue parsing.
    """
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        errors = data.get("errors") or data.get("messages") or []
        if isinstance(errors, dict):
            errors = [errors]
        extracted = [item for item in errors if isinstance(item, dict)]
        if not extracted and any(
            key in data for key in ("path", "filename", "file", "message")
        ):
            # Treat single error dict payload as one issue
            return [data]
        return extracted
    return []


def parse_mypy_output(output: str) -> list[MypyIssue]:
    """Parse mypy JSON or JSON-lines output into ``MypyIssue`` objects.

    Args:
        output: Raw stdout emitted by mypy using ``--output json``.

    Returns:
        A list of ``MypyIssue`` instances parsed from the output. Returns an
        empty list when no issues are present or the output cannot be decoded.
    """
    if not output or not output.strip():
        return []

    try:
        data = json.loads(output)
        items = _extract_errors(data)
        return [issue for item in items if (issue := _parse_issue(item))]
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse mypy JSON output: {e}")
    except (TypeError, ValueError) as e:
        logger.debug(f"Error processing mypy output: {e}")

    # Fallback: try JSON Lines format
    issues: list[MypyIssue] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        except (TypeError, ValueError) as e:
            logger.debug(f"Error parsing mypy JSON line: {e}")
            continue
        try:
            items = _extract_errors(data) if isinstance(data, (dict, list)) else []
            for item in items:
                parsed = _parse_issue(item)
                if parsed:
                    issues.append(parsed)
        except (TypeError, ValueError, KeyError) as e:
            logger.debug(f"Error extracting mypy errors: {e}")
            continue

    return issues
