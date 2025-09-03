"""Parser for Black output.

Black commonly emits terse messages like:
- "would reformat foo.py" (check mode with --check)
- "reformatted foo.py" (fix mode)
- or a summary line like "1 file would be reformatted".

We normalize per-file items into BlackIssue objects so the table formatter can
render consistent rows.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from lintro.parsers.black.black_issue import BlackIssue

_WOULD_REFORMAT = re.compile(r"^would reformat\s+(?P<file>.+)$", re.IGNORECASE)
_REFORMATTED = re.compile(r"^reformatted\s+(?P<file>.+)$", re.IGNORECASE)


def _iter_issue_lines(lines: Iterable[str]) -> Iterable[str]:
    for line in lines:
        s = line.strip()
        if not s:
            continue
        yield s


def parse_black_output(output: str) -> list[BlackIssue]:
    """Parse Black CLI output into a list of BlackIssue objects.

    Args:
        output: Raw stdout+stderr from a Black invocation.

    Returns:
        list[BlackIssue]: Per-file issues indicating formatting diffs.
    """
    if not output:
        return []

    issues: list[BlackIssue] = []
    for line in _iter_issue_lines(output.splitlines()):
        m = _WOULD_REFORMAT.match(line)
        if m:
            issues.append(
                BlackIssue(file=m.group("file"), message="Would reformat file"),
            )
            continue
        m = _REFORMATTED.match(line)
        if m:
            issues.append(BlackIssue(file=m.group("file"), message="Reformatted file"))
            continue

    return issues
