"""Output writers for different file formats.

Handles writing lintro results to various output formats (JSON, CSV, Markdown,
HTML, Plain).
"""

import csv
import datetime
import html
import json
from pathlib import Path

from lintro.enums.action import Action
from lintro.enums.output_format import OutputFormat


def write_output_file(
    *,
    output_path: str,
    output_format: OutputFormat,
    all_results: list,
    action: Action,
    total_issues: int,
    total_fixed: int,
) -> None:
    """Write results to user-specified output file.

    Args:
        output_path: str: Path to the output file.
        output_format: OutputFormat: Format for the output.
        all_results: list: List of ToolResult objects.
        action: Action: The action performed (check, fmt, test).
        total_issues: int: Total number of issues found.
        total_fixed: int: Total number of issues fixed.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_format == OutputFormat.JSON:
        # Build JSON structure similar to stdout JSON mode
        json_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action.value,
            "summary": {
                "total_issues": total_issues,
                "total_fixed": total_fixed,
                "tools_run": len(all_results),
            },
            "results": [],
        }
        for result in all_results:
            result_data = {
                "tool": result.name,
                "success": getattr(result, "success", True),
                "issues_count": getattr(result, "issues_count", 0),
                "output": getattr(result, "output", ""),
            }
            if hasattr(result, "issues") and result.issues:
                result_data["issues"] = [
                    {
                        "file": getattr(issue, "file", ""),
                        "line": getattr(issue, "line", ""),
                        "code": getattr(issue, "code", ""),
                        "message": getattr(issue, "message", ""),
                    }
                    for issue in result.issues
                ]
            json_data["results"].append(result_data)
        output_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    elif output_format == OutputFormat.CSV:
        # Write CSV format
        rows: list[list[str]] = []
        header: list[str] = ["tool", "issues_count", "file", "line", "code", "message"]
        for result in all_results:
            if hasattr(result, "issues") and result.issues:
                for issue in result.issues:
                    rows.append(
                        [
                            result.name,
                            str(getattr(result, "issues_count", 0)),
                            str(getattr(issue, "file", "")),
                            str(getattr(issue, "line", "")),
                            str(getattr(issue, "code", "")),
                            str(getattr(issue, "message", "")),
                        ],
                    )
            else:
                rows.append(
                    [
                        result.name,
                        str(getattr(result, "issues_count", 0)),
                        "",
                        "",
                        "",
                        "",
                    ],
                )
        with output_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    elif output_format == OutputFormat.MARKDOWN:
        # Write Markdown format
        lines: list[str] = ["# Lintro Report", ""]
        lines.append("## Summary\n")
        lines.append("| Tool | Issues |")
        lines.append("|------|--------|")
        for result in all_results:
            lines.append(f"| {result.name} | {getattr(result, 'issues_count', 0)} |")
        lines.append("")
        for result in all_results:
            issues_count = getattr(result, "issues_count", 0)
            lines.append(f"### {result.name} ({issues_count} issues)")
            if hasattr(result, "issues") and result.issues:
                lines.append("| File | Line | Code | Message |")
                lines.append("|------|------|------|---------|")
                for issue in result.issues:
                    file_val = str(getattr(issue, "file", "")).replace("|", r"\|")
                    line_val = getattr(issue, "line", "")
                    code_val = str(getattr(issue, "code", "")).replace("|", r"\|")
                    msg_val = str(getattr(issue, "message", "")).replace("|", r"\|")
                    lines.append(
                        f"| {file_val} | {line_val} | {code_val} | {msg_val} |",
                    )
                lines.append("")
            else:
                lines.append("No issues found.\n")
        output_file.write_text("\n".join(lines), encoding="utf-8")

    elif output_format == OutputFormat.HTML:
        # Write HTML format
        html_lines: list[str] = [
            "<html><head><title>Lintro Report</title></head><body>",
        ]
        html_lines.append("<h1>Lintro Report</h1>")
        html_lines.append("<h2>Summary</h2>")
        html_lines.append("<table border='1'><tr><th>Tool</th><th>Issues</th></tr>")
        for result in all_results:
            safe_name = html.escape(result.name)
            html_lines.append(
                f"<tr><td>{safe_name}</td>"
                f"<td>{getattr(result, 'issues_count', 0)}</td></tr>",
            )
        html_lines.append("</table>")
        for result in all_results:
            issues_count = getattr(result, "issues_count", 0)
            html_lines.append(
                f"<h3>{html.escape(result.name)} ({issues_count} issues)</h3>",
            )
            if hasattr(result, "issues") and result.issues:
                html_lines.append(
                    "<table border='1'><tr><th>File</th><th>Line</th>"
                    "<th>Code</th><th>Message</th></tr>",
                )
                for issue in result.issues:
                    f_val = html.escape(str(getattr(issue, "file", "")))
                    l_val = html.escape(str(getattr(issue, "line", "")))
                    c_val = html.escape(str(getattr(issue, "code", "")))
                    m_val = html.escape(str(getattr(issue, "message", "")))
                    html_lines.append(
                        f"<tr><td>{f_val}</td><td>{l_val}</td>"
                        f"<td>{c_val}</td><td>{m_val}</td></tr>",
                    )
                html_lines.append("</table>")
            else:
                html_lines.append("<p>No issues found.</p>")
        html_lines.append("</body></html>")
        output_file.write_text("\n".join(html_lines), encoding="utf-8")

    else:
        # Plain or Grid format - write formatted text output
        lines: list[str] = [f"Lintro {action.value.capitalize()} Report", "=" * 40, ""]
        for result in all_results:
            issues_count = getattr(result, "issues_count", 0)
            lines.append(f"{result.name}: {issues_count} issues")
            output_text = getattr(result, "output", "")
            if output_text and output_text.strip():
                lines.append(output_text.strip())
            lines.append("")
        lines.append(f"Total Issues: {total_issues}")
        if action == Action.FIX:
            lines.append(f"Total Fixed: {total_fixed}")
        output_file.write_text("\n".join(lines), encoding="utf-8")
