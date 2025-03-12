"""Terraform validation and formatting integration."""

import json
import re
import subprocess
from typing import Any

from lintro.tools import Tool, ToolConfig


class TerraformTool(Tool):
    """Terraform validation and formatting integration."""

    name = "terraform"
    description = "Infrastructure as Code validation and formatting for Terraform files"
    can_fix = True  # Terraform can both check (validate) and fix (fmt)

    # Configure tool with conflict information
    config = ToolConfig(
        priority=50,  # Medium priority
        conflicts_with=[],  # No direct conflicts
        file_patterns=["*.tf", "*.tfvars"],  # Terraform files
    )

    def __init__(self):
        """Initialize the tool with default options."""
        self.exclude_patterns = []
        self.include_venv = False
        self.recursive = True  # Default to recursive mode

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        recursive: bool | None = None,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            recursive: Whether to recursively check directories
        """
        super().set_options(exclude_patterns, include_venv)
        if recursive is not None:
            self.recursive = recursive

    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check Terraform files for validation and formatting issues.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        # First check formatting
        fmt_success, fmt_output = self._check_format(paths)
        
        # Then validate the Terraform files
        validate_success, validate_output = self._validate(paths)
        
        # Combine the outputs
        if fmt_success and validate_success:
            return True, "No Terraform issues found."
        
        combined_output = ""
        if not fmt_success:
            combined_output += "Formatting issues found:\n" + fmt_output + "\n\n"
        
        if not validate_success:
            combined_output += "Validation issues found:\n" + validate_output
            
        return False, combined_output.strip()

    def _check_format(self, paths: list[str]) -> tuple[bool, str]:
        """Check if Terraform files are properly formatted."""
        # Base command
        cmd = ["terraform", "fmt", "-check", "-diff"]
        
        # Add recursive flag if needed
        if self.recursive:
            cmd.append("-recursive")
            
        # Add paths
        cmd.extend(paths)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # If return code is 0, all files are properly formatted
            if result.returncode == 0:
                return True, "All Terraform files are properly formatted."
            
            # If return code is not 0, there are formatting issues
            return False, result.stdout or result.stderr or "Terraform formatting issues found."
                
        except subprocess.CalledProcessError as e:
            return False, f"Error running terraform fmt: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return False, "Terraform not found. Please install it from https://www.terraform.io/downloads.html"

    def _validate(self, paths: list[str]) -> tuple[bool, str]:
        """Validate Terraform files."""
        # For each path, run terraform validate
        all_outputs = []
        all_success = True
        
        for path in paths:
            # Base command
            cmd = ["terraform", "validate", "-json"]
            
            # Change to the directory containing the Terraform files
            try:
                # First initialize if needed
                init_cmd = ["terraform", "init", "-backend=false", "-input=false"]
                init_result = subprocess.run(
                    init_cmd, 
                    cwd=path, 
                    capture_output=True, 
                    text=True
                )
                
                # Run validate
                result = subprocess.run(
                    cmd, 
                    cwd=path, 
                    capture_output=True, 
                    text=True
                )
                
                # Parse the JSON output
                try:
                    output_json = json.loads(result.stdout)
                    
                    # Check if validation was successful
                    if output_json.get("valid", False):
                        all_outputs.append(f"Directory {path}: Valid")
                    else:
                        all_success = False
                        # Extract and format the error messages
                        diagnostics = output_json.get("diagnostics", [])
                        for diag in diagnostics:
                            severity = diag.get("severity", "error")
                            summary = diag.get("summary", "Unknown error")
                            detail = diag.get("detail", "")
                            
                            message = f"Directory {path}: [{severity.upper()}] {summary}"
                            if detail:
                                message += f"\nDetail: {detail}"
                                
                            all_outputs.append(message)
                except json.JSONDecodeError:
                    all_success = False
                    all_outputs.append(f"Directory {path}: Error parsing validation output")
                    all_outputs.append(result.stdout or result.stderr)
                    
            except subprocess.CalledProcessError as e:
                all_success = False
                all_outputs.append(f"Directory {path}: Error running terraform validate: {e.stderr or e.stdout}")
            except FileNotFoundError:
                all_success = False
                all_outputs.append("Terraform not found. Please install it from https://www.terraform.io/downloads.html")
                break
        
        if not all_outputs:
            return True, "No Terraform files found to validate."
            
        return all_success, "\n".join(all_outputs)

    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Format Terraform files.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: True if fixes were applied successfully, False otherwise
            - output: Output from the tool
        """
        # Base command
        cmd = ["terraform", "fmt"]
        
        # Add recursive flag if needed
        if self.recursive:
            cmd.append("-recursive")
            
        # Add paths
        cmd.extend(paths)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # If return code is 0, formatting was successful
            if result.returncode == 0:
                # Get the list of formatted files from the output
                formatted_files = result.stdout.strip().split("\n") if result.stdout else []
                num_files = len([f for f in formatted_files if f])
                
                if num_files > 0:
                    return True, f"Formatted {num_files} Terraform files:\n" + "\n".join(formatted_files)
                return True, "No Terraform files needed formatting."
            
            # If return code is not 0, there was an error
            return False, result.stderr or "Error formatting Terraform files."
                
        except subprocess.CalledProcessError as e:
            return False, f"Error running terraform fmt: {e.stderr or e.stdout}"
        except FileNotFoundError:
            return False, "Terraform not found. Please install it from https://www.terraform.io/downloads.html" 