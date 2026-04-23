import sys
from dataclasses import asdict

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

import app.services.interpretation_service as interpretation_service_module
from app.services.clinical_consistency import build_validated_findings, enforce_final_consistency
from interpreter.risk import assess_risk_details, compute_risk_status


def test_normal_cbc_produces_no_anemia_or_lymphopenia() -> None:
    payload = {
        "language": "en",
        "Hemoglobin": 145,
        "RBC": 4.8,
        "Hematocrit": 43,
        "Lymphocytes %": 32.7,
        "Lymphocytes abs.": 2.01,
        "WBC": 6.2,
        "Platelets": 250,
    }

    findings = build_validated_findings(payload=payload, abnormal_markers=[])
    assert findings.allowed_claims == ["normal"]
    assert findings.severity == "NORMAL"
    normalized = [asdict(marker) for marker in findings.normalized_markers]
    assert all(
        marker["status"] == "normal"
        for marker in normalized
        if marker["name"] in {"Hemoglobin", "RBC", "Hematocrit", "Lymphocytes %", "Lymphocytes abs."}
    )

    corrected, corrected_risk_status, validated_findings, issues = enforce_final_consistency(
        (
            "Overall status:\n"
            "Significant deviation\n\n"
            "Key observations:\n"
            "Main condition: Anemia with lymphopenia.\n"
            "Short explanation: Red-cell and lymphocyte markers are low.\n\n"
            "What this means:\n"
            "This is a significant blood-count abnormality.\n\n"
            "Next steps:\n"
            "Medical evaluation recommended.\n\n"
            "Final conclusion:\n"
            "Anemia with lymphopenia.\n"
        ),
        payload=payload,
        abnormal_markers=[],
        risk_status=compute_risk_status(payload, "en"),
        language="en",
    )

    assert corrected_risk_status is not None
    assert corrected_risk_status["color_key"] == "green"
    assert validated_findings["allowed_claims"] == ["normal"]
    assert "anemia" not in corrected.lower()
    assert "lymphopen" not in corrected.lower()
    assert {issue["code"] for issue in issues} >= {
        "unsupported_anemia_claim",
        "unsupported_lymphopenia_claim",
        "severity_mismatch",
        "next_steps_mismatch",
    }


def test_vitamin_d_and_zinc_case_stays_mild() -> None:
    payload = {
        "language": "en",
        "Hemoglobin": 145,
        "RBC": 4.8,
        "Hematocrit": 43,
        "Lymphocytes %": 32.7,
        "Lymphocytes abs.": 2.01,
        "WBC": 6.2,
        "Platelets": 250,
        "Vitamin D (25-OH)": 24,
        "Zinc": 8.8,
    }

    abnormal_markers = assess_risk_details(payload, "en").abnormal_markers
    findings = build_validated_findings(payload=payload, abnormal_markers=abnormal_markers)

    assert findings.micronutrient_only is True
    assert findings.severity == "MILD"
    assert set(findings.allowed_claims) == {"vitamin_d_deficiency", "zinc_deficiency", "mild"}

    corrected, corrected_risk_status, validated_findings, issues = enforce_final_consistency(
        (
            "Overall status:\n"
            "Significant deviation\n\n"
            "Key observations:\n"
            "Main condition: Immune dysfunction with lymphopenia.\n"
            "Short explanation: White-cell pattern is concerning.\n\n"
            "What this means:\n"
            "This suggests a significant immune disorder.\n\n"
            "Next steps:\n"
            "Medical evaluation recommended.\n\n"
            "Final conclusion:\n"
            "Immune disorder.\n"
        ),
        payload=payload,
        abnormal_markers=abnormal_markers,
        risk_status=compute_risk_status(payload, "en"),
        language="en",
    )

    assert corrected_risk_status is not None
    assert corrected_risk_status["color_key"] == "yellow"
    assert corrected_risk_status["label"] == "Mild deviation"
    assert validated_findings["severity"] == "MILD"
    assert "vitamin d" in corrected.lower()
    assert "zinc" in corrected.lower()
    assert "no significant hematologic abnormality" in corrected.lower()
    assert "immune" not in corrected.lower()
    assert "lymphopen" not in corrected.lower()
    assert "allowed claims" not in corrected.lower()
    assert "validated findings" not in corrected.lower()
    assert "final prose is constrained" not in corrected.lower()
    assert {issue["code"] for issue in issues} >= {
        "unsupported_immune_claim",
        "unsupported_lymphopenia_claim",
        "micronutrient_case_became_immune_claim",
        "severity_mismatch",
    }


