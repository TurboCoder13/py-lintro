"""Taplo parser module.

This module provides parsing functionality for taplo TOML linter/formatter output.
"""

from __future__ import annotations

from lintro.parsers.taplo.taplo_issue import TaploIssue
from lintro.parsers.taplo.taplo_parser import parse_taplo_output

__all__ = ["TaploIssue", "parse_taplo_output"]
