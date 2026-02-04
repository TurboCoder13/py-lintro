"""Ruby runtime information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RubyInfo:
    """Ruby runtime information."""

    version: str | None
    gem_version: str | None
    bundler_version: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Ruby"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        return [
            ("Version", self.version or "(unknown)"),
            ("gem", self.gem_version or "(not found)"),
            ("bundler", self.bundler_version or "(not installed)"),
        ]

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return self.version is not None
