from app.schemas.analysis import InterpretationResponse
from app.services.clinical_consistency import build_pre_llm_validated_context
from parser.source_selection import normalize_raw_values
from app.services.interpretation_payload import normalize_interpretation_markers
from interpreter.analyze import generate_interpretation


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
        if key not in {"age", "gender", "language"} and isinstance(value, (int, float))
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


def _build_integrity_meta(
    *,
    normalized_payload: dict[str, object],
    validated_context: dict[str, object],
    gating_reasons: list[str],
) -> dict[str, object]:
    markers_supplied = _count_marker_values(normalized_payload)
    return {
        "language": str(normalized_payload.get("language", "en")),
        "markers_supplied": markers_supplied,
        "decision_kind": "full",
        "extraction_issue": False,
        "status_label": "",
        "status_explanation": "",
        "summary_overview": "",
        "confidence_text": "",
        "confidence_score": 100 if markers_supplied else 0,
        "confidence_level": "high" if markers_supplied else "low",
        "confidence_explanation": "Legacy baseline interpretation path is active.",
        "recommendation_title": "",
        "recommended_action": "",
        "hide_marker_counts": False,
        "hide_priority_notes": False,
        "gating_reasons": gating_reasons,
        "validation_issues": [],
        "validated_findings": validated_context,
        "payload_markers": list(validated_context.get("payload_markers", [])),
        "display_markers": list(validated_context.get("display_markers", [])),
        "coverage_only_markers": list(validated_context.get("coverage_only_markers", [])),
        "supported_reasoning_markers_present": list(validated_context.get("supported_reasoning_markers_present", [])),
    }


class InterpretationService:
    def interpret(
        self,
        payload: dict[str, object],
        parse_context: dict[str, object] | None = None,
    ) -> InterpretationResponse:
        normalized_payload = _normalize_interpretation_payload(payload)
        validated_context = build_pre_llm_validated_context(normalized_payload)
        gating_reasons = ["legacy_baseline_flow"]
        if _should_gate_coverage_only_interpretation(validated_context):
            gating_reasons = [*gating_reasons, "coverage_only_markers_present"]
            return InterpretationResponse(
                summary=_coverage_only_gate_message(str(normalized_payload.get("language", "en"))),
                risk_status=None,
                meta=_build_integrity_meta(
                    normalized_payload=normalized_payload,
                    validated_context=validated_context,
                    gating_reasons=gating_reasons,
                ),
            )
        interpretation_payload = {
            **normalized_payload,
            "__validated_findings__": validated_context,
        }
        summary = generate_interpretation(interpretation_payload)
        return InterpretationResponse(
            summary=summary,
            risk_status=None,
            meta=_build_integrity_meta(
                normalized_payload=normalized_payload,
                validated_context=validated_context,
                gating_reasons=gating_reasons,
            ),
        )
