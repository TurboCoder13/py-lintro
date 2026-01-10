"""Data models for pytest parsing.

This module contains dataclasses used to represent pytest output.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PytestSummary:
    """Summary statistics from pytest execution.

    Attributes:
        total: Total number of tests run.
        passed: Number of tests that passed.
        failed: Number of tests that failed.
        skipped: Number of tests that were skipped.
        error: Number of tests that had errors (setup/teardown failures).
        xfailed: Number of tests that were expected to fail and did fail.
        xpassed: Number of tests that were expected to fail but passed.
        duration: Total execution duration in seconds.
    """

    total: int = field(default=0)
    passed: int = field(default=0)
    failed: int = field(default=0)
    skipped: int = field(default=0)
    error: int = field(default=0)
    xfailed: int = field(default=0)
    xpassed: int = field(default=0)
    duration: float = field(default=0.0)
