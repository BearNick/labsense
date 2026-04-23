import sys
import unittest
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
from app.services.interpretation_payload import normalize_interpretation_markers, resolve_semantic_marker
from app.services.semantic_markers import SEMANTIC_MARKER_REGISTRY
from parser.source_selection import select_and_extract_lab_data


class InterpretationPayloadTests(unittest.TestCase):
    def test_semantic_registry_defines_strict_marker_metadata(self) -> None:
        rbc = SEMANTIC_MARKER_REGISTRY["rbc"]
        nrbc = SEMANTIC_MARKER_REGISTRY["nrbc"]
        lym_percent = SEMANTIC_MARKER_REGISTRY["lym_percent"]
        re_lymp_absolute = SEMANTIC_MARKER_REGISTRY["re_lymp_absolute"]

        self.assertEqual(rbc.canonical_id, "rbc")
        self.assertEqual(rbc.interpretation_slot, "Эритроциты")
        self.assertEqual(rbc.kind, "concentration")
        self.assertIn("nrbc", rbc.must_not_merge_with)

        self.assertEqual(nrbc.interpretation_slot, "NRBC")
        self.assertEqual(nrbc.kind, "percent")
        self.assertIn("rbc", nrbc.must_not_merge_with)

        self.assertEqual(lym_percent.kind, "percent")
        self.assertEqual(re_lymp_absolute.kind, "absolute")
        self.assertIn("re_lymp_absolute", lym_percent.must_not_merge_with)

    def test_exact_alias_resolution_uses_semantic_registry(self) -> None:
        self.assertEqual(resolve_semantic_marker("RBC").canonical_id, "rbc")
        self.assertEqual(resolve_semantic_marker("NRBC").canonical_id, "nrbc")
        self.assertEqual(resolve_semantic_marker("LYM %").canonical_id, "lym_percent")
        self.assertEqual(resolve_semantic_marker("LYM abs").canonical_id, "lym_absolute")
        self.assertEqual(resolve_semantic_marker("NEU").canonical_id, "neu_percent")
        self.assertEqual(resolve_semantic_marker("ANC").canonical_id, "neu_absolute")
        self.assertEqual(resolve_semantic_marker("Na").canonical_id, "sodium")
        self.assertEqual(resolve_semantic_marker("K").canonical_id, "potassium")
        self.assertEqual(resolve_semantic_marker("Cl").canonical_id, "chloride")
        self.assertEqual(resolve_semantic_marker("Urea").canonical_id, "urea")
        self.assertEqual(resolve_semantic_marker("BUN").canonical_id, "bun")
        self.assertEqual(resolve_semantic_marker("Cr").canonical_id, "creatinine")
        self.assertEqual(resolve_semantic_marker("HbA1c").canonical_id, "hba1c")
        self.assertEqual(resolve_semantic_marker("Urine Albumin").canonical_id, "urine_albumin")
        self.assertEqual(resolve_semantic_marker("Urine Creatinine").canonical_id, "urine_creatinine")
        self.assertEqual(resolve_semantic_marker("ACR").canonical_id, "acr")
        self.assertEqual(resolve_semantic_marker("RE-LYMP abs").canonical_id, "re_lymp_absolute")
        self.assertEqual(resolve_semantic_marker("AS-LYMP abs").canonical_id, "as_lymp_absolute")
        self.assertIsNone(resolve_semantic_marker("лимф"))

    def test_new_international_markers_preserve_distinct_internal_slots(self) -> None:
        normalized = normalize_interpretation_markers(
            {
                "Na": 140,
                "K": 4.2,
                "Cl": 103,
                "Urea": 5.4,
                "BUN": 14,
                "Cr": 90,
                "eGFR": 96,
                "HbA1c": 5.4,
                "Urine Albumin": 12,
                "Urine Creatinine": 8.4,
                "ACR": 1.4,
            }
        )

        self.assertEqual(normalized["Натрий"], 140.0)
        self.assertEqual(normalized["Калий"], 4.2)
        self.assertEqual(normalized["Хлор"], 103.0)
        self.assertEqual(normalized["Мочевина"], 5.4)
        self.assertEqual(normalized["BUN"], 14.0)
        self.assertEqual(normalized["Креатинин"], 90.0)
        self.assertEqual(normalized["eGFR"], 96.0)
        self.assertEqual(normalized["HbA1c"], 5.4)
        self.assertEqual(normalized["Urine Albumin"], 12.0)
        self.assertEqual(normalized["Urine Creatinine"], 8.4)
        self.assertEqual(normalized["ACR"], 1.4)
        self.assertNotEqual(normalized["Мочевина"], normalized["BUN"])
        self.assertNotEqual(normalized["Креатинин"], normalized["Urine Creatinine"])

    def test_queue3_international_markers_survive_into_normalized_payload(self) -> None:
        payload = api_services._normalize_interpretation_payload(
            {
                "language": "en",
                "Na": 140,
                "K": 4.2,
                "Cl": 103,
                "Urea": 5.4,
                "BUN": 14,
                "Cr": 90,
                "eGFR": 96,
                "Glucose": 5.6,
                "AST": 20,
                "ALT": 22,
                "Uric Acid": 320,
                "HbA1c": 5.4,
                "Urine Albumin": 12,
                "Urine Creatinine": 8.4,
                "ACR": 1.4,
            }
        )

        assert payload["Натрий"] == 140.0
        assert payload["Калий"] == 4.2
        assert payload["Хлор"] == 103.0
        assert payload["Мочевина"] == 5.4
        assert payload["BUN"] == 14.0
        assert payload["Креатинин"] == 90.0
        assert payload["eGFR"] == 96.0
        assert payload["Глюкоза"] == 5.6
        assert payload["AST"] == 20.0
        assert payload["ALT"] == 22.0
        assert payload["Кислота мочевая"] == 320.0
        assert payload["HbA1c"] == 5.4
        assert payload["Urine Albumin"] == 12.0
        assert payload["Urine Creatinine"] == 8.4
        assert payload["ACR"] == 1.4

    def test_exact_marker_identity_is_preserved(self) -> None:
        marker_values = {
            "Эритроциты": 4.98,
            "NRBC": 0.00,
            "Лимфоциты %": 32.70,
            "Лимфоциты абс.": 1.37,
            "RE-LYMP abs": 0.08,
            "AS-LYMP abs": 0.01,
        }

        normalized = normalize_interpretation_markers(marker_values)

        self.assertEqual(normalized["Эритроциты"], 4.98)
        self.assertEqual(normalized["NRBC"], 0.00)
        self.assertEqual(normalized["Лимфоциты %"], 32.70)
        self.assertEqual(normalized["Лимфоциты абс."], 1.37)
        self.assertEqual(normalized["RE-LYMP abs"], 0.08)
        self.assertEqual(normalized["AS-LYMP abs"], 0.01)

    def test_percentage_and_absolute_markers_stay_separate(self) -> None:
        normalized = normalize_interpretation_markers(
            {
                "Лимфоциты %": 32.70,
                "Лимфоциты абс.": 1.37,
                "RE-LYMP abs": 0.08,
            }
        )

        self.assertNotEqual(normalized["Лимфоциты %"], normalized["RE-LYMP abs"])
        self.assertNotEqual(normalized["Лимфоциты %"], normalized["Лимфоциты абс."])

    def test_existing_marker_value_is_not_overwritten(self) -> None:
        normalized = normalize_interpretation_markers(
            {
                "Эритроциты": 4.98,
                "NRBC": 0.00,
            }
        )

        self.assertEqual(normalized["Эритроциты"], 4.98)
        self.assertEqual(normalized["NRBC"], 0.00)

    def test_true_synonym_fills_missing_slot_without_overwrite(self) -> None:
        normalized = normalize_interpretation_markers(
            {
                "Эритроциты": None,
                "RBC": 4.98,
            }
        )

        self.assertEqual(normalized["Эритроциты"], 4.98)

        normalized = normalize_interpretation_markers(
            {
                "Эритроциты": 4.98,
                "RBC": 4.7,
            }
        )

        self.assertEqual(normalized["Эритроциты"], 4.98)

    def test_api_payload_normalization_uses_exact_marker_mapping(self) -> None:
        payload = api_services._normalize_interpretation_payload(
            {
                "language": "ru",
                "Эритроциты": 4.98,
                "NRBC": 0.00,
                "Лимфоциты %": 32.70,
                "RE-LYMP abs": 0.08,
            }
        )

        self.assertEqual(payload["Эритроциты"], 4.98)
        self.assertEqual(payload["NRBC"], 0.00)
        self.assertEqual(payload["Лимфоциты %"], 32.70)
        self.assertEqual(payload["RE-LYMP abs"], 0.08)

    def test_must_not_merge_rbc_and_nrbc(self) -> None:
        payload = normalize_interpretation_markers({"RBC": 4.98, "NRBC": 0.00})

        self.assertEqual(payload["Эритроциты"], 4.98)
        self.assertEqual(payload["NRBC"], 0.00)
        self.assertNotEqual(payload["Эритроциты"], payload["NRBC"])

    def test_must_not_merge_lym_percent_and_lym_abs(self) -> None:
        payload = normalize_interpretation_markers({"LYM %": 32.70, "LYM abs": 2.01})

        self.assertEqual(payload["Лимфоциты %"], 32.70)
        self.assertEqual(payload["Лимфоциты абс."], 2.01)
        self.assertNotEqual(payload["Лимфоциты %"], payload["Лимфоциты абс."])

    def test_must_not_merge_lym_percent_and_re_lymp_abs(self) -> None:
        payload = normalize_interpretation_markers({"LYM %": 32.70, "RE-LYMP abs": 0.08})

        self.assertEqual(payload["Лимфоциты %"], 32.70)
        self.assertEqual(payload["RE-LYMP abs"], 0.08)
        self.assertNotEqual(payload["Лимфоциты %"], payload["RE-LYMP abs"])

    def test_must_not_merge_lym_percent_and_as_lymp_abs(self) -> None:
        payload = normalize_interpretation_markers({"LYM %": 32.70, "AS-LYMP abs": 0.01})

        self.assertEqual(payload["Лимфоциты %"], 32.70)
        self.assertEqual(payload["AS-LYMP abs"], 0.01)
        self.assertNotEqual(payload["Лимфоциты %"], payload["AS-LYMP abs"])

    def test_123_pdf_payload_expectations_remain_distinct(self) -> None:
        payload = normalize_interpretation_markers(
            {
                "Эритроциты": 4.98,
                "NRBC": 0.00,
                "Лимфоциты %": 32.70,
                "LYM abs": 2.01,
                "RE-LYMP abs": 0.08,
                "RE-LYMP %": 1.10,
                "Витамин D (25-OH)": 29,
                "Цинк": 8.5,
            }
        )

        self.assertEqual(payload["Эритроциты"], 4.98)
        self.assertEqual(payload["NRBC"], 0.00)
        self.assertEqual(payload["Лимфоциты %"], 32.70)
        self.assertEqual(payload["Лимфоциты абс."], 2.01)
        self.assertEqual(payload["RE-LYMP abs"], 0.08)
        self.assertEqual(payload["RE-LYMP %"], 1.10)
        self.assertEqual(payload["Витамин D (25-OH)"], 29.0)
        self.assertEqual(payload["Цинк"], 8.5)
        self.assertNotEqual(payload["Эритроциты"], payload["NRBC"])
        self.assertNotEqual(payload["Лимфоциты %"], payload["RE-LYMP abs"])

    def test_end_to_end_interpretation_payload_contains_correct_123_pdf_markers(self) -> None:
        captured: dict[str, object] = {}
        fake_analyze = ModuleType("interpreter.analyze")
        fake_risk = ModuleType("interpreter.risk")

        def fake_generate_interpretation(payload: dict[str, object]) -> str:
            captured.update(payload)
            return "ok"

        fake_analyze.generate_interpretation = fake_generate_interpretation
        fake_risk.compute_risk_status = lambda payload, language: {
            "label": "Normal",
            "color_key": "green",
            "explanation": "",
            "priority_notes": [],
        }

        with patch.dict(sys.modules, {"interpreter.analyze": fake_analyze, "interpreter.risk": fake_risk}):
            result = api_services.execute_interpretation_flow(
                {
                    "language": "ru",
                    "Эритроциты": 4.98,
                    "Лимфоциты %": 32.70,
                    "Лимфоциты абс.": 2.01,
                    "RE-LYMP абс.": 0.08,
                    "RE-LYMP %": 1.10,
                    "Витамин D (25-OH)": 29,
                    "Цинк": 8.5,
                }
            )

        self.assertEqual(result["interpretation"], "ok")
        self.assertEqual(captured["Лимфоциты %"], 32.70)
        self.assertEqual(captured["Лимфоциты абс."], 2.01)
        self.assertEqual(captured["RE-LYMP abs"], 0.08)
        self.assertEqual(captured["RE-LYMP %"], 1.10)
        self.assertEqual(captured["Витамин D (25-OH)"], 29.0)
        self.assertEqual(captured["Цинк"], 8.5)
        self.assertNotEqual(captured["Лимфоциты %"], captured["RE-LYMP abs"])
        self.assertIn("Цинк", captured)

    def test_parse_123_pdf_and_build_interpretation_payload_preserves_golden_markers(self) -> None:
        fixture_path = "/opt/labsense/backend/tests/fixtures/123.pdf"
        parse_result = select_and_extract_lab_data(fixture_path, language="ru", max_pages=5)

        payload = api_services._normalize_interpretation_payload(
            {
                "language": "ru",
                **parse_result.raw_values,
            }
        )

        self.assertEqual(payload["Эритроциты"], 4.98)
        self.assertEqual(payload["Витамин D (25-OH)"], 29.0)
        self.assertEqual(payload["Цинк"], 8.5)
        self.assertNotIn("Лимфоциты %", payload)


if __name__ == "__main__":
    unittest.main()
