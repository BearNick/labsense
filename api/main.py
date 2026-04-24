from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .schemas import (
    ErrorResponse,
    HealthResponse,
    InterpretLabDataRequest,
    InterpretLabDataResponse,
    UploadLabPdfResponse,
)
from .services import build_lab_value_payloads, execute_interpretation_flow, parse_lab_pdf


app = FastAPI(title="Labsense Minimal API", version="0.1.0")


def _safe_fraction(value: float | None) -> float:
    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if numeric != numeric:
        return 0.0
    return max(0.0, min(1.0, numeric))


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/upload-lab-pdf",
    response_model=UploadLabPdfResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_lab_pdf(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
) -> UploadLabPdfResponse:
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_file_type", "message": "Only PDF uploads are supported."},
            )

        parse_result = parse_lab_pdf(file, language=language)
        raw_values = parse_result.raw_values
        if not raw_values or not any(value is not None for value in raw_values.values()):
            raise HTTPException(
                status_code=422,
                detail={"error": "no_lab_values_extracted", "message": "No lab values were extracted from PDF."},
            )

        extracted_count = sum(1 for value in raw_values.values() if value is not None)
        return UploadLabPdfResponse(
            values=build_lab_value_payloads(raw_values, parse_result.marker_details),
            source=parse_result.source,
            selected_source=parse_result.selected_source,
            selection_reason=parse_result.selection_reason,
            initial_source=parse_result.initial_source,
            final_source=parse_result.final_source,
            fallback_used=parse_result.fallback_used,
            fallback_reason=parse_result.fallback_reason,
            confidence_score=parse_result.confidence_score,
            confidence_level=parse_result.confidence_level,
            confidence_reasons=parse_result.confidence_reasons,
            confidence_explanation=parse_result.confidence_explanation,
            reference_coverage=_safe_fraction(parse_result.reference_coverage),
            unit_coverage=_safe_fraction(parse_result.unit_coverage),
            structural_consistency=_safe_fraction(parse_result.structural_consistency),
            raw_values=raw_values,
            extracted_count=extracted_count,
            warnings=parse_result.warnings,
        )
    finally:
        await file.close()


@app.post(
    "/interpret-lab-data",
    response_model=InterpretLabDataResponse,
    responses={
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def interpret(request: InterpretLabDataRequest) -> InterpretLabDataResponse:
    payload = {
        "age": request.age,
        "gender": request.gender,
        "language": request.language,
        **request.raw_values,
    }
    result = execute_interpretation_flow(
        payload,
        request.parse_context.model_dump(exclude_none=True) if request.parse_context else None,
    )
    text = str(result["interpretation"])
    risk_status = result["risk_status"]
    plan = result["plan"]
    return InterpretLabDataResponse(
        interpretation=text,
        risk_status=risk_status,
        lifestyle_recommendations=result.get("lifestyle_recommendations"),
        meta=result.get("meta") or plan.build_meta(language=request.language, markers_supplied=len(request.raw_values)),
    )
