"""JSON output style implementation."""

import json
from datetime import datetime
from typing import Any

from lintro.formatters.core.output_style import OutputStyle


class JsonStyle(OutputStyle):  # type: ignore[misc]
    """Output format that renders data as structured JSON."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a table given columns and rows as structured JSON.

        Args:
            columns: List of column names.
            rows: List of row values (each row is a list of cell values).
            tool_name: Name of the tool that generated the data.
            **kwargs: Additional metadata; `metadata` can be provided here.

        Returns:
            Formatted data as structured JSON string.
        """
        metadata: dict[str, Any] | None = kwargs.pop("metadata", None)
        # Convert column names to standardized format
        normalized_columns = [col.lower().replace(" ", "_") for col in columns]

        # Convert rows to list of dictionaries with proper data types
        issues: list[dict[str, Any]] = []
        for row in rows:
            issue_dict: dict[str, Any] = {}
            for i, value in enumerate(row):
                if i < len(normalized_columns):
                    issue_dict[normalized_columns[i]] = value
            issues.append(issue_dict)

        # Create the final JSON structure
        result: dict[str, Any] = {
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "issues": issues,
        }

        # Add metadata if provided
        if metadata:
            result["metadata"] = metadata

        # Add any additional kwargs as metadata
        if kwargs:
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"].update(kwargs)

        return json.dumps(result, indent=2, ensure_ascii=False)
