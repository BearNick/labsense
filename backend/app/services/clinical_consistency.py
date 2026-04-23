from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ClinicalSeverity = Literal["CRITICAL", "SIGNIFICANT", "MODERATE", "MILD", "NORMAL", "INSUFFICIENT"]
MarkerStatus = Literal["low", "normal", "high", "unknown"]
MarkerType = Literal["absolute", "percentage", "hematologic", "micronutrient", "special", "general"]
NextStepsTier = Literal["urgent", "medical_review", "follow_up", "none", "data_review"]

MIN_MARKERS_FOR_VALIDATED_FINDINGS = 5

ABSOLUTE_MARKERS = {
    "Лимфоциты абс.",
    "Lymphocytes abs.",
    "Нейтрофилы абс.",
    "Neutrophils abs.",
    "RE-LYMP abs",
    "AS-LYMP abs",
}
PERCENTAGE_MARKERS = {
    "Лимфоциты %",
    "Lymphocytes %",
    "Нейтрофилы %",
    "Neutrophils %",
    "RE-LYMP %",
    "AS-LYMP %",
}
HEMATOLOGIC_MARKERS = {
    "Гемоглобин",
    "Hemoglobin",
    "Гематокрит",
    "Hematocrit",
    "Эритроциты",
    "RBC",
    "Лейкоциты",
    "WBC",
    "Тромбоциты",
    "Platelets",
    "Лимфоциты %",
    "Lymphocytes %",
    "Лимфоциты абс.",
    "Lymphocytes abs.",
    "Нейтрофилы %",
    "Neutrophils %",
    "Нейтрофилы абс.",
    "Neutrophils abs.",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
}
MICRONUTRIENT_MARKERS = {"Витамин D (25-OH)", "Vitamin D (25-OH)", "Цинк", "Zinc"}
SPECIAL_MARKERS = {"RE-LYMP abs", "RE-LYMP %", "AS-LYMP abs", "AS-LYMP %", "NRBC"}
BASE_DIAGNOSIS_EXCLUDED_MARKERS = SPECIAL_MARKERS
QUEUE3_COVERAGE_ONLY_MARKERS = {
    "Хлор",
    "Мочевина",
    "BUN",
    "AST",
    "ALT",
    "Кислота мочевая",
    "Urine Albumin",
    "Urine Creatinine",
    "ACR",
}
FIRST_WAVE_CHEMISTRY_MARKERS = {
    "Глюкоза",
    "Glucose",
    "Креатинин",
    "Creatinine",
    "Натрий",
    "Sodium",
    "Калий",
    "Potassium",
    "eGFR",
    "HbA1c",
}
SUPPORTED_REASONING_MARKERS = HEMATOLOGIC_MARKERS | MICRONUTRIENT_MARKERS | FIRST_WAVE_CHEMISTRY_MARKERS

REFERENCE_RULES: dict[str, tuple[float | None, float | None]] = {
    "Гемоглобин": (120.0, 170.0),
    "Hemoglobin": (120.0, 170.0),
    "Гематокрит": (36.0, 50.0),
    "Hematocrit": (36.0, 50.0),
    "Эритроциты": (3.8, 5.8),
    "RBC": (3.8, 5.8),
    "Лейкоциты": (4.0, 10.0),
    "WBC": (4.0, 10.0),
    "Тромбоциты": (150.0, 400.0),
    "Platelets": (150.0, 400.0),
    "Лимфоциты %": (20.0, 45.0),
    "Lymphocytes %": (20.0, 45.0),
    "Лимфоциты абс.": (1.0, 4.8),
    "Lymphocytes abs.": (1.0, 4.8),
    "Нейтрофилы %": (40.0, 75.0),
    "Neutrophils %": (40.0, 75.0),
    "Нейтрофилы абс.": (1.5, 7.7),
    "Neutrophils abs.": (1.5, 7.7),
    "MCV": (80.0, 100.0),
    "MCH": (27.0, 34.0),
    "MCHC": (320.0, 360.0),
    "RDW": (11.5, 14.5),
    "Витамин D (25-OH)": (30.0, 100.0),
    "Vitamin D (25-OH)": (30.0, 100.0),
    "Цинк": (10.7, 18.4),
    "Zinc": (10.7, 18.4),
    "Глюкоза": (3.9, 5.5),
    "Glucose": (3.9, 5.5),
    "Креатинин": (53.0, 115.0),
    "Creatinine": (53.0, 115.0),
    "eGFR": (60.0, None),
    "Натрий": (135.0, 145.0),
    "Sodium": (135.0, 145.0),
    "Калий": (3.5, 5.1),
    "Potassium": (3.5, 5.1),
    "HbA1c": (4.0, 5.6),
}

