from datetime import datetime

from pydantic import BaseModel, Field


class LabValuePayload(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: str = "unknown"
    category: str = "general"


class ParseResponse(BaseModel):
    analysis_id: str
    values: list[LabValuePayload]
    raw_values: dict[str, float | None]
    source: str
    selected_source: str | None = None
    selection_reason: str | None = None
    initial_source: str | None = None
    final_source: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    confidence_score: int | None = None
    confidence_level: str | None = None
    confidence_reasons: list[str] = Field(default_factory=list)
    confidence_explanation: str | None = None
    reference_coverage: float | None = None
    unit_coverage: float | None = None
    structural_consistency: float | None = None


class ParseContextPayload(BaseModel):
    extracted_count: int | None = None
    confidence_score: int | None = None
    confidence_level: str | None = None
    confidence_explanation: str | None = None
    reference_coverage: float | None = None
    unit_coverage: float | None = None
    structural_consistency: float | None = None
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    source: str | None = None


class InterpretationRequest(BaseModel):
    analysis_id: str | None = None
    age: int | None = None
    gender: str | None = None
    language: str = "en"
    raw_values: dict[str, float | None] = Field(default_factory=dict)
    parse_context: ParseContextPayload | None = None


class RiskStatusPayload(BaseModel):
    label: str
    color_key: str
    explanation: str
    priority_notes: list[str] = Field(default_factory=list)


class InterpretationResponse(BaseModel):
    summary: str
    risk_status: RiskStatusPayload | None = None
    lifestyle_recommendations: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    follow_up_tests: list[str] = Field(default_factory=list)
    meta: dict[str, object] = Field(default_factory=dict)


class AnalysisRecord(BaseModel):
    id: str
    created_at: datetime
    status: str
    values: list[LabValuePayload] = Field(default_factory=list)
    interpretation: str | None = None
