"""Parser for prettier output.

Handles typical Prettier CLI output for --check and --write modes,
including ANSI-colored lines produced in CI environments.
"""

import re

from lintro.parsers.prettier.prettier_issue import PrettierIssue


def parse_prettier_output(output: str) -> list[PrettierIssue]:
    """Parse prettier output into a list of PrettierIssue objects.

    Args:
        output: The raw output from prettier

    Returns:
        List of PrettierIssue objects
    """
    issues: list[PrettierIssue] = []

    if not output:
        return issues

    # Prettier output format when issues are found:
    # "Checking formatting..."
    # "[warn] path/to/file.js"
    # "[warn] Code style issues found in the above file. Run Prettier with --write \
    # to fix."
    # Normalize output by stripping ANSI escape sequences to make matching robust
    # across different terminals and CI runners.
    # Example: "[\x1b[33mwarn\x1b[39m] file.js" -> "[warn] file.js"
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    normalized_output = ansi_escape.sub("", output)

    lines = normalized_output.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Look for [warn] lines that contain file paths
        if line.startswith("[warn]") and not line.endswith("fix."):
            # Extract the file path from the [warn] line
            file_path = line[6:].strip()  # Remove "[warn] " prefix
            if file_path and not file_path.startswith("Code style issues"):
                # Create a generic issue for the file
                issues.append(
                    PrettierIssue(
                        file=file_path,
                        line=1,  # Prettier doesn't provide specific line numbers
                        code="FORMAT",
                        message="Code style issues found",
                        column=1,  # Prettier doesn't provide specific column numbers
                    ),
                )

    return issues
