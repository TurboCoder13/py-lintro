"""Tool configuration model."""

from pydantic import BaseModel, ConfigDict


class LintroToolConfig(BaseModel):
    """Configuration for a single tool.

    In the tiered model, tools use their native configs by default.
    Lintro only controls whether tools run and optionally specifies
    an explicit config source path.

    Attributes:
        model_config: Pydantic model configuration (class-level).
        enabled: Whether the tool is enabled.
        config_source: Optional explicit path to native config file.
            If not set, tool uses its own config discovery.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    enabled: bool = True
    config_source: str | None = None
