#!/usr/bin/env python3
"""Simple script to run lintro directly."""

import re
import subprocess
import sys
from lintro.tools.semgrep import SemgrepTool

def main():
    """Run lintro on the specified file."""
    if len(sys.argv) < 2:
        print("Usage: python run_lintro.py <file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Run semgrep directly
    cmd = ["semgrep", "scan", "--config=auto", file_path]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)}")
        print(f"Stderr length: {len(result.stderr)}")
        
        # Print the output
        print("\nStdout:")
        print(result.stdout)
        
        # Check if there are findings
        has_findings = "Code Findings" in result.stdout and not "0 Code Findings" in result.stdout
        
        print(f"\nHas findings: {has_findings}")
        
        # Extract the findings section
        findings_section = ""
        if has_findings:
            # Try a simpler approach: extract everything between the findings header and the summary header
            lines = result.stdout.splitlines()
            
            # Find the line with "Code Findings"
            findings_start = -1
            for i, line in enumerate(lines):
                if "Code Findings" in line:
                    findings_start = i
                    break
            
            if findings_start >= 0:
                # Skip the header box (3 lines) and extract the findings
                findings_lines = []
                for i in range(findings_start + 3, len(lines)):
                    if "Scan Summary" in lines[i]:
                        break
                    findings_lines.append(lines[i])
                
                findings_section = "\n".join(findings_lines)
                print("\nFindings section:")
                print(findings_section)
            else:
                print("\nNo findings section found")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running semgrep: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Semgrep not found. Please install it with 'pip install semgrep'.")
        sys.exit(1)
    
    # Create a semgrep tool
    print("\nRunning through SemgrepTool:")
    tool = SemgrepTool()
    
    # Update the check method to use our findings section
    original_check = tool.check
    
    def patched_check(paths):
        """Patched check method that returns our findings section."""
        if has_findings and findings_section:
            return False, findings_section
        else:
            return True, "No issues found."
    
    # Replace the check method
    tool.check = patched_check
    
    # Run the tool
    success, output = tool.check([file_path])
    
    # Print the results
    print(f"Success: {success}")
    print(f"Output: {output}")

if __name__ == "__main__":
    main() 