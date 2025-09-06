"""Parser for Black output.

Black commonly emits terse messages like:
- "would reformat foo.py" (check mode with --check)
- "reformatted foo.py" (fix mode)
- a summary line like "1 file would be reformatted" or
  "2 files reformatted" (with no per-file lines in some environments).

We normalize items into ``BlackIssue`` objects so the table formatter can
render consistent rows. When only a summary is present, we synthesize one
``BlackIssue`` per counted file with ``file`` set to "<unknown>" so totals
remain accurate across environments.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from lintro.parsers.black.black_issue import BlackIssue

_WOULD_REFORMAT = re.compile(r"^would reformat\s+(?P<file>.+)$", re.IGNORECASE)
_REFORMATTED = re.compile(r"^reformatted\s+(?P<file>.+)$", re.IGNORECASE)
_SUMMARY_WOULD = re.compile(
    r"(?P<count>\d+)\s+file(?:s)?\s+would\s+be\s+reformatted\.?",
    re.IGNORECASE,
)
_SUMMARY_REFORMATTED = re.compile(
    r"(?P<count>\d+)\s+file(?:s)?\s+reformatted\.?",
    re.IGNORECASE,
)


def _iter_issue_lines(lines: Iterable[str]) -> Iterable[str]:
    for line in lines:
        s = line.strip()
        if not s:
            continue
        yield s


def parse_black_output(output: str) -> list[BlackIssue]:
    """Parse Black CLI output into a list of ``BlackIssue`` objects.

    Args:
        output: Raw stdout+stderr from a Black invocation.

    Returns:
        list[BlackIssue]: Per-file issues indicating formatting diffs. If only
        a summary is present (no per-file lines), returns a synthesized list
        sized to the summary count with ``file`` set to "<unknown>".
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

    # Some environments (e.g., CI) may emit only a summary line without listing
    # per-file entries. In that case, synthesize issues so counts remain
    # consistent across environments.
    if not issues:
        m_sum = _SUMMARY_WOULD.search(output)
        if not m_sum:
            m_sum = _SUMMARY_REFORMATTED.search(output)
        if m_sum:
            try:
                count = int(m_sum.group("count"))
            except Exception:
                count = 0
            if count > 0:
                for _ in range(count):
                    issues.append(
                        BlackIssue(
                            file="<unknown>",
                            message="Formatting change detected",
                        ),
                    )

    return issues
