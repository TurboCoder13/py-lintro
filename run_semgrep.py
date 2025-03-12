#!/usr/bin/env python3
"""Simple script to run semgrep directly."""

import subprocess
import sys

def main():
    """Run semgrep on the specified file."""
    if len(sys.argv) < 2:
        print("Usage: python run_semgrep.py <file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Run semgrep
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
        
        print("\nStderr:")
        print(result.stderr)
        
        # Check if there are findings
        has_findings = "Code Findings" in result.stdout and not "0 Code Findings" in result.stdout
        
        print(f"\nHas findings: {has_findings}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running semgrep: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Semgrep not found. Please install it with 'pip install semgrep'.")
        sys.exit(1)

if __name__ == "__main__":
    main() 