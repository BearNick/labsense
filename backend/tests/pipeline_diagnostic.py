from __future__ import annotations

import importlib
import json
import os
import sys
import types
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path("/opt/labsense")
BACKEND_ROOT = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.clinical_consistency import (
    build_validated_findings,
    enforce_final_consistency,
    find_final_consistency_issues,
)
from app.services.interpretation_payload import normalize_interpretation_markers
from app.services.interpretation_validation import DecisionPlan, plan_decision
from interpreter.risk import assess_risk_details, compute_risk_status
from parser.postprocess import merge_canonical_markers
from parser.source_selection import normalize_raw_values


@dataclass(frozen=True)
class DecisionExpectation:
    kind: str
    risk_label: str
    risk_color_key: str
    priority_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FinalExpectation:
    prompt_must_contain: tuple[str, ...] = ()
    prompt_must_not_contain: tuple[str, ...] = ()
    interpretation_must_contain: tuple[str, ...] = ()
    interpretation_must_not_contain: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiagnosticFixture:
    name: str
    extracted_raw_values: dict[str, object]
    expected_merged_values: dict[str, float | None]
    expected_payload: dict[str, float | str | None]
    expected_abnormal_markers: tuple[str, ...]
    expected_decision: DecisionExpectation
    expected_final: FinalExpectation
    language: str = "ru"
    age: int = 30
    gender: str = "female"
    model_interpretation: str | None = None
    inconsistent_model_interpretation: str | None = None


@dataclass(frozen=True)
class PipelineTrace:
    fixture_name: str
    raw_values: dict[str, object]
    merged_values: dict[str, float | None]
    payload: dict[str, object]
    abnormal_markers: list[str]
    deviations: list[dict[str, object]]
    decision: dict[str, object]
    risk_status: dict[str, object] | None
    prompt: str
    final_response: dict[str, object]

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


def build_diagnostic_fixtures() -> list[DiagnosticFixture]:
    return [
        DiagnosticFixture(
            name="cbc_normal_panel",
            extracted_raw_values={
                "HGB": 148.10,
                "RBC": 4.98,
                "HCT": 41.60,
                "WBC": 4.19,
                "PLT": 298.0,
                "LYM %": 32.70,
            },
            expected_merged_values={
                "HCT": 41.60,
                "HGB": 148.10,
                "LYM %": 32.70,
                "PLT": 298.0,
                "RBC": 4.98,
                "WBC": 4.19,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "ru",
                "Гемоглобин": 148.10,
                "Гематокрит": 41.60,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Тромбоциты": 298.0,
                "Эритроциты": 4.98,
            },
            expected_abnormal_markers=(),
            expected_decision=DecisionExpectation(
                kind="full",
                risk_label="Норма",
                risk_color_key="green",
            ),
            expected_final=FinalExpectation(
                prompt_must_not_contain=("Лимфоциты % ниже референса.",),
                interpretation_must_not_contain=("lymphopen", "лимфопени", "значимое отклонение"),
            ),
            inconsistent_model_interpretation=(
                "Overall status:\n"
                "Significant deviation\n\n"
                "Key observations:\n"
                "Main condition: Lymphopenia.\n"
                "Short explanation: Lymphocytes % are below reference.\n\n"
                "What this means:\n"
                "This suggests a significant white-cell abnormality.\n\n"
                "Next steps:\n"
                "Medical evaluation recommended.\n\n"
                "Final conclusion:\n"
                "Significant abnormality.\n"
            ),
        ),
        DiagnosticFixture(
            name="cbc_distinct_special_markers",
            extracted_raw_values={
                "RBC": 4.98,
                "NRBC": 0.0,
                "LYM %": 32.70,
                "LYM abs": 2.01,
                "RE-LYMP abs": 0.08,
                "RE-LYMP %": 1.10,
                "AS-LYMP abs": 0.01,
                "AS-LYMP %": 0.40,
            },
            expected_merged_values={
                "AS-LYMP %": 0.40,
                "AS-LYMP abs": 0.01,
                "LYM %": 32.70,
                "LYM abs": 2.01,
                "NRBC": 0.0,
                "RBC": 4.98,
                "RE-LYMP %": 1.10,
                "RE-LYMP abs": 0.08,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "ru",
                "AS-LYMP %": 0.40,
                "AS-LYMP abs": 0.01,
                "RE-LYMP %": 1.10,
                "RE-LYMP abs": 0.08,
                "NRBC": 0.0,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Эритроциты": 4.98,
            },
            expected_abnormal_markers=(),
            expected_decision=DecisionExpectation(
                kind="full",
                risk_label="Норма",
                risk_color_key="green",
            ),
            expected_final=FinalExpectation(
                prompt_must_not_contain=("Лимфоциты % ниже референса.",),
                interpretation_must_not_contain=("lymphopen", "лимфопени"),
            ),
        ),
        DiagnosticFixture(
            name="cbc_vitamin_d_zinc",
            extracted_raw_values={
                "HGB": 148.10,
                "RBC": 4.98,
                "HCT": 41.60,
                "WBC": 4.19,
                "PLT": 298.0,
                "LYM %": 32.70,
                "Vitamin D (25-OH)": 29.0,
                "Zinc": 8.5,
            },
            expected_merged_values={
                "HCT": 41.60,
                "HGB": 148.10,
                "LYM %": 32.70,
                "PLT": 298.0,
                "RBC": 4.98,
                "Vitamin D (25-OH)": 29.0,
                "WBC": 4.19,
                "Zinc": 8.5,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "ru",
                "Витамин D (25-OH)": 29.0,
                "Гемоглобин": 148.10,
                "Гематокрит": 41.60,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Тромбоциты": 298.0,
                "Цинк": 8.5,
                "Эритроциты": 4.98,
            },
            expected_abnormal_markers=("Витамин D (25-OH)", "Цинк"),
            expected_decision=DecisionExpectation(
                kind="full",
                risk_label="Нужно наблюдение",
                risk_color_key="yellow",
                priority_notes=("Витамин D (25-OH) ниже референса.", "Цинк ниже референса."),
            ),
            expected_final=FinalExpectation(
                prompt_must_contain=("Витамин D (25-OH) ниже референса.", "Цинк ниже референса."),
                prompt_must_not_contain=("Лимфоциты % ниже референса.",),
                interpretation_must_contain=("витамин d", "цинк"),
                interpretation_must_not_contain=("lymphopen", "лимфопени", "significant abnormality", "значимое отклонение"),
            ),
            inconsistent_model_interpretation=(
                "Overall status:\n"
                "Significant deviation\n\n"
                "Key observations:\n"
                "Main condition: Lymphopenia.\n"
                "Short explanation: Lymphocytes % are below reference.\n\n"
                "What this means:\n"
                "This suggests a significant white-cell abnormality.\n\n"
                "Next steps:\n"
                "Medical evaluation recommended.\n\n"
                "Final conclusion:\n"
                "Significant abnormality.\n"
            ),
        ),
        DiagnosticFixture(
            name="cbc_decimal_scientific_variants",
            extracted_raw_values={
                "Гемоглобин": "148,10",
                "Эритроциты": "4,98",
                "Лейкоциты": "4,19",
                "Тромбоциты": "298",
                "Лимфоциты %": "32,70",
                "Лимфоциты абс.": "2,01",
                "RE-LYMP %": "1,10",
            },
            expected_merged_values={
                "RE-LYMP %": 1.10,
                "Гемоглобин": 148.10,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Тромбоциты": 298.0,
                "Эритроциты": 4.98,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "ru",
                "RE-LYMP %": 1.10,
                "Гемоглобин": 148.10,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Тромбоциты": 298.0,
                "Эритроциты": 4.98,
            },
            expected_abnormal_markers=(),
            expected_decision=DecisionExpectation(
                kind="full",
                risk_label="Норма",
                risk_color_key="green",
            ),
            expected_final=FinalExpectation(
                prompt_must_not_contain=("Лимфоциты % ниже референса.",),
                interpretation_must_not_contain=("lymphopen", "лимфопени"),
            ),
        ),
    ]


