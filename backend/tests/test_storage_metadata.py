import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/opt/labsense/backend")

try:
    from app.services.storage import LocalAnalysisStore  # noqa: E402
    from parser.postprocess import MarkerDetail  # noqa: E402
    HAVE_STORAGE_DEPS = True
except Exception:
    LocalAnalysisStore = None  # type: ignore[assignment]
    MarkerDetail = None  # type: ignore[assignment]
    HAVE_STORAGE_DEPS = False


class StorageMetadataTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_STORAGE_DEPS, "storage dependencies are not installed")
    def test_extracted_reference_and_unit_override_static_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalAnalysisStore(Path(tmpdir))
            record = store.create(
                {"CRP": 8.4},
                marker_details={
                    "CRP": MarkerDetail(
                        name="CRP",
                        value=8.4,
                        unit="mg/L",
                        reference_range="0 - 3",
                        confidence=7.0,
                    )
                },
            )

            self.assertEqual(record.values[0].unit, "mg/L")
            self.assertEqual(record.values[0].reference_range, "0 - 3")

    @unittest.skipUnless(HAVE_STORAGE_DEPS, "storage dependencies are not installed")
    def test_storage_keeps_percent_and_absolute_display_semantics_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalAnalysisStore(Path(tmpdir))
            record = store.create(
                {
                    "Нейтрофилы %": 58.4,
                    "Нейтрофилы абс.": 3.62,
                    "Базофилы %": 0.7,
                    "Базофилы абс.": 0.04,
                },
                marker_details={
                    "Нейтрофилы %": MarkerDetail(
                        name="Нейтрофилы %",
                        value=58.4,
                        unit="x10^9/L",
                        reference_range="1.5 - 7.7",
                        confidence=8.0,
                    ),
                    "Нейтрофилы абс.": MarkerDetail(
                        name="Нейтрофилы абс.",
                        value=3.62,
                        unit="x10^9/L",
                        reference_range="1.5 - 7.7",
                        confidence=8.0,
                    ),
                    "Базофилы %": MarkerDetail(
                        name="Базофилы %",
                        value=0.7,
                        unit="x10^9/L",
                        reference_range="0 - 0.1",
                        confidence=8.0,
                    ),
                    "Базофилы абс.": MarkerDetail(
                        name="Базофилы абс.",
                        value=0.04,
                        unit="x10^9/L",
                        reference_range="0 - 0.1",
                        confidence=8.0,
                    ),
                },
            )

            values_by_name = {item.name: item for item in record.values}
            self.assertEqual(values_by_name["Нейтрофилы %"].unit, "%")
            self.assertEqual(values_by_name["Нейтрофилы %"].reference_range, "47 - 72")
            self.assertEqual(values_by_name["Нейтрофилы абс."].unit, "x10^9/L")
            self.assertEqual(values_by_name["Нейтрофилы абс."].reference_range, "1.5 - 7.7")
            self.assertEqual(values_by_name["Базофилы %"].unit, "%")
            self.assertEqual(values_by_name["Базофилы %"].reference_range, "0 - 1")
            self.assertEqual(values_by_name["Базофилы абс."].unit, "x10^9/L")
            self.assertEqual(values_by_name["Базофилы абс."].reference_range, "0 - 0.1")


if __name__ == "__main__":
    unittest.main()