CANONICAL_MARKER_ALIASES: dict[str, tuple[str, ...]] = {
    "Лимфоциты %": ("Лимфоциты %", "Lymphocytes %", "LYM %"),
    "Лимфоциты абс.": ("Лимфоциты абс.", "Lymphocytes abs.", "LYM abs", "LYM ABS"),
    "Нейтрофилы %": ("Нейтрофилы %", "Neutrophils %", "NEUT %"),
    "Нейтрофилы абс.": ("Нейтрофилы абс.", "Neutrophils abs.", "NEUT abs", "NEUT ABS"),
    "Гемоглобин": ("Гемоглобин", "Hemoglobin", "HGB"),
    "Гематокрит": ("Гематокрит", "Hematocrit", "HCT"),
    "Эритроциты": ("Эритроциты", "RBC"),
    "Тромбоциты": ("Тромбоциты", "Platelets", "PLT"),
    "Витамин D (25-OH)": ("Витамин D (25-OH)", "Vitamin D (25-OH)"),
    "Цинк": ("Цинк", "Zinc"),
    "Глюкоза": ("Глюкоза", "Glucose"),
    "Креатинин": ("Креатинин", "Creatinine", "Cr"),
    "Натрий": ("Натрий", "Sodium", "Na"),
    "Калий": ("Калий", "Potassium", "K"),
    "eGFR": ("eGFR",),
    "HbA1c": ("HbA1c", "A1c"),
}

CLAIM_TOKENS = {
    "anemia": ("anemia", "anaemia", "анеми"),
    "lymphopenia": ("lymphopen", "лимфопени", "linfopen"),
    "neutropenia": ("neutropen", "нейтропени"),
    "thrombocytopenia": ("thrombocytopen", "тромбоцитопени"),
    "macrocytosis": ("macrocytosis", "macrocytic", "макроцит"),
    "immune_disorder": (
        "immune disorder",
        "immune dysfunction",
        "immune abnormal",
        "immunodefic",
        "white-cell disorder",
        "white-cell abnormality",
        "нарушение иммун",
        "иммунодефиц",
        "лейкоцитарн",
    ),
    "critical": ("critical", "urgent", "критич", "urgente"),
    "significant": ("significant", "значим", "significativa", "significativo"),
    "moderate": ("moderate", "умерен", "moderad"),
    "mild": ("mild", "leve", "легк"),
    "medical_review": ("medical evaluation", "medical review", "see a clinician", "обсудите с врачом", "valoración médica"),
    "urgent_review": ("urgent medical", "urgent assessment", "немедлен", "urgente"),
}


@dataclass(frozen=True)
class NormalizedMarker:
    name: str
    value: float | None
    ref_min: float | None
    ref_max: float | None
    status: MarkerStatus
    marker_types: list[MarkerType]
    supports_base_diagnosis: bool


@dataclass(frozen=True)
class ValidatedFinding:
    claim: str
    supporting_markers: list[str]
    summary: str


@dataclass(frozen=True)
class ValidatedFindings:
    incomplete_payload: bool
    normalized_markers: list[NormalizedMarker]
    abnormal_markers: list[str]
    validated_findings: list[ValidatedFinding]
    detected_patterns: list[str]
    allowed_claims: list[str]
    severity: ClinicalSeverity
    next_steps_tier: NextStepsTier
    micronutrient_only: bool


@dataclass(frozen=True)
class FinalConsistencyIssue:
    code: str
    message: str


def build_pre_llm_validated_context(payload: dict[str, object]) -> dict[str, object]:
    validated = build_validated_findings(payload=payload, abnormal_markers=[])
    payload_markers = _candidate_markers(payload)
    claims = [
        claim
        for claim in validated.allowed_claims
        if claim
        not in {
            "normal",
            "mild",
            "moderate",
            "significant",
            "critical",
            "insufficient",
        }
    ]
    supporting_markers = {
        finding.claim: list(finding.supporting_markers)
        for finding in validated.validated_findings
    }
    clinically_relevant_markers = _dedupe(
        [
            marker
            for markers in supporting_markers.values()
            for marker in markers
        ]
    )
    coverage_only_markers = _dedupe(
        [marker for marker in payload_markers if marker in QUEUE3_COVERAGE_ONLY_MARKERS]
    )
    supported_reasoning_markers_present = _dedupe(
        [marker for marker in payload_markers if marker in SUPPORTED_REASONING_MARKERS]
    )
    return {
        "severity": validated.severity,
        "allowed_claims": claims,
        "detected_patterns": list(validated.detected_patterns),
        "finding_summaries": [finding.summary for finding in validated.validated_findings],
        "supporting_markers": supporting_markers,
        "clinically_relevant_markers": clinically_relevant_markers,
        "micronutrient_only": validated.micronutrient_only,
        "payload_markers": payload_markers,
        "display_markers": payload_markers,
        "coverage_only_markers": coverage_only_markers,
        "supported_reasoning_markers_present": supported_reasoning_markers_present,
    }


