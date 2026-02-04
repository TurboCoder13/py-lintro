"""Lintro installation information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LintroInfo:
    """Lintro installation information."""

    version: str
    install_path: str
    config_file: str | None
    config_valid: bool

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Lintro"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        rows: list[tuple[str, str]] = [
            ("Version", self.version),
            ("Install Path", self.install_path),
            ("Config File", self.config_file or "(not found)"),
        ]
        if self.config_file:
            status = (
                "[green]\u2713[/green]" if self.config_valid else "[red]\u2717[/red]"
            )
            rows.append(("Config Valid", status))
        return rows

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return True
