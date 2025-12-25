"""Tool configuration information utilities.

This module is kept for backward compatibility.
The main function get_tool_config_summary() has been moved to unified_config.py
to avoid circular imports.
"""

from __future__ import annotations

# Re-export for backward compatibility
from lintro.utils.unified_config import get_tool_config_summary

__all__ = ["get_tool_config_summary"]
