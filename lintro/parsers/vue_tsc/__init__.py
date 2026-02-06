"""Vue-tsc parser package."""

from lintro.parsers.vue_tsc.vue_tsc_issue import VueTscIssue
from lintro.parsers.vue_tsc.vue_tsc_parser import (
    categorize_vue_tsc_issues,
    extract_missing_modules,
    parse_vue_tsc_output,
)

__all__ = [
    "VueTscIssue",
    "parse_vue_tsc_output",
    "categorize_vue_tsc_issues",
    "extract_missing_modules",
]
