"""Svelte-check parser package."""

from lintro.parsers.svelte_check.svelte_check_issue import SvelteCheckIssue
from lintro.parsers.svelte_check.svelte_check_parser import parse_svelte_check_output

__all__ = ["SvelteCheckIssue", "parse_svelte_check_output"]
