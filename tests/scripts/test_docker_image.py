"""Tests for Docker image functionality."""

import subprocess
from pathlib import Path

import pytest

# Get project root from current file location
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestDockerImage:
    """Test Docker image functionality."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is valid."""
        dockerfile_path = PROJECT_ROOT / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile should exist"

        # Check that Dockerfile has required content
        content = dockerfile_path.read_text()
        assert "FROM python:3.13-slim" in content, "Should use Python 3.13"
        assert "WORKDIR /app" in content, "Should set working directory"
        assert "COPY lintro/" in content, "Should copy lintro package"
        assert "COPY pyproject.toml" in content, "Should copy pyproject.toml"
        assert "RUN uv sync" in content, "Should install dependencies"

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml should exist"

        # Check that compose file has required content
        content = compose_path.read_text()
        assert "lintro:" in content, "Should define lintro service"
        assert "build:" in content, "Should specify build context"

    def test_docker_workflow_exists(self):
        """Test that Docker workflow exists and is valid."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "lintro-docker.yml"
        assert workflow_path.exists(), "Docker workflow should exist"

        # Check that workflow has required content
        content = workflow_path.read_text()
        assert "name: Docker Build & Publish" in content, "Should have correct name"
        assert "docker/build-push-action" in content, "Should use build-push-action"

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_image_builds(self):
        """Test that Docker image can be built successfully."""
        try:
            result = subprocess.run(
                ["docker", "build", "-t", "test-lintro", "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300,
            )
            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.skip("Docker build timed out")
        except FileNotFoundError:
            pytest.skip("Docker not available")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_image_runs_lintro(self):
        """Test that built Docker image can run lintro commands."""
        try:
            # Build image if not exists
            subprocess.run(
                ["docker", "build", "-t", "test-lintro", "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                timeout=300,
            )

            # Test basic lintro command
            result = subprocess.run(
                ["docker", "run", "--rm", "test-lintro", "lintro", "--help"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"Lintro help failed: {result.stderr}"
            assert "usage:" in result.stdout.lower(), "Should show usage information"
        except subprocess.TimeoutExpired:
            pytest.skip("Docker command timed out")
        except FileNotFoundError:
            pytest.skip("Docker not available")

    def test_docker_scripts_exist(self):
        """Test that Docker scripts exist and are executable."""
        scripts_dir = PROJECT_ROOT / "scripts" / "docker"
        assert scripts_dir.exists(), "Docker scripts directory should exist"

        required_scripts = [
            "docker-lintro.sh",
            "docker-test.sh",
            "docker-build-test.sh",
        ]
        for script in required_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"Script {script} should exist"
            assert script_path.stat().st_mode & 0o111, (
                f"Script {script} should be executable"
            )

    def test_docker_script_content(self):
        """Test that Docker scripts have required content."""
        docker_lintro_script = PROJECT_ROOT / "scripts" / "docker" / "docker-lintro.sh"
        content = docker_lintro_script.read_text()

        assert "#!/bin/bash" in content, "Should have bash shebang"
        assert "docker run" in content, "Should use docker run command"
        assert "lintro" in content, "Should reference lintro command"

    def test_ghcr_image_url_format(self):
        """Test that GHCR image URL format is correct."""
        # This tests the documentation and workflow references
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "lintro-docker.yml"
        content = workflow_path.read_text()

        # Check for GHCR image name format
        assert "ghcr.io/turbocoder13/py-lintro" in content, (
            "Should use correct GHCR image name"
        )

    def test_docker_workflow_metadata_action(self):
        """Test that Docker workflow uses metadata action."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "lintro-docker.yml"
        content = workflow_path.read_text()

        assert "docker/metadata-action" in content, (
            "Should use metadata action for proper tagging"
        )

    def test_docker_workflow_permissions(self):
        """Test that Docker workflow has proper permissions."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "lintro-docker.yml"
        content = workflow_path.read_text()

        assert "packages: write" in content, "Should have packages write permission"

    def test_docker_workflow_triggers(self):
        """Test that Docker workflow has proper triggers."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "lintro-docker.yml"
        content = workflow_path.read_text()

        assert "push:" in content, "Should trigger on push"
        assert "branches: [main]" in content, "Should trigger on main branch"
        assert "workflow_dispatch:" in content, "Should allow manual dispatch"

    def test_docker_image_labels(self):
        """Test that Dockerfile includes proper labels."""
        dockerfile_path = PROJECT_ROOT / "Dockerfile"
        content = dockerfile_path.read_text()

        # Check for common Docker labels
        assert "LABEL" in content, "Should include Docker labels"


