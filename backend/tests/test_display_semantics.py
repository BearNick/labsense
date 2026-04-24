import sys
import unittest

sys.path.insert(0, "/opt/labsense/backend")

from app.services.display_semantics import resolve_lab_value_display  # noqa: E402
from parser.postprocess import MarkerDetail  # noqa: E402


class DisplaySemanticsTests(unittest.TestCase):
    def test_percent_slots_do_not_keep_absolute_semantics(self) -> None:
        neut_percent = MarkerDetail(
            name="Нейтрофилы %",
            value=58.4,
            unit="x10^9/L",
            reference_range="1.5 - 7.7",
            confidence=8.0,
        )
        baso_percent = MarkerDetail(
            name="Базофилы %",
            value=0.7,
            unit="x10^9/L",
            reference_range="0 - 0.1",
            confidence=8.0,
        )

        neut_unit, neut_reference = resolve_lab_value_display("Нейтрофилы %", neut_percent)
        baso_unit, baso_reference = resolve_lab_value_display("Базофилы %", baso_percent)

        self.assertEqual(neut_unit, "%")
        self.assertNotEqual(neut_unit, "x10^9/L")
        self.assertEqual(neut_reference, "47 - 72")

        self.assertEqual(baso_unit, "%")
        self.assertNotEqual(baso_unit, "x10^9/L")
        self.assertEqual(baso_reference, "0 - 1")

    def test_absolute_slots_keep_absolute_semantics_and_references(self) -> None:
        cases = {
            "Нейтрофилы абс.": MarkerDetail(
                name="Нейтрофилы абс.",
                value=4.1,
                unit="x10^9/L",
                reference_range="1.8 - 7.7",
                confidence=8.0,
            ),
            "Лимфоциты абс.": MarkerDetail(
                name="Лимфоциты абс.",
                value=1.9,
                unit="x10^9/L",
                reference_range="1.0 - 4.8",
                confidence=8.0,
            ),
            "Моноциты абс.": MarkerDetail(
                name="Моноциты абс.",
                value=0.4,
                unit="x10^9/L",
                reference_range="0.2 - 0.8",
                confidence=8.0,
            ),
            "Эозинофилы абс.": MarkerDetail(
                name="Эозинофилы абс.",
                value=0.1,
                unit="x10^9/L",
                reference_range="0.0 - 0.5",
                confidence=8.0,
            ),
            "Базофилы абс.": MarkerDetail(
                name="Базофилы абс.",
                value=0.03,
                unit="x10^9/L",
                reference_range="0.0 - 0.1",
                confidence=8.0,
            ),
        }

        for name, detail in cases.items():
            unit, reference = resolve_lab_value_display(name, detail)
            self.assertEqual(unit, "x10^9/L")
            self.assertEqual(reference, detail.reference_range)

    def test_special_percent_and_absolute_slots_remain_separate(self) -> None:
        re_percent = MarkerDetail(
            name="RE-LYMP %",
            value=1.1,
            unit="x10^9/L",
            reference_range="0 - 0.3",
            confidence=8.0,
        )
        re_absolute = MarkerDetail(
            name="RE-LYMP abs",
            value=0.08,
            unit="x10^9/L",
            reference_range="0 - 0.3",
            confidence=8.0,
        )

        percent_unit, percent_reference = resolve_lab_value_display("RE-LYMP %", re_percent)
        absolute_unit, absolute_reference = resolve_lab_value_display("RE-LYMP abs", re_absolute)

        self.assertEqual(percent_unit, "%")
        self.assertEqual(percent_reference, "0 - 5")
        self.assertEqual(absolute_unit, "x10^9/L")
        self.assertEqual(absolute_reference, "0 - 0.3")


if __name__ == "__main__":
    unittest.main()