def build_normalized_marker_set(payload: dict[str, object]) -> list[NormalizedMarker]:
    markers: list[NormalizedMarker] = []
    for name in _candidate_markers(payload):
        value = payload.get(name)
        ref_min, ref_max = REFERENCE_RULES.get(name, (None, None))
        status = _marker_status(value, ref_min, ref_max)
        marker_types = _marker_types(name)
        markers.append(
            NormalizedMarker(
                name=name,
                value=float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
                ref_min=ref_min,
                ref_max=ref_max,
                status=status,
                marker_types=marker_types,
                supports_base_diagnosis=name not in BASE_DIAGNOSIS_EXCLUDED_MARKERS,
            )
        )
    return markers


def build_validated_findings(*, payload: dict[str, object], abnormal_markers: list[str]) -> ValidatedFindings:
    normalized_markers = build_normalized_marker_set(payload)
    marker_map = {marker.name: marker for marker in normalized_markers}
    numeric_marker_count = sum(marker.value is not None for marker in normalized_markers)
    incomplete_payload = numeric_marker_count < MIN_MARKERS_FOR_VALIDATED_FINDINGS

    validated: list[ValidatedFinding] = []
    detected_patterns: list[str] = []

    hemoglobin_low = _is_low(marker_map, "Гемоглобин", "Hemoglobin")
    hematocrit_low = _is_low(marker_map, "Гематокрит", "Hematocrit")
    rbc_low = _is_low(marker_map, "Эритроциты", "RBC")
    mcv_high = _is_high(marker_map, "MCV")
    lymphopenia_finding = _build_lymphopenia_finding(marker_map)
    neutrophils_low = _is_low(marker_map, "Нейтрофилы абс.", "Neutrophils abs.", "Нейтрофилы %", "Neutrophils %")
    platelets_low = _is_low(marker_map, "Тромбоциты", "Platelets")
    vitamin_d_low = _is_low(marker_map, "Витамин D (25-OH)", "Vitamin D (25-OH)")
    zinc_low = _is_low(marker_map, "Цинк", "Zinc")

    if hemoglobin_low:
        validated.append(
            ValidatedFinding(
                claim="anemia",
                supporting_markers=_present_markers(marker_map, "Гемоглобин", "Hemoglobin"),
                summary="Hemoglobin is below reference.",
            )
        )
    if lymphopenia_finding is not None:
        validated.append(lymphopenia_finding)
    if neutrophils_low:
        validated.append(
            ValidatedFinding(
                claim="neutropenia",
                supporting_markers=_present_markers(marker_map, "Нейтрофилы абс.", "Neutrophils abs.", "Нейтрофилы %", "Neutrophils %"),
                summary="Neutrophils are below reference.",
            )
        )
    if platelets_low:
        validated.append(
            ValidatedFinding(
                claim="thrombocytopenia",
                supporting_markers=_present_markers(marker_map, "Тромбоциты", "Platelets"),
                summary="Platelets are below reference.",
            )
        )
    if mcv_high:
        validated.append(
            ValidatedFinding(
                claim="macrocytosis",
                supporting_markers=_present_markers(marker_map, "MCV"),
                summary="MCV is above reference.",
            )
        )
    if vitamin_d_low:
        validated.append(
            ValidatedFinding(
                claim="vitamin_d_deficiency",
                supporting_markers=_present_markers(marker_map, "Витамин D (25-OH)", "Vitamin D (25-OH)"),
                summary="Vitamin D is below reference.",
            )
        )
    if zinc_low:
        validated.append(
            ValidatedFinding(
                claim="zinc_deficiency",
                supporting_markers=_present_markers(marker_map, "Цинк", "Zinc"),
                summary="Zinc is below reference.",
            )
        )

    if hemoglobin_low and (hematocrit_low or rbc_low) and mcv_high:
        detected_patterns.append("macrocytic_anemia")
        validated.append(
            ValidatedFinding(
                claim="macrocytic_anemia",
                supporting_markers=_present_markers(marker_map, "Гемоглобин", "Hemoglobin", "Гематокрит", "Hematocrit", "Эритроциты", "RBC", "MCV"),
                summary="Low hemoglobin with low hematocrit/RBC and high MCV forms a macrocytic anemia pattern.",
            )
        )

    abnormal_markers_deduped = _dedupe(abnormal_markers)
    micronutrient_only = bool(abnormal_markers_deduped) and set(abnormal_markers_deduped).issubset(MICRONUTRIENT_MARKERS)
    severity = _compute_severity(validated, detected_patterns, micronutrient_only, marker_map, incomplete_payload)
    next_steps_tier = _next_steps_for_severity(severity)

    return ValidatedFindings(
        incomplete_payload=incomplete_payload,
        normalized_markers=normalized_markers,
        abnormal_markers=abnormal_markers_deduped,
        validated_findings=validated,
        detected_patterns=detected_patterns,
        allowed_claims=_build_allowed_claims(validated, detected_patterns, severity),
        severity=severity,
        next_steps_tier=next_steps_tier,
        micronutrient_only=micronutrient_only,
    )


