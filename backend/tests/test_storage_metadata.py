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


if __name__ == "__main__":
    unittest.main()
