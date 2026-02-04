"""Operating system and shell information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SystemInfo:
    """Operating system and shell information."""

    os_name: str
    os_version: str
    platform_name: str
    architecture: str
    shell: str | None
    terminal: str | None
    locale: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "System"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        rows: list[tuple[str, str]] = [
            ("OS", f"{self.platform_name} ({self.os_version})"),
        ]
        # Include os_name if it differs from platform_name (provides additional detail)
        if self.os_name and self.os_name != self.platform_name:
            rows.append(("OS Name", self.os_name))
        rows.extend(
            [
                ("Architecture", self.architecture),
                ("Shell", self.shell or "(unknown)"),
                ("Terminal", self.terminal or "(unknown)"),
                ("Locale", self.locale or "(not set)"),
            ],
        )
        return rows

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return True