def find_final_consistency_issues(interpretation: str, *, validated_findings: ValidatedFindings) -> list[FinalConsistencyIssue]:
    text = interpretation.lower()
    issues: list[FinalConsistencyIssue] = []
    allowed_claims = set(validated_findings.allowed_claims)

    if validated_findings.incomplete_payload:
        return [
            FinalConsistencyIssue(
                code="insufficient_payload_for_interpretation",
                message="Incomplete payload must return data-insufficiency output only.",
            )
        ]

    claim_checks = {
        "anemia": "unsupported_anemia_claim",
        "lymphopenia": "unsupported_lymphopenia_claim",
        "neutropenia": "unsupported_neutropenia_claim",
        "thrombocytopenia": "unsupported_thrombocytopenia_claim",
        "macrocytosis": "unsupported_macrocytosis_claim",
    }
    for claim, issue_code in claim_checks.items():
        if _contains_any(text, CLAIM_TOKENS[claim]) and claim not in allowed_claims and "macrocytic_anemia" not in allowed_claims:
            issues.append(
                FinalConsistencyIssue(
                    code=issue_code,
                    message=f"Final prose mentioned unsupported claim: {claim}.",
                )
            )

    if _contains_any(text, CLAIM_TOKENS["immune_disorder"]) and not _immune_claim_allowed(validated_findings):
        issues.append(
            FinalConsistencyIssue(
                code="unsupported_immune_claim",
                message="Final prose introduced an unsupported immune or white-cell disorder claim.",
            )
        )

    if _severity_from_text(text) not in {None, validated_findings.severity}:
        issues.append(
            FinalConsistencyIssue(
                code="severity_mismatch",
                message="Final prose severity does not match validated findings.",
            )
        )

    if _next_steps_mismatch(text, validated_findings.next_steps_tier):
        issues.append(
            FinalConsistencyIssue(
                code="next_steps_mismatch",
                message="Final prose next steps do not match validated severity.",
            )
        )

    if validated_findings.micronutrient_only and _contains_any(text, CLAIM_TOKENS["immune_disorder"] + CLAIM_TOKENS["lymphopenia"]):
        issues.append(
            FinalConsistencyIssue(
                code="micronutrient_case_became_immune_claim",
                message="Micronutrient-only deviations must not become immune-disorder claims.",
            )
        )

    return _unique_issues(issues)


def enforce_final_consistency(
    interpretation: str,
    *,
    payload: dict[str, object],
    abnormal_markers: list[str],
    risk_status: dict[str, object] | None,
    language: str,
) -> tuple[str, dict[str, object] | None, dict[str, object], list[dict[str, str]]]:
    validated_findings = build_validated_findings(
        payload=payload,
        abnormal_markers=abnormal_markers,
    )
    issues = find_final_consistency_issues(interpretation, validated_findings=validated_findings)
    corrected_risk_status = _build_risk_status(validated_findings, language, risk_status)

    if not issues:
        return interpretation, corrected_risk_status, asdict(validated_findings), []

    return (
        build_deterministic_fallback(validated_findings=validated_findings, risk_status=corrected_risk_status, language=language),
        corrected_risk_status,
        asdict(validated_findings),
        [asdict(issue) for issue in issues],
    )


def build_deterministic_fallback(
    *,
    validated_findings: ValidatedFindings,
    risk_status: dict[str, object] | None,
    language: str,
) -> str:
    localized = _localized_templates(language)
    status = str((risk_status or {}).get("label") or localized["status_normal"])
    markers = _format_markers(validated_findings.abnormal_markers)
    display_claims = _format_display_claims(localized, validated_findings)

    if validated_findings.incomplete_payload:
        return (
            "Overall status:\n"
            f"{localized['status_insufficient']}\n\n"
            "Key observations:\n"
            f"Main condition: {localized['main_insufficient']}\n"
            f"Short explanation: {localized['short_insufficient']}\n\n"
            "What this means:\n"
            f"{localized['meaning_insufficient']}\n\n"
            "Next steps:\n"
            f"{localized['next_data_review']}\n\n"
            "Final conclusion:\n"
            f"{localized['conclusion_insufficient']}"
        )

    if validated_findings.severity == "NORMAL":
        return (
            "Overall status:\n"
            f"{status}\n\n"
            "Key observations:\n"
            f"Main condition: {localized['main_normal']}\n"
            f"Short explanation: {localized['short_normal']}\n\n"
            "What this means:\n"
            f"{localized['meaning_normal']}\n\n"
            "Next steps:\n"
            f"{localized['next_none']}\n\n"
            "Final conclusion:\n"
            f"{localized['conclusion_normal']}"
        )

    if "macrocytic_anemia" in validated_findings.allowed_claims:
        main = localized["main_macrocytic_anemia"]
        short = localized["short_macrocytic_anemia"].format(markers=markers)
        meaning = localized["meaning_macrocytic_anemia"]
    elif "anemia" in validated_findings.allowed_claims:
        main = localized["main_anemia"]
        short = localized["short_anemia"].format(markers=markers)
        meaning = localized["meaning_anemia"]
    else:
        main = localized["main_supported_markers"].format(markers=markers)
        short = localized["short_supported_markers"].format(claims=display_claims, markers=markers)
        meaning = localized["meaning_supported_markers"].format(claims=display_claims, markers=markers)

    return (
        "Overall status:\n"
        f"{status}\n\n"
        "Key observations:\n"
        f"Main condition: {main}\n"
        f"Short explanation: {short}\n\n"
        "What this means:\n"
        f"{meaning}\n\n"
        "Next steps:\n"
        f"{_localized_next_steps(localized, validated_findings, markers)}\n\n"
        "Final conclusion:\n"
        f"{localized['conclusion_supported'].format(claims=display_claims, markers=markers)}"
    )


