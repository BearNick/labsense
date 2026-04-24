import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense/backend")

from parser.postprocess import (  # noqa: E402
    MarkerDetail,
    build_marker_detail_from_text,
    build_marker_detail_from_row,
    merge_canonical_markers,
)


class PostprocessRegressionTests(unittest.TestCase):
    def test_recovers_russian_units_and_split_ranges_from_table_row(self) -> None:
        rows = [["Эритроциты", "4,98", "10^12/л", "3,8 5,8"]]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.name, "Эритроциты")
        self.assertEqual(detail.value, 4.98)
        self.assertEqual(detail.unit, "x10^12/L")
        self.assertEqual(detail.reference_range, "3.8 - 5.8")

    def test_recovers_reference_and_unit_from_same_table_row(self) -> None:
        rows = [["CRP", "8.4", "mg/L", "0 - 5"]]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.name, "CRP")
        self.assertEqual(detail.value, 8.4)
        self.assertEqual(detail.unit, "mg/L")
        self.assertEqual(detail.reference_range, "0 - 5")
        self.assertFalse(detail.reference_recovered)

    def test_inline_parenthetical_references_are_captured_from_text_lines(self) -> None:
        sodium = build_marker_detail_from_text("Sodium 141 mmol/L (135-145)")
        ast = build_marker_detail_from_text("AST 33 U/L (< 41)")
        glucose = build_marker_detail_from_text("Glucose 5.6 mmol/L (3.9 - 6.0)")

        self.assertIsNotNone(sodium)
        self.assertEqual(sodium.reference_range, "135-145")
        self.assertIsNotNone(ast)
        self.assertEqual(ast.reference_range, "< 41")
        self.assertIsNotNone(glucose)
        self.assertEqual(glucose.reference_range, "3.9 - 6.0")

    def test_recovers_reference_from_wrapped_neighbor_row_only_when_safe(self) -> None:
        rows = [
            ["Глюкоза", "5.2", "mmol/L", ""],
            ["", "", "", "3.9 - 5.5"],
        ]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.reference_range, "3.9 - 5.5")
        self.assertTrue(detail.reference_recovered)

    def test_recovers_unit_and_reference_from_adjacent_columns(self) -> None:
        rows = [["Platelets", "", "250", "x10^9/L", "150 - 400"]]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.name, "Тромбоциты")
        self.assertEqual(detail.value, 250.0)
        self.assertEqual(detail.unit, "x10^9/L")
        self.assertEqual(detail.reference_range, "150 - 400")

    def test_table_reference_columns_still_beat_inline_parenthetical_references(self) -> None:
        rows = [["AST 33 U/L (< 41)", "", "", "0 - 40"]]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.reference_range, "0 - 40")

    def test_does_not_recover_reference_from_neighbor_with_other_marker(self) -> None:
        rows = [
            ["ALT", "21", "U/L", ""],
            ["AST", "20", "U/L", "0 - 40"],
        ]

        detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertIsNone(detail.reference_range)

    def test_whitelisted_simple_rows_return_before_generic_cell_selection(self) -> None:
        rows = [["АЛТ", "9.2", "Ед/л", "< 33"]]

        with patch("parser.postprocess.extract_value", side_effect=AssertionError("smart path should be skipped")):
            with self.assertLogs("parser.postprocess", level="DEBUG") as captured:
                detail = build_marker_detail_from_row(rows, 0)

        self.assertIsNotNone(detail)
        self.assertEqual(detail.value, 9.2)
        self.assertTrue(any("marker=ALT path=whitelist_override value=9.2" in line for line in captured.output))

    def test_canonical_merge_keeps_existing_single_marker_name(self) -> None:
        raw_values = {"Гемоглобин": 135.0}
        details = {
            "Гемоглобин": MarkerDetail(
                name="Гемоглобин",
                value=135.0,
                unit="g/L",
                reference_range="120 - 170",
                confidence=7.5,
            )
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Гемоглобин": 135.0})
        self.assertIn("Гемоглобин", merged_details)

    def test_canonical_merge_collapses_synonyms_and_preserves_best_metadata(self) -> None:
        raw_values = {"CRP": 8.4, "С-реактивный белок": 8.4}
        details = {
            "CRP": MarkerDetail(name="CRP", value=8.4, confidence=4.0),
            "С-реактивный белок": MarkerDetail(
                name="С-реактивный белок",
                value=8.4,
                unit="mg/L",
                reference_range="0 - 5",
                confidence=7.0,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"CRP": 8.4})
        self.assertEqual(merged_details["CRP"].unit, "mg/L")
        self.assertEqual(merged_details["CRP"].reference_range, "0 - 5")

    def test_canonical_merge_collapses_common_blood_synonyms(self) -> None:
        raw_values = {"Platelets": 240.0, "Тромбоциты": 240.0}
        details = {
            "Platelets": MarkerDetail(name="Platelets", value=240.0, confidence=4.0),
            "Тромбоциты": MarkerDetail(
                name="Тромбоциты",
                value=240.0,
                unit="x10^9/L",
                reference_range="150 - 400",
                confidence=7.0,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Тромбоциты": 240.0})
        self.assertEqual(merged_details["Тромбоциты"].unit, "x10^9/L")
        self.assertEqual(merged_details["Тромбоциты"].reference_range, "150 - 400")

    def test_canonical_merge_preserves_non_zero_rbc_over_zero_localized_duplicate(self) -> None:
        raw_values = {
            "Эритроциты": 0.0,
            "RBC": 4.98,
            "Гемоглобин": 148.1,
            "Тромбоциты": 298.0,
        }
        details = {
            "Эритроциты": MarkerDetail(
                name="Эритроциты",
                value=0.0,
                source_text="Эритроциты 0",
                confidence=4.0,
            ),
            "RBC": MarkerDetail(
                name="RBC",
                value=4.98,
                unit="x10^12/L",
                source_text="Эритроциты (RBC) 4,98 10^12/л",
                confidence=6.0,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values["Эритроциты"], 4.98)
        self.assertEqual(merged_details["Эритроциты"].value, 4.98)
        self.assertEqual(merged_details["Эритроциты"].unit, "x10^12/L")
        self.assertEqual(merged_values["Гемоглобин"], 148.1)
        self.assertEqual(merged_values["Тромбоциты"], 298.0)

    def test_canonical_merge_prefers_non_zero_value_for_dict_backed_details(self) -> None:
        raw_values = {"Эритроциты": 0.0, "RBC": 4.98}
        details = {
            "Эритроциты": {"name": "Эритроциты", "value": 0.0, "confidence": 4.0},
            "RBC": {"name": "RBC", "value": 4.98, "unit": "x10^12/L", "confidence": 6.0},
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)  # type: ignore[arg-type]

        self.assertEqual(merged_values, {"Эритроциты": 4.98})
        self.assertEqual(merged_details["Эритроциты"].value, 4.98)
        self.assertEqual(merged_details["Эритроциты"].unit, "x10^12/L")

    def test_canonical_merge_prefers_hgb_candidate_by_value_quality_not_name(self) -> None:
        raw_values = {"Гемоглобин": 0.0, "HGB": 148.0, "Hb": 147.0}
        details = {
            "Гемоглобин": MarkerDetail(name="Гемоглобин", value=0.0, confidence=5.0),
            "HGB": MarkerDetail(
                name="HGB",
                value=148.0,
                unit="g/L",
                reference_range="120 - 170",
                confidence=7.0,
            ),
            "Hb": MarkerDetail(name="Hb", value=147.0, unit="g/L", confidence=6.0),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Гемоглобин": 148.0})
        self.assertEqual(merged_details["Гемоглобин"].value, 148.0)
        self.assertEqual(merged_details["Гемоглобин"].reference_range, "120 - 170")

    def test_canonical_merge_prefers_plt_candidate_over_zero_localized_duplicate(self) -> None:
        raw_values = {"Тромбоциты": 0.0, "PLT": 240.0}
        details = {
            "Тромбоциты": MarkerDetail(name="Тромбоциты", value=0.0, confidence=4.0),
            "PLT": MarkerDetail(
                name="PLT",
                value=240.0,
                unit="x10^9/L",
                reference_range="150 - 400",
                confidence=6.5,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Тромбоциты": 240.0})
        self.assertEqual(merged_details["Тромбоциты"].value, 240.0)
        self.assertEqual(merged_details["Тромбоциты"].unit, "x10^9/L")

    def test_canonical_merge_prefers_wbc_candidate_with_reference_and_unit(self) -> None:
        raw_values = {"Лейкоциты": 4.2, "WBC": 4.2}
        details = {
            "Лейкоциты": MarkerDetail(name="Лейкоциты", value=4.2, confidence=5.0),
            "WBC": MarkerDetail(
                name="WBC",
                value=4.2,
                unit="x10^9/L",
                reference_range="4.0 - 10.0",
                confidence=5.0,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Лейкоциты": 4.2})
        self.assertEqual(merged_details["Лейкоциты"].unit, "x10^9/L")
        self.assertEqual(merged_details["Лейкоциты"].reference_range, "4.0 - 10.0")

    def test_canonical_merge_prefers_plausible_rbc_value_over_extreme_artifact(self) -> None:
        raw_values = {"Эритроциты": 498.0, "RBC": 4.98}
        details = {
            "Эритроциты": MarkerDetail(name="Эритроциты", value=498.0, confidence=9.0),
            "RBC": MarkerDetail(
                name="RBC",
                value=4.98,
                unit="x10^12/L",
                reference_range="3.8 - 5.8",
                confidence=6.0,
            ),
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, details)

        self.assertEqual(merged_values, {"Эритроциты": 4.98})
        self.assertEqual(merged_details["Эритроциты"].value, 4.98)

    def test_canonical_merge_keeps_biologically_distinct_cbc_markers_separate(self) -> None:
        raw_values = {
            "Эритроциты": 4.98,
            "Нормобласты": 0.0,
            "Лимфоциты %": 32.70,
            "Лимфоциты абс.": 1.37,
            "RE-LYMP abs": 0.08,
            "AS-LYMP abs": 0.01,
        }

        merged_values, merged_details = merge_canonical_markers(raw_values, {})

        self.assertEqual(merged_values["Эритроциты"], 4.98)
        self.assertEqual(merged_values["Нормобласты"], 0.0)
        self.assertEqual(merged_values["Лимфоциты %"], 32.70)
        self.assertEqual(merged_values["Лимфоциты абс."], 1.37)
        self.assertEqual(merged_values["RE-LYMP abs"], 0.08)
        self.assertEqual(merged_values["AS-LYMP abs"], 0.01)
        self.assertEqual(merged_details, {})


if __name__ == "__main__":
    unittest.main()
