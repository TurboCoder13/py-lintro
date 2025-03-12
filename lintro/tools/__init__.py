"""Tool interfaces for Lintro."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class Tool(ABC):
    """Base class for all linting and formatting tools."""

    name: str
    description: str
    can_fix: bool

    @abstractmethod
    def check(self, paths: List[str]) -> Tuple[bool, str]:
        """
        Check the given paths for issues.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        pass

    @abstractmethod
    def fix(self, paths: List[str]) -> Tuple[bool, str]:
        """
        Fix issues in the given paths.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: True if fixes were applied successfully, False otherwise
            - output: Output from the tool
        """
        pass


# Import all tool implementations
from lintro.tools.black import BlackTool
from lintro.tools.isort import IsortTool
from lintro.tools.flake8 import Flake8Tool

# Register all available tools
AVAILABLE_TOOLS = {
    "black": BlackTool(),
    "isort": IsortTool(),
    "flake8": Flake8Tool(),
}

# Tools that can fix issues
FIX_TOOLS = {name: tool for name, tool in AVAILABLE_TOOLS.items() if tool.can_fix}

# Tools that can only check for issues
CHECK_TOOLS = AVAILABLE_TOOLS 