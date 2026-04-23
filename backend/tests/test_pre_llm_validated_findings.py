import sys
from types import ModuleType
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

fastapi_stub = ModuleType("fastapi")


class _HTTPException(Exception):
    pass


class _UploadFile:
    pass


fastapi_stub.HTTPException = _HTTPException
fastapi_stub.UploadFile = _UploadFile
sys.modules.setdefault("fastapi", fastapi_stub)

import api.services as api_services


def _fake_interpreter_module() -> ModuleType:
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        validated = payload["__validated_findings__"]
        claims = set(validated["allowed_claims"])
        if "macrocytic_anemia" in claims:
            return "Severe macrocytic anemia detected."
        if claims == {"vitamin_d_deficiency", "zinc_deficiency"}:
            return "Vitamin D and zinc deficiency without hematologic diagnosis."
        if "lymphopenia" in claims:
            return "Lymphopenia detected."
        if claims == set():
            return "Normal CBC with stable hematologic markers."
        return f"Validated claims: {sorted(claims)}"

    fake_analyze.generate_interpretation = fake_generate_interpretation
    return fake_analyze


def test_normal_cbc_validated_findings_remain_empty_of_false_diagnoses() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "en",
                "Hemoglobin": 145,
                "RBC": 4.8,
                "Hematocrit": 43,
                "Lymphocytes %": 32.7,
                "Lymphocytes abs.": 2.01,
                "WBC": 6.2,
                "Platelets": 250,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "anemia" not in interpretation
    assert "lymphopenia" not in interpretation


def test_vitamin_d_and_zinc_only_stay_independent_pre_llm_findings() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
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

    interpretation = str(result["interpretation"]).lower()
    assert "vitamin d" in interpretation
    assert "zinc" in interpretation
    assert "lymphopenia" not in interpretation
    assert "anemia" not in interpretation


def test_severe_macrocytic_anemia_is_available_pre_llm() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
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
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "macrocytic anemia" in interpretation


def test_re_lymp_presence_without_low_lym_does_not_create_lymphopenia_pre_llm() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
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
                "AS-LYMP abs": 0.01,
                "NRBC": 0.0,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "lymphopenia" not in interpretation
    assert "anemia" not in interpretation


def test_first_wave_chemistry_normal_panel_stays_normal_pre_llm() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "en",
                "Glucose": 5.2,
                "Creatinine": 90,
                "eGFR": 96,
                "Sodium": 140,
                "Potassium": 4.2,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "normal" in interpretation
    assert "kidney" not in interpretation
    assert "alarm" not in interpretation
    assert "abnormal" not in interpretation


def test_first_wave_hba1c_normal_panel_stays_normal_pre_llm() -> None:
    fake_analyze = _fake_interpreter_module()
    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "en",
                "HbA1c": 5.4,
                "Glucose": 5.2,
                "Creatinine": 90,
                "eGFR": 96,
                "Sodium": 140,
                "Potassium": 4.2,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "normal" in interpretation
    assert "abnormal" not in interpretation
    assert "diabetes" not in interpretation
