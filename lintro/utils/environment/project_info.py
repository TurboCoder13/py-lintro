"""Project detection information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectInfo:
    """Project detection information."""

    working_dir: str
    git_root: str | None
    languages: list[str]
    package_managers: dict[str, str]

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Project"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        rows: list[tuple[str, str]] = [
            ("Working Dir", self.working_dir),
            ("Git Root", self.git_root or "(not a git repo)"),
            ("Languages", ", ".join(self.languages) or "(none detected)"),
        ]
        for pm, manifest in sorted(self.package_managers.items()):
            rows.append((pm, manifest))
        return rows

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return True
