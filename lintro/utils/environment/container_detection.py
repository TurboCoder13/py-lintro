"""Container environment detection for Docker, Podman, and similar runtimes."""

from __future__ import annotations

import functools
import os
from pathlib import Path


@functools.lru_cache(maxsize=1)
def is_container_environment() -> bool:
    """Detect if running inside a Docker/container environment.

    Checks multiple indicators:
    1. ``/.dockerenv`` file exists (Docker)
    2. ``/run/.containerenv`` exists (Podman)
    3. ``CONTAINER`` environment variable is set
    4. ``/proc/1/cgroup`` contains docker/lxc/containerd/kubepods references

    Returns:
        True if a container environment is detected.
    """
    # Docker marker file
    if Path("/.dockerenv").exists():
        return True

    # Podman marker file
    if Path("/run/.containerenv").exists():
        return True

    # Environment variable (set by some container runtimes)
    if os.environ.get("CONTAINER"):
        return True

    # Check cgroup for container runtime references (Linux only)
    try:
        cgroup_path = Path("/proc/1/cgroup")
        if cgroup_path.exists():
            content = cgroup_path.read_text(encoding="utf-8", errors="ignore")
            for indicator in ("docker", "lxc", "containerd", "kubepods"):
                if indicator in content.lower():
                    return True
    except OSError:
        pass

    return False
