import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from lintro.formatters.core.output_style import OutputStyle


class JsonStyle(OutputStyle):
    """Output format that renders data as structured JSON."""

    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
        tool_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """Format a table given columns and rows as structured JSON.

        Args:
            columns: List of column names.
            rows: List of row values (each row is a list of cell values).
            tool_name: Name of the tool that generated the data.
            metadata: Tool-specific metadata.
            **kwargs: Additional metadata.

        Returns:
            Formatted data as structured JSON string.
        """
        # Convert column names to standardized format
        normalized_columns = [col.lower().replace(" ", "_") for col in columns]

        # Convert rows to list of dictionaries with proper data types
        issues = []
        for row in rows:
            issue = {}
            for i, col in enumerate(normalized_columns):
                if i < len(row):
                    value = row[i]
                    # Convert line numbers to integers
                    if (
                        col in ["line", "line_number", "row"]
                        and isinstance(value, str)
                        and value.isdigit()
                    ):
                        value = int(value)
                    # Convert column numbers to integers
                    elif (
                        col in ["column", "col", "position"]
                        and isinstance(value, str)
                        and value.isdigit()
                    ):
                        value = int(value)
                    # Keep other values as strings, but handle empty values
                    elif value == "":
                        value = None
                    issue[col] = value
                else:
                    issue[col] = None
            issues.append(issue)

        # Build tool-specific metadata
        tool_metadata = {
            "timestamp": datetime.now().isoformat(),
            "format_version": "1.0",
        }

        # Add tool-specific metadata if provided
        if metadata:
            tool_metadata.update(metadata)

        # Add any additional metadata from kwargs
        for key, value in kwargs.items():
            if key not in ["columns", "rows", "tool_name", "metadata"]:
                tool_metadata[key] = value

        # Build the tool result structure
        tool_result = {
            "metadata": tool_metadata,
            "summary": {"total_issues": len(issues), "has_issues": len(issues) > 0},
            "issues": issues,
        }

        # Group issues by severity if severity field exists
        if issues and any("severity" in issue for issue in issues):
            severity_counts = {}
            for issue in issues:
                severity = issue.get("severity", "unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            tool_result["summary"]["by_severity"] = severity_counts

        # Group issues by file if file field exists
        if issues and any("file" in issue for issue in issues):
            file_counts = {}
            for issue in issues:
                file_path = issue.get("file", "unknown")
                file_counts[file_path] = file_counts.get(file_path, 0) + 1
            tool_result["summary"]["by_file"] = file_counts

        # Group issues by code/rule if code field exists
        if issues and any(
            field in issue for issue in issues for field in ["code", "rule"]
        ):
            code_counts = {}
            for issue in issues:
                code = issue.get("code") or issue.get("rule") or "unknown"
                code_counts[code] = code_counts.get(code, 0) + 1
            tool_result["summary"]["by_code"] = code_counts

        # If no tool name provided, return just the tool result
        if not tool_name:
            return json.dumps(tool_result, indent=2, sort_keys=True)

        # Build the complete result structure with tool grouping
        result = {
            "lintro_results": {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "format_version": "1.0",
                    "format": "json",
                },
                "summary": {
                    "total_tools": 1,
                    "total_issues": len(issues),
                    "has_issues": len(issues) > 0,
                },
                "tools": {tool_name: tool_result},
            }
        }

        return json.dumps(result, indent=2, sort_keys=True)
