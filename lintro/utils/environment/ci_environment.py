"""CI/CD environment detection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CIEnvironment:
    """CI/CD environment detection."""

    name: str
    is_ci: bool
    details: dict[str, str] = field(default_factory=dict)

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "CI Environment"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        rows: list[tuple[str, str]] = [("Platform", self.name)]
        for key, value in self.details.items():
            rows.append((key, value))
        return rows

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return self.is_ci
