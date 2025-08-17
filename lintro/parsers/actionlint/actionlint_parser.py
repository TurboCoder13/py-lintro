"""Parser for actionlint CLI output.

This module parses the default text output produced by the ``actionlint``
binary into structured ``ActionlintIssue`` objects so that Lintro can render
uniform tables and reports across styles.
"""

from __future__ import annotations

import re
from typing import Iterable

from lintro.parsers.actionlint.actionlint_issue import ActionlintIssue

_LINE_RE: re.Pattern[str] = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*(?:(?P<level>error|warning):\s*)?(?P<msg>.*?)(?:\s*\[(?P<code>[A-Za-z0-9_\-\.]+)\])?$",
)


def parse_actionlint_output(output: str | None) -> list[ActionlintIssue]:
    """Parse raw actionlint output into structured issues.

    Args:
        output: Raw stdout/stderr combined output from actionlint.

    Returns:
        list[ActionlintIssue]: Parsed issues from the tool output.
    """
    if not output:
        return []

    issues: list[ActionlintIssue] = []
    for line in _iter_nonempty_lines(output):
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        file_path = m.group("file")
        line_no = int(m.group("line"))
        col_no = int(m.group("col"))
        level = m.group("level") or "error"
        msg = m.group("msg").strip()
        code = m.group("code")
        issues.append(
            ActionlintIssue(
                file=file_path,
                line=line_no,
                column=col_no,
                level=level,
                code=code,
                message=msg,
            ),
        )
    return issues


def _iter_nonempty_lines(text: str) -> Iterable[str]:
    """Iterate non-empty lines from a text block.

    Args:
        text: Input text to split into lines.

    Yields:
        Non-empty lines stripped of surrounding whitespace.
    """
    for ln in text.splitlines():
        if ln.strip():
            yield ln
