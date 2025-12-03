"""Documentation testing suite for Lintro.

This module tests various aspects of the project documentation to ensure
consistency, accuracy, and completeness.
"""

import re
import subprocess
from pathlib import Path

import pytest


class TestScriptDocumentation:
    """Test script documentation and functionality."""

    def test_scripts_have_help(self) -> None:
        """Test that all executable scripts support --help flag."""
        script_dir = Path("scripts")
        failed_scripts = []

        for script_file in script_dir.rglob("*.sh"):
            # Skip utility files that are sourced by other scripts
            if script_file.name in ["utils.sh", "install.sh"]:
                continue

            try:
                result = subprocess.run(
                    [str(script_file), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    failed_scripts.append(
                        f"{script_file}: exit code {result.returncode}",
                    )
            except subprocess.TimeoutExpired:
                failed_scripts.append(f"{script_file}: timeout")
            except Exception as e:
                failed_scripts.append(f"{script_file}: {e}")

        if failed_scripts:
            pytest.fail("Scripts without --help support:\n" + "\n".join(failed_scripts))

    def test_script_paths_in_docs_exist(self) -> None:
        """Test that all script paths mentioned in documentation exist."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/contributing.md",
            "docs/docker.md",
            "scripts/README.md",
        ]

        missing_paths = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Find script references (patterns like ./scripts/...)
            script_patterns = [
                r"\./scripts/[^`\s]+",
                r"`[^`]*scripts/[^`]+`",
            ]

            for pattern in script_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the match
                    script_path = match.strip("`").strip()
                    if script_path.startswith("./scripts/"):
                        # Extract just the script path (before any arguments)
                        script_path_only = script_path.split()[
                            0
                        ]  # Take first part before space
                        if not Path(script_path_only[2:]).exists():  # Remove ./
                            missing_paths.append(f"{doc_file}: {script_path}")

        if missing_paths:
            pytest.fail("Missing script paths in docs:\n" + "\n".join(missing_paths))

    def test_scripts_readme_coverage(self) -> None:
        """Test that all scripts are documented in scripts/README.md."""
        scripts_readme = Path("scripts/README.md")
        if not scripts_readme.exists():
            pytest.skip("scripts/README.md not found")

        with open(scripts_readme, encoding="utf-8") as f:
            content = f.read()

        # Get all script files
        script_files = set()
        for script_file in Path("scripts").rglob("*.sh"):
            script_files.add(script_file.name)
        for script_file in Path("scripts").rglob("*.py"):
            if script_file.name != "__init__.py":  # Exclude __init__.py files
                script_files.add(script_file.name)

        # Find documented scripts
        documented_scripts = set()
        for script_name in script_files:
            if script_name in content:
                documented_scripts.add(script_name)

        missing_docs = script_files - documented_scripts
        if missing_docs:
            pytest.fail(
                "Scripts not documented in scripts/README.md:\n"
                + "\n".join(missing_docs),
            )


class TestCLIDocumentation:
    """Test CLI documentation and examples."""

    def test_cli_help_works(self) -> None:
        """Test that lintro --help works and shows expected commands."""
        try:
            result = subprocess.run(
                ["uv", "run", "python", "-m", "lintro", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, "lintro --help should succeed"
            assert "check" in result.stdout, "Should show check command"
            assert "format" in result.stdout, "Should show format command"
            assert "list-tools" in result.stdout, "Should show list-tools command"
        except subprocess.TimeoutExpired:
            pytest.fail("lintro --help timed out")

    def test_cli_examples_in_docs(self) -> None:
        """Test that CLI examples in documentation are valid."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/configuration.md",
        ]

        invalid_examples = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Find code blocks with lintro commands
            code_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
            for block in code_blocks:
                lines = block.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("lintro ") and not self._is_valid_lintro_command(
                        line,
                    ):
                        # Basic validation of command structure
                        invalid_examples.append(f"{doc_file}: {line}")

        if invalid_examples:
            pytest.fail("Invalid CLI examples in docs:\n" + "\n".join(invalid_examples))

    def _is_valid_lintro_command(self, command: str) -> bool:
        """Validate basic lintro command structure.

        Args:
            command (str): The command to validate.

        Returns:
            bool: True if the command is valid, False otherwise.
        """
        # Remove comments
        command = re.sub(r"#.*$", "", command).strip()
        if not command:
            return True

        # Check for valid commands
        valid_commands = ["check", "format", "list-tools", "test", "--help", "-h"]
        parts = command.split()

        if len(parts) < 2 or parts[0] != "lintro":
            return False

        return parts[1] in valid_commands


class TestDocumentationLinks:
    """Test documentation links and references."""

    def test_internal_doc_links(self) -> None:
        """Test that internal documentation links are valid."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/contributing.md",
            "docs/docker.md",
            "docs/github-integration.md",
            "scripts/README.md",
        ]

        broken_links = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Find markdown links
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
            for link_text, link_url in links:
                if link_url.startswith("docs/") or link_url.startswith("./docs/"):
                    # Internal documentation link
                    link_path = link_url
                    if link_path.startswith("./"):
                        link_path = link_path[2:]

                    if not Path(link_path).exists():
                        broken_links.append(f"{doc_file}: {link_text} -> {link_url}")

        if broken_links:
            pytest.fail("Broken internal links:\n" + "\n".join(broken_links))

    def test_workflow_file_references(self) -> None:
        """Test that workflow file references in docs match actual files."""
        workflows_dir = Path(".github/workflows")
        if not workflows_dir.exists():
            pytest.skip("No workflows directory found")

        actual_workflows = {f.name for f in workflows_dir.glob("*.yml")}

        doc_files = [
            "docs/github-integration.md",
            "README.md",
        ]

        invalid_refs = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Find workflow references
            workflow_refs = re.findall(r"\.github/workflows/([^)\s`*]+)", content)
            for ref in workflow_refs:
                if ref not in actual_workflows:
                    invalid_refs.append(f"{doc_file}: {ref}")

        if invalid_refs:
            pytest.fail("Invalid workflow references:\n" + "\n".join(invalid_refs))


class TestDocumentationCompleteness:
    """Test documentation completeness and coverage."""

    def test_all_docs_have_titles(self) -> None:
        """Test that all documentation files have proper titles."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/contributing.md",
            "docs/docker.md",
            "docs/github-integration.md",
            "docs/configuration.md",
            "scripts/README.md",
        ]

        files_without_titles = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                first_line = f.readline().strip()

            if not first_line.startswith("# "):
                files_without_titles.append(doc_file)

        if files_without_titles:
            pytest.fail("Docs without titles:\n" + "\n".join(files_without_titles))

    def test_scripts_directory_structure_documented(self) -> None:
        """Test that scripts directory structure is documented."""
        scripts_readme = Path("scripts/README.md")
        if not scripts_readme.exists():
            pytest.skip("scripts/README.md not found")

        with open(scripts_readme, encoding="utf-8") as f:
            content = f.read()

        # Check for directory structure section
        if "Directory Structure" not in content:
            pytest.fail("scripts/README.md should document directory structure")

        # Check for all subdirectories
        subdirs = ["ci/", "docker/", "local/", "utils/"]
        for subdir in subdirs:
            if subdir not in content:
                pytest.fail(f"scripts/README.md should mention {subdir} directory")


