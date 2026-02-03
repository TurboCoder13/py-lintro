"""Environment information collection for diagnostics.

Collects comprehensive runtime environment information useful for debugging,
bug reports, and CI diagnostics.
"""

from lintro.utils.environment._protocol import Renderable
from lintro.utils.environment.ci_environment import CIEnvironment
from lintro.utils.environment.collectors import (
    collect_environment_vars,
    collect_full_environment,
    collect_go_info,
    collect_lintro_info,
    collect_node_info,
    collect_project_info,
    collect_python_info,
    collect_ruby_info,
    collect_rust_info,
    collect_system_info,
    detect_ci_environment,
)
from lintro.utils.environment.environment_report import EnvironmentReport
from lintro.utils.environment.go_info import GoInfo
from lintro.utils.environment.lintro_info import LintroInfo
from lintro.utils.environment.node_info import NodeInfo
from lintro.utils.environment.project_info import ProjectInfo
from lintro.utils.environment.python_info import PythonInfo
from lintro.utils.environment.renderer import render_environment_report, render_section
from lintro.utils.environment.ruby_info import RubyInfo
from lintro.utils.environment.rust_info import RustInfo
from lintro.utils.environment.system_info import SystemInfo

__all__ = [
    # Protocol
    "Renderable",
    # Dataclasses
    "CIEnvironment",
    "EnvironmentReport",
    "GoInfo",
    "LintroInfo",
    "NodeInfo",
    "ProjectInfo",
    "PythonInfo",
    "RubyInfo",
    "RustInfo",
    "SystemInfo",
    # Collection functions
    "collect_environment_vars",
    "collect_full_environment",
    "collect_go_info",
    "collect_lintro_info",
    "collect_node_info",
    "collect_project_info",
    "collect_python_info",
    "collect_ruby_info",
    "collect_rust_info",
    "collect_system_info",
    "detect_ci_environment",
    # Rendering functions
    "render_environment_report",
    "render_section",
]
