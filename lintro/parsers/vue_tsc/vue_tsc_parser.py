"""Parser for vue-tsc output.

Vue-tsc outputs in the same format as tsc (TypeScript compiler), so this
parser uses the same pattern matching logic.
"""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.vue_tsc.vue_tsc_issue import VueTscIssue

# Error codes that indicate missing dependencies rather than actual type errors
# These are the same as tsc since vue-tsc uses the same error codes
DEPENDENCY_ERROR_CODES: frozenset[str] = frozenset(
    {
        "TS2307",  # Cannot find module 'X' or its corresponding type declarations
        "TS2688",  # Cannot find type definition file for 'X'
        "TS7016",  # Could not find a declaration file for module 'X'
    },
)

# Pattern for vue-tsc output (same as tsc with --pretty false):
# file.vue(line,col): error TS1234: message
# file.vue(line,col): warning TS1234: message
VUE_TSC_ISSUE_PATTERN = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*"
    r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*"
    r"(?P<message>.+)$",
)

# Patterns for extracting module names from dependency error messages
_MODULE_PATTERN = re.compile(r"Cannot find module ['\"]([^'\"]+)['\"]")
_TYPEDEF_PATTERN = re.compile(r"type definition file for ['\"]([^'\"]+)['\"]")
_DECL_PATTERN = re.compile(r"declaration file for module ['\"]([^'\"]+)['\"]")


def _parse_line(line: str) -> VueTscIssue | None:
    """Parse a single vue-tsc output line into a VueTscIssue.

    Args:
        line: A single line of vue-tsc output.

    Returns:
        A VueTscIssue instance or None if the line doesn't match.
    """
    line = line.strip()
    if not line:
        return None

    match = VUE_TSC_ISSUE_PATTERN.match(line)
    if not match:
        return None

    try:
        file_path = match.group("file")
        line_num = int(match.group("line"))
        column = int(match.group("column"))
        severity = match.group("severity")
        code = match.group("code")
        message = match.group("message").strip()

        # Normalize Windows paths to forward slashes
        file_path = file_path.replace("\\", "/")

        return VueTscIssue(
            file=file_path,
            line=line_num,
            column=column,
            code=code,
            message=message,
            severity=severity,
        )
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse vue-tsc line: {e}")
        return None


def parse_vue_tsc_output(output: str) -> list[VueTscIssue]:
    """Parse vue-tsc output into VueTscIssue objects.

    Args:
        output: Raw stdout emitted by vue-tsc with --pretty false.

    Returns:
        A list of VueTscIssue instances parsed from the output.

    Examples:
        >>> output = "src/App.vue(10,5): error TS2322: Type error."
        >>> issues = parse_vue_tsc_output(output)
        >>> len(issues)
        1
        >>> issues[0].code
        'TS2322'
    """
    if not output or not output.strip():
        return []

    # Strip ANSI codes for consistent parsing
    output = strip_ansi_codes(output)

    issues: list[VueTscIssue] = []
    for line in output.splitlines():
        parsed = _parse_line(line)
        if parsed:
            issues.append(parsed)

    return issues


def categorize_vue_tsc_issues(
    issues: list[VueTscIssue],
) -> tuple[list[VueTscIssue], list[VueTscIssue]]:
    """Categorize vue-tsc issues into type errors and dependency errors.

    Separates actual type errors from errors caused by missing dependencies
    (e.g., when node_modules is not installed).

    Args:
        issues: List of VueTscIssue objects to categorize.

    Returns:
        A tuple of (type_errors, dependency_errors).
    """
    type_errors: list[VueTscIssue] = []
    dependency_errors: list[VueTscIssue] = []

    for issue in issues:
        if issue.code and issue.code in DEPENDENCY_ERROR_CODES:
            dependency_errors.append(issue)
        else:
            type_errors.append(issue)

    return type_errors, dependency_errors


def extract_missing_modules(dependency_errors: list[VueTscIssue]) -> list[str]:
    """Extract module names from dependency error messages.

    Args:
        dependency_errors: List of VueTscIssue objects with dependency errors.

    Returns:
        List of unique module names that are missing.
    """
    modules: set[str] = set()

    for error in dependency_errors:
        message = error.message or ""

        for pattern in (_MODULE_PATTERN, _TYPEDEF_PATTERN, _DECL_PATTERN):
            match = pattern.search(message)
            if match:
                modules.add(match.group(1))
                break

    return sorted(modules)
