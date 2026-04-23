from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from parser.config import MAX_PDF_PAGES
from parser.format_normalization import preprocess_extracted_data
from parser.postprocess import extract_legacy_text_with_details
from parser.source_selection import ParserSelectionResult, normalize_raw_values


class ParserService:
    def parse_upload(self, upload: UploadFile, language: str = "en") -> ParserSelectionResult:
        suffix = Path(upload.filename or "analysis.pdf").suffix or ".pdf"
        with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            tmp.write(upload.file.read())
            tmp.flush()
            text_result = extract_legacy_text_with_details(tmp.name, max_pages=MAX_PDF_PAGES)
            raw_values = normalize_raw_values(text_result.raw_values)
            _, marker_details, _ = preprocess_extracted_data(
                raw_values=text_result.raw_values,
                marker_details=text_result.marker_details,
                raw_text="",
                language_hint=language,
            )
            extracted_count = sum(1 for value in raw_values.values() if value is not None)
            return ParserSelectionResult(
                raw_values=raw_values,
                marker_details=marker_details,
                source="pdfplumber",
                selected_source="text",
                selection_reason="legacy_text_baseline",
                initial_source="text",
                final_source="text",
                fallback_used=False,
                fallback_reason=None,
                confidence_score=100 if extracted_count else 0,
                confidence_level="high" if extracted_count else "low",
                confidence_reasons=["legacy_text_baseline"],
                confidence_explanation="Legacy baseline text extraction path is active.",
                reference_coverage=0.0,
                unit_coverage=0.0,
                structural_consistency=1.0 if extracted_count else 0.0,
                warnings=[],
            )
