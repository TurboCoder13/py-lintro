"""Issue model for cargo-audit output."""

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class CargoAuditIssue(BaseIssue):
    """Represents a security vulnerability found by cargo-audit.

    Attributes:
        advisory_id: RustSec advisory ID (e.g., RUSTSEC-2021-0124).
        package_name: Name of the vulnerable crate.
        package_version: Version of the vulnerable crate.
        severity: Severity level (e.g., LOW, MEDIUM, HIGH, CRITICAL).
        title: Short title of the vulnerability.
        description: Detailed description of the vulnerability.
        url: URL with more information about the advisory.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "code": "advisory_id",
        "severity": "severity",
        "message": "message",
    }

    advisory_id: str = field(default="")
    package_name: str = field(default="")
    package_version: str = field(default="")
    severity: str = field(default="UNKNOWN")
    title: str = field(default="")
    description: str = field(default="")
    url: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the inherited fields."""
        # Set file to Cargo.lock since that's what cargo-audit scans
        if not self.file:
            self.file = "Cargo.lock"
        # Build the message from components
        self.message = self._get_message()

    def _get_message(self) -> str:
        """Get the formatted issue message.

        Returns:
            str: Formatted issue message.
        """
        return (
            f"[{self.advisory_id}] {self.package_name}@{self.package_version}: "
            f"{self.title}"
        )