def _candidate_markers(payload: dict[str, object]) -> list[str]:
    return _dedupe(
        [
            key
            for key, value in payload.items()
            if key not in {"age", "gender", "language"} and isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
    )


def _marker_status(value: object, ref_min: float | None, ref_max: float | None) -> MarkerStatus:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "unknown"
    numeric = float(value)
    if ref_min is not None and numeric < ref_min:
        return "low"
    if ref_max is not None and numeric > ref_max:
        return "high"
    return "normal"


def _marker_types(name: str) -> list[MarkerType]:
    types: list[MarkerType] = []
    if name in ABSOLUTE_MARKERS:
        types.append("absolute")
    if name in PERCENTAGE_MARKERS:
        types.append("percentage")
    if name in HEMATOLOGIC_MARKERS:
        types.append("hematologic")
    if name in MICRONUTRIENT_MARKERS:
        types.append("micronutrient")
    if name in SPECIAL_MARKERS:
        types.append("special")
    if not types:
        types.append("general")
    return types


def _is_low(marker_map: dict[str, NormalizedMarker], *names: str) -> bool:
    return any(_resolve_marker(marker_map, name).status == "low" for name in names)


def _is_high(marker_map: dict[str, NormalizedMarker], *names: str) -> bool:
    return any(_resolve_marker(marker_map, name).status == "high" for name in names)


def _present_markers(marker_map: dict[str, NormalizedMarker], *names: str) -> list[str]:
    present: list[str] = []
    for name in names:
        marker = _resolve_marker(marker_map, name)
        if marker.value is not None and marker.name not in present:
            present.append(marker.name)
    return present


def _build_lymphopenia_finding(marker_map: dict[str, NormalizedMarker]) -> ValidatedFinding | None:
    lymph_percent = _resolve_marker(marker_map, "Лимфоциты %")
    if lymph_percent.status == "low":
        return ValidatedFinding(
            claim="lymphopenia",
            supporting_markers=[lymph_percent.name],
            summary="Lymphocyte percentage is below reference.",
        )

    lymph_absolute = _resolve_marker(marker_map, "Лимфоциты абс.")
    if lymph_absolute.status == "low":
        return ValidatedFinding(
            claim="lymphopenia",
            supporting_markers=[lymph_absolute.name],
            summary="Absolute lymphocyte count is below reference.",
        )

    return None


def _compute_severity(
    validated: list[ValidatedFinding],
    detected_patterns: list[str],
    micronutrient_only: bool,
    marker_map: dict[str, NormalizedMarker],
    incomplete_payload: bool,
) -> ClinicalSeverity:
    if incomplete_payload:
        return "INSUFFICIENT"

    hemoglobin = _value(marker_map, "Гемоглобин", "Hemoglobin")
    if hemoglobin is not None and hemoglobin < 80:
        return "CRITICAL"
    if "macrocytic_anemia" in detected_patterns:
        return "SIGNIFICANT"
    if any(finding.claim in {"anemia", "neutropenia", "thrombocytopenia"} for finding in validated):
        return "MODERATE"
    if micronutrient_only:
        return "MILD"
    if validated:
        return "MILD"
    return "NORMAL"


def _next_steps_for_severity(severity: ClinicalSeverity) -> NextStepsTier:
    return {
        "CRITICAL": "urgent",
        "SIGNIFICANT": "medical_review",
        "MODERATE": "medical_review",
        "MILD": "follow_up",
        "NORMAL": "none",
        "INSUFFICIENT": "data_review",
    }[severity]


def _build_allowed_claims(
    validated: list[ValidatedFinding],
    detected_patterns: list[str],
    severity: ClinicalSeverity,
) -> list[str]:
    claims = [finding.claim for finding in validated]
    claims.extend(detected_patterns)
    claims.append(severity.lower())
    return _dedupe(claims)


def _immune_claim_allowed(validated_findings: ValidatedFindings) -> bool:
    allowed = set(validated_findings.allowed_claims)
    return bool({"lymphopenia", "neutropenia"}.intersection(allowed)) and not validated_findings.micronutrient_only


def _severity_from_text(text: str) -> ClinicalSeverity | None:
    if _contains_any(text, CLAIM_TOKENS["critical"]):
        return "CRITICAL"
    if _contains_any(text, CLAIM_TOKENS["significant"]):
        return "SIGNIFICANT"
    if _contains_any(text, CLAIM_TOKENS["moderate"]):
        return "MODERATE"
    if _contains_any(text, CLAIM_TOKENS["mild"]):
        return "MILD"
    return None


def _next_steps_mismatch(text: str, tier: NextStepsTier) -> bool:
    if tier == "urgent":
        return not _contains_any(text, CLAIM_TOKENS["urgent_review"])
    if tier == "medical_review":
        return _contains_any(text, CLAIM_TOKENS["urgent_review"]) or not _contains_any(text, CLAIM_TOKENS["medical_review"])
    if tier == "follow_up":
        return _contains_any(text, CLAIM_TOKENS["urgent_review"] + CLAIM_TOKENS["medical_review"])
    if tier == "none":
        return _contains_any(text, CLAIM_TOKENS["urgent_review"] + CLAIM_TOKENS["medical_review"])
    return "re-upload" not in text and "verify" not in text and "повторно" not in text


def _build_risk_status(
    validated_findings: ValidatedFindings,
    language: str,
    prior_risk_status: dict[str, object] | None,
) -> dict[str, object] | None:
    localized = _localized_templates(language)
    priority_notes = list((prior_risk_status or {}).get("priority_notes", []))

    if validated_findings.severity == "INSUFFICIENT":
        return None
    if validated_findings.severity == "NORMAL":
        return {
            "label": localized["status_normal"],
            "color_key": "green",
            "explanation": localized["status_normal_explanation"],
            "priority_notes": [],
        }
    if validated_findings.severity in {"MILD", "MODERATE"}:
        return {
            "label": localized["status_mild"] if validated_findings.severity == "MILD" else localized["status_moderate"],
            "color_key": "yellow",
            "explanation": localized["status_mild_explanation"] if validated_findings.severity == "MILD" else localized["status_moderate_explanation"],
            "priority_notes": priority_notes,
        }
    return {
        "label": localized["status_significant"] if validated_findings.severity == "SIGNIFICANT" else localized["status_critical"],
        "color_key": "red",
        "explanation": localized["status_significant_explanation"] if validated_findings.severity == "SIGNIFICANT" else localized["status_critical_explanation"],
        "priority_notes": priority_notes,
    }


def _localized_next_steps(localized: dict[str, str], validated_findings: ValidatedFindings, markers: str) -> str:
    if validated_findings.next_steps_tier == "urgent":
        return localized["next_urgent"]
    if validated_findings.next_steps_tier == "medical_review":
        return localized["next_medical_review"]
    if validated_findings.next_steps_tier == "follow_up":
        return localized["next_follow_up"].format(markers=markers)
    if validated_findings.next_steps_tier == "data_review":
        return localized["next_data_review"]
    return localized["next_none"]


def _format_display_claims(localized: dict[str, str], validated_findings: ValidatedFindings) -> str:
    claim_labels = {
        finding.claim
        for finding in validated_findings.validated_findings
        if finding.claim != "macrocytic_anemia"
    }
    claim_labels.update(validated_findings.detected_patterns)
    if not claim_labels:
        return localized["no_claims"]
    return ", ".join(localized.get(f"claim_{claim}", claim.replace("_", " ")) for claim in sorted(claim_labels))


def _value(marker_map: dict[str, NormalizedMarker], *names: str) -> float | None:
    for name in names:
        marker = _resolve_marker(marker_map, name)
        if marker and marker.value is not None:
            return marker.value
    return None


def _resolve_marker(marker_map: dict[str, NormalizedMarker], name: str) -> NormalizedMarker:
    marker = marker_map.get(name)
    if marker is not None:
        return marker
    for alias in CANONICAL_MARKER_ALIASES.get(name, ()):
        marker = marker_map.get(alias)
        if marker is not None:
            return marker
    return _unknown_marker(name)


def _unknown_marker(name: str) -> NormalizedMarker:
    return NormalizedMarker(name=name, value=None, ref_min=None, ref_max=None, status="unknown", marker_types=["general"], supports_base_diagnosis=False)


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _format_markers(markers: list[str]) -> str:
    return ", ".join(_dedupe(markers)) or "supported markers"


def _dedupe(values: list[str]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def _unique_issues(issues: list[FinalConsistencyIssue]) -> list[FinalConsistencyIssue]:
    seen: set[str] = set()
    unique: list[FinalConsistencyIssue] = []
    for issue in issues:
        if issue.code in seen:
            continue
        seen.add(issue.code)
        unique.append(issue)
    return unique


def _localized_templates(language: str) -> dict[str, str]:
    templates = {
        "en": {
            "status_normal": "Normal",
            "status_mild": "Mild deviation",
            "status_moderate": "Moderate deviation",
            "status_significant": "Significant deviation",
            "status_critical": "Critical deviation",
            "status_insufficient": "Data insufficiency",
            "status_normal_explanation": "Results are within range or do not support a clinically meaningful abnormality.",
            "status_mild_explanation": "Only mild deviations are present.",
            "status_moderate_explanation": "The results support a moderate clinical abnormality.",
            "status_significant_explanation": "The results support a significant clinical abnormality.",
            "status_critical_explanation": "The results support a critical clinical abnormality.",
            "main_insufficient": "Insufficient extracted data.",
            "short_insufficient": "The available results are not complete enough for a reliable clinical interpretation.",
            "meaning_insufficient": "A fuller data set is needed before the laboratory pattern can be assessed safely.",
            "conclusion_insufficient": "Interpretation is deferred until more complete results are available.",
            "main_normal": "No significant hematologic abnormality is evident.",
            "short_normal": "CBC values are within reference, and reactive cell markers do not indicate lymphopenia or another hematologic disorder.",
            "meaning_normal": "The blood count does not show anemia, lymphopenia, neutropenia, thrombocytopenia, or another clinically meaningful hematologic pattern.",
            "conclusion_normal": "Overall, the hematologic profile appears stable.",
            "main_anemia": "Findings are consistent with anemia.",
            "short_anemia": "The supported abnormalities involve {markers}.",
            "meaning_anemia": "Hemoglobin is below reference, which supports an anemic pattern in the current results.",
            "main_macrocytic_anemia": "Findings are consistent with macrocytic anemia.",
            "short_macrocytic_anemia": "The current abnormalities support macrocytic anemia, including {markers}.",
            "meaning_macrocytic_anemia": "Low hemoglobin with low RBC/hematocrit and high MCV forms a complete macrocytic anemia pattern.",
            "main_supported_markers": "The main deviations involve {markers}.",
            "short_supported_markers": "The current results support {claims}.",
            "meaning_supported_markers": "These findings are based on the abnormal markers identified in the report: {markers}.",
            "conclusion_supported": "Overall, the abnormalities are limited to {claims}.",
            "next_urgent": "Urgent medical assessment is recommended based on the severity of the current findings.",
            "next_medical_review": "Medical evaluation is recommended based on the current findings.",
            "next_follow_up": "Repeat or review the listed markers if clinically needed: {markers}.",
            "next_none": "No immediate follow-up is required.",
            "next_data_review": "Re-upload the report or verify the extracted values before interpretation.",
            "no_claims": "no supported diagnosis",
            "claim_anemia": "anemia",
            "claim_lymphopenia": "lymphopenia",
            "claim_neutropenia": "neutropenia",
            "claim_thrombocytopenia": "thrombocytopenia",
            "claim_macrocytosis": "macrocytosis",
            "claim_macrocytic_anemia": "macrocytic anemia",
            "claim_vitamin_d_deficiency": "vitamin D deficiency",
            "claim_zinc_deficiency": "zinc deficiency",
        },
        "ru": {
            "status_normal": "Норма",
            "status_mild": "Легкое отклонение",
            "status_moderate": "Умеренное отклонение",
            "status_significant": "Значимое отклонение",
            "status_critical": "Критическое отклонение",
            "status_insufficient": "Недостаточно данных",
            "status_normal_explanation": "Результаты находятся в пределах нормы или не указывают на клинически значимое отклонение.",
            "status_mild_explanation": "Есть только легкие отклонения.",
            "status_moderate_explanation": "Результаты поддерживают умеренное клиническое отклонение.",
            "status_significant_explanation": "Результаты поддерживают значимое клиническое отклонение.",
            "status_critical_explanation": "Результаты поддерживают критическое клиническое отклонение.",
            "main_insufficient": "Недостаточно извлеченных данных.",
            "short_insufficient": "Имеющихся результатов недостаточно для надежной клинической интерпретации.",
            "meaning_insufficient": "Для безопасной оценки лабораторной картины нужен более полный набор данных.",
            "conclusion_insufficient": "Интерпретация отложена до получения более полных результатов.",
            "main_normal": "Значимых гематологических отклонений не выявлено.",
            "short_normal": "Показатели общего анализа крови в пределах референса, а реактивные клеточные маркеры не указывают на лимфопению или другое гематологическое нарушение.",
            "meaning_normal": "По текущим данным нет признаков анемии, лимфопении, нейтропении, тромбоцитопении или другого клинически значимого гематологического паттерна.",
            "conclusion_normal": "В целом гематологический профиль выглядит стабильным.",
            "main_anemia": "Данные соответствуют анемии.",
            "short_anemia": "Подтвержденные отклонения затрагивают маркеры: {markers}.",
            "meaning_anemia": "Гемоглобин ниже референса, что поддерживает анемический характер изменений.",
            "main_macrocytic_anemia": "Данные соответствуют макроцитарной анемии.",
            "short_macrocytic_anemia": "Текущие отклонения поддерживают макроцитарную анемию, включая {markers}.",
            "meaning_macrocytic_anemia": "Низкий гемоглобин вместе с низкими RBC/гематокритом и высоким MCV формирует полный макроцитарный анемический паттерн.",
            "main_supported_markers": "Основные отклонения связаны с маркерами: {markers}.",
            "short_supported_markers": "Текущие результаты указывают на {claims}.",
            "meaning_supported_markers": "Эти выводы основаны на отклонениях, отмеченных в показателях: {markers}.",
            "conclusion_supported": "В целом выявленные изменения ограничиваются: {claims}.",
            "next_urgent": "С учетом выраженности текущих изменений рекомендуется срочная медицинская оценка.",
            "next_medical_review": "На основании текущих результатов рекомендуется медицинская оценка.",
            "next_follow_up": "При клинической необходимости пересдайте или перепроверьте маркеры: {markers}.",
            "next_none": "Немедленных дополнительных действий не требуется.",
            "next_data_review": "Повторно загрузите отчет или проверьте извлеченные значения перед интерпретацией.",
            "no_claims": "нет подтвержденного диагноза",
            "claim_anemia": "анемию",
            "claim_lymphopenia": "лимфопению",
            "claim_neutropenia": "нейтропению",
            "claim_thrombocytopenia": "тромбоцитопению",
            "claim_macrocytosis": "макроцитоз",
            "claim_macrocytic_anemia": "макроцитарную анемию",
            "claim_vitamin_d_deficiency": "дефицит витамина D",
            "claim_zinc_deficiency": "дефицит цинка",
        },
        "es": {
            "status_normal": "Normal",
            "status_mild": "Desviación leve",
            "status_moderate": "Desviación moderada",
            "status_significant": "Desviación significativa",
            "status_critical": "Desviación crítica",
            "status_insufficient": "Datos insuficientes",
            "status_normal_explanation": "Los resultados están en rango o no respaldan una anomalía clínicamente relevante.",
            "status_mild_explanation": "Solo hay desviaciones leves.",
            "status_moderate_explanation": "Los resultados respaldan una anomalía clínica moderada.",
            "status_significant_explanation": "Los resultados respaldan una anomalía clínica significativa.",
            "status_critical_explanation": "Los resultados respaldan una anomalía clínica crítica.",
            "main_insufficient": "Datos extraídos insuficientes.",
            "short_insufficient": "Los resultados disponibles no son suficientes para una interpretación clínica fiable.",
            "meaning_insufficient": "Se necesita un conjunto de datos más completo para valorar el patrón de laboratorio con seguridad.",
            "conclusion_insufficient": "La interpretación se difiere hasta contar con resultados más completos.",
            "main_normal": "No hay una anomalía hematológica significativa.",
            "short_normal": "El hemograma está dentro del rango de referencia y los marcadores celulares reactivos no sugieren linfopenia ni otro trastorno hematológico.",
            "meaning_normal": "Los resultados actuales no muestran anemia, linfopenia, neutropenia, trombocitopenia ni otro patrón hematológico clínicamente relevante.",
            "conclusion_normal": "En conjunto, el perfil hematológico parece estable.",
            "main_anemia": "Los hallazgos son compatibles con anemia.",
            "short_anemia": "Las alteraciones respaldadas incluyen {markers}.",
            "meaning_anemia": "La hemoglobina está por debajo del rango de referencia, lo que respalda un patrón anémico.",
            "main_macrocytic_anemia": "Los hallazgos son compatibles con anemia macrocítica.",
            "short_macrocytic_anemia": "Las alteraciones actuales respaldan anemia macrocítica, incluyendo {markers}.",
            "meaning_macrocytic_anemia": "La hemoglobina baja con RBC/hematocrito bajos y MCV alto forma un patrón completo de anemia macrocítica.",
            "main_supported_markers": "Las principales desviaciones afectan a {markers}.",
            "short_supported_markers": "Los resultados actuales respaldan {claims}.",
            "meaning_supported_markers": "Estas conclusiones se basan en los marcadores alterados identificados en el informe: {markers}.",
            "conclusion_supported": "En conjunto, las alteraciones se limitan a {claims}.",
            "next_urgent": "Se recomienda evaluación médica urgente según la gravedad de los hallazgos actuales.",
            "next_medical_review": "Se recomienda valoración médica según los hallazgos actuales.",
            "next_follow_up": "Repite o revisa los marcadores listados si es clínicamente necesario: {markers}.",
            "next_none": "No se requiere seguimiento inmediato.",
            "next_data_review": "Vuelve a subir el informe o verifica los valores extraídos antes de interpretar.",
            "no_claims": "sin diagnóstico respaldado",
            "claim_anemia": "anemia",
            "claim_lymphopenia": "linfopenia",
            "claim_neutropenia": "neutropenia",
            "claim_thrombocytopenia": "trombocitopenia",
            "claim_macrocytosis": "macrocitosis",
            "claim_macrocytic_anemia": "anemia macrocítica",
            "claim_vitamin_d_deficiency": "deficiencia de vitamina D",
            "claim_zinc_deficiency": "deficiencia de zinc",
        },
    }
    return templates.get(language, templates["en"])
