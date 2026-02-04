"""Go runtime information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GoInfo:
    """Go runtime information."""

    version: str | None
    gopath: str | None
    goroot: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Go"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        return [
            ("Version", self.version or "(unknown)"),
            ("GOPATH", self.gopath or "(not set)"),
            ("GOROOT", self.goroot or "(not set)"),
        ]

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return self.version is not None
