from __future__ import annotations

import sys
from dataclasses import dataclass
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


@dataclass(frozen=True)
class GoldenFixture:
    name: str
    category: str
    language: str
    extracted_raw_values: dict[str, object]
    expected_extraction: dict[str, float | None]
    expected_payload: dict[str, object]
    interpretation_must_contain: tuple[str, ...]
    interpretation_must_not_contain: tuple[str, ...]


class DummyUpload:
    def __init__(self, content: bytes, filename: str = "report.pdf") -> None:
        self.file = BytesIO(content)
        self.filename = filename


def _golden_fixtures() -> list[GoldenFixture]:
    return [
        GoldenFixture(
            name="normal_cbc",
            category="normal CBC",
            language="en",
            extracted_raw_values={
                "HGB": 148.1,
                "RBC": 4.98,
                "HCT": 41.6,
                "WBC": 4.19,
                "PLT": 298.0,
                "LYM %": 32.70,
                "LYM abs": 2.01,
            },
            expected_extraction={
                "HCT": 41.6,
                "HGB": 148.1,
                "LYM %": 32.70,
                "LYM abs": 2.01,
                "PLT": 298.0,
                "RBC": 4.98,
                "WBC": 4.19,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "en",
                "Гематокрит": 41.6,
                "Гемоглобин": 148.1,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Тромбоциты": 298.0,
                "Эритроциты": 4.98,
            },
            interpretation_must_contain=("normal cbc",),
            interpretation_must_not_contain=("anemia", "lymphopen"),
        ),
        GoldenFixture(
            name="cbc_vitamin_d_zinc",
            category="CBC + vitamin D + zinc",
            language="en",
            extracted_raw_values={
                "HGB": 148.1,
                "RBC": 4.98,
                "HCT": 41.6,
                "WBC": 4.19,
                "PLT": 298.0,
                "LYM %": 32.70,
                "LYM abs": 2.01,
                "Vitamin D (25-OH)": 29.0,
                "Zinc": 8.5,
            },
            expected_extraction={
                "HCT": 41.6,
                "HGB": 148.1,
                "LYM %": 32.70,
                "LYM abs": 2.01,
                "PLT": 298.0,
                "RBC": 4.98,
                "Vitamin D (25-OH)": 29.0,
                "WBC": 4.19,
                "Zinc": 8.5,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "en",
                "Витамин D (25-OH)": 29.0,
                "Гематокрит": 41.6,
                "Гемоглобин": 148.1,
                "Лейкоциты": 4.19,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Тромбоциты": 298.0,
                "Цинк": 8.5,
                "Эритроциты": 4.98,
            },
            interpretation_must_contain=("vitamin d", "zinc"),
            interpretation_must_not_contain=("anemia", "lymphopen"),
        ),
        GoldenFixture(
            name="severe_macrocytic_anemia",
            category="severe macrocytic anemia",
            language="en",
            extracted_raw_values={
                "Hemoglobin": 82,
                "RBC": 2.6,
                "Hematocrit": 26,
                "MCV": 108,
                "MCH": 35.2,
                "RDW": 16.8,
                "WBC": 6.1,
                "Platelets": 220,
            },
            expected_extraction={
                "Hematocrit": 26.0,
                "Hemoglobin": 82.0,
                "MCH": 35.2,
                "MCV": 108.0,
                "Platelets": 220.0,
                "RBC": 2.6,
                "RDW": 16.8,
                "WBC": 6.1,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "en",
                "MCH": 35.2,
                "MCV": 108.0,
                "RDW": 16.8,
                "Гематокрит": 26.0,
                "Гемоглобин": 82.0,
                "Лейкоциты": 6.1,
                "Тромбоциты": 220.0,
                "Эритроциты": 2.6,
            },
            interpretation_must_contain=("severe macrocytic anemia",),
            interpretation_must_not_contain=(),
        ),
        GoldenFixture(
            name="mixed_differential",
            category="mixed differential with LYM/RE-LYMP/AS-LYMP/NRBC",
            language="en",
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
            expected_extraction={
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
                "language": "en",
                "AS-LYMP %": 0.40,
                "AS-LYMP abs": 0.01,
                "NRBC": 0.0,
                "RE-LYMP %": 1.10,
                "RE-LYMP abs": 0.08,
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 2.01,
                "Эритроциты": 4.98,
            },
            interpretation_must_contain=("normal lymphocyte profile", "re-lymp", "as-lymp", "nrbc"),
            interpretation_must_not_contain=("anemia", "lymphopen"),
        ),
        GoldenFixture(
            name="thyroid_case",
            category="thyroid chemistry",
            language="en",
            extracted_raw_values={
                "TSH": 2.1,
                "Free T4": 14.2,
                "Anti-thyroid peroxidase antibodies (anti-TPO)": 18.0,
                "Glucose": 5.1,
                "Creatinine": 84.0,
            },
            expected_extraction={
                "Anti-thyroid peroxidase antibodies (anti-TPO)": 18.0,
                "Creatinine": 84.0,
                "Free T4": 14.2,
                "Glucose": 5.1,
                "TSH": 2.1,
            },
            expected_payload={
                "age": 30,
                "gender": "female",
                "language": "en",
                "Anti-thyroid peroxidase antibodies (anti-TPO)": 18.0,
                "Free T4": 14.2,
                "TSH": 2.1,
                "Глюкоза": 5.1,
                "Креатинин": 84.0,
            },
            interpretation_must_contain=("thyroid and chemistry markers are stable",),
            interpretation_must_not_contain=("anemia", "lymphopen"),
        ),
    ]


