import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense/backend")

from parser.extract_pdf import (  # noqa: E402
    _is_simple_scalar_row,
    extract_lab_data_from_pdf,
    convert_value_safely,
    extract_reference_range,
    extract_unit,
    extract_value,
    match_indicator,
)
from parser.marker_metadata import get_marker_metadata  # noqa: E402
from parser.postprocess import build_marker_detail_from_text, merge_canonical_markers  # noqa: E402
from parser.source_selection import select_and_extract_lab_data  # noqa: E402


class ExtractPdfRegressionTests(unittest.TestCase):
    @staticmethod
    def _extract_fixture_lines(lines: list[str]) -> dict[str, float | None]:
        extracted: dict[str, float | None] = {}
        for line in lines:
            key, value = match_indicator(line)
            if key is not None:
                extracted[key] = value
        merged_values, _ = merge_canonical_markers(extracted, {})
        return merged_values

    def test_text_rich_pdf_uses_canonical_text_path(self) -> None:
        fixture_path = Path("/opt/labsense/backend/tests/fixtures/123.pdf")

        result = select_and_extract_lab_data(str(fixture_path), language="ru", max_pages=5)

        self.assertEqual(result.selected_source, "text")
        self.assertEqual(result.final_source, "text")
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.source, "pdfplumber")
        self.assertIn("canonical_text_path", result.selection_reason)
        self.assertEqual(result.raw_values["Гемоглобин"], 148.1)
        self.assertEqual(result.raw_values["Эритроциты"], 4.98)
        self.assertEqual(result.raw_values["Гематокрит"], 41.6)
        self.assertEqual(result.raw_values["Тромбоциты"], 298.0)
        self.assertEqual(result.raw_values["Лейкоциты"], 4.19)
        self.assertEqual(result.raw_values["Витамин D (25-OH)"], 29.0)
        self.assertEqual(result.raw_values["Цинк"], 8.5)

    def test_does_not_match_short_alias_inside_regular_words(self) -> None:
        self.assertEqual(match_indicator("Boarding starts 20 minutes before departure."), (None, None))
        self.assertEqual(match_indicator("Dangerous goods are forbidden on this flight."), (None, None))

    def test_extracts_value_after_alias_not_from_leading_noise(self) -> None:
        key, value = match_indicator("12 AST 20 U/L 0 - 40")
        self.assertEqual(key, "AST")
        self.assertEqual(value, 20.0)

    def test_keeps_specific_cbc_markers_separate_from_broader_aliases(self) -> None:
        self.assertEqual(match_indicator("NRBC 0.00 %"), ("Нормобласты", 0.0))
        self.assertEqual(match_indicator("Эритроциты с ядром 0,00 %"), ("Нормобласты", 0.0))
        self.assertEqual(match_indicator("LYM % 32.70 %"), ("Лимфоциты %", 32.7))
        self.assertEqual(match_indicator("Лимфоциты абс. 0,08 10^9/л"), ("Лимфоциты абс.", 0.08))
        self.assertEqual(match_indicator("Reactive lymphocytes 0.08 x10^9/L"), ("RE-LYMP abs", 0.08))
        self.assertEqual(match_indicator("Plasma cells 0.01 x10^9/L"), ("AS-LYMP abs", 0.01))

    def test_additive_aliases_capture_crp_and_vitamin_d(self) -> None:
        self.assertEqual(match_indicator("C-reactive protein 8.4 mg/L 0 - 5")[0], "CRP")
        self.assertEqual(match_indicator("Vitamin D 25-OH 21 ng/mL 30 - 100")[0], "Витамин D (25-OH)")

    def test_western_chemistry_fixture_extracts_queue_one_markers_into_canonical_keys(self) -> None:
        lines = [
            "Na 140 mmol/L",
            "K 4.2 mmol/L",
            "Cl 103 mmol/L",
            "Urea 5.4 mmol/L",
            "Creatinine 90 µmol/L",
            "eGFR 96 mL/min/1.73m2",
            "Glucose 5.6 mmol/L",
            "AST 20 U/L",
            "ALT 22 U/L",
            "HbA1c 5.4 %",
            "Urine Albumin 12 mg/L",
            "Urine Creatinine 8.4 mmol/L",
            "ACR 1.4 mg/mmol",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Натрий"], 140.0)
        self.assertEqual(extracted["Калий"], 4.2)
        self.assertEqual(extracted["Хлор"], 103.0)
        self.assertEqual(extracted["Мочевина"], 5.4)
        self.assertEqual(extracted["Креатинин"], 90.0)
        self.assertEqual(extracted["eGFR"], 96.0)
        self.assertEqual(extracted["Глюкоза"], 5.6)
        self.assertEqual(extracted["AST"], 20.0)
        self.assertEqual(extracted["ALT"], 22.0)
        self.assertEqual(extracted["HbA1c"], 5.4)
        self.assertEqual(extracted["Urine Albumin"], 12.0)
        self.assertEqual(extracted["Urine Creatinine"], 8.4)
        self.assertEqual(extracted["ACR"], 1.4)

    def test_western_chemistry_fixture_keeps_bun_distinct_from_urea(self) -> None:
        extracted = self._extract_fixture_lines(
            [
                "BUN 14 mg/dL",
                "Urea 5.4 mmol/L",
            ]
        )

        self.assertEqual(extracted["BUN"], 14.0)
        self.assertEqual(extracted["Мочевина"], 5.4)
        self.assertNotEqual(extracted["BUN"], extracted["Мочевина"])

    def test_western_cbc_fixture_extracts_core_and_differential_markers_correctly(self) -> None:
        lines = [
            "HGB 148 g/L",
            "HCT 43.2 %",
            "RBC 4.91 x10^12/L",
            "WBC 6.2 x10^9/L",
            "PLT 235 x10^9/L",
            "NEU 58.4 %",
            "ANC 3.62 x10^9/L",
            "LYM 29.5 %",
            "MON 7.8 %",
            "EOS 3.6 %",
            "BASO 0.7 %",
            "MCV 88.0 fL",
            "MCH 30.1 pg",
            "MCHC 341 g/L",
            "RDW 12.8 %",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Гемоглобин"], 148.0)
        self.assertEqual(extracted["Гематокрит"], 43.2)
        self.assertEqual(extracted["Эритроциты"], 4.91)
        self.assertEqual(extracted["Лейкоциты"], 6.2)
        self.assertEqual(extracted["Тромбоциты"], 235.0)
        self.assertEqual(extracted["Нейтрофилы %"], 58.4)
        self.assertEqual(extracted["Нейтрофилы абс."], 3.62)
        self.assertEqual(extracted["Лимфоциты %"], 29.5)
        self.assertEqual(extracted["Моноциты %"], 7.8)
        self.assertEqual(extracted["Эозинофилы %"], 3.6)
        self.assertEqual(extracted["Базофилы %"], 0.7)
        self.assertEqual(extracted["MCV"], 88.0)
        self.assertEqual(extracted["MCH"], 30.1)
        self.assertEqual(extracted["MCHC"], 341.0)
        self.assertEqual(extracted["RDW"], 12.8)

    def test_reference_and_unit_helpers_are_conservative(self) -> None:
        line = "CRP 8.4 mg/L 0 - 5"
        self.assertEqual(extract_unit(line), "mg/L")
        self.assertEqual(extract_reference_range(line), "0 - 5")
        self.assertEqual(extract_reference_range("LDL 3.9 mmol/L < 3.0"), "< 3.0")

    def test_extract_reference_range_supports_inline_parenthetical_formats(self) -> None:
        self.assertEqual(extract_reference_range("Sodium 141 mmol/L (135-145)"), "135-145")
        self.assertEqual(extract_reference_range("Glucose 5.6 mmol/L (3.9 - 6.0)"), "3.9 - 6.0")
        self.assertEqual(extract_reference_range("AST 33 U/L (< 41)"), "< 41")
        self.assertEqual(extract_reference_range("Urine Albumin 1.5 mg/L (< 20.1)"), "< 20.1")
        self.assertEqual(extract_reference_range("Potassium 4.2 mmol/L (> 3.5)"), "> 3.5")
        self.assertEqual(extract_reference_range("ACR < 0.1 mg Alb/mmol (< 3.5)"), "< 3.5")

    def test_extract_reference_range_keeps_existing_column_style_reference_priority_over_inline_parentheses(self) -> None:
        self.assertEqual(extract_reference_range("Sodium 141 mmol/L 135-145 (130-150)"), "135-145")
        self.assertIsNone(extract_reference_range("Sodium 141 mmol/L (fasting sample)"))

    def test_decimal_separator_and_unicode_unit_normalization(self) -> None:
        self.assertEqual(extract_unit("Creatinine 90 µmol/L"), "umol/L")
        self.assertEqual(extract_unit("Platelets 250 x10⁹/L"), "x10^9/L")
        self.assertEqual(match_indicator("Glucose 5,6 mmol/L 3,9 - 5,5"), ("Глюкоза", 5.6))
        self.assertEqual(extract_unit("Эритроциты 4,98 10^12/л"), "x10^12/L")
        self.assertEqual(extract_unit("Гемоглобин 148,10 г/л"), "g/L")
        self.assertEqual(extract_unit("Витамин D (25-OH) 29 нг/мл"), "ng/mL")
        self.assertEqual(extract_unit("Цинк 8,5 мкмоль/л"), "umol/L")
        self.assertEqual(extract_unit("eGFR 96 mL/min/1.73m2"), "mL/min/1.73m2")
        self.assertEqual(extract_unit("ACR 1.4 mg/mmol"), "mg/mmol")
        self.assertEqual(extract_unit("MCV 88.0 fL"), "fL")
        self.assertEqual(extract_unit("MCH 30.1 pg"), "pg")
        self.assertEqual(extract_unit("WBC 6.0 K/uL"), "K/uL")
        self.assertEqual(extract_unit("RBC 5.0 M/uL"), "M/uL")
        self.assertEqual(extract_unit("HbA1c 33 mmol/mol"), "mmol/mol")
        self.assertEqual(extract_unit("ACR <0.1 mg Alb/mmol"), "mg Alb/mmol")

    def test_international_unit_recognition_preserves_numeric_values_without_conversion(self) -> None:
        self.assertEqual(extract_value("HGB 140 g/L", "Гемоглобин", "hgb"), 140.0)
        self.assertEqual(extract_unit("HGB 140 g/L"), "g/L")
        self.assertEqual(extract_value("HGB 14.0 g/dL", "Гемоглобин", "hgb"), 14.0)
        self.assertEqual(extract_unit("HGB 14.0 g/dL"), "g/dL")
        self.assertEqual(extract_value("RBC 5.0 M/uL", "Эритроциты", "rbc"), 5.0)
        self.assertEqual(extract_unit("RBC 5.0 M/uL"), "M/uL")
        self.assertEqual(extract_value("WBC 6.0 K/uL", "Лейкоциты", "wbc"), 6.0)
        self.assertEqual(extract_unit("WBC 6.0 K/uL"), "K/uL")
        self.assertEqual(extract_value("HbA1c 33 mmol/mol", "HbA1c", "hba1c"), 33.0)
        self.assertEqual(extract_unit("HbA1c 33 mmol/mol"), "mmol/mol")

    def test_marker_detail_captures_new_unit_aliases_without_rescaling(self) -> None:
        hgb_detail = build_marker_detail_from_text("HGB 14.0 g/dL")
        rbc_detail = build_marker_detail_from_text("RBC 5.0 M/uL")
        wbc_detail = build_marker_detail_from_text("WBC 6.0 K/uL")
        hba1c_detail = build_marker_detail_from_text("HbA1c 33 mmol/mol")
        acr_detail = build_marker_detail_from_text("ACR <0.1 mg Alb/mmol")

        self.assertIsNotNone(hgb_detail)
        self.assertEqual(hgb_detail.value, 14.0)
        self.assertEqual(hgb_detail.unit, "g/dL")
        self.assertIsNotNone(rbc_detail)
        self.assertEqual(rbc_detail.value, 5.0)
        self.assertEqual(rbc_detail.unit, "M/uL")
        self.assertIsNotNone(wbc_detail)
        self.assertEqual(wbc_detail.value, 6.0)
        self.assertEqual(wbc_detail.unit, "K/uL")
        self.assertIsNotNone(hba1c_detail)
        self.assertEqual(hba1c_detail.value, 33.0)
        self.assertEqual(hba1c_detail.unit, "mmol/mol")
        self.assertIsNotNone(acr_detail)
        self.assertEqual(acr_detail.value, 0.1)
        self.assertEqual(acr_detail.unit, "mg Alb/mmol")

    def test_prevents_numeric_concatenation_and_recovers_decimal_spacing(self) -> None:
        self.assertEqual(extract_value("Glucose 5 6 mmol/L", "Глюкоза", "glucose"), 5.6)
        self.assertEqual(extract_value("Platelets 7 500 x10^9/L", "Тромбоциты", "platelets"), 7500.0)
        self.assertEqual(extract_value("RBC 4,98 10^12/л", "Эритроциты", "rbc"), 4.98)
        self.assertEqual(extract_value("WBC 4,19 10^9/л", "Лейкоциты", "wbc"), 4.19)
        self.assertEqual(extract_value("Гемоглобин 148,10 г/л", "Гемоглобин", "гемоглобин"), 148.1)

    def test_layout_aware_value_extraction_keeps_result_separate_from_reference_digits(self) -> None:
        self.assertEqual(extract_value("PLATELETS 309 150-450 10^9/L", "Тромбоциты", "platelets"), 309.0)
        self.assertEqual(extract_value("HEMOGLOBIN 144 110-150 g/L", "Гемоглобин", "hemoglobin"), 144.0)
        self.assertEqual(extract_value("RBC 5.3 4.2-5.6 10^12/L", "Эритроциты", "rbc"), 5.3)
        self.assertEqual(extract_value("WBC 6.2 4.0-11.0 10^9/L", "Лейкоциты", "wbc"), 6.2)

    def test_layout_concatenation_guard_rejects_corrupted_result_plus_reference_values(self) -> None:
        self.assertEqual(extract_value("Platelets 309 150-450 10^9/L", "Тромбоциты", "platelets"), 309.0)
        self.assertEqual(extract_value("RBC 53 4.2-5.6 10^12/L", "Эритроциты", "rbc"), 53.0)

    def test_primary_value_selection_stops_before_reference_digits(self) -> None:
        cases = {
            "ALT 9.2 U/L < 33": ("ALT", "alt", 9.2),
            "AST 11.7 U/L < 32": ("AST", "ast", 11.7),
            "Glucose 4.84 mmol/L 3.9 - 6.1": ("Глюкоза", "glucose", 4.84),
            "IgE 79.3 МЕ/мл < 100": ("IgE", "ige", 79.3),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

        self.assertNotEqual(extract_value("ALT 9.2 U/L < 33", "ALT", "alt"), 50429.2)
        self.assertNotEqual(extract_value("AST 11.7 U/L < 32", "AST", "ast"), 5.041)
        self.assertNotEqual(extract_value("Glucose 4.84 mmol/L 3.9 - 6.1", "Глюкоза", "glucose"), 5.023)
        self.assertNotEqual(extract_value("IgE 79.3 МЕ/мл < 100", "IgE", "ige"), 5054001)

    def test_simple_single_line_rows_bypass_candidate_scoring_with_positional_value_selection(self) -> None:
        cases = {
            "АЛТ 9.2 Ед/л < 33": ("АЛТ", "алт", 9.2, 5.042),
            "АСТ 11.7 Ед/л < 32": ("АСТ", "аст", 11.7, 5.041),
            "Глюкоза 4.84 ммоль/л 4.11 - 6.1": ("Глюкоза", "глюкоза", 4.84, 5.023),
            "Иммуноглобулин IgE общий 79.3 МЕ/мл < 100": ("IgE", "ige", 79.3, 5.054),
            "АТ-ТГ 55.6 МЕ/мл 0 - 115": ("anti-TG", "ат-тг", 55.6, 6.017),
            "АТ-ТПО 44.80 МЕ/мл 0 - 34": ("anti-TPO", "ат-тпо", 44.8, 6.045),
            "Мочевина 3.7 ммоль/л 2.6 - 6.4": ("Мочевина", "мочевина", 3.7, 5.017),
            "Общий белок 69.0 г/л 64 - 83": ("Общий белок", "общий белок", 69.0, 5.01),
        }

        for line, (metric_name, alias, expected, corrupted) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)
            self.assertNotEqual(extract_value(line, metric_name, alias), corrupted)

    def test_simple_scalar_row_classifier_is_structural_not_marker_whitelist_based(self) -> None:
        simple_rows = {
            "ALT 9.2 U/L < 33": ("ALT", " 9.2 U/L < 33"),
            "AST 11.7 U/L < 32": ("AST", " 11.7 U/L < 32"),
            "Glucose 4.84 mmol/L 4.11 - 6.1": ("Глюкоза", " 4.84 mmol/L 4.11 - 6.1"),
            "IgE 79.3 IU/mL < 100": ("IgE", " 79.3 IU/mL < 100"),
            "anti-TG 55.6 U/mL 0 - 115": ("anti-TG", " 55.6 U/mL 0 - 115"),
            "anti-TPO 44.80 U/mL 0 - 34": ("anti-TPO", " 44.80 U/mL 0 - 34"),
            "Urea 3.7 mmol/L 2.6 - 6.4": ("Мочевина", " 3.7 mmol/L 2.6 - 6.4"),
            "Total Protein 69.0 g/L 64 - 83": ("Общий белок", " 69.0 g/L 64 - 83"),
            "Creatinine 84 umol/L 44 - 80": ("Креатинин", " 84 umol/L 44 - 80"),
            "Sodium 140 mmol/L 136 - 145": ("Натрий", " 140 mmol/L 136 - 145"),
        }
        non_simple_rows = {
            "RBC 4.98 x10^12/L": ("Эритроциты", " 4.98 x10^12/L"),
            "WBC 6.2 x10^9/L": ("Лейкоциты", " 6.2 x10^9/L"),
            "NEU % 33.2 50-70 %": ("Нейтрофилы %", " % 33.2 50-70 %"),
            "Neutrophils 3.3 10^9/L": ("Нейтрофилы абс.", " 3.3 10^9/L"),
            "TSH 2.1 mIU/L\nSee text": ("TSH", " 2.1 mIU/L\nSee text"),
            "ALT Смотри текст": ("ALT", " Смотри текст"),
        }

        for line, (metric_name, source_text) in simple_rows.items():
            self.assertTrue(_is_simple_scalar_row(line, source_text, metric_name))

        for line, (metric_name, source_text) in non_simple_rows.items():
            self.assertFalse(_is_simple_scalar_row(line, source_text, metric_name))

    def test_generic_simple_scalar_rows_keep_closest_value_before_unit(self) -> None:
        lines = [
            "АЛТ 9.2 Ед/л < 33",
            "АСТ 11.7 Ед/л < 32",
            "Глюкоза 4.84 ммоль/л 4.11 - 6.1",
            "Иммуноглобулин IgE общий 79.3 МЕ/мл < 100",
            "АТ-ТГ 55.6 МЕ/мл 0 - 115",
            "АТ-ТПО 44.80 МЕ/мл 0 - 34",
            "Мочевина 3.7 ммоль/л 2.6 - 6.4",
            "Общий белок 69.0 г/л 64 - 83",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["ALT"], 9.2)
        self.assertEqual(extracted["AST"], 11.7)
        self.assertEqual(extracted["Глюкоза"], 4.84)
        self.assertEqual(extracted["IgE"], 79.3)
        self.assertEqual(extracted["anti-TG"], 55.6)
        self.assertEqual(extracted["anti-TPO"], 44.8)
        self.assertEqual(extracted["Мочевина"], 3.7)
        self.assertEqual(extracted["Общий белок"], 69.0)

    def test_generic_simple_scalar_rows_keep_unit_adjacent_result_token_when_references_follow_unit(self) -> None:
        cases = {
            "ALT 9.2 U/L < 33": ("ALT", "alt", 9.2),
            "AST 11.7 U/L < 32": ("AST", "ast", 11.7),
            "Glucose 4.84 mmol/L 4.11 - 6.1": ("Глюкоза", "glucose", 4.84),
            "IgE 79.3 IU/mL < 100": ("IgE", "ige", 79.3),
            "anti-TG 55.6 U/mL 0 - 115": ("anti-TG", "anti-tg", 55.6),
            "anti-TPO 44.80 U/mL 0 - 34": ("anti-TPO", "anti-tpo", 44.8),
            "Urea 3.7 mmol/L 2.6 - 6.4": ("Мочевина", "urea", 3.7),
            "Total Protein 69.0 g/L 64 - 83": ("Общий белок", "total protein", 69.0),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_generic_simple_scalar_rows_do_not_degrade_into_later_reference_digits(self) -> None:
        protected_cases = {
            "ALT 9.2 U/L < 33": ("ALT", "alt", {33.0, 50429.2}),
            "AST 11.7 U/L < 32": ("AST", "ast", {32.0, 5.041}),
            "Glucose 4.84 mmol/L 4.11 - 6.1": ("Глюкоза", "glucose", {4.11, 6.1, 5.023}),
            "IgE 79.3 IU/mL < 100": ("IgE", "ige", {100.0, 5054001.0}),
            "anti-TG 55.6 U/mL 0 - 115": ("anti-TG", "anti-tg", {0.0, 115.0, 6.017}),
            "anti-TPO 44.80 U/mL 0 - 34": ("anti-TPO", "anti-tpo", {0.0, 34.0, 6.045}),
            "Urea 3.7 mmol/L 2.6 - 6.4": ("Мочевина", "urea", {2.6, 6.4, 5.017}),
            "Total Protein 69.0 g/L 64 - 83": ("Общий белок", "total protein", {64.0, 83.0, 5.01}),
        }

        for line, (metric_name, alias, forbidden_values) in protected_cases.items():
            value = extract_value(line, metric_name, alias)
            self.assertNotIn(value, forbidden_values)

    def test_localized_simple_scalar_units_are_recognized_by_override_path(self) -> None:
        self.assertEqual(extract_unit("Ед/л"), "U/L")
        self.assertEqual(extract_unit("МЕ/мл"), "IU/mL")
        self.assertEqual(extract_unit("ммоль/л"), "mmol/L")
        self.assertEqual(extract_unit("г/л"), "g/L")
        self.assertEqual(extract_unit("мкмоль/л"), "umol/L")

        cases = {
            "АЛТ 9.2 Ед/л < 33": ("АЛТ", "алт", 9.2),
            "АСТ 11.7 Ед/л < 32": ("АСТ", "аст", 11.7),
            "Иммуноглобулин IgE общий 79.3 МЕ/мл < 100": ("IgE", "ige", 79.3),
            "АТ-ТГ 55.6 МЕ/мл 0 - 115": ("anti-TG", "ат-тг", 55.6),
            "АТ-ТПО 44.80 МЕ/мл 0 - 34": ("anti-TPO", "ат-тпо", 44.8),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_simple_scalar_rows_parse_leading_numeric_portion_of_annotated_tokens(self) -> None:
        cases = {
            "АТ-ТПО 44.80++ МЕ/мл 0 - 34": ("anti-TPO", "ат-тпо", 44.8),
            "Токсокароз IgG 2.11+ коэф.позитив. 0 - 1": ("IgG", "igg", 2.11),
            "ЭКБ 36.3++ нг/мл < 24.0": ("ЭКБ", "экб", 36.3),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_simple_scalar_override_can_ignore_one_leading_numeric_noise_token(self) -> None:
        cases = {
            "Глюкоза 5.023 4.84 ммоль/л 4.11 - 6.1": ("Глюкоза", "глюкоза", 4.84),
            "Мочевина 5.017 3.7 ммоль/л 2.6 - 6.4": ("Мочевина", "мочевина", 3.7),
            "Общий белок 5.01 69.0 г/л 64 - 83": ("Общий белок", "общий белок", 69.0),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_simple_scalar_override_can_ignore_one_leading_numeric_noise_token_for_cyrillic_units(self) -> None:
        cases = {
            "АЛТ 5.042 9.2 Ед/л < 33": ("АЛТ", "алт", 9.2),
            "АСТ 5.041 11.7 Ед/л < 32": ("АСТ", "аст", 11.7),
            "Иммуноглобулин IgE общий 5.054 79.3 МЕ/мл < 100": ("IgE", "ige", 79.3),
            "АТ-ТГ 6.017 55.6 МЕ/мл 0 - 115": ("anti-TG", "ат-тг", 55.6),
            "АТ-ТПО 6.045 44.80 МЕ/мл 0 - 34": ("anti-TPO", "ат-тпо", 44.8),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_simple_scalar_override_anchors_to_detected_unit_and_ignores_all_earlier_numbers(self) -> None:
        cases = {
            "Глюкоза 1.111 5.023 4.84 ммоль/л 4.11 - 6.1": ("Глюкоза", "глюкоза", 4.84),
            "Мочевина 0.500 5.017 3.7 ммоль/л 2.6 - 6.4": ("Мочевина", "мочевина", 3.7),
            "Общий белок 2.000 5.01 69.0 г/л 64 - 83": ("Общий белок", "общий белок", 69.0),
            "IgE 1.000 5.054 79.3 МЕ/мл < 100": ("IgE", "ige", 79.3),
            "АТ-ТГ 2.000 6.017 55.6 МЕ/мл 0 - 115": ("anti-TG", "ат-тг", 55.6),
            "АТ-ТПО 3.000 6.045 44.80 МЕ/мл 0 - 34": ("anti-TPO", "ат-тпо", 44.8),
        }

        for line, (metric_name, alias, expected) in cases.items():
            self.assertEqual(extract_value(line, metric_name, alias), expected)

    def test_scientific_notation_and_existing_anemia_baselines_remain_unchanged(self) -> None:
        self.assertEqual(extract_value("RBC 4.98 10^12/L", "Эритроциты", "rbc"), 4.98)
        self.assertEqual(extract_value("PLT 298 10^9/L", "Тромбоциты", "plt"), 298.0)
        anemia_lines = [
            "HGB 82 g/L",
            "RBC 2.61 x10^12/L",
            "HCT 26.4 %",
            "MCV 101.1 fL",
        ]

        extracted = self._extract_fixture_lines(anemia_lines)

        self.assertEqual(extracted["Гемоглобин"], 82.0)
        self.assertEqual(extracted["Эритроциты"], 2.61)
        self.assertEqual(extracted["Гематокрит"], 26.4)
        self.assertEqual(extracted["MCV"], 101.1)

    def test_percentage_rows_do_not_absorb_adjacent_reference_digits_from_layout(self) -> None:
        self.assertEqual(extract_value("NEUTROPHILS 22 1-80 %", "Нейтрофилы %", "neutrophils"), 22.0)
        self.assertEqual(extract_value("MONOCYTES 6 2-10 %", "Моноциты %", "monocytes"), 6.0)
        self.assertEqual(extract_value("EOS 33.2 0.0-6.0 %", "Эозинофилы %", "eos"), 33.2)

    def test_western_percent_markers_stay_on_true_result_values_not_reference_digits(self) -> None:
        lines = [
            "NEU % 33.2 50-70 %",
            "LYM % 22 20-40 %",
            "MON % 8.0 2-10 %",
            "EOS % 1.10 0.0-6.0 %",
            "BASO % 0.70 0.0-2.0 %",
            "NEU# 3.62 x10^9/L",
            "LYM# 2.01 x10^9/L",
            "MON# 0.48 x10^9/L",
            "EOS# 0.08 x10^9/L",
            "BASO# 0.04 x10^9/L",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Нейтрофилы %"], 33.2)
        self.assertEqual(extracted["Лимфоциты %"], 22.0)
        self.assertEqual(extracted["Моноциты %"], 8.0)
        self.assertEqual(extracted["Эозинофилы %"], 1.1)
        self.assertEqual(extracted["Базофилы %"], 0.7)
        self.assertEqual(extracted["Нейтрофилы абс."], 3.62)
        self.assertEqual(extracted["Лимфоциты абс."], 2.01)
        self.assertEqual(extracted["Моноциты абс."], 0.48)
        self.assertEqual(extracted["Эозинофилы абс."], 0.08)
        self.assertEqual(extracted["Базофилы абс."], 0.04)

    def test_western_differential_absolute_count_rows_populate_only_absolute_slots(self) -> None:
        lines = [
            "Neutrophils 3.3 10^9/L",
            "Lymphocytes 2.0 10^9/L",
            "Monocytes 0.8 10^9/L",
            "Eosinophils 0.1 10^9/L",
            "Basophils 0.1 10^9/L",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Нейтрофилы абс."], 3.3)
        self.assertEqual(extracted["Лимфоциты абс."], 2.0)
        self.assertEqual(extracted["Моноциты абс."], 0.8)
        self.assertEqual(extracted["Эозинофилы абс."], 0.1)
        self.assertEqual(extracted["Базофилы абс."], 0.1)
        self.assertNotIn("Нейтрофилы %", extracted)
        self.assertNotIn("Лимфоциты %", extracted)
        self.assertNotIn("Моноциты %", extracted)
        self.assertNotIn("Эозинофилы %", extracted)
        self.assertNotIn("Базофилы %", extracted)

    def test_russian_percent_markers_remain_unchanged(self) -> None:
        self.assertEqual(match_indicator("Нейтрофилы % 58,4 % 50-70"), ("Нейтрофилы %", 58.4))
        self.assertEqual(match_indicator("Лимфоциты % 32,7 % 20-45"), ("Лимфоциты %", 32.7))
        self.assertEqual(match_indicator("Моноциты % 7,8 % 2-10"), ("Моноциты %", 7.8))
        self.assertEqual(match_indicator("Эозинофилы % 3,6 % 0-5"), ("Эозинофилы %", 3.6))
        self.assertEqual(match_indicator("Базофилы % 0,7 % 0-1"), ("Базофилы %", 0.7))

    def test_russian_differential_absolute_and_percent_rows_remain_separate(self) -> None:
        lines = [
            "Нейтрофилы 3,3 10^9/л",
            "Нейтрофилы % 58,4 %",
            "Лимфоциты 2,0 10^9/л",
            "Лимфоциты % 32,7 %",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Нейтрофилы абс."], 3.3)
        self.assertEqual(extracted["Нейтрофилы %"], 58.4)
        self.assertEqual(extracted["Лимфоциты абс."], 2.0)
        self.assertEqual(extracted["Лимфоциты %"], 32.7)

    def test_differential_percent_rows_do_not_populate_absolute_slots(self) -> None:
        lines = [
            "Neutrophils 58.4 %",
            "Lymphocytes 32.7 %",
            "Monocytes 7.8 %",
            "Eosinophils 3.6 %",
            "Basophils 0.7 %",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Нейтрофилы %"], 58.4)
        self.assertEqual(extracted["Лимфоциты %"], 32.7)
        self.assertEqual(extracted["Моноциты %"], 7.8)
        self.assertEqual(extracted["Эозинофилы %"], 3.6)
        self.assertEqual(extracted["Базофилы %"], 0.7)
        self.assertNotIn("Нейтрофилы абс.", extracted)
        self.assertNotIn("Лимфоциты абс.", extracted)
        self.assertNotIn("Моноциты абс.", extracted)
        self.assertNotIn("Эозинофилы абс.", extracted)
        self.assertNotIn("Базофилы абс.", extracted)

    def test_mixed_differential_percent_and_absolute_markers_remain_distinct(self) -> None:
        lines = [
            "LYM % 32.70 20-45 %",
            "LYM abs 2.01 x10^9/L",
            "RE-LYMP % 1.10 0.0-5.0 %",
            "RE-LYMP abs 0.08 x10^9/L",
        ]

        extracted = self._extract_fixture_lines(lines)

        self.assertEqual(extracted["Лимфоциты %"], 32.7)
        self.assertEqual(extracted["Лимфоциты абс."], 2.01)
        self.assertEqual(extracted["RE-LYMP %"], 1.1)
        self.assertEqual(extracted["RE-LYMP abs"], 0.08)
        self.assertNotEqual(extracted["Лимфоциты %"], extracted["Лимфоциты абс."])
        self.assertNotEqual(extracted["Лимфоциты %"], extracted["RE-LYMP abs"])

    def test_decimal_fix_stays_conservative_for_whitelisted_metrics(self) -> None:
        self.assertEqual(extract_value("Glucose 56 mmol/L", "Глюкоза", "glucose"), 56.0)
        self.assertEqual(extract_value("ALT 327 U/L", "ALT", "alt"), 327.0)
        self.assertEqual(extract_value("MCV 96 фл", "MCV", "mcv"), 96.0)

    def test_explicit_units_and_plausible_cbc_values_block_decimal_rescaling(self) -> None:
        self.assertEqual(extract_value("Гемоглобин 158 г/л", "Гемоглобин", "гемоглобин"), 158.0)
        self.assertEqual(extract_value("Гемоглобин 126 г/л", "Гемоглобин", "гемоглобин"), 126.0)
        self.assertEqual(extract_value("Гемоглобин 140 г/л", "Гемоглобин", "гемоглобин"), 140.0)
        self.assertEqual(extract_value("Гематокрит 41,6 %", "Гематокрит", "гематокрит"), 41.6)
        self.assertEqual(extract_value("MCV 96 фл", "MCV", "mcv"), 96.0)
        self.assertEqual(extract_value("Эритроциты 4,98 10^12/л", "Эритроциты", "эритроциты"), 4.98)
        self.assertEqual(extract_value("Тромбоциты 298 10^9/л", "Тромбоциты", "тромбоциты"), 298.0)

    def test_decimal_fix_can_still_apply_in_truly_ambiguous_unitless_case(self) -> None:
        self.assertEqual(extract_value("Glucose 56", "Глюкоза", "glucose"), 5.6)

    def test_extract_reference_range_handles_split_european_table_layouts(self) -> None:
        self.assertEqual(extract_reference_range("30 100"), "30 - 100")
        self.assertEqual(extract_reference_range("3,8 5,8"), "3.8 - 5.8")
        self.assertEqual(extract_reference_range("Витамин D (25-OH) 29 нг/мл 30 100"), "30 - 100")

    def test_western_chemistry_marker_details_capture_inline_parenthetical_references(self) -> None:
        cases = {
            "Sodium 141 mmol/L (135-145)": ("Натрий", "135-145"),
            "Potassium 4.1 mmol/L (3.5-5.1)": ("Калий", "3.5-5.1"),
            "Chloride 99 mmol/L (95-110)": ("Хлор", "95-110"),
            "Urea 7.1 mmol/L (3.0-10.0)": ("Мочевина", "3.0-10.0"),
            "Creatinine 88 umol/L (44-110)": ("Креатинин", "44-110"),
            "Glucose 5.6 mmol/L (3.9 - 6.0)": ("Глюкоза", "3.9 - 6.0"),
            "AST 33 U/L (< 41)": ("AST", "< 41"),
            "ALT 25 U/L (< 51)": ("ALT", "< 51"),
            "Uric Acid 0.21 mmol/L (0.15-0.45)": ("Кислота мочевая", "0.15-0.45"),
            "Urine Albumin 1.5 mg/L (< 20.1)": ("Urine Albumin", "< 20.1"),
            "Urine Creatinine 16.80 mmol/L (4.00-25.00)": ("Urine Creatinine", "4.00-25.00"),
            "ACR < 0.1 mg Alb/mmol (< 3.5)": ("ACR", "< 3.5"),
        }

        for line, (name, reference_range) in cases.items():
            detail = build_marker_detail_from_text(line)
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.name, name)
            self.assertEqual(detail.reference_range, reference_range)

    def test_convert_value_safely_preserves_existing_behavior(self) -> None:
        self.assertEqual(convert_value_safely("ANA", "1:160"), 160.0)
        self.assertEqual(convert_value_safely("Глюкоза", "90 mg/dL"), 90.0)

    def test_marker_metadata_is_available_for_common_markers(self) -> None:
        metadata = get_marker_metadata("CRP")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["unit"], "mg/L")
        self.assertEqual(metadata["reference_range"], "0 - 5")

    def test_123_pdf_fixture_stays_on_legacy_text_baseline_without_fabricating_missing_markers(self) -> None:
        fixture_path = Path("/opt/labsense/backend/tests/fixtures/123.pdf")

        result = select_and_extract_lab_data(str(fixture_path), language="ru", max_pages=5)

        self.assertEqual(result.raw_values["Эритроциты"], 4.98)
        self.assertEqual(result.raw_values["Витамин D (25-OH)"], 29.0)
        self.assertEqual(result.raw_values["Цинк"], 8.5)
        self.assertNotIn("Лимфоциты %", result.raw_values)
        self.assertNotIn("Лимфоциты абс.", result.raw_values)
        self.assertNotIn("RE-LYMP abs", result.raw_values)
        self.assertNotIn("RE-LYMP %", result.raw_values)
        self.assertNotIn("Нормобласты", result.raw_values)

    def test_123_pdf_matches_legacy_text_extraction_golden_values(self) -> None:
        fixture_path = Path("/opt/labsense/backend/tests/fixtures/123.pdf")

        result = select_and_extract_lab_data(str(fixture_path), language="ru", max_pages=5)

        self.assertEqual(result.source, "pdfplumber")
        self.assertEqual(result.selected_source, "text")
        self.assertEqual(result.final_source, "text")
        self.assertFalse(result.fallback_used)
        self.assertIn("canonical_text_path", result.selection_reason)
        self.assertEqual(result.raw_values["Гемоглобин"], 148.10)
        self.assertEqual(result.raw_values["Эритроциты"], 4.98)
        self.assertEqual(result.raw_values["Гематокрит"], 41.60)
        self.assertEqual(result.raw_values["Тромбоциты"], 298.0)
        self.assertEqual(result.raw_values["Лейкоциты"], 4.19)
        self.assertEqual(result.raw_values["Витамин D (25-OH)"], 29.0)
        self.assertEqual(result.raw_values["Цинк"], 8.5)

    def test_extract_lab_data_from_pdf_uses_configured_default_page_limit_of_twenty(self) -> None:
        class _FakePage:
            def __init__(self, index: int) -> None:
                self.index = index

            def extract_text(self) -> str:
                return f"Glucose {self.index} mmol/L"

        class _FakePdf:
            def __init__(self, page_count: int) -> None:
                self.pages = [_FakePage(index + 1) for index in range(page_count)]

            def __enter__(self) -> "_FakePdf":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        fake_pdfplumber = type("_FakePdfPlumber", (), {"open": lambda self, _: _FakePdf(25)})()
        with patch("parser.extract_pdf.pdfplumber", new=fake_pdfplumber):
            result = extract_lab_data_from_pdf("/tmp/fake.pdf")

        self.assertEqual(result["Глюкоза"], 20.0)

    def test_extract_lab_data_from_pdf_preserves_explicit_shorter_page_limit(self) -> None:
        class _FakePage:
            def __init__(self, index: int) -> None:
                self.index = index

            def extract_text(self) -> str:
                return f"Glucose {self.index} mmol/L"

        class _FakePdf:
            def __init__(self, page_count: int) -> None:
                self.pages = [_FakePage(index + 1) for index in range(page_count)]

            def __enter__(self) -> "_FakePdf":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        fake_pdfplumber = type("_FakePdfPlumber", (), {"open": lambda self, _: _FakePdf(25)})()
        with patch("parser.extract_pdf.pdfplumber", new=fake_pdfplumber):
            result = extract_lab_data_from_pdf("/tmp/fake.pdf", max_pages=3)

        self.assertEqual(result["Глюкоза"], 3.0)


if __name__ == "__main__":
    unittest.main()
