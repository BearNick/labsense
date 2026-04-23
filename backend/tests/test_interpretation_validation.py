import sys

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

import api.services as api_services
import app.services.interpretation_service as interpretation_service_module
from app.services.interpretation_validation import plan_decision, validate_before_interpretation


def test_validator_flags_impossible_and_extreme_values() -> None:
    result = validate_before_interpretation(
        {
            "language": "en",
            "RBC": 0,
            "Platelets": 2501,
            "Hemoglobin": 25,
        }
    )

    assert result is not None
    assert result.outcome == "extraction_issue"
    assert result.message == (
        "Possible extraction error detected in the lab values. "
        "Please re-upload the report or check the values manually."
    )
    assert {issue.marker for issue in result.issues} == {"RBC", "Platelets", "Hemoglobin"}


def test_api_interpretation_short_circuits_on_invalid_values(monkeypatch) -> None:
    monkeypatch.setenv("LABSENSE_ENABLE_VALIDATION_HARD_STOP", "1")
    called = {"interpret": False, "risk": False}

    def fake_generate_interpretation(payload):
        called["interpret"] = True
        return "should not run"

    def fake_compute_risk_status(payload, language):
        called["risk"] = True
        return {"label": "Normal", "color_key": "green", "explanation": "", "priority_notes": []}

    monkeypatch.setattr("interpreter.analyze.generate_interpretation", fake_generate_interpretation)
    monkeypatch.setattr("interpreter.risk.compute_risk_status", fake_compute_risk_status)

    payload = {"language": "en", "RBC": 0, "Platelets": 250}

    text = api_services.interpret_lab_data(payload)
    risk_status = api_services.build_risk_status(payload)

    assert text == (
        "Possible extraction error detected in the lab values. "
        "Please re-upload the report or check the values manually."
    )
    assert risk_status is None
    assert called == {"interpret": False, "risk": False}


def test_api_interpretation_stops_when_extracted_marker_count_is_below_threshold(monkeypatch) -> None:
    called = {"interpret": False, "risk": False}

    def fake_generate_interpretation(payload):
        called["interpret"] = True
        return "should not run"

    def fake_compute_risk_status(payload, language):
        called["risk"] = True
        return {"label": "Normal", "color_key": "green", "explanation": "", "priority_notes": []}

    monkeypatch.setattr("interpreter.analyze.generate_interpretation", fake_generate_interpretation)
    monkeypatch.setattr("interpreter.risk.compute_risk_status", fake_compute_risk_status)

    payload = {"language": "ru", "Hemoglobin": 142, "WBC": 6.1}

    text = api_services.interpret_lab_data(payload)
    risk_status = api_services.build_risk_status(payload)
    flow = api_services.execute_interpretation_flow(payload)

    assert text == "Не удалось корректно извлечь данные из отчёта"
    assert risk_status is None
    assert flow["interpretation"] == "Не удалось корректно извлечь данные из отчёта"
    assert flow["plan"].gating_reasons == ["insufficient_extracted_markers"]
    assert called == {"interpret": False, "risk": False}


def test_plan_decision_limits_partial_low_confidence_extraction() -> None:
    plan = plan_decision(
        {
            "language": "en",
            "Hemoglobin": 142,
            "WBC": 6.1,
        },
        {
            "extracted_count": 2,
            "confidence_score": 48,
            "confidence_level": "low",
            "reference_coverage": 0.2,
            "structural_consistency": 0.4,
        },
    )

    assert plan.kind == "limited"
    assert plan.allow_interpretation is False
    assert plan.allow_severity is False
    assert plan.status_label == "Low confidence"
    assert plan.summary_overview == "Data may contain inaccuracies."
    assert plan.interpretation_message == "Data may contain inaccuracies; verify the report before interpretation."


def test_validator_marks_sparse_but_plausible_report_as_low_confidence() -> None:
    result = validate_before_interpretation(
        {
            "language": "ru",
            "Hemoglobin": 142,
            "WBC": 6.1,
        },
        {
            "extracted_count": 2,
            "confidence_level": "low",
            "structural_consistency": 0.41,
        },
    )

    assert result is not None
    assert result.outcome == "low_confidence"
    assert result.message == "данные могут содержать неточности"


def test_plan_decision_keeps_severe_but_consistent_report_in_normal_flow() -> None:
    plan = plan_decision(
        {
            "language": "en",
            "Hemoglobin": 68,
            "RBC": 2.35,
            "Hematocrit": 22,
            "WBC": 7.2,
            "Platelets": 320,
        },
        {
            "extracted_count": 5,
            "confidence_score": 84,
            "confidence_level": "high",
            "reference_coverage": 0.8,
            "structural_consistency": 0.92,
        },
    )

    assert plan.kind == "full"
    assert plan.allow_interpretation is True
    assert plan.allow_severity is True


