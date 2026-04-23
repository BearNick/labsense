import io
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense/backend")

try:
    from fastapi import UploadFile  # noqa: E402
    from app.services.parser_service import ParserService  # noqa: E402
    from parser.postprocess import MarkerDetail, TextPostprocessResult  # noqa: E402
    HAVE_PARSER_SERVICE_DEPS = True
except Exception:
    UploadFile = None  # type: ignore[assignment]
    ParserService = None  # type: ignore[assignment]
    MarkerDetail = None  # type: ignore[assignment]
    TextPostprocessResult = None  # type: ignore[assignment]
    HAVE_PARSER_SERVICE_DEPS = False


class ParserServiceRegressionTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_PARSER_SERVICE_DEPS, "parser service dependencies are not installed")
    @patch("app.services.parser_service.preprocess_extracted_data")
    @patch("app.services.parser_service.extract_legacy_text_with_details")
    def test_parse_upload_preserves_extracted_marker_details_for_ui_propagation(
        self,
        extract_legacy_text_with_details,
        preprocess_extracted_data,
    ) -> None:
        detail = MarkerDetail(
            name="Натрий",
            value=141.0,
            unit="mmol/L",
            reference_range="135-145",
            source_text="Sodium 141 mmol/L (135-145)",
            confidence=7.5,
        )
        extract_legacy_text_with_details.return_value = TextPostprocessResult(
            raw_values={"Натрий": 141.0},
            marker_details={"Натрий": detail},
        )
        preprocess_extracted_data.return_value = (
            {"Натрий": 141.0},
            {"Натрий": detail},
            object(),
        )

        upload = UploadFile(filename="chemistry.pdf", file=io.BytesIO(b"%PDF-1.4"))

        result = ParserService().parse_upload(upload, language="en")

        self.assertEqual(result.raw_values, {"Натрий": 141.0})
        self.assertIn("Натрий", result.marker_details)
        self.assertEqual(result.marker_details["Натрий"].reference_range, "135-145")
        self.assertEqual(result.marker_details["Натрий"].unit, "mmol/L")


if __name__ == "__main__":
    unittest.main()
