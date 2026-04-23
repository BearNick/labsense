from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class LabValuePayload(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: str = "unknown"
    category: str = "general"


class UploadLabPdfResponse(BaseModel):
    values: list[LabValuePayload] = Field(default_factory=list)
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
    raw_values: dict[str, float | None]
    extracted_count: int
    warnings: list[str] = Field(default_factory=list)


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


class InterpretLabDataRequest(BaseModel):
    age: int | None = None
    gender: str | None = None
    language: str = "en"
    raw_values: dict[str, float | None] = Field(default_factory=dict)
    parse_context: ParseContextPayload | None = None


class RiskStatusResponse(BaseModel):
    label: str
    color_key: str
    explanation: str
    priority_notes: list[str] = Field(default_factory=list)


class InterpretLabDataResponse(BaseModel):
    interpretation: str
    risk_status: RiskStatusResponse | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: dict[str, Any] | None = None
