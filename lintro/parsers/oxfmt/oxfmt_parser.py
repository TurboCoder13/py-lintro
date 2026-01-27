"""Parser for oxfmt output.

Handles oxfmt CLI output in --list-different mode which outputs
one file path per line for files that need formatting.
"""

from loguru import logger

from lintro.parsers.base_parser import strip_ansi_codes
from lintro.parsers.oxfmt.oxfmt_issue import OxfmtIssue

# Known error message patterns from oxfmt that should be ignored
_ERROR_PATTERNS: tuple[str, ...] = (
    "Expected at least one target file",
    "error:",
    "Error:",
    "ERROR:",
    "warning:",
    "Warning:",
    "WARNING:",
    "Usage:",
    "usage:",
    "USAGE:",
)

# Valid file extensions that oxfmt processes
_VALID_EXTENSIONS: tuple[str, ...] = (
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".mts",
    ".cts",
    ".tsx",
    ".vue",
    ".svelte",
    ".astro",
)


def _is_valid_file_path(line: str) -> bool:
    """Check if a line looks like a valid file path that oxfmt would process.

    Args:
        line: The line to check.

    Returns:
        True if the line appears to be a valid file path, False otherwise.
    """
    # Skip known error message patterns
    for pattern in _ERROR_PATTERNS:
        if pattern in line:
            return False

    # Check if it has a valid extension
    lower_line = line.lower()
    return any(lower_line.endswith(ext) for ext in _VALID_EXTENSIONS)


def parse_oxfmt_output(output: str | None) -> list[OxfmtIssue]:
    """Parse oxfmt output into a list of OxfmtIssue objects.

    Args:
        output: The raw output from oxfmt --list-different.

    Returns:
        List of OxfmtIssue objects for each file needing formatting.
    """
    issues: list[OxfmtIssue] = []

    if not output:
        return issues

    # Normalize output by stripping ANSI escape sequences
    normalized_output = strip_ansi_codes(output)

    for line in normalized_output.splitlines():
        try:
            line = line.strip()
            if not line:
                continue

            # Skip lines that don't look like valid file paths
            if not _is_valid_file_path(line):
                logger.debug(f"Skipping non-file-path line from oxfmt: '{line}'")
                continue

            # Each valid line is a file path that needs formatting
            issues.append(
                OxfmtIssue(
                    file=line,
                    line=1,
                    column=1,
                    message="File is not formatted",
                    code="FORMAT",
                ),
            )
        except (AttributeError, TypeError) as e:
            logger.debug(f"Failed to parse oxfmt line '{line}': {e}")
            continue

    return issues
