"""Node.js runtime information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NodeInfo:
    """Node.js runtime information."""

    version: str | None
    path: str | None
    npm_version: str | None
    bun_version: str | None
    pnpm_version: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Node.js"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        return [
            ("Version", self.version or "(unknown)"),
            ("Path", self.path or "(unknown)"),
            ("npm", self.npm_version or "(not found)"),
            ("bun", self.bun_version or "(not installed)"),
            ("pnpm", self.pnpm_version or "(not installed)"),
        ]

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return self.version is not None or self.path is not None
