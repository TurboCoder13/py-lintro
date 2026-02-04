"""Protocol for renderable environment sections."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderable(Protocol):
    """Protocol for environment sections that can render themselves.

    This protocol defines the contract for rendering environment info
    to Rich console output. All environment dataclasses implement this.
    """

    @property
    def section_title(self) -> str:
        """Return the section title for display (e.g., 'Python')."""
        ...

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering.

        Returns:
            List of (label, value) tuples. Values can include Rich markup.
        """
        ...

    def is_available(self) -> bool:
        """Return whether this section has data to display.

        For optional sections (Node, Rust, Go, Ruby), this returns False
        when the runtime is not installed. For required sections, always True.
        """
        ...