def test_validator_treats_extreme_single_marker_with_normal_cbc_context_as_extraction_issue() -> None:
    result = validate_before_interpretation(
        {
            "language": "en",
            "Hemoglobin": 68,
            "RBC": 4.8,
            "Hematocrit": 42,
            "WBC": 6.1,
            "Platelets": 250,
        }
    )

    assert result is not None
    assert result.outcome == "extraction_issue"
    assert any(issue.reason == "conflicts with Hemoglobin" for issue in result.issues)


def test_plan_decision_allows_full_flow_for_strong_coverage() -> None:
    plan = plan_decision(
        {
            "language": "en",
            "Hemoglobin": 142,
            "RBC": 4.8,
            "Hematocrit": 43,
            "WBC": 6.1,
            "Platelets": 240,
        },
        {
            "extracted_count": 5,
            "confidence_score": 84,
            "confidence_level": "high",
            "reference_coverage": 0.8,
            "structural_consistency": 0.9,
        },
    )

    assert plan.kind == "full"
    assert plan.allow_interpretation is True
    assert plan.allow_severity is True


def test_interpretation_service_short_circuits_on_invalid_values(monkeypatch) -> None:
    monkeypatch.setenv("LABSENSE_ENABLE_VALIDATION_HARD_STOP", "1")
    called = {"interpret": False, "risk": False}

    def fake_generate_interpretation(payload):
        called["interpret"] = True
        return "should not run"

    def fake_compute_risk_status(payload, language):
        called["risk"] = True
        return {"label": "Normal", "color_key": "green", "explanation": "", "priority_notes": []}

    monkeypatch.setattr(interpretation_service_module, "generate_interpretation", fake_generate_interpretation)
    monkeypatch.setattr(interpretation_service_module, "compute_risk_status", fake_compute_risk_status)

    result = interpretation_service_module.InterpretationService().interpret(
        {"language": "en", "Hemoglobin": 20}
    )

    assert result.summary == (
        "Possible extraction error detected in the lab values. "
        "Please re-upload the report or check the values manually."
    )
    assert result.risk_status is None
    assert result.meta["decision_kind"] == "extraction_issue"
    assert called == {"interpret": False, "risk": False}


def test_hard_stop_validation_is_bypassed_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LABSENSE_ENABLE_VALIDATION_HARD_STOP", raising=False)

    plan = plan_decision(
        {
            "language": "ru",
            "RBC": 0,
            "Platelets": 29810,
            "Hemoglobin": 25,
            "Hematocrit": 44,
        },
        {
            "extracted_count": 4,
            "confidence_score": 72,
            "confidence_level": "medium",
            "reference_coverage": 0.75,
            "structural_consistency": 0.9,
        },
    )

    assert plan.kind == "limited"
    assert plan.allow_interpretation is True
    assert plan.allow_severity is True
    assert plan.hide_marker_counts is False
    assert plan.hide_priority_notes is False
    assert "hard_stop_validation_bypassed" in plan.gating_reasons
    assert plan.status_label == "Низкая уверенность"


def test_interpretation_service_allows_low_confidence_reports(monkeypatch) -> None:
    called = {"interpret": False, "risk": False}

    def fake_generate_interpretation(payload):
        called["interpret"] = True
        return "Interpretation stays available."

    def fake_compute_risk_status(payload, language):
        called["risk"] = True
        return {"label": "Needs observation", "color_key": "yellow", "explanation": "", "priority_notes": []}

    monkeypatch.setattr(interpretation_service_module, "generate_interpretation", fake_generate_interpretation)
    monkeypatch.setattr(interpretation_service_module, "compute_risk_status", fake_compute_risk_status)

    result = interpretation_service_module.InterpretationService().interpret(
        {"language": "ru", "Hemoglobin": 142, "WBC": 6.1},
        {"extracted_count": 2, "confidence_level": "low", "structural_consistency": 0.41},
    )

    assert result.summary == "данные могут содержать неточности; требуется проверка перед интерпретацией"
    assert result.risk_status is None
    assert result.meta["decision_kind"] == "limited"
    assert result.meta["summary_overview"] == "данные могут содержать неточности"
    assert result.meta["hide_marker_counts"] is False
    assert result.meta["hide_priority_notes"] is False
    assert called == {"interpret": False, "risk": False}
