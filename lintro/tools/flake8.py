"""Flake8 linter integration."""

import subprocess
from typing import List, Tuple

from lintro.tools import Tool


class Flake8Tool(Tool):
    """Flake8 linter integration."""

    name = "flake8"
    description = "Python style guide enforcement"
    can_fix = False  # Flake8 can only check, not fix

    def check(self, paths: List[str]) -> Tuple[bool, str]:
        """Check files with Flake8."""
        cmd = ["flake8"] + paths
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "No style issues found."
        except subprocess.CalledProcessError as e:
            # Flake8 returns exit code 1 when it finds style issues
            return False, e.stdout or e.stderr

    def fix(self, paths: List[str]) -> Tuple[bool, str]:
        """Flake8 cannot fix issues, only report them."""
        return False, "Flake8 cannot automatically fix issues. Run 'lintro check' to see issues." 