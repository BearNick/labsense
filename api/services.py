from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import HTTPException, UploadFile


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_LANGUAGES = {"en", "ru", "es"}

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from parser.source_selection import (  # noqa: E402
    ParserSelectionResult,
    normalize_raw_values,
)
from parser.config import MAX_PDF_PAGES  # noqa: E402
from parser.format_normalization import preprocess_extracted_data  # noqa: E402
from parser.postprocess import MarkerDetail, extract_legacy_text_with_details  # noqa: E402
from app.services.clinical_consistency import build_pre_llm_validated_context, enforce_final_consistency  # noqa: E402
from app.services.display_semantics import resolve_lab_value_display  # noqa: E402
from app.services.interpretation_payload import normalize_interpretation_markers  # noqa: E402
from app.services.interpretation_validation import DecisionPlan, ParseContext  # noqa: E402
from app.services.lifestyle_recommendations import generate_lifestyle_recommendations  # noqa: E402
from interpreter.risk import assess_risk_details, compute_risk_status  # noqa: E402

MIN_MARKERS_FOR_INTERPRETATION = 5
EXTRACTION_FAILURE_MESSAGE = "Не удалось корректно извлечь данные из отчёта"


def build_lab_value_payloads(
    raw_values: dict[str, float | None],
    marker_details: dict[str, MarkerDetail] | None = None,
) -> list[dict[str, object | None]]:
    marker_details = marker_details or {}
    payloads: list[dict[str, object | None]] = []

    for name, value in raw_values.items():
        detail = marker_details.get(name)
        unit, reference_range = resolve_lab_value_display(name, detail)
        payloads.append(
            {
                "name": name,
                "value": value,
                "unit": unit,
                "reference_range": reference_range,
                "status": "unknown",
                "category": "general",
            }
        )

    return payloads


def parse_lab_pdf(upload: UploadFile, language: str = "en") -> ParserSelectionResult:
    selected_language = language if language in SUPPORTED_LANGUAGES else "en"
    suffix = Path(upload.filename or "analysis.pdf").suffix or ".pdf"

    file_bytes = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_file",
                "message": "Uploaded PDF is empty.",
            },
        )

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": "PDF exceeds the 10 MB upload limit.",
            },
        )

    with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        text_result = extract_legacy_text_with_details(tmp.name, max_pages=MAX_PDF_PAGES)
        raw_values = normalize_raw_values(text_result.raw_values)
        _, marker_details, _ = preprocess_extracted_data(
            raw_values=text_result.raw_values,
            marker_details=text_result.marker_details,
            raw_text="",
            language_hint=selected_language,
        )
        extracted_count = sum(1 for value in raw_values.values() if value is not None)
        return ParserSelectionResult(
            raw_values=raw_values,
            marker_details=marker_details,
            source="pdfplumber",
            selected_source="text",
            selection_reason="legacy_text_baseline",
            initial_source="text",
            final_source="text",
            fallback_used=False,
            fallback_reason=None,
            confidence_score=100 if extracted_count else 0,
            confidence_level="high" if extracted_count else "low",
            confidence_reasons=["legacy_text_baseline"],
            confidence_explanation="Legacy baseline text extraction path is active.",
            reference_coverage=0.0,
            unit_coverage=0.0,
            structural_consistency=1.0 if extracted_count else 0.0,
            warnings=[],
        )


def plan_interpretation_flow(
    payload: dict[str, object],
    parse_context: ParseContext | dict[str, object] | None = None,
) -> DecisionPlan:
    return _build_legacy_plan(_normalize_interpretation_payload(payload))


def _normalize_interpretation_payload(payload: dict[str, object]) -> dict[str, object]:
    marker_values = {
        key: value
        for key, value in payload.items()
        if key not in {"age", "gender", "language"}
    }
    normalized_markers = normalize_interpretation_markers(normalize_raw_values(marker_values))
    return {
        "age": payload.get("age"),
        "gender": payload.get("gender"),
        "language": payload.get("language", "en"),
        **normalized_markers,
    }


def _count_marker_values(payload: dict[str, object]) -> int:
    return sum(
        1
        for key, value in payload.items()
        if key not in {"age", "gender", "language"} and isinstance(value, (int, float)) and not isinstance(value, bool)
    )


def _build_extraction_failure_plan() -> DecisionPlan:
    return DecisionPlan(
        kind="extraction_issue",
        confidence_score=0,
        confidence_level="low",
        confidence_explanation=EXTRACTION_FAILURE_MESSAGE,
        status_label="Extraction issue",
        status_explanation=EXTRACTION_FAILURE_MESSAGE,
        summary_overview=EXTRACTION_FAILURE_MESSAGE,
        confidence_text=EXTRACTION_FAILURE_MESSAGE,
        interpretation_message=EXTRACTION_FAILURE_MESSAGE,
        recommendation_title="Re-upload",
        recommended_action="",
        hide_marker_counts=False,
        hide_priority_notes=False,
        gating_reasons=["insufficient_extracted_markers"],
    )


def _build_legacy_plan(normalized_payload: dict[str, object]) -> DecisionPlan:
    markers_supplied = _count_marker_values(normalized_payload)
    return DecisionPlan(
        kind="full",
        confidence_score=100 if markers_supplied else 0,
        confidence_level="high" if markers_supplied else "low",
        confidence_explanation="Legacy baseline interpretation path is active.",
        status_label="",
        status_explanation="",
        summary_overview="",
        confidence_text="",
        interpretation_message=None,
        recommendation_title="",
        recommended_action="",
        hide_marker_counts=False,
        hide_priority_notes=False,
        gating_reasons=["legacy_baseline_flow"],
    )


