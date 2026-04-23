from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal


ConfidenceLevel = Literal["high", "medium", "low"]
DecisionKind = Literal["full", "limited", "extraction_issue"]
ValidationOutcome = Literal["low_confidence", "extraction_issue"]


@dataclass(frozen=True)
class ValidationIssue:
    marker: str
    value: float | None
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    outcome: ValidationOutcome
    issues: list[ValidationIssue]
    message: str


@dataclass(frozen=True)
class ValidationRule:
    aliases: tuple[str, ...]
    reason: str
    predicate: Callable[[float], bool]


@dataclass(frozen=True)
class ParseContext:
    extracted_count: int | None = None
    confidence_score: int | None = None
    confidence_level: str | None = None
    confidence_explanation: str | None = None
    reference_coverage: float | None = None
    unit_coverage: float | None = None
    structural_consistency: float | None = None
    fallback_used: bool = False
    warnings: list[str] = field(default_factory=list)
    source: str | None = None


@dataclass(frozen=True)
class DecisionPlan:
    kind: DecisionKind
    confidence_score: int
    confidence_level: ConfidenceLevel
    confidence_explanation: str
    status_label: str
    status_explanation: str
    summary_overview: str
    confidence_text: str
    interpretation_message: str | None
    recommendation_title: str
    recommended_action: str
    hide_marker_counts: bool
    hide_priority_notes: bool
    validation_issues: list[ValidationIssue] = field(default_factory=list)
    gating_reasons: list[str] = field(default_factory=list)

    @property
    def allow_interpretation(self) -> bool:
        return self.kind == "full"

    @property
    def allow_severity(self) -> bool:
        return self.kind == "full"

    def build_meta(self, *, language: str, markers_supplied: int) -> dict[str, object]:
        return {
            "language": language,
            "markers_supplied": markers_supplied,
            "decision_kind": self.kind,
            "extraction_issue": self.kind == "extraction_issue",
            "status_label": self.status_label,
            "status_explanation": self.status_explanation,
            "summary_overview": self.summary_overview,
            "confidence_text": self.confidence_text,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "confidence_explanation": self.confidence_explanation,
            "recommendation_title": self.recommendation_title,
            "recommended_action": self.recommended_action,
            "hide_marker_counts": self.hide_marker_counts,
            "hide_priority_notes": self.hide_priority_notes,
            "gating_reasons": self.gating_reasons,
            "validation_issues": [
                {
                    "marker": issue.marker,
                    "value": issue.value,
                    "reason": issue.reason,
                }
                for issue in self.validation_issues
            ],
        }


def _is_less_than(threshold: float) -> Callable[[float], bool]:
    return lambda value: value < threshold


def _is_greater_than(threshold: float) -> Callable[[float], bool]:
    return lambda value: value > threshold


def _is_non_positive(value: float) -> bool:
    return value <= 0


def _get_numeric_value(payload: dict[str, object], aliases: tuple[str, ...]) -> tuple[str, float] | None:
    for alias in aliases:
        raw_value = payload.get(alias)
        if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
            continue
        return alias, float(raw_value)
    return None


