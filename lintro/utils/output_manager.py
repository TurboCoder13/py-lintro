"""Output manager for Lintro auto-generated results.

Handles creation of timestamped output directories and writing all required formats.
"""

import csv
import datetime
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lintro.models.core.tool_result import ToolResult


def _markdown_escape(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ")


def _html_escape(text: str) -> str:
    import html

    return html.escape(text)


class OutputManager:
    """Manages output directories and result files for Lintro runs.

    This class creates a timestamped directory under .lintro/run-{timestamp}/
    and provides methods to write all required output formats.
    """

    def __init__(self, base_dir: str = ".lintro", keep_last: int = 10) -> None:
        """Initialize the OutputManager.

        Args:
            base_dir: Base directory for output (default: .lintro)
            keep_last: Number of runs to keep (default: 10)
        """
        # Allow override via environment variable
        env_base_dir = os.environ.get("LINTRO_LOG_DIR")
        if env_base_dir:
            self.base_dir = Path(env_base_dir)
        else:
            self.base_dir = Path(base_dir)
        self.keep_last = keep_last
        self.run_dir = self._create_run_dir()

    def _create_run_dir(self) -> Path:
        """Create a new timestamped run directory.

        Returns:
            Path to the created run directory.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = self.base_dir / f"run-{timestamp}"
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to temp directory if not writable
            temp_base = Path(tempfile.gettempdir()) / ".lintro"
            run_dir = temp_base / f"run-{timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_console_log(self, content: str) -> None:
        """Write the console log to console.log in the run directory.

        Args:
            content: The console output as a string.
        """
        (self.run_dir / "console.log").write_text(content, encoding="utf-8")

    def write_json(self, data: Any, filename: str = "results.json") -> None:
        """Write data as JSON to the run directory.

        Args:
            data: The data to serialize as JSON.
            filename: The output filename (default: results.json)
        """
        with open(self.run_dir / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def write_markdown(self, content: str, filename: str = "report.md") -> None:
        """Write Markdown content to the run directory.

        Args:
            content: Markdown content as a string.
            filename: The output filename (default: report.md)
        """
        (self.run_dir / filename).write_text(content, encoding="utf-8")

    def write_html(self, content: str, filename: str = "report.html") -> None:
        """Write HTML content to the run directory.

        Args:
            content: HTML content as a string.
            filename: The output filename (default: report.html)
        """
        (self.run_dir / filename).write_text(content, encoding="utf-8")

    def write_csv(
        self, rows: list[list[str]], header: list[str], filename: str = "summary.csv"
    ) -> None:
        """Write CSV data to the run directory.

        Args:
            rows: List of rows (each row is a list of strings)
            header: List of column headers
            filename: The output filename (default: summary.csv)
        """
        with open(self.run_dir / filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    def write_reports_from_results(self, results: list["ToolResult"]) -> None:
        """Generate and write Markdown, HTML, and CSV reports from tool results.

        Args:
            results: List of ToolResult objects from a Lintro run.
        """
        self._write_markdown_report(results)
        self._write_html_report(results)
        self._write_csv_summary(results)

    def _write_markdown_report(self, results: list["ToolResult"]) -> None:
        """Write a Markdown report summarizing all tool results and issues.

        Args:
            results: List of ToolResult objects from the linting run.
        """
        lines = ["# Lintro Report", ""]
        lines.append("## Summary\n")
        lines.append("| Tool | Issues |\n|------|--------|\n")
        for r in results:
            lines.append(f"| {r.name} | {r.issues_count} |")
        lines.append("")
        for r in results:
            lines.append(f"### {r.name} ({r.issues_count} issues)")
            if hasattr(r, "issues") and r.issues:
                lines.append("| File | Line | Code | Message |")
                lines.append("|------|------|------|---------|")
                for issue in r.issues:
                    file = _markdown_escape(getattr(issue, "file", ""))
                    line = getattr(issue, "line", "")
                    code = _markdown_escape(getattr(issue, "code", ""))
                    msg = _markdown_escape(getattr(issue, "message", ""))
                    lines.append(f"| {file} | {line} | {code} | {msg} |")
                lines.append("")
            else:
                lines.append("No issues found.\n")
        self.write_markdown("\n".join(lines))

    def _write_html_report(self, results: list["ToolResult"]) -> None:
        """Write an HTML report summarizing all tool results and issues.

        Args:
            results: List of ToolResult objects from the linting run.
        """
        html = ["<html><head><title>Lintro Report</title></head><body>"]
        html.append("<h1>Lintro Report</h1>")
        html.append("<h2>Summary</h2>")
        html.append("<table border='1'><tr><th>Tool</th><th>Issues</th></tr>")
        for r in results:
            html.append(
                f"<tr><td>{_html_escape(r.name)}</td><td>{r.issues_count}</td></tr>"
            )
        html.append("</table>")
        for r in results:
            html.append(f"<h3>{_html_escape(r.name)} ({r.issues_count} issues)</h3>")
            if hasattr(r, "issues") and r.issues:
                html.append(
                    "<table border='1'><tr><th>File</th><th>Line</th><th>Code</th>"
                    "<th>Message</th></tr>"
                )
                for issue in r.issues:
                    file = _html_escape(getattr(issue, "file", ""))
                    line = getattr(issue, "line", "")
                    code = _html_escape(getattr(issue, "code", ""))
                    msg = _html_escape(getattr(issue, "message", ""))
                    html.append(
                        f"<tr><td>{file}</td><td>{line}</td><td>{code}</td><td>{msg}</td></tr>"
                    )
                html.append("</table>")
            else:
                html.append("<p>No issues found.</p>")
        html.append("</body></html>")
        self.write_html("\n".join(html))

    def _write_csv_summary(self, results: list["ToolResult"]) -> None:
        """Write a CSV summary of all tool results and issues.

        Args:
            results: List of ToolResult objects from the linting run.
        """
        rows = []
        header = ["tool", "issues_count", "file", "line", "code", "message"]
        for r in results:
            if hasattr(r, "issues") and r.issues:
                for issue in r.issues:
                    rows.append(
                        [
                            r.name,
                            r.issues_count,
                            getattr(issue, "file", ""),
                            getattr(issue, "line", ""),
                            getattr(issue, "code", ""),
                            getattr(issue, "message", ""),
                        ]
                    )
            else:
                rows.append([r.name, r.issues_count, "", "", "", ""])
        self.write_csv(rows=rows, header=header)

    def cleanup_old_runs(self) -> None:
        """Remove old run directories, keeping only the most recent N runs."""
        if not self.base_dir.exists():
            return
        runs = sorted(
            [
                d
                for d in self.base_dir.iterdir()
                if d.is_dir() and d.name.startswith("run-")
            ],
            key=lambda d: d.name,
            reverse=True,
        )
        for old_run in runs[self.keep_last :]:
            shutil.rmtree(old_run)

    def get_run_dir(self) -> Path:
        """Get the current run directory.

        Returns:
            Path to the current run directory.
        """
        return self.run_dir