def test_macrocytic_anemia_is_detected_as_complete_pattern() -> None:
    payload = {
        "language": "en",
        "Hemoglobin": 82,
        "RBC": 2.6,
        "Hematocrit": 26,
        "MCV": 108,
        "MCH": 35.2,
        "RDW": 16.8,
        "WBC": 6.1,
        "Platelets": 220,
    }

    abnormal_markers = assess_risk_details(payload, "en").abnormal_markers
    findings = build_validated_findings(payload=payload, abnormal_markers=abnormal_markers)

    assert findings.detected_patterns == ["macrocytic_anemia"]
    assert set(findings.allowed_claims) == {"anemia", "macrocytosis", "macrocytic_anemia", "significant"}
    assert findings.severity == "SIGNIFICANT"

    interpretation = (
        "Overall status:\n"
        "Significant deviation\n\n"
        "Key observations:\n"
        "Main condition: Severe macrocytic anemia.\n"
        "Short explanation: Hemoglobin is markedly low with macrocytosis.\n\n"
        "What this means:\n"
        "This is a significant red-cell pattern.\n\n"
        "Next steps:\n"
        "Medical evaluation recommended.\n\n"
        "Final conclusion:\n"
        "Severe macrocytic anemia.\n"
    )

    corrected, corrected_risk_status, validated_findings, issues = enforce_final_consistency(
        interpretation,
        payload=payload,
        abnormal_markers=abnormal_markers,
        risk_status=compute_risk_status(payload, "en"),
        language="en",
    )

    assert issues == []
    assert corrected == interpretation
    assert corrected_risk_status is not None
    assert corrected_risk_status["color_key"] == "red"
    assert validated_findings["detected_patterns"] == ["macrocytic_anemia"]


def test_re_lymp_presence_does_not_trigger_lymphopenia() -> None:
    payload = {
        "language": "en",
        "Hemoglobin": 145,
        "RBC": 4.8,
        "Hematocrit": 43,
        "Lymphocytes %": 32.7,
        "Lymphocytes abs.": 2.01,
        "WBC": 6.2,
        "Platelets": 250,
        "RE-LYMP abs": 0.08,
        "RE-LYMP %": 1.10,
        "NRBC": 0.0,
    }

    findings = build_validated_findings(payload=payload, abnormal_markers=[])
    assert "lymphopenia" not in findings.allowed_claims
    assert findings.severity == "NORMAL"

    corrected, corrected_risk_status, validated_findings, issues = enforce_final_consistency(
        (
            "Overall status:\n"
            "Moderate deviation\n\n"
            "Key observations:\n"
            "Main condition: Lymphopenia.\n"
            "Short explanation: RE-LYMP suggests a lymphocyte deficit.\n\n"
            "What this means:\n"
            "This may reflect a white-cell abnormality.\n\n"
            "Next steps:\n"
            "Medical evaluation recommended.\n\n"
            "Final conclusion:\n"
            "Lymphopenia.\n"
        ),
        payload=payload,
        abnormal_markers=[],
        risk_status=compute_risk_status(payload, "en"),
        language="en",
    )

    assert corrected_risk_status is not None
    assert corrected_risk_status["color_key"] == "green"
    assert validated_findings["allowed_claims"] == ["normal"]
    assert "lymphopen" not in corrected.lower()
    assert {issue["code"] for issue in issues} >= {
        "unsupported_lymphopenia_claim",
        "unsupported_immune_claim",
        "severity_mismatch",
    }


def test_reactive_markers_with_normal_lym_aliases_do_not_trigger_lymphopenia() -> None:
    payload = {
        "language": "en",
        "HGB": 145,
        "RBC": 4.8,
        "HCT": 43,
        "LYM %": 32.7,
        "LYM abs": 2.01,
        "WBC": 6.2,
        "PLT": 250,
        "RE-LYMP abs": 0.08,
        "RE-LYMP %": 1.10,
        "AS-LYMP abs": 0.01,
        "AS-LYMP %": 0.40,
        "NRBC": 0.0,
    }

    findings = build_validated_findings(payload=payload, abnormal_markers=[])
    assert "lymphopenia" not in findings.allowed_claims
    assert findings.severity == "NORMAL"