VALIDATION_RULES: tuple[ValidationRule, ...] = (
    ValidationRule(("RBC", "Эритроциты", "Eritrocitos"), "must be greater than 0", _is_non_positive),
    ValidationRule(("RBC", "Эритроциты", "Eritrocitos"), "is implausibly high", _is_greater_than(10)),
    ValidationRule(("WBC", "Лейкоциты", "Leucocitos"), "must be greater than 0", _is_non_positive),
    ValidationRule(("WBC", "Лейкоциты", "Leucocitos"), "is implausibly high", _is_greater_than(200)),
    ValidationRule(("Platelets", "Тромбоциты", "Plaquetas"), "must be greater than 0", _is_non_positive),
    ValidationRule(("Platelets", "Тромбоциты", "Plaquetas"), "is implausibly high", _is_greater_than(2000)),
    ValidationRule(("Hemoglobin", "Гемоглобин", "Hemoglobina"), "is implausibly low", _is_less_than(30)),
    ValidationRule(("Hemoglobin", "Гемоглобин", "Hemoglobina"), "is implausibly high", _is_greater_than(250)),
    ValidationRule(("Hematocrit", "Гематокрит", "Hematocrito"), "is implausibly low", _is_less_than(10)),
    ValidationRule(("Hematocrit", "Гематокрит", "Hematocrito"), "is implausibly high", _is_greater_than(75)),
    ValidationRule(("Glucose", "Глюкоза", "Glucosa"), "must be greater than 0", _is_non_positive),
    ValidationRule(("Glucose", "Глюкоза", "Glucosa"), "is implausibly high", _is_greater_than(40)),
    ValidationRule(("Creatinine", "Креатинин", "Creatinina"), "must be greater than 0", _is_non_positive),
    ValidationRule(("Creatinine", "Креатинин", "Creatinina"), "is implausibly high", _is_greater_than(2000)),
    ValidationRule(("MCV",), "is implausibly low", _is_less_than(40)),
    ValidationRule(("MCV",), "is implausibly high", _is_greater_than(150)),
    ValidationRule(("MCH",), "is implausibly low", _is_less_than(10)),
    ValidationRule(("MCH",), "is implausibly high", _is_greater_than(60)),
    ValidationRule(("MCHC",), "is implausibly low", _is_less_than(200)),
    ValidationRule(("MCHC",), "is implausibly high", _is_greater_than(450)),
)


_MESSAGES = {
    "en": {
        "validation_warning": "Possible extraction error detected in the lab values. Please re-upload the report or check the values manually.",
        "limited_warning": "Data may contain inaccuracies.",
        "limited_action": "",
        "limited_label": "Low confidence",
        "limited_status": "The report looks plausible, but extraction confidence is reduced.",
        "limited_confidence": "Data may contain inaccuracies.",
        "limited_confidence_note": "Data may contain inaccuracies.",
        "limited_recommendation_title": "Verification",
        "limited_interpretation": "Data may contain inaccuracies; verify the report before interpretation.",
        "extraction_label": "Extraction issue",
        "extraction_status": "Some extracted results look internally inconsistent or physiologically implausible.",
        "extraction_overview": "Possible extraction issue detected. The report was not interpreted.",
        "extraction_confidence": "Interpretation was stopped for safety.",
        "extraction_recommendation_title": "Re-upload",
    },
    "ru": {
        "validation_warning": "Обнаружена возможная ошибка извлечения значений. Пожалуйста, загрузите отчёт повторно или проверьте значения вручную.",
        "limited_warning": "данные могут содержать неточности",
        "limited_action": "",
        "limited_label": "Низкая уверенность",
        "limited_status": "Отчёт выглядит правдоподобно, но уверенность в извлечении снижена.",
        "limited_confidence": "данные могут содержать неточности",
        "limited_confidence_note": "данные могут содержать неточности",
        "limited_recommendation_title": "Проверка",
        "limited_interpretation": "данные могут содержать неточности; требуется проверка перед интерпретацией",
        "extraction_label": "Ошибка извлечения",
        "extraction_status": "Часть извлечённых результатов противоречива или физиологически маловероятна.",
        "extraction_overview": "Обнаружена возможная ошибка извлечения. Интерпретация отчёта остановлена.",
        "extraction_confidence": "Интерпретация остановлена из соображений безопасности.",
        "extraction_recommendation_title": "Повторная загрузка",
    },
    "es": {
        "validation_warning": "Se detectó un posible error de extracción en los valores. Vuelve a subir el informe o revisa los datos manualmente.",
        "limited_warning": "Los datos pueden contener imprecisiones.",
        "limited_action": "",
        "limited_label": "Confianza baja",
        "limited_status": "El informe parece plausible, pero la confianza de extracción es reducida.",
        "limited_confidence": "Los datos pueden contener imprecisiones.",
        "limited_confidence_note": "Los datos pueden contener imprecisiones.",
        "limited_recommendation_title": "Verificación",
        "limited_interpretation": "Los datos pueden contener imprecisiones; conviene verificar el informe antes de interpretarlo.",
        "extraction_label": "Problema de extracción",
        "extraction_status": "Algunos resultados extraídos son internamente inconsistentes o fisiológicamente poco plausibles.",
        "extraction_overview": "Se detectó un posible problema de extracción. El informe no se interpretó.",
        "extraction_confidence": "La interpretación se detuvo por seguridad.",
        "extraction_recommendation_title": "Nueva carga",
    },
}


