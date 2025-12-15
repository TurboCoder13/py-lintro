"""Parser for Biome JSON output.

Handles Biome JSON format output from --reporter=json flag.
"""

import json
from typing import Any

from lintro.parsers.biome.biome_issue import BiomeIssue


def _char_to_line_column(source_code: str, char_pos: int) -> tuple[int, int]:
    """Convert character position to 1-based line and column numbers.

    Args:
        source_code: The source code string
        char_pos: 0-based character position

    Returns:
        Tuple of (line, column) as 1-based numbers
    """
    if char_pos < 0:
        return 1, 1

    # Clamp to source code length
    char_pos = min(char_pos, len(source_code))

    line = 1
    column = 1

    for i in range(char_pos):
        if source_code[i] == "\n":
            line += 1
            column = 1
        else:
            column += 1

    return line, column


def parse_biome_output(output: str) -> list[BiomeIssue]:
    """Parse Biome JSON output into a list of BiomeIssue objects.

    Args:
        output: The raw JSON output from Biome.

    Returns:
        List of BiomeIssue objects.
    """
    issues: list[BiomeIssue] = []

    if not output:
        return issues

    try:
        # Biome JSON format is a single object with diagnostics array
        # Extract JSON from output (Biome may add extra text after JSON)
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            return issues
        json_content = output[json_start:json_end]
        biome_data: dict[str, Any] = json.loads(json_content)
    except (json.JSONDecodeError, ValueError):
        # If output is not valid JSON, return empty list
        return issues

    diagnostics = biome_data.get("diagnostics", [])
    for diagnostic in diagnostics:
        # Extract location information
        location = diagnostic.get("location", {})
        path_info = location.get("path", {})
        file_path = (
            path_info.get("file", "") if isinstance(path_info, dict) else str(path_info)
        )

        # Extract span (character positions array)
        span = location.get("span", [])
        if isinstance(span, list) and len(span) >= 1:
            start_char = span[0]
            # Convert character position to line/column
            # Note: Biome spans are absolute positions in the file, but we use
            # the sourceCode snippet for relative positioning within the error context
            source_code = location.get("sourceCode", "")
            if source_code:
                # Only calculate line/column if start position is within the
                # source code snippet (Biome sometimes provides absolute file
                # positions beyond the snippet)
                if start_char <= len(source_code):
                    line, column = _char_to_line_column(source_code, start_char)
                else:
                    # Start position beyond snippet, use defaults
                    line = 1
                    column = 1

                # End position (optional) - only set if span has end position
                if len(span) >= 2:
                    end_char = span[1]
                    # Only set end position if it's within the source code snippet
                    # (Biome sometimes provides absolute file positions)
                    if end_char <= len(source_code):
                        end_line, end_column = _char_to_line_column(
                            source_code,
                            end_char,
                        )
                    else:
                        end_line = None
                        end_column = None
                else:
                    end_line = None
                    end_column = None
            else:
                # No source code available, use defaults
                line = 1
                column = 1
                end_line = None
                end_column = None
        else:
            # Fallback for malformed span
            line = 1
            column = 1
            end_line = None
            end_column = None

        # Extract diagnostic details
        category = diagnostic.get("category", "unknown")
        severity = diagnostic.get("severity", "error")
        description = diagnostic.get("description", "")

        # Check if fixable
        tags = diagnostic.get("tags", [])
        fixable = "fixable" in tags

        # Skip if no file path
        if not file_path:
            continue

        issues.append(
            BiomeIssue(
                file=file_path,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
                code=category,
                message=description,
                severity=severity,
                fixable=fixable,
            ),
        )

    return issues
