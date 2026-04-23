import io
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

try:
    from fastapi.testclient import TestClient  # noqa: E402
    from api.main import app  # noqa: E402
    from api.services import build_lab_value_payloads, parse_lab_pdf  # noqa: E402
    from parser.postprocess import MarkerDetail, TextPostprocessResult  # noqa: E402
    from parser.source_selection import ParserSelectionResult  # noqa: E402
    HAVE_API_DEPS = True
except Exception:
    TestClient = None  # type: ignore[assignment]
    app = None  # type: ignore[assignment]
    build_lab_value_payloads = None  # type: ignore[assignment]
    parse_lab_pdf = None  # type: ignore[assignment]
    MarkerDetail = None  # type: ignore[assignment]
    TextPostprocessResult = None  # type: ignore[assignment]
    ParserSelectionResult = None  # type: ignore[assignment]
    HAVE_API_DEPS = False


WESTERN_REFERENCE_CASES = {
    "Sodium": ("135-145", "mmol/L", 141.0),
    "Potassium": ("3.5-5.1", "mmol/L", 4.1),
    "Chloride": ("95-110", "mmol/L", 99.0),
    "Urea": ("3.0-10.0", "mmol/L", 7.1),
    "Creatinine": ("44-110", "umol/L", 88.0),
    "Uric Acid": ("0.15-0.45", "mmol/L", 0.21),
    "AST": ("< 41", "U/L", 33.0),
    "ALT": ("< 51", "U/L", 25.0),
    "Glucose": ("3.9 - 6.0", "mmol/L", 5.6),
    "Urine Albumin": ("< 20.1", "mg/L", 1.5),
    "Urine Creatinine": ("4.00-25.00", "mmol/L", 16.8),
    "ACR": ("< 3.5", "mg Alb/mmol", 0.1),
}


def _marker_detail(name: str, reference_range: str, unit: str, value: float) -> "MarkerDetail":
    return MarkerDetail(
        name=name,
        value=value,
        unit=unit,
        reference_range=reference_range,
        source_text=f"{name} {value} {unit} ({reference_range})",
        confidence=8.0,
    )


class ApiReferencePropagationTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_API_DEPS, "api dependencies are not installed")
    @patch("api.services.preprocess_extracted_data")
    @patch("api.services.extract_legacy_text_with_details")
    def test_parse_lab_pdf_preserves_extracted_inline_reference_ranges(
        self,
        extract_legacy_text_with_details_mock,
        preprocess_extracted_data_mock,
    ) -> None:
        marker_details = {
            name: _marker_detail(name, reference_range, unit, value)
            for name, (reference_range, unit, value) in WESTERN_REFERENCE_CASES.items()
        }
        raw_values = {name: value for name, (_, _, value) in WESTERN_REFERENCE_CASES.items()}
        extract_legacy_text_with_details_mock.return_value = TextPostprocessResult(
            raw_values=raw_values,
            marker_details=marker_details,
        )
        preprocess_extracted_data_mock.return_value = (raw_values, marker_details, object())

        from fastapi import UploadFile

        result = parse_lab_pdf(UploadFile(filename="western-chemistry.pdf", file=io.BytesIO(b"%PDF-1.4")), language="en")

        self.assertEqual(result.marker_details["Sodium"].reference_range, "135-145")
        self.assertEqual(result.marker_details["AST"].reference_range, "< 41")
        self.assertEqual(result.marker_details["Glucose"].reference_range, "3.9 - 6.0")
        self.assertEqual(result.marker_details["Urine Albumin"].reference_range, "< 20.1")
        self.assertEqual(result.marker_details["ACR"].reference_range, "< 3.5")

    @unittest.skipUnless(HAVE_API_DEPS, "api dependencies are not installed")
    def test_build_lab_value_payloads_keep_extracted_reference_ranges(self) -> None:
        raw_values = {name: value for name, (_, _, value) in WESTERN_REFERENCE_CASES.items()}
        marker_details = {
            name: _marker_detail(name, reference_range, unit, value)
            for name, (reference_range, unit, value) in WESTERN_REFERENCE_CASES.items()
        }

        payloads = build_lab_value_payloads(raw_values, marker_details)
        payload_by_name = {item["name"]: item for item in payloads}

        self.assertEqual(payload_by_name["Sodium"]["reference_range"], "135-145")
        self.assertEqual(payload_by_name["AST"]["reference_range"], "< 41")
        self.assertEqual(payload_by_name["Glucose"]["reference_range"], "3.9 - 6.0")
        self.assertEqual(payload_by_name["Urine Albumin"]["reference_range"], "< 20.1")
        self.assertEqual(payload_by_name["ACR"]["reference_range"], "< 3.5")

    @unittest.skipUnless(HAVE_API_DEPS, "api dependencies are not installed")
    @patch("api.main.parse_lab_pdf")
    def test_upload_route_exposes_reference_ranges_in_api_payload(self, parse_lab_pdf_mock) -> None:
        raw_values = {name: value for name, (_, _, value) in WESTERN_REFERENCE_CASES.items()}
        marker_details = {
            name: _marker_detail(name, reference_range, unit, value)
            for name, (reference_range, unit, value) in WESTERN_REFERENCE_CASES.items()
        }
        parse_lab_pdf_mock.return_value = ParserSelectionResult(
            raw_values=raw_values,
            marker_details=marker_details,
            source="pdfplumber",
            selected_source="text",
            selection_reason="legacy_text_baseline",
            initial_source="text",
            final_source="text",
            fallback_used=False,
            fallback_reason=None,
            confidence_score=100,
            confidence_level="high",
            confidence_reasons=["legacy_text_baseline"],
            confidence_explanation="Legacy baseline text extraction path is active.",
            reference_coverage=0.0,
            unit_coverage=0.0,
            structural_consistency=1.0,
            warnings=[],
        )

        client = TestClient(app)
        response = client.post(
            "/upload-lab-pdf",
            files={"file": ("western-chemistry.pdf", b"%PDF-1.4", "application/pdf")},
            data={"language": "en"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        value_by_name = {item["name"]: item for item in payload["values"]}
        self.assertEqual(value_by_name["Sodium"]["reference_range"], "135-145")
        self.assertEqual(value_by_name["AST"]["reference_range"], "< 41")
        self.assertEqual(value_by_name["Glucose"]["reference_range"], "3.9 - 6.0")
        self.assertEqual(value_by_name["Urine Albumin"]["reference_range"], "< 20.1")
        self.assertEqual(value_by_name["ACR"]["reference_range"], "< 3.5")


if __name__ == "__main__":
    unittest.main()