def _build_fake_interpreter() -> ModuleType:
    fake_analyze = ModuleType("interpreter.analyze")

    def fake_generate_interpretation(payload: dict[str, object]) -> str:
        hemoglobin = payload.get("Hemoglobin", payload.get("HGB", payload.get("Гемоглобин")))
        hematocrit = payload.get("Hematocrit", payload.get("HCT", payload.get("Гематокрит")))
        rbc = payload.get("RBC", payload.get("Эритроциты"))
        mcv = payload.get("MCV")
        lymph_percent = payload.get("LYM %", payload.get("Lymphocytes %"))
        lymph_abs = payload.get("LYM abs", payload.get("Lymphocytes abs.", payload.get("Лимфоциты абс.")))
        if lymph_percent is None:
            lymph_percent = payload.get("Лимфоциты %")
        platelets = payload.get("Platelets", payload.get("Тромбоциты"))
        vitamin_d = payload.get("Vitamin D (25-OH)", payload.get("Витамин D (25-OH)"))
        zinc = payload.get("Zinc", payload.get("Цинк"))
        tsh = payload.get("TSH")
        free_t4 = payload.get("Free T4")
        glucose = payload.get("Glucose", payload.get("Глюкоза"))
        creatinine = payload.get("Creatinine", payload.get("Креатинин"))

        if all(
            isinstance(value, (int, float))
            for value in (hemoglobin, hematocrit, rbc, mcv, platelets)
        ) and float(hemoglobin) < 100 and float(hematocrit) < 30 and float(rbc) < 3.0 and float(mcv) > 100:
            return "Severe macrocytic anemia detected."

        if all(
            isinstance(value, (int, float))
            for value in (lymph_percent, lymph_abs)
        ) and 20 <= float(lymph_percent) <= 45 and 1.0 <= float(lymph_abs) <= 4.8:
            if "RE-LYMP abs" in payload or "AS-LYMP abs" in payload or "NRBC" in payload:
                return "Normal lymphocyte profile with RE-LYMP, AS-LYMP, and NRBC preserved."

        if isinstance(vitamin_d, (int, float)) and isinstance(zinc, (int, float)) and float(vitamin_d) < 30 and float(zinc) < 10.7:
            return "Vitamin D and zinc remain present as mild nutritional deviations."

        if all(isinstance(value, (int, float)) for value in (tsh, free_t4, glucose, creatinine)):
            return "Thyroid and chemistry markers are stable."

        return "Normal CBC with stable red-cell and lymphocyte values."

    fake_analyze.generate_interpretation = fake_generate_interpretation
    return fake_analyze


def test_golden_fixtures_cover_required_categories() -> None:
    categories = {fixture.category for fixture in _golden_fixtures()}
    assert categories == {
        "normal CBC",
        "CBC + vitamin D + zinc",
        "severe macrocytic anemia",
        "mixed differential with LYM/RE-LYMP/AS-LYMP/NRBC",
        "thyroid chemistry",
    }


def test_golden_baseline_extraction_payload_and_interpretation() -> None:
    fake_analyze = _build_fake_interpreter()

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        for fixture in _golden_fixtures():
            parse_result = None
            with patch.object(api_services, "extract_lab_data_from_pdf", return_value=fixture.extracted_raw_values):
                parse_result = api_services.parse_lab_pdf(DummyUpload(b"pdf-bytes"), language=fixture.language)

            assert parse_result is not None
            assert parse_result.raw_values == fixture.expected_extraction
            assert parse_result.selected_source == "text"
            assert parse_result.selection_reason == "legacy_text_baseline"

            payload = api_services._normalize_interpretation_payload(
                {
                    "age": 30,
                    "gender": "female",
                    "language": fixture.language,
                    **parse_result.raw_values,
                }
            )
            assert payload == fixture.expected_payload

            result = api_services.execute_interpretation_flow(payload)
            interpretation = str(result["interpretation"]).lower()

            assert result["risk_status"] is None
            assert result["plan"].gating_reasons == ["legacy_baseline_flow"]
            for token in fixture.interpretation_must_contain:
                assert token in interpretation, (fixture.name, token, interpretation)
            for token in fixture.interpretation_must_not_contain:
                assert token not in interpretation, (fixture.name, token, interpretation)


def test_normal_cbc_has_no_false_anemia() -> None:
    fixture = next(item for item in _golden_fixtures() if item.name == "normal_cbc")
    fake_analyze = _build_fake_interpreter()

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "age": 30,
                "gender": "female",
                "language": fixture.language,
                **fixture.expected_extraction,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "anemia" not in interpretation


def test_normal_lym_values_do_not_become_false_lymphopenia() -> None:
    fixture = next(item for item in _golden_fixtures() if item.name == "mixed_differential")
    fake_analyze = _build_fake_interpreter()

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "age": 30,
                "gender": "female",
                "language": fixture.language,
                **fixture.expected_extraction,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "lymphopen" not in interpretation


def test_vitamin_d_and_zinc_remain_present_when_extracted() -> None:
    fixture = next(item for item in _golden_fixtures() if item.name == "cbc_vitamin_d_zinc")
    fake_analyze = _build_fake_interpreter()

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "age": 30,
                "gender": "female",
                "language": fixture.language,
                **fixture.expected_extraction,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "vitamin d" in interpretation
    assert "zinc" in interpretation


def test_severe_macrocytic_anemia_is_still_detected() -> None:
    fixture = next(item for item in _golden_fixtures() if item.name == "severe_macrocytic_anemia")
    fake_analyze = _build_fake_interpreter()

    with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze}):
        result = api_services.execute_interpretation_flow(
            {
                "age": 30,
                "gender": "female",
                "language": fixture.language,
                **fixture.expected_extraction,
            }
        )

    interpretation = str(result["interpretation"]).lower()
    assert "severe macrocytic anemia" in interpretation
