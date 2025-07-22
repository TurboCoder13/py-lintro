"""Output manager for Lintro auto-generated results.

Handles creation of timestamped output directories and writing all required formats.
"""

import os
import shutil
import json
import csv
import datetime
from pathlib import Path
from typing import Any

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

    def write_csv(self, rows: list[list[str]], header: list[str], filename: str = "summary.csv") -> None:
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

    def cleanup_old_runs(self) -> None:
        """Remove old run directories, keeping only the most recent N runs."""
        if not self.base_dir.exists():
            return
        runs = sorted(
            [d for d in self.base_dir.iterdir() if d.is_dir() and d.name.startswith("run-")],
            key=lambda d: d.name,
            reverse=True,
        )
        for old_run in runs[self.keep_last:]:
            shutil.rmtree(old_run)

    def get_run_dir(self) -> Path:
        """Get the current run directory.

        Returns:
            Path to the current run directory.
        """
        return self.run_dir 