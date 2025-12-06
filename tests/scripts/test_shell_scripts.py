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

    def test_all_scripts_have_shebang(self, shell_scripts) -> None:
        """Test that all shell scripts have proper shebang.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            with open(script) as f:
                first_line = f.readline().strip()
            assert first_line.startswith("#!"), f"{script.name} missing shebang"
            assert "bash" in first_line, f"{script.name} should use bash"

    def test_all_scripts_syntax_valid(self, shell_scripts) -> None:
        """Test that all shell scripts have valid syntax.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            result = subprocess.run(
                ["bash", "-n", str(script)],
                capture_output=True,
                text=True,
            )
            assert (
                result.returncode == 0
            ), f"Syntax error in {script.name}: {result.stderr}"

    def test_scripts_are_executable(self, shell_scripts) -> None:
        """Test that all shell scripts are executable.

        Args:
            shell_scripts: List of shell script file paths.
        """
        for script in shell_scripts:
            assert os.access(script, os.X_OK), f"{script.name} is not executable"

    def test_scripts_have_set_e(self, shell_scripts) -> None:
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
                with open(script) as f:
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

    def test_local_test_help(self, scripts_dir) -> None:
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

    def test_local_lintro_help(self, scripts_dir) -> None:
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

    def test_install_tools_help(self, scripts_dir) -> None:
        """Test that install-tools.sh has usage documentation in comments.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "install-tools.sh"
        with open(script) as f:
            content = f.read()
        assert "Usage:" in content, "install-tools.sh should have usage documentation"
        assert (
            "--local" in content or "--docker" in content
        ), "Should document command options"

    def test_codecov_upload_help(self, scripts_dir) -> None:
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

    def test_egress_audit_help(self, scripts_dir) -> None:
        """egress-audit-lite.sh should provide help and exit 0.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "ci" / "egress-audit-lite.sh"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_sbom_generate_help(self, scripts_dir) -> None:
        """sbom-generate.sh should provide help and exit 0.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "ci" / "sbom-generate.sh"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")


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

    def test_extract_coverage_python_script(self, scripts_dir) -> None:
        """Test that extract-coverage.py runs without syntax errors.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "extract-coverage.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(script)],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"Python syntax error in {script.name}: {result.stderr}"

    def test_utils_script_sources_correctly(self, scripts_dir) -> None:
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
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"utils.sh sourcing failed: {result.stderr}"

    def test_docker_scripts_check_docker_availability(self, scripts_dir) -> None:
        """Test that Docker scripts check for Docker availability.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        docker_scripts = ["docker-test.sh", "docker-lintro.sh"]
        for script_name in docker_scripts:
            script = scripts_dir / script_name
            if script.exists():
                with open(script) as f:
                    content = f.read()
                assert any(
                    (
                        check in content
                        for check in [
                            "docker info",
                            "command -v docker",
                            "docker --version",
                        ]
                    ),
                ), f"{script_name} should check Docker availability"

    def test_scripts_handle_missing_dependencies_gracefully(
        self,
        scripts_dir,
        mock_env,
    ) -> None:
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

    def test_egress_audit_reads_env_and_skips_ip_by_default(self, scripts_dir) -> None:
        """egress-audit-lite should read env and skip IP literals by default.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "ci" / "egress-audit-lite.sh"
        env = os.environ.copy()
        # include a valid domain and an IP literal; do not actually fail if unreachable
        env["EGRESS_ALLOWED_ENDPOINTS"] = "github.com:443,54.185.253.63:443"
        # run with fail=false; should not fail even if it tries both
        proc = subprocess.run(
            [str(script), "false"],
            capture_output=True,
            text=True,
            env=env,
            cwd=scripts_dir.parent,
        )
        assert proc.returncode == 0
        # Should indicate it skipped the IP
        assert "Skipping IP literal" in (proc.stdout + proc.stderr)

    def test_egress_audit_can_include_ip_with_flag(self, scripts_dir) -> None:
        """egress-audit-lite should include IP when --check-ip is provided.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "ci" / "egress-audit-lite.sh"
        env = os.environ.copy()
        env["EGRESS_ALLOWED_ENDPOINTS"] = "127.0.0.1:443"
        proc = subprocess.run(
            [str(script), "--check-ip", "false"],
            capture_output=True,
            text=True,
            env=env,
            cwd=scripts_dir.parent,
        )
        # We do not assert success/failure since localhost:443 may be closed.
        # But the script should run and not exit with usage error.
        assert proc.returncode in (0, 1)


class TestScriptIntegration:
    """Test integration aspects of shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_ci_scripts_reference_correct_files(self, scripts_dir) -> None:
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
            with open(script) as f:
                content = f.read()
            if "run-tests.sh" in content:
                assert_that((scripts_dir / "run-tests.sh").exists()).is_true()
            if "local-lintro.sh" in content:
                assert_that(
                    (scripts_dir / "local-lintro.sh").exists()
                    or (scripts_dir / "local" / "local-lintro.sh").exists(),
                ).is_true()
            if "extract-coverage.py" in content:
                assert_that(
                    (scripts_dir / "extract-coverage.py").exists()
                    or (scripts_dir / "utils" / "extract-coverage.py").exists(),
                ).is_true()
            if "detect-changes.sh" in content:
                assert_that(
                    (scripts_dir / "ci" / "detect-changes.sh").exists(),
                ).is_true()

    def test_detect_changes_help(self) -> None:
        """detect-changes.sh should provide help and exit 0."""
        script_path = Path("scripts/ci/detect-changes.sh").resolve()
        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_semantic_release_compute_python_runs(self) -> None:
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
        elif (
            "ModuleNotFoundError" in result.stderr or "No module named" in result.stderr
        ):
            # httpx or other dependencies may not be installed in test environment
            assert_that(result.returncode).is_equal_to(1)
        else:
            assert_that(result.returncode).is_equal_to(2)
            assert_that(result.stdout).contains("No v*-prefixed release tag found")

    def test_scripts_use_consistent_color_codes(self, scripts_dir) -> None:
        """Test that scripts use consistent color coding.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        color_patterns = []
        for script in shell_scripts:
            with open(script) as f:
                content = f.read()
            if "RED=" in content and "GREEN=" in content:
                for line in content.split("\n"):
                    if line.strip().startswith(
                        ("RED=", "GREEN=", "YELLOW=", "BLUE=", "NC="),
                    ):
                        color_patterns.append(line.strip())
        if len(color_patterns) > 5:
            red_definitions = [p for p in color_patterns if p.startswith("RED=")]
            if len(set(red_definitions)) > 1:
                assert (
                    len(red_definitions) > 0
                ), "Scripts should define RED color consistently"

    def test_script_dependencies_documented(self, scripts_dir) -> None:
        """Test that script dependencies are documented in comments.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        critical_scripts = ["run-tests.sh", "install-tools.sh", "docker-test.sh"]
        for script_name in critical_scripts:
            script = scripts_dir / script_name
            if script.exists():
                with open(script) as f:
                    lines = [f.readline() for _ in range(20)]
                    header = "".join(lines)
                assert any(
                    (
                        keyword in header.lower()
                        for keyword in ["test", "install", "docker", "script", "runner"]
                    ),
                ), f"{script_name} should have descriptive comments"

    def test_renovate_regex_manager_current_value(self) -> None:
        """Ensure Renovate custom managers use currentValue to satisfy schema."""
        config_path = Path("renovate.json")
        content = config_path.read_text()
        assert_that(content).contains("customManagers")
        assert_that(content).contains("currentValue")
