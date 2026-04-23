import sys

sys.path.insert(0, "/opt/labsense/backend")

from interpreter.risk import assess_risk, compute_risk_status


def test_normal_case_stays_normal() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 145,
            "WBC": 6.2,
            "Platelets": 250,
            "Glucose": 4.9,
            "Vitamin D (25-OH)": 35,
        }
    )

    assert result["label"] == "Normal"
    assert result["color_key"] == "green"
    assert result["priority_notes"] == []


def test_vitamin_d_deficiency_maps_to_borderline() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 145,
            "WBC": 6.2,
            "Vitamin D (25-OH)": 24,
        }
    )

    assert result["label"] == "Needs observation"
    assert result["color_key"] == "yellow"
    assert result["priority_notes"] == ["Vitamin D (25-OH) is below range."]


def test_anemia_maps_to_significant() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 108,
            "WBC": 6.2,
            "Platelets": 250,
        }
    )

    assert result["label"] == "Significant deviation"
    assert result["color_key"] == "red"
    assert result["priority_notes"] == ["Hemoglobin is below range."]


def test_isolated_mild_wbc_abnormality_stays_borderline() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 145,
            "WBC": 6.2,
            "Lymphocytes %": 17,
            "Platelets": 250,
            "ESR": 12,
        }
    )

    assert result["label"] == "Needs observation"
    assert result["color_key"] == "yellow"
    assert result["priority_notes"] == ["Lymphocytes % is below range."]


def test_isolated_basophil_elevation_stays_borderline() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 145,
            "WBC": 6.2,
            "Basophils %": 1.8,
            "Platelets": 250,
            "ESR": 12,
        }
    )

    assert result["label"] == "Needs observation"
    assert result["color_key"] == "yellow"
    assert result["priority_notes"] == ["Basophils % is above range."]


def test_multiple_mild_relevant_abnormalities_can_be_significant() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 145,
            "WBC": 6.2,
            "Lymphocytes %": 17,
            "Eosinophils %": 7,
            "Platelets": 250,
            "ESR": 12,
        }
    )

    assert result["label"] == "Significant deviation"
    assert result["color_key"] == "red"


def test_secondary_wbc_differential_abnormalities_are_surfaceable() -> None:
    result = compute_risk_status(
        {
            "language": "en",
            "Hemoglobin": 108,
            "WBC": 6.2,
            "Platelets": 250,
            "ESR": 12,
            "Lymphocytes %": 17,
            "Eosinophils %": 7,
        }
    )

    assert result["label"] == "Significant deviation"
    assert "Hemoglobin is below range." in result["priority_notes"]


def test_assess_risk_includes_lymphocyte_and_eosinophil_secondary_notes() -> None:
    _, _, all_notes = assess_risk(
        {
            "language": "en",
            "Hemoglobin": 108,
            "WBC": 6.2,
            "Platelets": 250,
            "ESR": 12,
            "Lymphocytes %": 17,
            "Eosinophils %": 7,
        },
        "en",
    )

    assert "Lymphocytes % is below range." in all_notes
    assert "Eosinophils % is above range." in all_notes
