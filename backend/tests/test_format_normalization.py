import sys
import unittest

sys.path.insert(0, "/opt/labsense/backend")

from parser.format_normalization import detect_report_format, preprocess_extracted_data  # noqa: E402
from parser.postprocess import MarkerDetail  # noqa: E402
from parser.source_selection import normalize_raw_values  # noqa: E402


class FormatNormalizationTests(unittest.TestCase):
    def test_detects_russian_eu_format_from_cyrillic_units_and_commas(self) -> None:
        profile = detect_report_format(
            raw_text="Эритроциты 4,98 10^12/л\nГемоглобин 148,10 г/л\nВитамин D 29 нг/мл 30 100",
            language_hint="ru",
        )

        self.assertEqual(profile.region, "ru_eu")
        self.assertEqual(profile.decimal_separator, ",")
        self.assertEqual(profile.unit_style, "cyrillic")
        self.assertFalse(profile.mixed)

    def test_detects_us_format_from_dot_decimals_and_us_units(self) -> None:
        profile = detect_report_format(
            raw_text="Hemoglobin 14.8 g/dL\nGlucose 92 mg/dL\nPlatelets 298 x10^9/L",
            language_hint="en",
        )

        self.assertEqual(profile.region, "us")
        self.assertEqual(profile.decimal_separator, ".")
        self.assertEqual(profile.unit_style, "latin")

    def test_detects_mixed_format_when_signals_conflict(self) -> None:
        profile = detect_report_format(
            raw_text="Glucose 5,6 mmol/L\nHemoglobin 14.8 g/dL",
            language_hint="en",
        )

        self.assertEqual(profile.region, "mixed")
        self.assertTrue(profile.mixed)

    def test_preprocess_normalizes_russian_marker_details_without_rescaling(self) -> None:
        raw_values = {
            "Эритроциты": "4,98",
            "Гемоглобин": "148,10",
            "Тромбоциты": "298",
            "Лейкоциты": "4,19",
            "Витамин D (25-OH)": "29",
            "Цинк": "8,5",
        }
        marker_details = {
            "Эритроциты": MarkerDetail(
                name="Эритроциты",
                value=4.98,
                unit=None,
                reference_range=None,
                source_text="Эритроциты 4,98 10^12/л 3,8 5,8",
            ),
            "Гемоглобин": MarkerDetail(
                name="Гемоглобин",
                value=148.1,
                unit=None,
                reference_range=None,
                source_text="Гемоглобин 148,10 г/л 120 170",
            ),
            "Тромбоциты": MarkerDetail(
                name="Тромбоциты",
                value=298.0,
                unit=None,
                reference_range=None,
                source_text="Тромбоциты 298 10^9/л 150 400",
            ),
            "Лейкоциты": MarkerDetail(
                name="Лейкоциты",
                value=4.19,
                unit=None,
                reference_range=None,
                source_text="Лейкоциты 4,19 10^9/л 4,0 10,0",
            ),
            "Витамин D (25-OH)": MarkerDetail(
                name="Витамин D (25-OH)",
                value=29.0,
                unit=None,
                reference_range=None,
                source_text="Витамин D (25-OH) 29 нг/мл 30 100",
            ),
            "Цинк": MarkerDetail(
                name="Цинк",
                value=8.5,
                unit=None,
                reference_range=None,
                source_text="Цинк 8,5 мкмоль/л",
            ),
        }

        normalized_values, normalized_details, profile = preprocess_extracted_data(
            raw_values=raw_values,
            marker_details=marker_details,
            raw_text="\n".join(detail.source_text for detail in marker_details.values()),
            language_hint="ru",
        )

        self.assertEqual(profile.region, "ru_eu")
        self.assertEqual(normalized_values["Эритроциты"], 4.98)
        self.assertEqual(normalized_values["Гемоглобин"], 148.1)
        self.assertEqual(normalized_values["Тромбоциты"], 298.0)
        self.assertEqual(normalized_values["Лейкоциты"], 4.19)
        self.assertEqual(normalized_values["Витамин D (25-OH)"], 29.0)
        self.assertEqual(normalized_values["Цинк"], 8.5)
        self.assertEqual(normalized_details["Эритроциты"].unit, "x10^12/L")
        self.assertEqual(normalized_details["Эритроциты"].reference_range, "3.8 - 5.8")
        self.assertEqual(normalized_details["Гемоглобин"].unit, "g/L")
        self.assertEqual(normalized_details["Тромбоциты"].unit, "x10^9/L")
        self.assertEqual(normalized_details["Лейкоциты"].unit, "x10^9/L")
        self.assertEqual(normalized_details["Витамин D (25-OH)"].unit, "ng/mL")
        self.assertEqual(normalized_details["Витамин D (25-OH)"].reference_range, "30 - 100")
        self.assertEqual(normalized_details["Цинк"].unit, "µmol/L")

    def test_preprocess_keeps_us_values_and_units_stable(self) -> None:
        raw_values = {
            "Hemoglobin": "14.8",
            "Glucose": "92",
            "Platelets": "298",
        }
        marker_details = {
            "Hemoglobin": MarkerDetail(
                name="Hemoglobin",
                value=14.8,
                unit="g/dL",
                reference_range="12 - 17",
                source_text="Hemoglobin 14.8 g/dL 12 - 17",
            ),
            "Glucose": MarkerDetail(
                name="Glucose",
                value=92.0,
                unit="mg/dL",
                reference_range="70 - 99",
                source_text="Glucose 92 mg/dL 70 - 99",
            ),
        }

        normalized_values, normalized_details, profile = preprocess_extracted_data(
            raw_values=raw_values,
            marker_details=marker_details,
            raw_text="Hemoglobin 14.8 g/dL\nGlucose 92 mg/dL\nPlatelets 298 x10^9/L",
            language_hint="en",
        )

        self.assertEqual(profile.region, "us")
        self.assertEqual(normalized_values["Hemoglobin"], 14.8)
        self.assertEqual(normalized_values["Glucose"], 92.0)
        self.assertEqual(normalized_details["Hemoglobin"].unit, "g/dL")
        self.assertEqual(normalized_details["Glucose"].unit, "mg/dL")

    def test_preprocess_recognizes_new_international_unit_aliases_without_value_conversion(self) -> None:
        raw_values = {
            "RBC": "5.0",
            "WBC": "6.0",
            "HbA1c": "33",
            "ACR": "0.1",
        }
        marker_details = {
            "RBC": MarkerDetail(
                name="RBC",
                value=5.0,
                unit="M/uL",
                reference_range=None,
                source_text="RBC 5.0 M/uL",
            ),
            "WBC": MarkerDetail(
                name="WBC",
                value=6.0,
                unit="K/uL",
                reference_range=None,
                source_text="WBC 6.0 K/uL",
            ),
            "HbA1c": MarkerDetail(
                name="HbA1c",
                value=33.0,
                unit="mmol/mol",
                reference_range=None,
                source_text="HbA1c 33 mmol/mol",
            ),
            "ACR": MarkerDetail(
                name="ACR",
                value=0.1,
                unit="mg Alb/mmol",
                reference_range="<0.1",
                source_text="ACR <0.1 mg Alb/mmol",
            ),
        }

        normalized_values, normalized_details, _ = preprocess_extracted_data(
            raw_values=raw_values,
            marker_details=marker_details,
            raw_text="\n".join(detail.source_text for detail in marker_details.values()),
            language_hint="en",
        )

        self.assertEqual(normalized_values["RBC"], 5.0)
        self.assertEqual(normalized_details["RBC"].unit, "M/uL")
        self.assertEqual(normalized_values["WBC"], 6.0)
        self.assertEqual(normalized_details["WBC"].unit, "K/uL")
        self.assertEqual(normalized_values["HbA1c"], 33.0)
        self.assertEqual(normalized_details["HbA1c"].unit, "mmol/mol")
        self.assertEqual(normalized_values["ACR"], 0.1)
        self.assertEqual(normalized_details["ACR"].unit, "mg Alb/mmol")

    def test_preprocess_preserves_already_working_severe_anemia_values(self) -> None:
        normalized_values, _, _ = preprocess_extracted_data(
            raw_values={
                "Hemoglobin": 68.0,
                "RBC": 2.2,
                "Hematocrit": 21.0,
                "MCV": 103.0,
                "Platelets": 290.0,
                "WBC": 6.8,
            }
        )

        self.assertEqual(normalized_values["Hemoglobin"], 68.0)
        self.assertEqual(normalized_values["RBC"], 2.2)
        self.assertEqual(normalized_values["Hematocrit"], 21.0)
        self.assertEqual(normalized_values["MCV"], 103.0)
        self.assertEqual(normalized_values["Platelets"], 290.0)
        self.assertEqual(normalized_values["WBC"], 6.8)

    def test_preprocess_preserves_known_bad_extraction_values_for_validation(self) -> None:
        normalized_values, _, _ = preprocess_extracted_data(
            raw_values={
                "RBC": 0,
                "Platelets": 29810,
                "Hemoglobin": 25,
            }
        )

        self.assertEqual(normalized_values["RBC"], 0.0)
        self.assertEqual(normalized_values["Platelets"], 29810.0)
        self.assertEqual(normalized_values["Hemoglobin"], 25.0)

    def test_preprocess_refuses_risky_value_transformations(self) -> None:
        normalized_values, _, _ = preprocess_extracted_data(
            raw_values={
                "Hemoglobin": "148,10 120 170",
                "Glucose": "56",
                "Platelets": "298 10^9/л",
            }
        )

        self.assertIsNone(normalized_values["Hemoglobin"])
        self.assertEqual(normalized_values["Glucose"], 56.0)
        self.assertEqual(normalized_values["Platelets"], 298.0)

    def test_preprocess_recovers_scientific_units_and_references_from_source_text(self) -> None:
        _, normalized_details, _ = preprocess_extracted_data(
            raw_values={},
            marker_details={
                "Эритроциты": MarkerDetail(
                    name="Эритроциты",
                    value=None,
                    unit=None,
                    reference_range=None,
                    source_text="Эритроциты 4,98 10^12/л 3,5 - 6,2",
                ),
                "Тромбоциты": MarkerDetail(
                    name="Тромбоциты",
                    value=None,
                    unit=None,
                    reference_range=None,
                    source_text="Тромбоциты 298 10^9/л 150 400",
                ),
                "АЛТ": MarkerDetail(
                    name="АЛТ",
                    value=32.0,
                    unit=None,
                    reference_range=None,
                    source_text="АЛТ 32 ед/л < 40",
                ),
            },
            raw_text="Эритроциты 4,98 10^12/л 3,5 - 6,2\nТромбоциты 298 10^9/л 150 400\nАЛТ 32 ед/л < 40",
            language_hint="ru",
        )

        self.assertEqual(normalized_details["Эритроциты"].value, 4.98)
        self.assertEqual(normalized_details["Эритроциты"].unit, "x10^12/L")
        self.assertEqual(normalized_details["Эритроциты"].reference_range, "3.5 - 6.2")
        self.assertEqual(normalized_details["Тромбоциты"].value, 298.0)
        self.assertEqual(normalized_details["Тромбоциты"].unit, "x10^9/L")
        self.assertEqual(normalized_details["Тромбоциты"].reference_range, "150 - 400")
        self.assertEqual(normalized_details["АЛТ"].unit, "U/L")
        self.assertEqual(normalized_details["АЛТ"].reference_range, "< 40")

    def test_validation_input_path_receives_normalized_values(self) -> None:
        normalized = normalize_raw_values(
            {
                "Эритроциты": "4,98",
                "Тромбоциты": "298 10^9/л",
                "Витамин D (25-OH)": "29",
            }
        )

        self.assertEqual(normalized["Эритроциты"], 4.98)
        self.assertEqual(normalized["Тромбоциты"], 298.0)
        self.assertEqual(normalized["Витамин D (25-OH)"], 29.0)


if __name__ == "__main__":
    unittest.main()