def test_true_lymphopenia_remains_supported() -> None:
    payload = {
        "language": "en",
        "Hemoglobin": 139,
        "RBC": 4.7,
        "Hematocrit": 41,
        "Lymphocytes %": 14.2,
        "Lymphocytes abs.": 0.76,
        "WBC": 5.3,
        "Platelets": 230,
        "RE-LYMP abs": 0.09,
        "RE-LYMP %": 1.20,
    }

    findings = build_validated_findings(payload=payload, abnormal_markers=["Lymphocytes %", "Lymphocytes abs."])
    assert "lymphopenia" in findings.allowed_claims
    assert findings.severity == "MILD"

    corrected, corrected_risk_status, validated_findings, issues = enforce_final_consistency(
        (
            "Overall status:\n"
            "Mild deviation\n\n"
            "Key observations:\n"
            "Main condition: Lymphopenia.\n"
            "Short explanation: Lymphocyte percentage and absolute count are below reference.\n\n"
            "What this means:\n"
            "This is a mild white-cell abnormality.\n\n"
            "Next steps:\n"
            "Repeat or review the listed markers if clinically needed.\n\n"
            "Final conclusion:\n"
            "Mild lymphopenia.\n"
        ),
        payload=payload,
        abnormal_markers=["Lymphocytes %", "Lymphocytes abs."],
        risk_status=compute_risk_status(payload, "en"),
        language="en",
    )

    assert issues == []
    assert corrected_risk_status is not None
    assert corrected == (
        "Overall status:\n"
        "Mild deviation\n\n"
        "Key observations:\n"
        "Main condition: Lymphopenia.\n"
        "Short explanation: Lymphocyte percentage and absolute count are below reference.\n\n"
        "What this means:\n"
        "This is a mild white-cell abnormality.\n\n"
        "Next steps:\n"
        "Repeat or review the listed markers if clinically needed.\n\n"
        "Final conclusion:\n"
        "Mild lymphopenia.\n"
    )
    assert "lymphopenia" in validated_findings["allowed_claims"]


def test_interpretation_service_exposes_validated_findings(monkeypatch) -> None:
    monkeypatch.setattr(
        interpretation_service_module,
        "generate_interpretation",
        lambda payload: (
            "Overall status:\n"
            "Significant deviation\n\n"
            "Key observations:\n"
            "Main condition: Immune dysfunction with lymphopenia.\n"
            "Short explanation: White-cell pattern is concerning.\n\n"
            "What this means:\n"
            "This suggests a significant immune disorder.\n\n"
            "Next steps:\n"
            "Medical evaluation recommended.\n\n"
            "Final conclusion:\n"
            "Immune disorder.\n"
        ),
    )

    result = interpretation_service_module.InterpretationService().interpret(
        {
            "language": "en",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "Lymphocytes %": 32.7,
            "Lymphocytes abs.": 2.01,
            "WBC": 6.2,
            "Platelets": 250,
            "Vitamin D (25-OH)": 24,
            "Zinc": 8.8,
        }
    )

    assert result.risk_status is not None
    assert result.risk_status.label == "Mild deviation"
    assert result.meta["validated_findings"]["micronutrient_only"] is True
    assert result.meta["validated_findings"]["severity"] == "MILD"
    assert set(result.meta["validated_findings"]["allowed_claims"]) == {"vitamin_d_deficiency", "zinc_deficiency", "mild"}


def test_interpretation_service_exposes_queue3_marker_integrity_without_enabling_diagnosis(monkeypatch) -> None:
    def _unexpected_llm_call(payload: dict[str, object]) -> str:
        raise AssertionError("Coverage-only marker payloads should not be interpreted yet.")

    monkeypatch.setattr(
        interpretation_service_module,
        "generate_interpretation",
        _unexpected_llm_call,
    )

    result = interpretation_service_module.InterpretationService().interpret(
        {
            "language": "en",
            "Cl": 103,
            "Urea": 5.4,
            "BUN": 14,
            "AST": 20,
            "ALT": 22,
            "Uric Acid": 320,
            "Urine Albumin": 12,
            "Urine Creatinine": 8.4,
            "ACR": 1.4,
        }
    )

    assert "not enabled" in result.summary.lower()
    assert result.meta["gating_reasons"] == ["legacy_baseline_flow", "coverage_only_markers_present"]
    assert result.meta["validated_findings"]["allowed_claims"] == []
    assert set(result.meta["coverage_only_markers"]) == {
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
