import sys
from io import BytesIO
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


class DummyUpload:
    def __init__(self, content: bytes, filename: str = "report.pdf") -> None:
        self.file = BytesIO(content)
        self.filename = filename


def test_parse_lab_pdf_uses_legacy_text_baseline() -> None:
    with patch.object(api_services, "extract_lab_data_from_pdf", return_value={"HGB": 145, "WBC": 6.1}):
        result = api_services.parse_lab_pdf(DummyUpload(b"pdf-bytes"), language="en")

    assert result.raw_values == {"HGB": 145, "WBC": 6.1}
    assert result.selected_source == "text"
    assert result.initial_source == "text"
    assert result.final_source == "text"
    assert result.selection_reason == "legacy_text_baseline"
    assert result.fallback_used is False
    assert result.confidence_reasons == ["legacy_text_baseline"]


def test_execute_interpretation_flow_returns_raw_llm_output_without_backend_rewrite() -> None:
    captured: dict[str, object] = {}
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        captured.update(payload)
        return "legacy baseline output"

    fake_analyze.generate_interpretation = fake_generate_interpretation

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "ru",
                "Эритроциты": 4.98,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "RE-LYMP abs": 0.08,
                "Витамин D (25-OH)": 29,
            }
        )

    assert result["interpretation"] == "legacy baseline output"
    assert result["risk_status"] is None
    assert result["plan"].gating_reasons == ["legacy_baseline_flow"]
    assert captured["Лимфоциты %"] == 32.70
    assert captured["Лимфоциты абс."] == 2.01
    assert captured["RE-LYMP abs"] == 0.08


def test_baseline_payload_normalization_canonicalizes_common_cbc_aliases() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "age": 30,
            "gender": "female",
            "language": "ru",
            "HGB": 148.1,
            "HCT": 41.6,
            "RBC": 4.98,
            "WBC": 4.19,
            "PLT": 298.0,
            "LYM %": 32.7,
            "LYM abs": 2.01,
            "Vitamin D (25-OH)": 29.0,
            "Zinc": 8.5,
        }
    )

    assert payload == {
        "age": 30,
        "gender": "female",
        "language": "ru",
        "Витамин D (25-OH)": 29.0,
        "Гемоглобин": 148.1,
        "Гематокрит": 41.6,
        "Лейкоциты": 4.19,
        "Лимфоциты %": 32.7,
        "Лимфоциты абс.": 2.01,
        "Тромбоциты": 298.0,
        "Цинк": 8.5,
        "Эритроциты": 4.98,
    }


def test_baseline_payload_keeps_rbc_and_nrbc_separate() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "language": "ru",
            "RBC": 4.98,
            "NRBC": 0.00,
        }
    )

    assert payload["Эритроциты"] == 4.98
    assert payload["NRBC"] == 0.00


def test_queue3_coverage_only_markers_survive_to_final_response_meta_and_do_not_trigger_llm() -> None:
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        raise AssertionError("Coverage-only marker payloads should be gated before LLM interpretation.")

    fake_analyze.generate_interpretation = fake_generate_interpretation

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
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

    assert "not enabled" in result["interpretation"].lower()
    assert result["risk_status"] is None
    assert result["plan"].gating_reasons == ["legacy_baseline_flow", "coverage_only_markers_present"]
    assert result["meta"]["payload_markers"] == result["meta"]["display_markers"]
    assert set(result["meta"]["coverage_only_markers"]) == {
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
    assert result["validated_findings"]["allowed_claims"] == []
    assert result["validated_findings"]["payload_markers"] == result["meta"]["payload_markers"]
    assert result["validated_findings"]["display_markers"] == result["meta"]["display_markers"]


def test_queue3_gate_does_not_change_existing_cbc_interpretation_path() -> None:
    captured: dict[str, object] = {}
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        captured.update(payload)
        return "cbc baseline output"

    fake_analyze.generate_interpretation = fake_generate_interpretation

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "en",
                "HGB": 145,
                "RBC": 4.8,
                "HCT": 43,
                "WBC": 6.2,
                "PLT": 250,
                "LYM %": 32.7,
                "LYM abs": 2.01,
            }
        )

    assert result["interpretation"] == "cbc baseline output"
    assert result["plan"].gating_reasons == ["legacy_baseline_flow"]
    assert "coverage_only_markers_present" not in result["meta"]["gating_reasons"]
    assert captured["Гемоглобин"] == 145.0
    assert captured["Эритроциты"] == 4.8
    assert captured["Гематокрит"] == 43.0
    assert captured["Лейкоциты"] == 6.2
    assert captured["Тромбоциты"] == 250.0


def test_first_wave_chemistry_markers_are_not_coverage_gated() -> None:
    captured: dict[str, object] = {}
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        captured.update(payload)
        return "first wave chemistry output"

    fake_analyze.generate_interpretation = fake_generate_interpretation

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "language": "en",
                "Na": 140,
                "K": 4.2,
                "Glucose": 5.2,
                "Cr": 90,
                "eGFR": 96,
            }
        )

    assert result["interpretation"] == "first wave chemistry output"
    assert result["plan"].gating_reasons == ["legacy_baseline_flow"]
    assert result["meta"]["coverage_only_markers"] == []
    assert set(result["meta"]["supported_reasoning_markers_present"]) == {
        "Натрий",
        "Калий",
        "Глюкоза",
        "Креатинин",
        "eGFR",
    }
    assert captured["Натрий"] == 140.0
    assert captured["Калий"] == 4.2
    assert captured["Глюкоза"] == 5.2
    assert captured["Креатинин"] == 90.0
    assert captured["eGFR"] == 96.0


def test_baseline_payload_keeps_lym_percent_and_absolute_separate() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "language": "ru",
            "LYM %": 32.70,
            "LYM abs": 2.01,
        }
    )

    assert payload["Лимфоциты %"] == 32.70
    assert payload["Лимфоциты абс."] == 2.01
    assert payload["Лимфоциты %"] != payload["Лимфоциты абс."]


def test_baseline_payload_keeps_lym_and_re_lymp_separate() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "language": "ru",
            "LYM %": 32.70,
            "RE-LYMP abs": 0.08,
        }
    )

    assert payload["Лимфоциты %"] == 32.70
    assert payload["RE-LYMP abs"] == 0.08
    assert payload["Лимфоциты %"] != payload["RE-LYMP abs"]


def test_baseline_payload_keeps_lym_and_as_lymp_separate() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "language": "ru",
            "LYM %": 32.70,
            "AS-LYMP abs": 0.01,
        }
    )

    assert payload["Лимфоциты %"] == 32.70
    assert payload["AS-LYMP abs"] == 0.01
    assert payload["Лимфоциты %"] != payload["AS-LYMP abs"]


def test_baseline_payload_preserves_vitamin_d_and_zinc() -> None:
    payload = api_services._normalize_interpretation_payload(
        {
            "language": "ru",
            "Vitamin D (25-OH)": 29.0,
            "Zinc": 8.5,
        }
    )

    assert payload["Витамин D (25-OH)"] == 29.0
    assert payload["Цинк"] == 8.5
