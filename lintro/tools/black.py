"""Black code formatter integration."""

import subprocess
from typing import List, Tuple

from lintro.tools import Tool


class BlackTool(Tool):
    """Black code formatter integration."""

    name = "black"
    description = "The uncompromising Python code formatter"
    can_fix = True

    def check(self, paths: List[str]) -> Tuple[bool, str]:
        """Check if files would be reformatted by Black."""
        cmd = ["black", "--check"] + paths
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, "All files would be left unchanged."
        except subprocess.CalledProcessError as e:
            # Black returns exit code 1 when it would reformat files
            return False, e.stdout or e.stderr

    def fix(self, paths: List[str]) -> Tuple[bool, str]:
        """Format files with Black."""
        cmd = ["black"] + paths
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, result.stdout or "All files formatted successfully."
        except subprocess.CalledProcessError as e:
            return False, e.stderr or "Failed to format files with Black." 