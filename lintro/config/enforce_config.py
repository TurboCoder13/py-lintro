"""Enforce configuration model."""

from pydantic import BaseModel, ConfigDict, Field


class EnforceConfig(BaseModel):
    """Cross-cutting settings enforced across all tools via CLI flags.

    These settings override native tool configs to ensure consistency
    across different tools for shared concerns.

    Attributes:
        model_config: Pydantic model configuration.
        line_length: Line length limit injected via CLI flags.
            Injected as: --line-length (ruff, black)
        target_python: Python version target (e.g., "py313").
            Injected as: --target-version (ruff, black)
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    line_length: int | None = Field(default=None, ge=1, le=500)
    target_python: str | None = None
