from __future__ import annotations

from pydantic import BaseModel, Field


class VLMVerdict(BaseModel):
    """Structured output aligned with the architecture prompt (JSON contract)."""

    defect_found: bool = Field(description="True if assembly defect detected")
    reason: str = Field(description="Human-readable explanation for QA / MES")
    severity: str = Field(
        description="One of: none, low, medium, high, critical",
        pattern="^(none|low|medium|high|critical)$",
    )


class AnalyzeResponse(BaseModel):
    pack_id: str
    verdict: VLMVerdict
    latency_ms: float
