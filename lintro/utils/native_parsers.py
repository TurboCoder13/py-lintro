"""Native configuration parsers for various tools.

Handles loading and parsing of tool-specific configuration files (JSON, YAML, etc.).
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from lintro.enums.tool_name import ToolName

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Configuration file patterns for different tools
YAMLLINT_CONFIG_FILES = [".yamllint", ".yamllint.yaml", ".yamllint.yml"]
# Note: prettier.config.js is listed but not yet parsed (requires JS parser)
PRETTIER_CONFIG_FILES = [
    ".prettierrc",
    ".prettierrc.json",
]  # prettier.config.js not supported
BIOME_CONFIG_FILES = ["biome.json", "biome.jsonc"]
MARKDOWNLINT_CONFIG_FILES = [
    ".markdownlint.json",
    ".markdownlint.yaml",
    ".markdownlint.yml",
    ".markdownlint.jsonc",
]


def _load_json_config(config_path: Path) -> dict[str, Any]:
    """Load and parse a JSON configuration file.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        Parsed configuration as dict, or empty dict on error.
    """
    try:
        with config_path.open(encoding="utf-8") as f:
            loaded = json.load(f)
            return loaded if isinstance(loaded, dict) else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _strip_jsonc_comments(content: str) -> str:
    """Strip JSONC comments from content, preserving strings.

    This function safely removes // and /* */ comments from JSONC content
    while preserving comment-like sequences inside string values.

    Args:
        content: JSONC content as string

    Returns:
        Content with comments stripped

    Note:
        This is a simple implementation that handles most common cases.
        For complex JSONC with nested comments or edge cases, consider
        using a proper JSONC parser library (e.g., json5 or commentjson).
    """
    result: list[str] = []
    i = 0
    content_len = len(content)
    in_string = False
    escape_next = False
    in_block_comment = False

    while i < content_len:
        char = content[i]

        if escape_next:
            escape_next = False
            if not in_block_comment:
                result.append(char)
            i += 1
            continue

        if char == "\\" and in_string:
            escape_next = True
            if not in_block_comment:
                result.append(char)
            i += 1
            continue

        if char == '"' and not in_block_comment:
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string:
            result.append(char)
            i += 1
            continue

        # Check for block comment start /* ... */
        if i < content_len - 1 and char == "/" and content[i + 1] == "*":
            in_block_comment = True
            i += 2
            continue

        # Check for block comment end */ (when we see *)
        if (
            char == "*"
            and in_block_comment
            and i < content_len - 1
            and content[i + 1] == "/"
        ):
            in_block_comment = False
            i += 2  # Skip both * and /
            continue

        # Check for line comment //
        if (
            i < content_len - 1
            and char == "/"
            and content[i + 1] == "/"
            and not in_block_comment
        ):
            # Skip to end of line
            while i < content_len and content[i] != "\n":
                i += 1
            # Include the newline if present
            if i < content_len:
                result.append("\n")
                i += 1
            continue

        if not in_block_comment:
            result.append(char)

        i += 1

    if in_block_comment:
        logger.warning("Unclosed block comment in JSONC content")

    return "".join(result)


def _load_native_tool_config(tool_name: str) -> dict[str, Any]:
    """Load native configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Native configuration dictionary
    """
    from lintro.utils.config import load_pyproject

    # Convert string to ToolName enum for consistent comparisons
    try:
        tool_enum = ToolName(tool_name)
    except ValueError:
        # Unknown tool, return empty config
        return {}

    pyproject = load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}

    # Tools with pyproject.toml config
    if tool_enum in (ToolName.RUFF, ToolName.BLACK, ToolName.BANDIT):
        config_value = tool_section.get(tool_name, {})
        return config_value if isinstance(config_value, dict) else {}

    # Yamllint: check native config files (not pyproject.toml)
    if tool_enum == ToolName.YAMLLINT:
        for config_file in YAMLLINT_CONFIG_FILES:
            config_path = Path(config_file)
            if config_path.exists():
                if yaml is None:
                    logger.debug(
                        f"[UnifiedConfig] Found {config_file} but yaml not installed",
                    )
                    return {}
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                        return content if isinstance(content, dict) else {}
                except (yaml.YAMLError, OSError) as e:
                    logger.debug(f"[UnifiedConfig] Failed to parse {config_file}: {e}")
        return {}

    # Prettier: check multiple config file formats
    if tool_enum == ToolName.PRETTIER:
        for config_file in PRETTIER_CONFIG_FILES:
            config_path = Path(config_file)
            if config_path.exists():
                # Try parsing as JSON (works for both .json files and .prettierrc)
                loaded = _load_json_config(config_path)
                if loaded:
                    return loaded
        # Check package.json prettier field
        pkg_path = Path("package.json")
        if pkg_path.exists():
            try:
                with pkg_path.open(encoding="utf-8") as f:
                    pkg = json.load(f)
                    if isinstance(pkg, dict) and "prettier" in pkg:
                        prettier_cfg = pkg.get("prettier", {})
                        return prettier_cfg if isinstance(prettier_cfg, dict) else {}
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.debug(
                    "[UnifiedConfig] Failed to parse prettier config "
                    f"from package.json: {e}",
                )
        return {}

    # Biome: check config files
    if tool_enum == ToolName.BIOME:
        # Check Biome config files
        for config_file in BIOME_CONFIG_FILES:
            config_path = Path(config_file)
            if not config_path.exists():
                continue
            # Handle JSON files
            try:
                content = config_path.read_text(encoding="utf-8")
                if config_file.endswith(".jsonc"):
                    content = _strip_jsonc_comments(content)
                loaded = json.loads(content)
                return loaded if isinstance(loaded, dict) else {}
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.debug(
                    f"[UnifiedConfig] Failed to parse {config_file}: {e}",
                )
        return {}

    # Markdownlint: check config files
    if tool_enum == ToolName.MARKDOWNLINT:
        for config_file in MARKDOWNLINT_CONFIG_FILES:
            config_path = Path(config_file)
            if not config_path.exists():
                continue

            # Handle JSON/JSONC files
            if config_file.endswith((".json", ".jsonc")):
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = f.read()
                        # Strip JSONC comments safely (preserves strings)
                        content = _strip_jsonc_comments(content)
                        loaded = json.loads(content)
                        return loaded if isinstance(loaded, dict) else {}
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.debug(
                        f"[UnifiedConfig] Failed to parse {config_file}: {e}",
                    )

            # Handle YAML files
            elif config_file.endswith((".yaml", ".yml")):
                if yaml is None:
                    logger.warning(
                        "PyYAML not available; cannot parse .markdownlint.yaml",
                    )
                    continue
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                        # Handle multi-document YAML (coerce to dict)
                        if isinstance(content, list) and len(content) > 0:
                            logger.debug(
                                "[UnifiedConfig] Markdownlint YAML config "
                                "contains multiple documents, using first "
                                "document",
                            )
                            content = content[0]
                        if isinstance(content, dict):
                            return content
                except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
                    # Continue to next config file if this one fails to parse
                    logger.debug(
                        f"Failed to parse {config_path}: {type(e).__name__}: {e}",
                    )
        return {}

    return {}
