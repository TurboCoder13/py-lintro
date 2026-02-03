"""Python runtime information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PythonInfo:
    """Python runtime information."""

    version: str
    executable: str
    virtual_env: str | None
    pip_version: str | None
    uv_version: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Python"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        return [
            ("Version", self.version),
            ("Executable", self.executable),
            ("Virtual Env", self.virtual_env or "(none)"),
            ("pip", self.pip_version or "(not found)"),
            ("uv", self.uv_version or "(not found)"),
        ]

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return True
