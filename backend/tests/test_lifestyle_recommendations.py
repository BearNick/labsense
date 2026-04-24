import sys

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

from app.services.lifestyle_recommendations import generate_lifestyle_recommendations


def test_lifestyle_recommendations_cover_low_vitamin_d() -> None:
    text = generate_lifestyle_recommendations(
        {
            "language": "en",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "WBC": 6.2,
            "Platelets": 250,
            "Vitamin D (25-OH)": 24,
        },
        language="en",
    )

    assert text is not None
    assert "What matters now" in text
    assert "Nutrition" in text
    assert "What to discuss with a clinician" in text
    lowered = text.lower()
    assert "vitamin d 24" in lowered
    assert "daylight" in lowered or "fortified" in lowered
    assert "supplementation" in lowered


def test_lifestyle_recommendations_cover_macrocytic_anemia_safely() -> None:
    text = generate_lifestyle_recommendations(
        {
            "language": "en",
            "Hemoglobin": 82,
            "RBC": 2.6,
            "Hematocrit": 26,
            "MCV": 108,
            "MCH": 35.2,
            "RDW": 16.8,
            "WBC": 6.1,
            "Platelets": 220,
        },
        language="en",
    )

    assert text is not None
    assert "Physical activity" in text
    assert "Sleep and recovery" in text
    lowered = text.lower()
    assert "macrocytic anemia pattern" in lowered
    assert "avoid intense exercise" in lowered
    assert "vitamin b12 and folate testing" in lowered
    assert "starting treatment on your own" not in lowered


def test_lifestyle_recommendations_stay_minimal_for_normal_report() -> None:
    text = generate_lifestyle_recommendations(
        {
            "language": "en",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "Lymphocytes %": 32.7,
            "Lymphocytes abs.": 2.01,
            "WBC": 6.2,
            "Platelets": 250,
        },
        language="en",
    )

    assert text is not None
    assert "What matters now" in text
    assert "Nutrition" not in text
    lowered = text.lower()
    assert "no confirmed out-of-range markers" in lowered
    assert "consistent sleep" in lowered or "sleep" in lowered
    assert "walking" in lowered


def test_lifestyle_recommendations_follow_russian_language() -> None:
    text = generate_lifestyle_recommendations(
        {
            "language": "ru",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "WBC": 6.2,
            "Platelets": 250,
            "Vitamin D (25-OH)": 24,
        },
        language="ru",
    )

    assert text is not None
    assert "Что важно сейчас" in text
    assert "Питание" in text
    assert "Что обсудить с врачом" in text
    assert "витамин D 24" in text
    assert "Имеет смысл обсудить повторный контроль витамина D" in text
    assert "These suggestions are supportive only" not in text


def test_lifestyle_recommendations_follow_spanish_language() -> None:
    text = generate_lifestyle_recommendations(
        {
            "language": "es",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "WBC": 6.2,
            "Platelets": 250,
            "Vitamin D (25-OH)": 24,
        },
        language="es",
    )

    assert text is not None
    assert "Qué importa ahora" in text
    assert "Nutrición" in text
    assert "Qué comentar con un profesional" in text
    assert "vitamina D 24" in text
    assert "Puede ser útil comentar la repetición del análisis de vitamina D" in text
    assert "These suggestions are supportive only" not in text
