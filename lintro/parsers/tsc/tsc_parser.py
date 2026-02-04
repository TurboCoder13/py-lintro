"""Parser for tsc (TypeScript Compiler) text output."""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.tsc.tsc_issue import TscIssue

# Error codes that indicate missing dependencies rather than actual type errors
# These occur when node_modules is missing or dependencies aren't installed
# Note: TS2792 is intentionally excluded from DEPENDENCY_ERROR_CODES because it
# indicates module resolution/configuration problems rather than missing deps
DEPENDENCY_ERROR_CODES: frozenset[str] = frozenset(
    {
        "TS2307",  # Cannot find module 'X' or its corresponding type declarations
        "TS2688",  # Cannot find type definition file for 'X'
        "TS7016",  # Could not find a declaration file for module 'X'
    },
)

# Pattern for tsc output with --pretty false:
# file.ts(line,col): error TS1234: message
# file.ts(line,col): warning TS1234: message
# Also handles Windows paths with backslashes
TSC_ISSUE_PATTERN = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*"
    r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*"
    r"(?P<message>.+)$",
)


def _parse_line(line: str) -> TscIssue | None:
    """Parse a single tsc output line into a TscIssue.

    Args:
        line: A single line of tsc output.

    Returns:
        A TscIssue instance or None if the line doesn't match the expected format.
    """
    line = line.strip()
    if not line:
        return None

    match = TSC_ISSUE_PATTERN.match(line)
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

        return TscIssue(
            file=file_path,
            line=line_num,
            column=column,
            code=code,
            message=message,
            severity=severity,
        )
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse tsc line: {e}")
        return None


def parse_tsc_output(output: str) -> list[TscIssue]:
    """Parse tsc text output into TscIssue objects.

    Args:
        output: Raw stdout emitted by tsc with --pretty false.

    Returns:
        A list of TscIssue instances parsed from the output. Returns an
        empty list when no issues are present or the output cannot be decoded.

    Examples:
        >>> output = "src/main.ts(10,5): error TS2322: Type error."
        >>> issues = parse_tsc_output(output)
        >>> len(issues)
        1
        >>> issues[0].code
        'TS2322'
    """
    if not output or not output.strip():
        return []

    # Strip ANSI codes for consistent parsing across environments
    output = strip_ansi_codes(output)

    issues: list[TscIssue] = []
    for line in output.splitlines():
        parsed = _parse_line(line)
        if parsed:
            issues.append(parsed)

    return issues


def categorize_tsc_issues(
    issues: list[TscIssue],
) -> tuple[list[TscIssue], list[TscIssue]]:
    """Categorize tsc issues into type errors and dependency errors.

    Separates actual type errors from errors caused by missing dependencies
    (e.g., when node_modules is not installed).

    Args:
        issues: List of TscIssue objects to categorize.

    Returns:
        A tuple of (type_errors, dependency_errors) where:
        - type_errors: Issues that are actual type errors in the code
        - dependency_errors: Issues caused by missing modules/dependencies

    Examples:
        >>> issues = [
        ...     TscIssue(
        ...         file="a.ts", line=1, column=1,
        ...         code="TS2322", message="Type error",
        ...     ),
        ...     TscIssue(
        ...         file="b.ts", line=1, column=1,
        ...         code="TS2307", message="Cannot find module",
        ...     ),
        ... ]
        >>> type_errors, dep_errors = categorize_tsc_issues(issues)
        >>> len(type_errors)
        1
        >>> len(dep_errors)
        1
    """
    type_errors: list[TscIssue] = []
    dependency_errors: list[TscIssue] = []

    for issue in issues:
        if issue.code and issue.code in DEPENDENCY_ERROR_CODES:
            dependency_errors.append(issue)
        else:
            type_errors.append(issue)

    return type_errors, dependency_errors


def extract_missing_modules(dependency_errors: list[TscIssue]) -> list[str]:
    """Extract module names from dependency error messages.

    Parses the error messages to extract the names of missing modules
    for clearer user feedback.

    Args:
        dependency_errors: List of TscIssue objects with dependency errors.

    Returns:
        List of unique module names that are missing.

    Examples:
        >>> from lintro.parsers.tsc.tsc_issue import TscIssue
        >>> errors = [
        ...     TscIssue(
        ...         file="a.ts", line=1, column=1, code="TS2307",
        ...         message="Cannot find module 'react'.",
        ...     ),
        ... ]
        >>> extract_missing_modules(errors)
        ['react']
    """
    modules: set[str] = set()

    # Pattern to extract module name from common tsc error messages
    # Matches: "Cannot find module 'X'" or "Cannot find module \"X\""
    module_pattern = re.compile(r"Cannot find module ['\"]([^'\"]+)['\"]")
    # Matches: "type definition file for 'X'"
    typedef_pattern = re.compile(r"type definition file for ['\"]([^'\"]+)['\"]")
    # Matches: "declaration file for module 'X'"
    decl_pattern = re.compile(r"declaration file for module ['\"]([^'\"]+)['\"]")

    for error in dependency_errors:
        message = error.message or ""

        for pattern in (module_pattern, typedef_pattern, decl_pattern):
            match = pattern.search(message)
            if match:
                modules.add(match.group(1))
                break

    return sorted(modules)
