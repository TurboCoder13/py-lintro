"""Parser for shfmt output.

Shfmt outputs in unified diff format when run with the -d flag. This parser
extracts file and line information from diff headers and creates ShfmtIssue
objects for each file that needs formatting.

Example shfmt diff output:
--- script.sh.orig
+++ script.sh
@@ -1,3 +1,3 @@
-if [  "$foo" = "bar" ]; then
+if [ "$foo" = "bar" ]; then
   echo "match"
 fi
"""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.shfmt.shfmt_issue import ShfmtIssue

# Pattern for diff file header: --- path or +++ path
_DIFF_FILE_HEADER = re.compile(r"^(?:---|\+\+\+)\s+(.+?)(?:\.orig)?$")

# Pattern for diff hunk header: @@ -start,count +start,count @@
_DIFF_HUNK_HEADER = re.compile(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")


def parse_shfmt_output(output: str | None) -> list[ShfmtIssue]:
    """Parse shfmt diff output into a list of ShfmtIssue objects.

    Shfmt outputs unified diff format when run with -d flag. This function
    parses the diff output and extracts:
    - File path from diff headers
    - Line numbers from hunk headers
    - Diff content for context

    Args:
        output: Raw stdout from shfmt -d invocation. May be None or empty
            if no formatting issues were found.

    Returns:
        List of ShfmtIssue objects, one per file that needs formatting.
        Returns empty list if output is None, empty, or contains no diffs.
    """
    if not output or not output.strip():
        return []

    issues: list[ShfmtIssue] = []
    current_file: str | None = None
    current_line: int = 0
    current_diff_lines: list[str] = []

    try:
        lines = output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for diff file header (--- or +++)
            file_match = _DIFF_FILE_HEADER.match(line)
            if file_match:
                # When we see a new --- header, save any pending issue
                if line.startswith("---"):
                    if current_file is not None and current_diff_lines:
                        issues.append(
                            ShfmtIssue(
                                file=current_file,
                                line=current_line,
                                column=0,
                                message="Needs formatting",
                                diff_content="\n".join(current_diff_lines),
                                fixable=True,
                            ),
                        )
                    # Start tracking new file
                    current_file = file_match.group(1)
                    current_line = 0
                    current_diff_lines = [line]
                elif line.startswith("+++") and current_file is not None:
                    # Add +++ line to current diff
                    current_diff_lines.append(line)
                i += 1
                continue

            # Check for hunk header
            hunk_match = _DIFF_HUNK_HEADER.match(line)
            if hunk_match and current_file is not None:
                # Use the first line number from the hunk if not set
                if current_line == 0:
                    current_line = int(hunk_match.group(2))
                current_diff_lines.append(line)
                i += 1
                continue

            # Collect diff content lines (starting with -, +, or space)
            if current_file is not None and (
                line.startswith("-")
                or line.startswith("+")
                or line.startswith(" ")
                or line == ""
            ):
                current_diff_lines.append(line)

            i += 1

        # Don't forget the last file
        if current_file is not None and current_diff_lines:
            issues.append(
                ShfmtIssue(
                    file=current_file,
                    line=current_line if current_line > 0 else 1,
                    column=0,
                    message="Needs formatting",
                    diff_content="\n".join(current_diff_lines),
                    fixable=True,
                ),
            )

    except (ValueError, AttributeError, IndexError) as e:
        logger.debug(f"Error parsing shfmt output: {e}")

    return issues