def _coverage_only_gate_message(language: str) -> str:
    messages = {
        "en": "Extracted markers are available in the payload, but clinical interpretation is not enabled for this marker set yet.",
        "ru": "Извлечённые маркеры доступны в payload, но клиническая интерпретация для этого набора пока не включена.",
        "es": "Los marcadores extraídos están disponibles en el payload, pero la interpretación clínica para este conjunto aún no está habilitada.",
    }
    return messages.get(language, messages["en"])


def _should_gate_coverage_only_interpretation(validated_context: dict[str, object]) -> bool:
    coverage_only_markers = validated_context.get("coverage_only_markers", [])
    supported_reasoning_markers = validated_context.get("supported_reasoning_markers_present", [])
    return bool(coverage_only_markers) and not bool(supported_reasoning_markers)


def _build_marker_integrity_meta(
    *,
    normalized_payload: dict[str, object],
    validated_context: dict[str, object],
    plan: DecisionPlan,
) -> dict[str, object]:
    markers_supplied = _count_marker_values(normalized_payload)
    meta = plan.build_meta(
        language=str(normalized_payload.get("language", "en")),
        markers_supplied=markers_supplied,
    )
    meta["validated_findings"] = validated_context
    meta["payload_markers"] = list(validated_context.get("payload_markers", []))
    meta["display_markers"] = list(validated_context.get("display_markers", []))
    meta["coverage_only_markers"] = list(validated_context.get("coverage_only_markers", []))
    meta["supported_reasoning_markers_present"] = list(validated_context.get("supported_reasoning_markers_present", []))
    return meta


def interpret_lab_data(payload: dict[str, object]) -> str:
    normalized_payload = _normalize_interpretation_payload(payload)
    validated_context = build_pre_llm_validated_context(normalized_payload)
    if _should_gate_coverage_only_interpretation(validated_context):
        return _coverage_only_gate_message(str(normalized_payload.get("language", "en")))
    interpretation_payload = {
        **normalized_payload,
        "__validated_findings__": validated_context,
    }

    try:
        from interpreter.analyze import generate_interpretation
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "interpretation_unavailable",
                "message": f"Failed to initialize interpreter: {exc}",
            },
        ) from exc

    try:
        interpretation = generate_interpretation(interpretation_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "interpretation_failed",
                "message": str(exc),
            },
        ) from exc
    return interpretation


def build_risk_status(payload: dict[str, object]) -> dict[str, object] | None:
    normalized_payload = _normalize_interpretation_payload(payload)
    validated_context = build_pre_llm_validated_context(normalized_payload)
    if _should_gate_coverage_only_interpretation(validated_context):
        return None
    return compute_risk_status(
        normalized_payload,
        str(normalized_payload.get("language", "en")),
    )


def execute_interpretation_flow(
    payload: dict[str, object],
    parse_context: ParseContext | dict[str, object] | None = None,
) -> dict[str, object]:
    normalized_payload = _normalize_interpretation_payload(payload)
    validated_context = build_pre_llm_validated_context(normalized_payload)
    interpretation_payload = {
        **normalized_payload,
        "__validated_findings__": validated_context,
    }
    plan = _build_legacy_plan(normalized_payload)
    if _should_gate_coverage_only_interpretation(validated_context):
        gated_plan = replace(
            plan,
            gating_reasons=[*plan.gating_reasons, "coverage_only_markers_present"],
        )
        return {
            "interpretation": _coverage_only_gate_message(str(normalized_payload.get("language", "en"))),
            "risk_status": None,
            "lifestyle_recommendations": None,
            "plan": gated_plan,
            "meta": _build_marker_integrity_meta(
                normalized_payload=normalized_payload,
                validated_context=validated_context,
                plan=gated_plan,
            ),
            "validated_findings": validated_context,
            "consistency_issues": [],
        }

    try:
        from interpreter.analyze import generate_interpretation
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "interpretation_unavailable",
                "message": f"Failed to initialize interpreter: {exc}",
            },
        ) from exc

    try:
        interpretation = generate_interpretation(interpretation_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "interpretation_failed",
                "message": str(exc),
            },
        ) from exc

    try:
        lifestyle_recommendations = generate_lifestyle_recommendations(
            normalized_payload,
            language=str(normalized_payload.get("language", "en")),
            risk_status=None,
        )
    except Exception:
        lifestyle_recommendations = None

    language = str(normalized_payload.get("language", "en"))
    raw_risk_status = compute_risk_status(normalized_payload, language)
    abnormal_markers = assess_risk_details(normalized_payload, language).abnormal_markers
    final_interpretation, risk_status, validated_findings, consistency_issues = enforce_final_consistency(
        interpretation,
        payload=normalized_payload,
        abnormal_markers=abnormal_markers,
        risk_status=raw_risk_status,
        language=language,
    )
    meta = _build_marker_integrity_meta(
        normalized_payload=normalized_payload,
        validated_context=validated_context,
        plan=plan,
    )
    meta["validated_findings"] = validated_findings
    meta["consistency_issues"] = consistency_issues

    return {
        "interpretation": final_interpretation,
        "risk_status": risk_status,
        "lifestyle_recommendations": lifestyle_recommendations,
        "plan": plan,
        "meta": meta,
        "validated_findings": validated_findings,
        "consistency_issues": consistency_issues,
    }
