"""Rust runtime information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RustInfo:
    """Rust runtime information."""

    rustc_version: str | None
    cargo_version: str | None
    rustfmt_version: str | None
    clippy_version: str | None

    @property
    def section_title(self) -> str:
        """Return the section title for display."""
        return "Rust"

    def to_display_rows(self) -> list[tuple[str, str]]:
        """Return label-value pairs for rendering."""
        return [
            ("rustc", self.rustc_version or "(unknown)"),
            ("cargo", self.cargo_version or "(unknown)"),
            ("rustfmt", self.rustfmt_version or "(not found)"),
            ("clippy", self.clippy_version or "(not found)"),
        ]

    def is_available(self) -> bool:
        """Return whether this section has data to display."""
        return self.rustc_version is not None or self.cargo_version is not None