def _decision_to_dict(plan: DecisionPlan) -> dict[str, object]:
    return {
        "kind": plan.kind,
        "status_label": plan.status_label,
        "status_explanation": plan.status_explanation,
        "summary_overview": plan.summary_overview,
        "confidence_score": plan.confidence_score,
        "confidence_level": plan.confidence_level,
        "confidence_explanation": plan.confidence_explanation,
        "allow_interpretation": plan.allow_interpretation,
        "allow_severity": plan.allow_severity,
        "gating_reasons": list(plan.gating_reasons),
    }


def _load_analyze_module():
    os.environ["OPENAI_API_KEY"] = "test-key"
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: object()
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules.pop("interpreter.analyze", None)
    original_openai = sys.modules.get("openai")
    original_dotenv = sys.modules.get("dotenv")
    try:
        sys.modules["openai"] = fake_openai
        sys.modules["dotenv"] = fake_dotenv
        return importlib.import_module("interpreter.analyze")
    finally:
        if original_openai is None:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = original_openai
        if original_dotenv is None:
            sys.modules.pop("dotenv", None)
        else:
            sys.modules["dotenv"] = original_dotenv


def _default_interpretation(trace_language: str, abnormal_markers: list[str], risk_status: dict[str, object] | None) -> str:
    label = str((risk_status or {}).get("label", "Normal"))
    if not abnormal_markers:
        return (
            "Overall status:\n"
            f"{label}\n\n"
            "Key observations:\n"
            "Main condition: No clinically meaningful deviation.\n"
            "Short explanation: The detected markers remain within range.\n\n"
            "What this means:\n"
            "No clinically relevant pattern is visible.\n\n"
            "Next steps:\n"
            "No immediate follow-up is required.\n\n"
            "Final conclusion:\n"
            "Stable laboratory picture."
        )
    marker_text = ", ".join(abnormal_markers)
    if trace_language == "ru":
        return (
            "Overall status:\n"
            f"{label}\n\n"
            "Key observations:\n"
            f"Main condition: Отклонения ограничены маркерами {marker_text}.\n"
            f"Short explanation: По данным payload подтверждены только {marker_text}.\n\n"
            "What this means:\n"
            "Общая картина остается ограниченной.\n\n"
            "Next steps:\n"
            f"Перепроверьте маркеры {marker_text} при клинической необходимости.\n\n"
            "Final conclusion:\n"
            "Пограничные отклонения без признаков ложной лимфопении."
        )
    return (
        "Overall status:\n"
        f"{label}\n\n"
        "Key observations:\n"
        f"Main condition: Detected deviations are limited to {marker_text}.\n"
        f"Short explanation: Only {marker_text} are supported by the payload.\n\n"
        "What this means:\n"
        "The overall pattern remains limited.\n\n"
        "Next steps:\n"
        f"Review {marker_text} if clinically needed.\n\n"
        "Final conclusion:\n"
        "Detected deviations remain limited to the supported markers."
    )


