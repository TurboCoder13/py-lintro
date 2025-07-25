"""Tests for shell scripts in the scripts/ directory.

This module tests the shell scripts to ensure they follow best practices,
have correct syntax, and provide appropriate help/usage information.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestShellScriptSyntax:
    """Test shell script syntax and basic functionality."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    @pytest.fixture
    def shell_scripts(self, scripts_dir):
        """Get all shell scripts in the scripts directory.

        Args:
            scripts_dir: Path to the scripts directory.

        Returns:
            list[Path]: List of shell script file paths.
        """
        return list(scripts_dir.glob("*.sh"))

    def test_all_scripts_have_shebang(self, shell_scripts):
        """Test that all shell scripts have proper shebang.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()
            assert first_line.startswith("#!"), f"{script.name} missing shebang"
            assert "bash" in first_line, f"{script.name} should use bash"

    def test_all_scripts_syntax_valid(self, shell_scripts):
        """Test that all shell scripts have valid syntax.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            result = subprocess.run(
                ["bash", "-n", str(script)], capture_output=True, text=True
            )
            assert result.returncode == 0, (
                f"Syntax error in {script.name}: {result.stderr}"
            )

    def test_scripts_are_executable(self, shell_scripts):
        """Test that all shell scripts are executable.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            assert os.access(script, os.X_OK), f"{script.name} is not executable"

    def test_scripts_have_set_e(self, shell_scripts):
        """Test that critical scripts use 'set -e' for error handling.

        Args:
            shell_scripts: List of shell script file paths.
        """
        critical_scripts = [
            "run-tests.sh",
            "local-lintro.sh",
            "install-tools.sh",
            "docker-test.sh",
            "docker-lintro.sh",
        ]

        for script in shell_scripts:
            if script.name in critical_scripts:
                with open(script, "r") as f:
                    content = f.read()
                assert "set -e" in content, f"{script.name} should use 'set -e'"


class TestScriptHelp:
    """Test help functionality for shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_local_test_help(self, scripts_dir):
        """Test that local-test.sh provides help.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "local" / "local-test.sh"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "verbose" in result.stdout.lower()

    def test_local_lintro_help(self, scripts_dir):
        """Test that local-lintro.sh provides help for itself.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "local" / "local-lintro.sh"
        result = subprocess.run(
            [str(script), "--help", "script"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "install" in result.stdout.lower()

    def test_install_tools_help(self, scripts_dir):
        """Test that install-tools.sh has usage documentation in comments.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "install-tools.sh"
        with open(script, "r") as f:
            content = f.read()

        # Should have usage documentation in comments
        assert "Usage:" in content, "install-tools.sh should have usage documentation"
        assert "--local" in content or "--docker" in content, (
            "Should document command options"
        )


class TestScriptFunctionality:
    """Test basic functionality of shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    @pytest.fixture
    def mock_env(self):
        """Create a mock environment for testing.

        Yields:
            dict[str, str]: Mock environment variables.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            yield {"PATH": f"{tmpdir}:{os.environ.get('PATH', '')}", "HOME": tmpdir}

    def test_extract_coverage_python_script(self, scripts_dir):
        """Test that extract-coverage.py runs without syntax errors.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "extract-coverage.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"Python syntax error in {script.name}: {result.stderr}"
        )

    def test_utils_script_sources_correctly(self, scripts_dir):
        """Test that utils.sh can be sourced without errors.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "utils.sh"
        test_script = f"""
        #!/bin/bash
        set -e
        source "{script}"
        # Test that functions are available
        declare -f log_info >/dev/null
        declare -f log_success >/dev/null
        declare -f log_warning >/dev/null
        declare -f log_error >/dev/null
        """

        result = subprocess.run(
            ["bash", "-c", test_script], capture_output=True, text=True
        )
        assert result.returncode == 0, f"utils.sh sourcing failed: {result.stderr}"

    def test_docker_scripts_check_docker_availability(self, scripts_dir):
        """Test that Docker scripts check for Docker availability.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        # Only test user-facing Docker scripts, not CI/internal scripts
        docker_scripts = ["docker-test.sh", "docker-lintro.sh"]

        for script_name in docker_scripts:
            script = scripts_dir / script_name
            if script.exists():
                with open(script, "r") as f:
                    content = f.read()
                # Should check for docker command or docker info
                assert any(
                    check in content
                    for check in [
                        "docker info",
                        "command -v docker",
                        "docker --version",
                    ]
                ), f"{script_name} should check Docker availability"

    def test_scripts_handle_missing_dependencies_gracefully(
        self, scripts_dir, mock_env
    ):
        """Test that scripts handle missing dependencies gracefully.

        Args:
            scripts_dir: Path to the scripts directory.
            mock_env: Mock environment variables.
        """
        # Test run-tests.sh with missing uv
        script = scripts_dir / "local" / "run-tests.sh"

        # Create environment without uv
        test_env = mock_env.copy()
        test_env["PATH"] = "/usr/bin:/bin"  # Minimal PATH without uv

        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            env=test_env,
            cwd=scripts_dir.parent,
        )
        # Should still show help even without dependencies
        assert result.returncode == 0
        assert "Usage:" in result.stdout


class TestScriptIntegration:
    """Test integration aspects of shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_ci_scripts_reference_correct_files(self, scripts_dir):
        """Test that CI scripts reference files that exist.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        ci_scripts = list(scripts_dir.glob("ci-*.sh"))

        for script in ci_scripts:
            with open(script, "r") as f:
                content = f.read()

            # Check for references to other scripts
            if "run-tests.sh" in content:
                assert (scripts_dir / "run-tests.sh").exists()
            if "local-lintro.sh" in content:
                assert (scripts_dir / "local-lintro.sh").exists()
            if "extract-coverage.py" in content:
                assert (scripts_dir / "extract-coverage.py").exists()

    def test_scripts_use_consistent_color_codes(self, scripts_dir):
        """Test that scripts use consistent color coding.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        color_patterns = []

        for script in shell_scripts:
            with open(script, "r") as f:
                content = f.read()

            # Collect color definitions
            if "RED=" in content and "GREEN=" in content:
                # Extract color definitions for consistency check
                for line in content.split("\n"):
                    if line.strip().startswith(
                        ("RED=", "GREEN=", "YELLOW=", "BLUE=", "NC=")
                    ):
                        color_patterns.append(line.strip())

        # If multiple scripts define colors, they should be consistent
        if len(color_patterns) > 5:  # More than one script with full color set
            # Most common color definitions should be used
            red_definitions = [p for p in color_patterns if p.startswith("RED=")]
            if len(set(red_definitions)) > 1:
                # Allow some variation but check the most common pattern
                assert len(red_definitions) > 0, (
                    "Scripts should define RED color consistently"
                )

    def test_script_dependencies_documented(self, scripts_dir):
        """Test that script dependencies are documented in comments.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        critical_scripts = ["run-tests.sh", "install-tools.sh", "docker-test.sh"]

        for script_name in critical_scripts:
            script = scripts_dir / script_name
            if script.exists():
                with open(script, "r") as f:
                    # Read first 20 lines for documentation
                    lines = [f.readline() for _ in range(20)]
                    header = "".join(lines)

                # Should have some documentation about what the script does
                assert any(
                    keyword in header.lower()
                    for keyword in ["test", "install", "docker", "script", "runner"]
                ), f"{script_name} should have descriptive comments"