class TestDocumentationConsistency:
    """Test documentation consistency and formatting."""

    def test_command_consistency(self) -> None:
        """Test that CLI commands are consistently documented."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/configuration.md",
        ]

        inconsistent_commands = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Check for old command aliases that shouldn't be in docs
            old_aliases = ["lintro fmt", "lintro chk", "lintro ls"]
            for alias in old_aliases:
                if alias in content:
                    inconsistent_commands.append(
                        f"{doc_file}: uses old alias '{alias}'",
                    )

        if inconsistent_commands:
            pytest.fail(
                "Inconsistent command usage:\n" + "\n".join(inconsistent_commands),
            )

    def test_output_format_consistency(self) -> None:
        """Test that output format options are consistently documented."""
        doc_files = [
            "README.md",
            "docs/getting-started.md",
            "docs/configuration.md",
            "docs/docker.md",
        ]

        inconsistent_formats = []
        for doc_file in doc_files:
            if not Path(doc_file).exists():
                continue

            with open(doc_file, encoding="utf-8") as f:
                content = f.read()

            # Check for old --table-format references
            if "--table-format" in content:
                inconsistent_formats.append(
                    f"{doc_file}: uses old --table-format option",
                )

        if inconsistent_formats:
            pytest.fail(
                "Inconsistent output format options:\n"
                + "\n".join(inconsistent_formats),
            )


if __name__ == "__main__":
    pytest.main([__file__])
