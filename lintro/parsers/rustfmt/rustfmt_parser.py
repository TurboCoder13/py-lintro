"""Parser for rustfmt output.

Rustfmt with --check outputs diff-style format when files need formatting:
- "Diff in /path/to/file.rs at line N:" followed by diff content
- Or simply lists files that would be reformatted

We parse this output to extract file paths and create RustfmtIssue objects.
"""

from __future__ import annotations

import re

from loguru import logger

from lintro.parsers.rustfmt.rustfmt_issue import RustfmtIssue

# Pattern to match "Diff in <file>:<line>:" format (actual rustfmt output)
_DIFF_IN_RE = re.compile(r"^Diff in (?P<file>.+?):(?P<line>\d+):?$")

# Pattern to match file paths that would be reformatted
# cargo fmt -- --check may output just the file path when using certain options
_FILE_PATH_RE = re.compile(r"^(?P<file>.+\.rs)$")


def parse_rustfmt_output(output: str | None) -> list[RustfmtIssue]:
    """Parse rustfmt output into issues.

    Args:
        output: Raw stdout/stderr from rustfmt/cargo fmt --check.

    Returns:
        List of parsed issues, one per file that needs formatting.
    """
    if not output:
        return []

    issues: list[RustfmtIssue] = []
    seen_files: set[str] = set()

    try:
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Try to match "Diff in <file> at line <n>:" format
            m = _DIFF_IN_RE.match(line)
            if m:
                file_path = m.group("file")
                line_num = int(m.group("line"))

                # Only add first occurrence per file to avoid duplicates
                if file_path not in seen_files:
                    seen_files.add(file_path)
                    issues.append(
                        RustfmtIssue(
                            file=file_path,
                            line=line_num,
                            column=0,
                            message="File needs formatting",
                            fixable=True,
                        ),
                    )
                continue

            # Try to match standalone file paths (some rustfmt output modes)
            m = _FILE_PATH_RE.match(line)
            if m:
                file_path = m.group("file")
                if file_path not in seen_files:
                    seen_files.add(file_path)
                    issues.append(
                        RustfmtIssue(
                            file=file_path,
                            line=0,
                            column=0,
                            message="File needs formatting",
                            fixable=True,
                        ),
                    )
                continue

    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Error parsing rustfmt output: {e}")

    return issues
