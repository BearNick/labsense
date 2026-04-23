from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.schemas.analysis import (
    AnalysisRecord,
    InterpretationRequest,
    InterpretationResponse,
    ParseResponse
)
from app.services.interpretation_service import InterpretationService
from app.services.parser_service import ParserService
from app.services.storage import LocalAnalysisStore

router = APIRouter(prefix="/analyses", tags=["analyses"])


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


def get_store(settings: Settings = Depends(get_settings)) -> LocalAnalysisStore:
    return LocalAnalysisStore(settings.local_data_dir / "analyses")


@router.post("/parse", response_model=ParseResponse)
async def parse_analysis(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    store: LocalAnalysisStore = Depends(get_store)
) -> ParseResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    parser = ParserService()
    parse_result = parser.parse_upload(file, language=language)
    raw_values = parse_result.raw_values
    if not raw_values:
        raise HTTPException(status_code=422, detail="No lab values were extracted.")

    record = store.create(raw_values, marker_details=parse_result.marker_details)
    return ParseResponse(
        analysis_id=record.id,
        values=record.values,
        raw_values=raw_values,
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
    )


@router.post("/interpret", response_model=InterpretationResponse)
async def interpret_analysis(
    payload: InterpretationRequest,
    store: LocalAnalysisStore = Depends(get_store)
) -> InterpretationResponse:
    raw_values = payload.raw_values
    if payload.analysis_id:
        stored = store.get(payload.analysis_id)
        raw_values = {
            value.name: value.value
            for value in stored.values
        }

    result = InterpretationService().interpret(
        {
            "age": payload.age,
            "gender": payload.gender,
            "language": payload.language,
            **raw_values
        },
        payload.parse_context.model_dump(exclude_none=True) if payload.parse_context else None,
    )

    if payload.analysis_id:
        store.save_interpretation(payload.analysis_id, result.summary)

    return result


@router.get("/{analysis_id}", response_model=AnalysisRecord)
async def get_analysis(
    analysis_id: str,
    store: LocalAnalysisStore = Depends(get_store)
) -> AnalysisRecord:
    return store.get(analysis_id)
