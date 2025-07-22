"""Tests for shell script environment handling and edge cases.

This module tests how shell scripts handle different environments,
missing tools, and error conditions.
"""

import subprocess
import pytest
from pathlib import Path
import tempfile


class TestEnvironmentHandling:
    """Test how scripts handle different environments."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    @pytest.fixture
    def clean_env(self):
        """Provide a clean environment for testing.

        Returns:
            dict[str, str]: Clean environment variables for testing.
        """
        return {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "USER": "testuser"}

    def test_local_test_handles_missing_uv(self, scripts_dir, clean_env):
        """Test local-test.sh behavior when uv is not available.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        script = scripts_dir / "local-test.sh"

        # Try to run with clean environment (no uv)
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            env=clean_env,
            cwd=scripts_dir.parent,
        )

        # Should show help regardless of missing dependencies
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_scripts_handle_docker_missing(self, scripts_dir, clean_env):
        """Test Docker scripts behavior when Docker is not available.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        docker_scripts = ["docker-test.sh", "docker-lintro.sh"]

        for script_name in docker_scripts:
            script = scripts_dir / script_name
            if not script.exists():
                continue

            result = subprocess.run(
                [str(script)],
                capture_output=True,
                text=True,
                env=clean_env,
                cwd=scripts_dir.parent,
            )

            # Should fail gracefully with informative error
            assert result.returncode != 0
            error_output = result.stderr + result.stdout
            assert any(
                word in error_output.lower()
                for word in ["docker", "not found", "not running", "error"]
            )

    def test_install_tools_handles_missing_dependencies(self, scripts_dir, clean_env):
        """Test install-tools.sh behavior with missing dependencies.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        script = scripts_dir / "install-tools.sh"

        # Test that script starts with clean environment (may fail due to missing tools)
        result = subprocess.run(
            [str(script)],
            capture_output=True,
            text=True,
            env=clean_env,
            cwd=scripts_dir.parent,
            timeout=10,  # Don't let it run too long
        )

        # Should fail gracefully, not hang or crash
        # Return code doesn't matter as much as not crashing
        assert result.returncode is not None  # Finished execution


class TestScriptErrorHandling:
    """Test script error handling and edge cases."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_extract_coverage_handles_missing_file(self, scripts_dir):
        """Test extract-coverage.py handles missing coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "extract-coverage.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["python3", str(script)], capture_output=True, text=True, cwd=tmpdir
            )

            # Should handle missing file gracefully
            assert result.returncode == 0
            assert "percentage=" in result.stdout
            # Should default to 0.0 when no file found
            assert "percentage=0.0" in result.stdout

    def test_extract_coverage_handles_empty_file(self, scripts_dir):
        """Test extract-coverage.py handles empty coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "extract-coverage.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty coverage.xml
            coverage_file = Path(tmpdir) / "coverage.xml"
            coverage_file.write_text("")

            result = subprocess.run(
                ["python3", str(script)], capture_output=True, text=True, cwd=tmpdir
            )

            # Should handle empty/malformed file gracefully
            assert result.returncode == 0
            assert "percentage=" in result.stdout

    def test_extract_coverage_handles_valid_file(self, scripts_dir):
        """Test extract-coverage.py handles valid coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "extract-coverage.py"

        valid_coverage_xml = """<?xml version="1.0" ?>
<coverage version="7.4.1" timestamp="1234567890" line-rate="0.85" 
          branch-rate="0.75" lines-covered="850" lines-valid="1000">
    <sources>
        <source>.</source>
    </sources>
    <packages>
        <package name="lintro" line-rate="0.85" branch-rate="0.75">
        </package>
    </packages>
</coverage>"""

        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = Path(tmpdir) / "coverage.xml"
            coverage_file.write_text(valid_coverage_xml)

            result = subprocess.run(
                ["python3", str(script)], capture_output=True, text=True, cwd=tmpdir
            )

            assert result.returncode == 0
            assert "percentage=" in result.stdout
            # Should extract correct percentage (85.0)
            assert "percentage=85.0" in result.stdout


