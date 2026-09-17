from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class KgMemoryPluginConfig(BaseModel):
    """Where remembered decisions come from, and how many reach a new agent."""

    model_config = {"frozen": True, "extra": "forbid"}

    source: Path | None = Field(
        default=None,
        description=(
            "Path to a JSON file of remembered facts. Left unset, the plugin stays "
            "inert and agents are created exactly as before."
        ),
    )
    max_facts: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Upper bound on facts prepended to an agent's first message.",
    )
    min_score: int = Field(
        default=1,
        ge=1,
        description="A fact needs at least this many query terms in it to be recalled.",
    )