def _message(language: str, key: str) -> str:
    selected = _MESSAGES.get(language, _MESSAGES["en"])
    return selected[key]


def _hard_stop_validation_enabled() -> bool:
    raw = os.getenv("LABSENSE_ENABLE_VALIDATION_HARD_STOP", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _normalize_context(parse_context: ParseContext | dict[str, object] | None) -> ParseContext:
    if isinstance(parse_context, ParseContext):
        return parse_context
    if not isinstance(parse_context, dict):
        return ParseContext()
    return ParseContext(
        extracted_count=int(parse_context["extracted_count"]) if isinstance(parse_context.get("extracted_count"), int) else None,
        confidence_score=int(parse_context["confidence_score"]) if isinstance(parse_context.get("confidence_score"), int) else None,
        confidence_level=str(parse_context["confidence_level"]) if parse_context.get("confidence_level") is not None else None,
        confidence_explanation=str(parse_context["confidence_explanation"]) if parse_context.get("confidence_explanation") is not None else None,
        reference_coverage=float(parse_context["reference_coverage"]) if isinstance(parse_context.get("reference_coverage"), (int, float)) else None,
        unit_coverage=float(parse_context["unit_coverage"]) if isinstance(parse_context.get("unit_coverage"), (int, float)) else None,
        structural_consistency=float(parse_context["structural_consistency"]) if isinstance(parse_context.get("structural_consistency"), (int, float)) else None,
        fallback_used=bool(parse_context.get("fallback_used", False)),
        warnings=[str(item) for item in parse_context.get("warnings", [])] if isinstance(parse_context.get("warnings"), list) else [],
        source=str(parse_context["source"]) if parse_context.get("source") is not None else None,
    )


def _build_cross_marker_issues(payload: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    hemoglobin = _get_numeric_value(payload, ("Hemoglobin", "Гемоглобин", "Hemoglobina"))
    hematocrit = _get_numeric_value(payload, ("Hematocrit", "Гематокрит", "Hematocrito"))
    rbc = _get_numeric_value(payload, ("RBC", "Эритроциты", "Eritrocitos"))
    platelets = _get_numeric_value(payload, ("Platelets", "Тромбоциты", "Plaquetas"))
    mpv = _get_numeric_value(payload, ("MPV",))

    if hemoglobin and hematocrit:
        hb_alias, hb_value = hemoglobin
        hct_alias, hct_value = hematocrit
        if hb_value < 80 and hct_value >= 36:
            issues.append(ValidationIssue(hb_alias, hb_value, f"conflicts with {hct_alias}"))
        if hb_value >= 120 and hct_value < 25:
            issues.append(ValidationIssue(hct_alias, hct_value, f"conflicts with {hb_alias}"))

    if rbc and hematocrit:
        rbc_alias, rbc_value = rbc
        hct_alias, hct_value = hematocrit
        if rbc_value < 2 and hct_value >= 35:
            issues.append(ValidationIssue(rbc_alias, rbc_value, f"conflicts with {hct_alias}"))
        if rbc_value >= 3.5 and hct_value < 15:
            issues.append(ValidationIssue(hct_alias, hct_value, f"conflicts with {rbc_alias}"))

    if rbc and hemoglobin:
        rbc_alias, rbc_value = rbc
        hb_alias, hb_value = hemoglobin
        if rbc_value >= 7.5 and hb_value < 90:
            issues.append(ValidationIssue(rbc_alias, rbc_value, f"conflicts with {hb_alias}"))
        if rbc_value < 2 and hb_value >= 120:
            issues.append(ValidationIssue(hb_alias, hb_value, f"conflicts with {rbc_alias}"))

    if platelets and mpv:
        platelets_alias, platelets_value = platelets
        _, mpv_value = mpv
        if platelets_value > 1200 and (mpv_value < 4 or mpv_value > 20):
            issues.append(ValidationIssue(platelets_alias, platelets_value, "conflicts with MPV"))

    return issues


def validate_before_interpretation(
    payload: dict[str, object],
    parse_context: ParseContext | dict[str, object] | None = None,
) -> ValidationResult | None:
    normalized_context = _normalize_context(parse_context)
    hard_issues: list[ValidationIssue] = []

    for rule in VALIDATION_RULES:
        for alias in rule.aliases:
            raw_value = payload.get(alias)
            if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
                continue
            numeric_value = float(raw_value)
            if rule.predicate(numeric_value):
                hard_issues.append(ValidationIssue(marker=alias, value=numeric_value, reason=rule.reason))

    hard_issues.extend(_build_cross_marker_issues(payload))

    extracted_count = normalized_context.extracted_count
    if extracted_count is None:
        extracted_count = sum(
            1
            for key, value in payload.items()
            if key not in {"language", "age", "gender", "parse_context"} and isinstance(value, (int, float)) and not isinstance(value, bool)
        )

    core_marker_count = _count_present_markers(
        payload,
        (
            ("Hemoglobin", "Гемоглобин", "Hemoglobina"),
            ("RBC", "Эритроциты", "Eritrocitos"),
            ("Hematocrit", "Гематокрит", "Hematocrito"),
            ("WBC", "Лейкоциты", "Leucocitos"),
            ("Platelets", "Тромбоциты", "Plaquetas"),
        ),
    )

    if extracted_count <= 1:
        hard_issues.append(ValidationIssue(marker="report", value=float(extracted_count), reason="too few markers extracted"))
    elif extracted_count <= 2 and core_marker_count <= 1 and (
        normalized_context.structural_consistency is None or normalized_context.structural_consistency < 0.3
    ):
        hard_issues.append(
            ValidationIssue(marker="report", value=float(extracted_count), reason="multiple key markers missing or corrupted")
        )

    language = str(payload.get("language", "en"))
    if hard_issues:
        return ValidationResult(
            outcome="extraction_issue",
            issues=hard_issues,
            message=_message(language, "validation_warning"),
        )

    low_confidence_issues: list[ValidationIssue] = []
    if normalized_context.confidence_level == "low":
        low_confidence_issues.append(ValidationIssue(marker="report", value=None, reason="parser_confidence_low"))
    if extracted_count < 3:
        low_confidence_issues.append(ValidationIssue(marker="report", value=float(extracted_count), reason="limited_marker_coverage"))
    if core_marker_count < 2 and extracted_count < 5:
        low_confidence_issues.append(
            ValidationIssue(marker="report", value=float(core_marker_count), reason="limited_core_marker_coverage")
        )
    if normalized_context.reference_coverage is not None and extracted_count >= 4 and normalized_context.reference_coverage < 0.35:
        low_confidence_issues.append(
            ValidationIssue(marker="report", value=normalized_context.reference_coverage, reason="reference_coverage_low")
        )
    if normalized_context.structural_consistency is not None and extracted_count >= 3 and normalized_context.structural_consistency < 0.45:
        low_confidence_issues.append(
            ValidationIssue(marker="report", value=normalized_context.structural_consistency, reason="structure_weak")
        )
    if normalized_context.fallback_used:
        low_confidence_issues.append(ValidationIssue(marker="report", value=None, reason="fallback_used"))
    if normalized_context.warnings:
        low_confidence_issues.append(ValidationIssue(marker="report", value=None, reason="parser_warnings"))

    if not low_confidence_issues:
        return None

    return ValidationResult(
        outcome="low_confidence",
        issues=low_confidence_issues,
        message=_message(language, "limited_confidence_note"),
    )


def _count_present_markers(payload: dict[str, object], aliases: tuple[tuple[str, ...], ...]) -> int:
    count = 0
    for alias_group in aliases:
        if _get_numeric_value(payload, alias_group) is not None:
            count += 1
    return count


def _derive_confidence(
    payload: dict[str, object],
    parse_context: ParseContext,
) -> tuple[int, ConfidenceLevel, str, list[str]]:
    extracted_count = parse_context.extracted_count
    if extracted_count is None:
        extracted_count = sum(
            1
            for key, value in payload.items()
            if key not in {"language", "age", "gender", "parse_context"} and isinstance(value, (int, float)) and not isinstance(value, bool)
        )

    core_marker_count = _count_present_markers(
        payload,
        (
            ("Hemoglobin", "Гемоглобин", "Hemoglobina"),
            ("RBC", "Эритроциты", "Eritrocitos"),
            ("Hematocrit", "Гематокрит", "Hematocrito"),
            ("WBC", "Лейкоциты", "Leucocitos"),
            ("Platelets", "Тромбоциты", "Plaquetas"),
        ),
    )

    if parse_context.confidence_score is not None:
        score = parse_context.confidence_score
    elif extracted_count >= 8:
        score = 78
    elif extracted_count >= 5:
        score = 68
    elif extracted_count >= 3:
        score = 56
    else:
        score = 42

    reasons: list[str] = []
    if extracted_count < 3:
        score -= 18
        reasons.append("few_markers")
    elif extracted_count < 5:
        score -= 8
        reasons.append("limited_marker_set")

    if core_marker_count < 2:
        score -= 12
        reasons.append("weak_core_coverage")
    elif core_marker_count >= 3 and extracted_count >= 5:
        score += 4
        reasons.append("core_coverage_good")

    if parse_context.reference_coverage is not None and extracted_count >= 4 and parse_context.reference_coverage < 0.35:
        score -= 10
        reasons.append("reference_coverage_low")

    if parse_context.structural_consistency is not None and extracted_count >= 3 and parse_context.structural_consistency < 0.45:
        score -= 10
        reasons.append("structure_weak")

    if parse_context.fallback_used:
        score -= 5
        reasons.append("fallback_used")

    if parse_context.warnings:
        score -= 4
        reasons.append("parser_warnings")

    score = _clamp_score(score)
    if score >= 80:
        return score, "high", "Extraction quality looks strong and consistent.", reasons
    if score >= 55:
        return score, "medium", "Extraction quality looks usable, but some signals are limited.", reasons
    return score, "low", "Extraction quality is limited and should be verified before strong conclusions.", reasons


def plan_decision(
    payload: dict[str, object],
    parse_context: ParseContext | dict[str, object] | None = None,
) -> DecisionPlan:
    normalized_context = _normalize_context(parse_context)
    score, level, explanation, reasons = _derive_confidence(payload, normalized_context)
    # Keep confidence metadata available, but disable the validation-driven
    # blocking/override layer so reports continue through the normal flow.
    return DecisionPlan(
        kind="full",
        confidence_score=score,
        confidence_level=level,
        confidence_explanation=explanation,
        status_label="",
        status_explanation="",
        summary_overview="",
        confidence_text="",
        interpretation_message=None,
        recommendation_title="",
        recommended_action="",
        hide_marker_counts=False,
        hide_priority_notes=False,
        gating_reasons=sorted(set(reasons)),
    )
