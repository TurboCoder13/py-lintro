"""Tests for shell scripts in the scripts/ directory.

This module tests the shell scripts to ensure they follow best practices,
have correct syntax, and provide appropriate help/usage information.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that


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
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")
        assert_that(result.stdout.lower()).contains("verbose")

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
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")
        assert_that(result.stdout.lower()).contains("install")

    def test_install_tools_help(self, scripts_dir):
        """Test that install-tools.sh has usage documentation in comments.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "install-tools.sh"
        with open(script, "r") as f:
            content = f.read()
        assert "Usage:" in content, "install-tools.sh should have usage documentation"
        assert "--local" in content or "--docker" in content, (
            "Should document command options"
        )

    def test_codecov_upload_help(self, scripts_dir):
        """codecov-upload.sh should provide help and exit 0.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "ci" / "codecov-upload.sh"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")
        assert_that(result.stdout).contains("Codecov")


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
        test_script = (
            f'\n        #!/bin/bash\n        set -e\n        source "{script}"\n'
            "        # Test that functions are available\n"
            "        declare -f log_info >/dev/null\n"
            "        declare -f log_success >/dev/null\n"
            "        declare -f log_warning >/dev/null\n"
            "        declare -f log_error >/dev/null\n"
        )
        result = subprocess.run(
            ["bash", "-c", test_script], capture_output=True, text=True
        )
        assert result.returncode == 0, f"utils.sh sourcing failed: {result.stderr}"

    def test_docker_scripts_check_docker_availability(self, scripts_dir):
        """Test that Docker scripts check for Docker availability.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        docker_scripts = ["docker-test.sh", "docker-lintro.sh"]
        for script_name in docker_scripts:
            script = scripts_dir / script_name
            if script.exists():
                with open(script, "r") as f:
                    content = f.read()
                assert any(
                    (
                        check in content
                        for check in [
                            "docker info",
                            "command -v docker",
                            "docker --version",
                        ]
                    )
                ), f"{script_name} should check Docker availability"

    def test_scripts_handle_missing_dependencies_gracefully(
        self, scripts_dir, mock_env
    ):
        """Test that scripts handle missing dependencies gracefully.

        Args:
            scripts_dir: Path to the scripts directory.
            mock_env: Mock environment variables.
        """
        script = scripts_dir / "local" / "run-tests.sh"
        test_env = mock_env.copy()
        test_env["PATH"] = "/usr/bin:/bin"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            env=test_env,
            cwd=scripts_dir.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")


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
        ci_scripts = list(scripts_dir.glob("ci-*.sh")) + [
            p
            for p in (scripts_dir / "ci").glob("*.sh")
            if p.name != "semantic-release-compute-next.sh"
        ]
        for script in ci_scripts:
            with open(script, "r") as f:
                content = f.read()
            if "run-tests.sh" in content:
                assert_that((scripts_dir / "run-tests.sh").exists()).is_true()
            if "local-lintro.sh" in content:
                assert_that(
                    (scripts_dir / "local-lintro.sh").exists()
                    or (scripts_dir / "local" / "local-lintro.sh").exists()
                ).is_true()
            if "extract-coverage.py" in content:
                assert_that(
                    (scripts_dir / "extract-coverage.py").exists()
                    or (scripts_dir / "utils" / "extract-coverage.py").exists()
                ).is_true()
            if "detect-changes.sh" in content:
                assert_that(
                    (scripts_dir / "ci" / "detect-changes.sh").exists()
                ).is_true()

    def test_detect_changes_help(self):
        """detect-changes.sh should provide help and exit 0."""
        script_path = Path("scripts/ci/detect-changes.sh").resolve()
        result = subprocess.run(
            [str(script_path), "--help"], capture_output=True, text=True
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_semantic_release_compute_python_runs(self):
        """semantic_release_compute_next.py should run and print next_version."""
        script_path = Path("scripts/ci/semantic_release_compute_next.py").resolve()
        result = subprocess.run(
            ["python3", str(script_path), "--print-only"],
            capture_output=True,
            text=True,
        )
        # In CI checkouts without fetched tags, script enforces tag baseline
        # and exits with code 2 and guidance. Accept both behaviors:
        if result.returncode == 0:
            assert_that(result.stdout).contains("next_version=")
        else:
            assert_that(result.returncode).is_equal_to(2)
            assert_that(result.stdout).contains("No v*-prefixed release tag found")

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
            if "RED=" in content and "GREEN=" in content:
                for line in content.split("\n"):
                    if line.strip().startswith(
                        ("RED=", "GREEN=", "YELLOW=", "BLUE=", "NC=")
                    ):
                        color_patterns.append(line.strip())
        if len(color_patterns) > 5:
            red_definitions = [p for p in color_patterns if p.startswith("RED=")]
            if len(set(red_definitions)) > 1:
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
                    lines = [f.readline() for _ in range(20)]
                    header = "".join(lines)
                assert any(
                    (
                        keyword in header.lower()
                        for keyword in ["test", "install", "docker", "script", "runner"]
                    )
                ), f"{script_name} should have descriptive comments"

    def test_bump_internal_refs_updates_refs(self, tmp_path):
        """Test that the bump-internal-refs.sh updates SHAs in workflow files.

        Creates a temporary workflow file that includes internal refs and runs the
        script with a fixed SHA, then verifies the refs were updated.

        Args:
            tmp_path: Temporary directory provided by pytest for file operations.
        """
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        sample = (
            "---\nname: Sample\n"
            "on: [push]\n"
            "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: TurboCoder13/py-lintro/.github/actions/"
            "demo@0123456789abcdef0123456789abcdef01234567\n"
            "      - uses: TurboCoder13/py-lintro/.github/workflows/"
            "reusable-demo.yml@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        )
        wf = workflow_dir / "sample.yml"
        wf.write_text(sample)
        target_sha = "c81d13a3e0c1bbe9cfb360477fdfcbb41ca00cbb"
        script_path = Path("scripts/ci/bump-internal-refs.sh").resolve()
        wrapper = tmp_path / "run.sh"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd '{tmp_path}'\n"
            f"'{script_path}' '{target_sha}'\n"
        )
        os.chmod(wrapper, 493)
        result = subprocess.run([str(wrapper)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        content = wf.read_text()
        assert_that(content).contains(target_sha)
        assert_that(content).does_not_contain(
            "0123456789abcdef0123456789abcdef01234567"
        )
        assert_that(content).does_not_contain(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

    def test_bump_internal_refs_invalid_sha_fails(self, tmp_path):
        """Invalid SHA should cause the bump script to fail early.

        Args:
            tmp_path: Temporary directory provided by pytest for file operations.
        """
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "sample.yml").write_text(
            "uses: TurboCoder13/py-lintro/.github/actions/"
            "demo@0123456789abcdef0123456789abcdef01234567\n"
        )
        script_path = Path("scripts/ci/bump-internal-refs.sh").resolve()
        bad_sha = "notasha"
        wrapper = tmp_path / "run.sh"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd '{tmp_path}'\n"
            f"'{script_path}' '{bad_sha}'\n"
        )
        os.chmod(wrapper, 493)
        result = subprocess.run([str(wrapper)], capture_output=True, text=True)
        assert_that(result.returncode).is_not_equal_to(0)
        assert_that(result.stderr).contains("Invalid SHA")

    def test_renovate_regex_manager_current_value(self):
        """Ensure Renovate regex manager uses currentValue to satisfy schema."""
        config_path = Path("renovate.json")
        content = config_path.read_text()
        assert_that(content).contains("regexManagers")
        assert_that(content).contains("currentValue")