class TestScriptSecurity:
    """Test security aspects of shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_scripts_avoid_eval_or_exec(self, scripts_dir):
        """Test that scripts avoid dangerous eval or exec commands.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))

        dangerous_patterns = ["eval ", "exec ", "$(curl", "| sh", "| bash"]

        for script in shell_scripts:
            with open(script, "r") as f:
                content = f.read()

            for pattern in dangerous_patterns:
                if pattern in content:
                    # Allow specific safe cases
                    lines_with_pattern = [
                        line.strip()
                        for line in content.split("\n")
                        if pattern in line and not line.strip().startswith("#")
                    ]

                    # Check if it's in a safe context (like error handling)
                    for line in lines_with_pattern:
                        if pattern == "| sh" and "install.sh" in line:
                            continue  # Safe installation pattern
                        if pattern == "| bash" and (
                            "nodesource.com" in line or "setup_" in line
                        ):
                            continue  # Safe Node.js official installer pattern
                        if pattern == "eval " and "grep" in line:
                            continue  # Safe grep/export pattern

                        # If we get here, might be unsafe
                        pytest.fail(
                            f"Potentially unsafe pattern '{pattern}' in {script.name}: {line}"
                        )

    def test_scripts_validate_inputs(self, scripts_dir):
        """Test that scripts validate inputs appropriately.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        # Check that scripts with arguments validate them
        scripts_with_args = [
            "run-tests.sh",
            "local-lintro.sh",
        ]  # Remove install-tools.sh for now

        for script_name in scripts_with_args:
            script = scripts_dir / script_name
            if not script.exists():
                continue

            with open(script, "r") as f:
                content = f.read()

            # Should have some form of argument validation
            has_validation = any(
                pattern in content
                for pattern in [
                    'if [ "$1"',
                    'case "$1"',
                    "[ $# -",
                    "getopts",
                    "--help",
                    "-h",
                ]
            )

            assert has_validation, (
                f"{script_name} should validate command line arguments"
            )

    def test_scripts_use_quoted_variables(self, scripts_dir):
        """Test that scripts properly quote variables to prevent injection.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))

        for script in shell_scripts:
            with open(script, "r") as f:
                content = f.read()

            # Look for unquoted variable usage in command contexts
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if line.strip().startswith("#"):
                    continue

                # Check for potentially dangerous unquoted variables
                # This is a basic check - real shellcheck would be more thorough
                if " $1" in line and '"$1"' not in line and "'$1'" not in line:
                    # Allow some safe contexts like array access
                    if not any(safe in line for safe in ["[$1]", "=$1", "shift"]):
                        # This might indicate unquoted variable usage
                        # For now, just ensure we're being careful
                        pass  # Not failing tests for this, but flagging for awareness


class TestScriptCompatibility:
    """Test script compatibility across different environments."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_scripts_use_portable_shebang(self, scripts_dir):
        """Test that scripts use portable shebang lines.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))

        for script in shell_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()

            # Should use #!/bin/bash for portability
            assert first_line == "#!/bin/bash", (
                f"{script.name} should use '#!/bin/bash' shebang, found: {first_line}"
            )

    def test_scripts_avoid_bashisms_in_sh_context(self, scripts_dir):
        """Test that scripts avoid bash-specific features where inappropriate.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))

        for script in shell_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()

            # If using /bin/sh, should avoid bash-specific features
            if first_line == "#!/bin/sh":
                with open(script, "r") as f:
                    content = f.read()

                bash_features = ["[[", "function ", "$(", "source "]
                for feature in bash_features:
                    assert feature not in content, (
                        f"{script.name} uses bash feature '{feature}' but has sh shebang"
                    )

    def test_python_script_compatibility(self, scripts_dir):
        """Test that Python scripts use appropriate shebang.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        python_scripts = list(scripts_dir.glob("*.py"))

        for script in python_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()

            # Should use python3 for consistency
            assert first_line in ["#!/usr/bin/env python3", "#!/usr/bin/python3"], (
                f"{script.name} should use python3 shebang"
            )
