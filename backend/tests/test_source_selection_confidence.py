import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense/backend")

from parser.source_selection import (  # noqa: E402
    ExtractionAssessment,
    TextInspection,
    _decide_source,
    _build_confidence,
    _normalize_fraction,
    _safe_fraction,
    select_and_extract_lab_data,
)


class SourceSelectionConfidenceTests(unittest.TestCase):
    def _inspection(self, *, refs: int, meaningful: int, garbage: float) -> TextInspection:
        return TextInspection(
            raw_text="sample",
            char_count=500,
            word_count=90,
            meaningful_lines=meaningful,
            numeric_count=20,
            reference_count=refs,
            garbage_ratio=garbage,
            image_pages=0,
            text_pages=1,
            total_pages=1,
            text_markers={"ALT": 21.0, "AST": 20.0},
        )

    def test_machine_readable_tables_prefer_text(self) -> None:
        selected, reason = _decide_source(
            TextInspection(
                raw_text="sample",
                char_count=240,
                word_count=45,
                meaningful_lines=4,
                numeric_count=16,
                reference_count=2,
                garbage_ratio=0.01,
                image_pages=1,
                text_pages=1,
                total_pages=1,
                text_markers={"ALT": 21.0, "AST": 20.0, "CRP": 8.4},
                table_row_count=8,
            ),
            vision_available=True,
        )

        self.assertEqual(selected, "text")
        self.assertEqual(reason, "machine_readable_tables_detected")

    def test_high_confidence_for_strong_text_extraction(self) -> None:
        result = _build_confidence(
            inspection=self._inspection(refs=4, meaningful=8, garbage=0.01),
            final_source="text",
            final_assessment=ExtractionAssessment(
                source="text",
                marker_count=10,
                populated_ratio=0.7,
                weak=False,
                weak_reason=None,
            ),
            fallback_used=False,
            fallback_reason=None,
            selection_reason="strong_text_marker_match",
        )
        self.assertEqual(result.level, "high")
        self.assertGreaterEqual(result.score, 80)

    def test_medium_confidence_for_usable_vision_output(self) -> None:
        result = _build_confidence(
            inspection=self._inspection(refs=0, meaningful=1, garbage=0.02),
            final_source="vision",
            final_assessment=ExtractionAssessment(
                source="vision",
                marker_count=5,
                populated_ratio=0.1,
                weak=False,
                weak_reason=None,
            ),
            fallback_used=False,
            fallback_reason=None,
            selection_reason="image_heavy_pdf",
        )
        self.assertEqual(result.level, "medium")
        self.assertGreaterEqual(result.score, 55)
        self.assertLess(result.score, 80)

    def test_low_confidence_when_fallback_and_weak_signals_stack(self) -> None:
        result = _build_confidence(
            inspection=self._inspection(refs=0, meaningful=1, garbage=0.18),
            final_source="vision",
            final_assessment=ExtractionAssessment(
                source="vision",
                marker_count=2,
                populated_ratio=0.03,
                weak=True,
                weak_reason="too_few_markers_from_vision",
            ),
            fallback_used=True,
            fallback_reason="text_weak:poor_text_structure",
            selection_reason="text_fallback_to_limited_vision;initial=weak_text_signal",
        )
        self.assertEqual(result.level, "low")
        self.assertLess(result.score, 55)

    def test_safe_fraction_clamps_overflow_and_handles_zero_division(self) -> None:
        self.assertEqual(_safe_fraction(3, 2), 1.0)
        self.assertEqual(_safe_fraction(1, 0), 0.0)

    def test_normalize_fraction_handles_percent_like_and_invalid_values(self) -> None:
        self.assertEqual(_normalize_fraction(80), 0.8)
        self.assertEqual(_normalize_fraction(1.2), 1.0)
        self.assertEqual(_normalize_fraction(float("nan")), 0.0)

    @patch("parser.source_selection.extract_lab_data_via_vision")
    @patch("parser.source_selection._inspect_pdf_text")
    def test_selection_result_applies_canonical_merge_to_vision_output(
        self,
        inspect_pdf_text,
        extract_lab_data_via_vision,
    ) -> None:
        inspect_pdf_text.return_value = TextInspection(
            raw_text="",
            char_count=20,
            word_count=3,
            meaningful_lines=0,
            numeric_count=2,
            reference_count=0,
            garbage_ratio=0.0,
            image_pages=1,
            text_pages=0,
            total_pages=1,
            text_markers={},
            text_marker_details={},
        )
        extract_lab_data_via_vision.return_value = {"Эритроциты": 0.0, "RBC": 4.98}

        result = select_and_extract_lab_data("/tmp/sample.pdf", max_pages=1)

        self.assertEqual(result.source, "vision")
        self.assertEqual(result.raw_values, {"Эритроциты": 4.98})
        self.assertEqual(result.marker_details["Эритроциты"].value, 4.98)


if __name__ == "__main__":
    unittest.main()