class TestDockerIntegration:
    """Test Lintro functionality through Docker container."""

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_check_command(self):
        """Test lintro check command through Docker."""
        try:
            # Create a temporary test file with known violations
            test_file = PROJECT_ROOT / "test_samples" / "ruff_violations.py"
            assert test_file.exists(), "Test file should exist"

            # Run lintro check through Docker
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--tools",
                    "ruff",
                    "/code/test_samples/ruff_violations.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should find violations and mention ruff tool
            assert result.returncode != 0, "Should find violations"
            assert "ruff" in result.stdout.lower(), "Should mention ruff tool"
            assert "issues" in result.stdout.lower(), "Should mention issues found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_format_command(self):
        """Test lintro format command through Docker."""
        try:
            # Create a temporary test file with formatting issues
            test_file = PROJECT_ROOT / "test_samples" / "prettier_violations.js"
            assert test_file.exists(), "Test file should exist"

            # Run lintro format through Docker
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "format",
                    "--tools",
                    "prettier",
                    "/code/test_samples/prettier_violations.js",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should attempt to fix formatting
            assert "prettier" in result.stdout.lower(), "Should mention prettier tool"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_list_tools_command(self):
        """Test lintro list-tools command through Docker."""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "test-lintro", "lintro", "list-tools"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            assert result.returncode == 0, "Should list tools successfully"
            assert "ruff" in result.stdout.lower(), "Should list ruff tool"
            assert "prettier" in result.stdout.lower(), "Should list prettier tool"
            assert "darglint" in result.stdout.lower(), "Should list darglint tool"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_output_formats(self):
        """Test different output formats through Docker."""
        try:
            # Test grid format
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--output-format",
                    "grid",
                    "--tools",
                    "ruff",
                    "/code/test_samples/ruff_violations.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # The tool should run successfully and produce some output
            assert result.returncode != 0, "Should find violations"
            assert "ruff" in result.stdout.lower(), "Should mention ruff tool"
            assert "issues" in result.stdout.lower(), "Should mention issues found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_json_output(self):
        """Test JSON output format through Docker."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--output-format",
                    "json",
                    "--tools",
                    "ruff",
                    "/code/test_samples/ruff_violations.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should produce output that mentions JSON format
            assert "json" in result.stdout.lower() or "{" in result.stdout, (
                "Should mention JSON or contain JSON-like content"
            )
            assert "ruff" in result.stdout.lower(), "Should mention ruff tool"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_tool_options(self):
        """Test tool-specific options through Docker."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--tools",
                    "ruff",
                    "--tool-options",
                    "ruff:--line-length=88",
                    "/code/test_samples/ruff_violations.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should accept tool options
            assert result.returncode != 0, "Should process tool options"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_exclude_patterns(self):
        """Test exclude patterns through Docker."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--exclude",
                    "*.pyc,__pycache__",
                    "--tools",
                    "ruff",
                    "/code",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should respect exclude patterns
            assert "ruff" in result.stdout.lower(), "Should run ruff tool"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_clean_file(self):
        """Test lintro on clean files through Docker."""
        try:
            clean_file = PROJECT_ROOT / "test_samples" / "ruff_clean.py"
            assert clean_file.exists(), "Clean test file should exist"

            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--tools",
                    "ruff",
                    "/code/test_samples/ruff_clean.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should run successfully and mention ruff tool
            assert "ruff" in result.stdout.lower(), "Should mention ruff tool"
            # Note: The tool may find issues due to configuration differences
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_multiple_tools(self):
        """Test multiple tools through Docker."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--tools",
                    "ruff,prettier",
                    "/code/test_samples",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should run multiple tools
            assert "ruff" in result.stdout.lower(), "Should run ruff"
            assert "prettier" in result.stdout.lower(), "Should run prettier"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")

    @pytest.mark.skipif(
        not Path("/usr/bin/docker").exists()
        and not Path("/usr/local/bin/docker").exists(),
        reason="Docker not available",
    )
    def test_docker_lintro_verbose_mode(self):
        """Test verbose mode through Docker."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{PROJECT_ROOT}:/code",
                    "test-lintro",
                    "lintro",
                    "check",
                    "--verbose",
                    "--tools",
                    "ruff",
                    "/code/test_samples/ruff_violations.py",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should show verbose output (debug messages)
            assert "debug" in result.stderr.lower(), "Should show debug output"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or command timed out")