def trace_pipeline(
    fixture: DiagnosticFixture,
    *,
    apply_consistency_guard: bool = True,
    force_inconsistent_model: bool = False,
) -> PipelineTrace:
    raw_values = dict(sorted(fixture.extracted_raw_values.items(), key=lambda item: item[0].lower()))
    normalized_raw_values = normalize_raw_values(fixture.extracted_raw_values)
    merged_values, _ = merge_canonical_markers(normalized_raw_values, {})
    merged_values = dict(sorted(merged_values.items(), key=lambda item: item[0].lower()))

    payload = {
        "age": fixture.age,
        "gender": fixture.gender,
        "language": fixture.language,
        **normalize_interpretation_markers(merged_values),
    }
    payload = dict(sorted(payload.items(), key=lambda item: item[0].lower()))

    risk_details = assess_risk_details(payload, fixture.language)
    decision = plan_decision(payload)
    risk_status = compute_risk_status(payload, fixture.language) if decision.allow_severity else None

    analyze = _load_analyze_module()
    prompt = analyze.build_prompt(payload)

    if force_inconsistent_model and fixture.inconsistent_model_interpretation is not None:
        raw_interpretation = fixture.inconsistent_model_interpretation
    elif fixture.model_interpretation is not None:
        raw_interpretation = fixture.model_interpretation
    else:
        raw_interpretation = _default_interpretation(fixture.language, risk_details.abnormal_markers, risk_status)

    if apply_consistency_guard:
        final_interpretation, risk_status, _, consistency_issues = enforce_final_consistency(
            raw_interpretation,
            payload=payload,
            abnormal_markers=risk_details.abnormal_markers,
            risk_status=risk_status,
            language=fixture.language,
        )
    else:
        final_interpretation = raw_interpretation
        consistency_issues = [
            asdict(issue)
            for issue in find_final_consistency_issues(
                raw_interpretation,
                validated_findings=build_validated_findings(
                    payload=payload,
                    abnormal_markers=risk_details.abnormal_markers,
                ),
            )
        ]

    return PipelineTrace(
        fixture_name=fixture.name,
        raw_values=raw_values,
        merged_values=merged_values,
        payload=payload,
        abnormal_markers=risk_details.abnormal_markers,
        deviations=[asdict(deviation) for deviation in risk_details.deviations],
        decision=_decision_to_dict(decision),
        risk_status=risk_status,
        prompt=prompt,
        final_response={
            "raw_interpretation": raw_interpretation,
            "interpretation": final_interpretation,
            "risk_status": risk_status,
            "plan": _decision_to_dict(decision),
            "consistency_issues": consistency_issues,
        },
    )


def first_divergence_layer(fixture: DiagnosticFixture, trace: PipelineTrace) -> str | None:
    if trace.raw_values != fixture.extracted_raw_values:
        return "extraction_raw_values"
    if trace.merged_values != fixture.expected_merged_values:
        return "merged_values"
    if trace.payload != fixture.expected_payload:
        return "semantic_payload"
    if tuple(trace.abnormal_markers) != fixture.expected_abnormal_markers:
        return "abnormal_marker_selection"

    risk_status = trace.risk_status or {}
    if trace.decision["kind"] != fixture.expected_decision.kind:
        return "risk_decision"
    if risk_status.get("label") != fixture.expected_decision.risk_label:
        return "risk_decision"
    if risk_status.get("color_key") != fixture.expected_decision.risk_color_key:
        return "risk_decision"
    if tuple(risk_status.get("priority_notes", [])) != fixture.expected_decision.priority_notes:
        return "risk_decision"

    prompt_low = trace.prompt.lower()
    interpretation_low = str(trace.final_response.get("interpretation", "")).lower()
    for token in fixture.expected_final.prompt_must_contain:
        if token.lower() not in prompt_low:
            return "final_interpretation_response"
    for token in fixture.expected_final.prompt_must_not_contain:
        if token.lower() in prompt_low:
            return "final_interpretation_response"
    for token in fixture.expected_final.interpretation_must_contain:
        if token.lower() not in interpretation_low:
            return "final_interpretation_response"
    for token in fixture.expected_final.interpretation_must_not_contain:
        if token.lower() in interpretation_low:
            return "final_interpretation_response"
    return None
