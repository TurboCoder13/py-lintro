"""isort import sorter integration."""

import subprocess
from typing import List, Tuple

from lintro.tools import Tool


class IsortTool(Tool):
    """isort import sorter integration."""

    name = "isort"
    description = "Sort Python imports"
    can_fix = True

    def check(self, paths: List[str]) -> Tuple[bool, str]:
        """Check if imports would be sorted by isort."""
        cmd = ["isort", "--check-only"] + paths
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "All imports are correctly sorted."
        except subprocess.CalledProcessError as e:
            # isort returns exit code 1 when it would sort imports
            return False, e.stdout or e.stderr

    def fix(self, paths: List[str]) -> Tuple[bool, str]:
        """Sort imports with isort."""
        cmd = ["isort"] + paths
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, result.stdout or "All imports sorted successfully."
        except subprocess.CalledProcessError as e:
            return False, e.stderr or "Failed to sort imports with isort." 