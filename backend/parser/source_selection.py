from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Literal

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency in test env
    pdfplumber = None

from parser.config import resolve_pdf_page_limit
from parser.format_normalization import preprocess_extracted_data
from parser.postprocess import MarkerDetail, extract_legacy_text_with_details, merge_canonical_markers

try:
    from parser.vision_extract import extract_lab_data_via_vision
except Exception:  # pragma: no cover - preserve text parser fallback
    extract_lab_data_via_vision = None


SelectedSource = Literal["text", "vision"]
ConfidenceLevel = Literal["high", "medium", "low"]

_NUMERIC_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_REFERENCE_RE = re.compile(r"(?:\b\d+(?:[.,]\d+)?\s*[-–]\s*\d+(?:[.,]\d+)?\b|[<>≤≥]\s*\d+(?:[.,]\d+)?)")
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁёÁÉÍÓÚÜÑáéíóúüñ0-9%./:+-]+")
_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁёÁÉÍÓÚÜÑáéíóúüñ]")
_ALLOWED_SYMBOLS = set(".:,;%/()[]<>+-–=_*°µ")


@dataclass(frozen=True)
class ParserSelectionResult:
    raw_values: dict[str, float | None]
    source: str
    selected_source: SelectedSource
    selection_reason: str
    initial_source: SelectedSource
    final_source: SelectedSource
    fallback_used: bool
    fallback_reason: str | None
    confidence_score: int
    confidence_level: ConfidenceLevel
    confidence_reasons: list[str]
    confidence_explanation: str
    reference_coverage: float
    unit_coverage: float
    structural_consistency: float
    warnings: list[str]
    marker_details: dict[str, MarkerDetail] = field(default_factory=dict)


@dataclass(frozen=True)
class TextInspection:
    raw_text: str
    char_count: int
    word_count: int
    meaningful_lines: int
    numeric_count: int
    reference_count: int
    garbage_ratio: float
    image_pages: int
    text_pages: int
    total_pages: int
    text_markers: dict[str, float | None]
    text_marker_details: dict[str, MarkerDetail] = field(default_factory=dict)
    table_count: int = 0
    table_row_count: int = 0


@dataclass(frozen=True)
class ExtractionAssessment:
    source: SelectedSource
    marker_count: int
    populated_ratio: float
    weak: bool
    weak_reason: str | None
    reference_coverage: float = 0.0
    unit_coverage: float = 0.0
    structural_consistency: float = 0.0


@dataclass(frozen=True)
class ConfidenceAssessment:
    score: int
    level: ConfidenceLevel
    reasons: list[str]
    explanation: str


def normalize_raw_values(raw_values: dict[str, Any]) -> dict[str, float | None]:
    normalized_values, _, _ = preprocess_extracted_data(raw_values=raw_values)
    normalized: dict[str, float | None] = {}
    for raw_name, raw_value in normalized_values.items():
        name = str(raw_name).strip()
        if not name:
            continue
        if raw_value is None:
            normalized[name] = None
            continue
        normalized[name] = raw_value if math.isfinite(raw_value) else None
    return dict(sorted(normalized.items(), key=lambda item: item[0].lower()))


def _has_usable_values(raw_values: dict[str, float | None]) -> bool:
    return any(value is not None for value in raw_values.values())


def _count_non_null_values(raw_values: dict[str, float | None]) -> int:
    return sum(1 for value in raw_values.values() if value is not None)


def _normalize_fraction(value: float | int | None, fallback: float = 0.0) -> float:
    if value is None:
        return fallback

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback

    if not math.isfinite(numeric):
        return fallback

    # Defensive compatibility: if a percent-like value slips through, normalize it.
    if numeric > 1.0 and numeric <= 100.0 and numeric >= 5.0:
        numeric /= 100.0

    return max(0.0, min(1.0, numeric))


def _safe_fraction(numerator: int | float, denominator: int | float, fallback: float = 0.0) -> float:
    try:
        denominator_value = float(denominator)
        numerator_value = float(numerator)
    except (TypeError, ValueError):
        return fallback

    if denominator_value <= 0 or not math.isfinite(denominator_value) or not math.isfinite(numerator_value):
        return fallback

    return _normalize_fraction(numerator_value / denominator_value, fallback=fallback)


def _inspect_pdf_text(pdf_path: str, max_pages: int | None = None) -> TextInspection:
    page_limit = resolve_pdf_page_limit(max_pages)
    text_postprocess = extract_legacy_text_with_details(pdf_path, max_pages=page_limit)
    text_chunks: list[str] = []
    image_pages = 0
    text_pages = 0
    total_pages = 0
    table_count = 0
    table_row_count = 0

    try:
        if pdfplumber is None:
            raise RuntimeError("pdfplumber unavailable")

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(len(pdf.pages), page_limit)

            for index in range(total_pages):
                page = pdf.pages[index]
                page_text = (page.extract_text() or "").strip()
                text_chunks.append(page_text)
                if page_text:
                    text_pages += 1
                if getattr(page, "images", None):
                    image_pages += 1
                page_tables = page.extract_tables() or []
                table_count += len(page_tables)
                table_row_count += sum(len(table or []) for table in page_tables)
    except Exception:
        normalized_values, normalized_details, _ = preprocess_extracted_data(
            raw_values=text_postprocess.raw_values,
            marker_details=text_postprocess.marker_details,
            raw_text="",
        )
        return TextInspection(
            raw_text="",
            char_count=0,
            word_count=0,
            meaningful_lines=0,
            numeric_count=0,
            reference_count=0,
            garbage_ratio=0.0,
            image_pages=0,
            text_pages=0,
            total_pages=0,
            text_markers=normalized_values,
            text_marker_details=normalized_details,
            table_count=text_postprocess.table_count,
            table_row_count=text_postprocess.table_row_count,
        )

    raw_text = "\n".join(chunk for chunk in text_chunks if chunk)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    compact_text = "".join(raw_text.split())
    weird_char_count = sum(
        1
        for char in compact_text
        if not (char.isalnum() or char.isspace() or char in _ALLOWED_SYMBOLS)
    )
    garbage_ratio = weird_char_count / max(len(compact_text), 1)
    meaningful_lines = sum(1 for line in lines if _LETTER_RE.search(line) and _NUMERIC_RE.search(line))
    normalized_values, normalized_details, _ = preprocess_extracted_data(
        raw_values=text_postprocess.raw_values,
        marker_details=text_postprocess.marker_details,
        raw_text=raw_text,
    )
    return TextInspection(
        raw_text=raw_text,
        char_count=len(compact_text),
        word_count=len(_WORD_RE.findall(raw_text)),
        meaningful_lines=meaningful_lines,
        numeric_count=len(_NUMERIC_RE.findall(raw_text)),
        reference_count=len(_REFERENCE_RE.findall(raw_text)),
        garbage_ratio=garbage_ratio,
        image_pages=image_pages,
        text_pages=text_pages,
        total_pages=total_pages,
        text_markers=normalized_values,
        text_marker_details=normalized_details,
        table_count=table_count,
        table_row_count=table_row_count,
    )


def _decide_source(inspection: TextInspection, vision_available: bool) -> tuple[SelectedSource, str]:
    marker_count = sum(1 for value in inspection.text_markers.values() if value is not None)

    if not vision_available:
        return "text", "vision_unavailable"

    if inspection.table_row_count >= 6 and marker_count >= 3 and inspection.text_pages > 0:
        return "text", "machine_readable_tables_detected"

    if inspection.char_count < 80 or inspection.word_count < 20 or inspection.text_pages == 0:
        return "vision", "sparse_machine_text"

    if inspection.image_pages >= max(1, inspection.total_pages) and marker_count < 3 and inspection.char_count < 400:
        return "vision", "image_heavy_pdf"

    if inspection.garbage_ratio > 0.12 and marker_count < 3:
        return "vision", "garbled_text_extraction"

    if marker_count >= 5:
        return "text", "strong_text_marker_match"

    if marker_count >= 3 and (inspection.reference_count >= 1 or inspection.meaningful_lines >= 4):
        return "text", "reliable_text_extraction"

    if marker_count <= 1 and (inspection.reference_count == 0 or inspection.numeric_count < 8):
        return "vision", "weak_text_signal"

    if marker_count == 2 and inspection.reference_count == 0 and inspection.meaningful_lines < 4:
        return "vision", "incomplete_text_structure"

    return "text", "text_preferred_by_default"


def _build_selection_reason(reason: str, inspection: TextInspection) -> str:
    marker_count = _count_non_null_values(inspection.text_markers)
    return (
        f"{reason};markers={marker_count};refs={inspection.reference_count};"
        f"chars={inspection.char_count};garbage={inspection.garbage_ratio:.2f}"
    )


def _is_text_rich_pdf(inspection: TextInspection) -> bool:
    marker_count = _count_non_null_values(inspection.text_markers)
    has_machine_text = inspection.text_pages > 0 and inspection.char_count >= 80 and inspection.word_count >= 20
    has_structured_content = inspection.table_row_count >= 6 or inspection.meaningful_lines >= 6 or marker_count >= 5
    return has_machine_text and has_structured_content


def _assess_text_extraction(raw_values: dict[str, float | None], inspection: TextInspection) -> ExtractionAssessment:
    total_keys = max(len(raw_values), 1)
    marker_count = _count_non_null_values(raw_values)
    missing_value_count = sum(1 for value in raw_values.values() if value is None)
    populated_ratio = marker_count / total_keys
    populated_details = [
        detail for detail in inspection.text_marker_details.values()
        if detail.value is not None and detail.name in raw_values
    ]
    reference_count = min(sum(1 for detail in populated_details if detail.reference_range), marker_count)
    unit_count = min(sum(1 for detail in populated_details if detail.unit), marker_count)
    reference_coverage = _safe_fraction(reference_count, marker_count, fallback=0.0)
    unit_coverage = _safe_fraction(unit_count, marker_count, fallback=0.0)
    structural_consistency = min(
        1.0,
        (
            (1.0 if inspection.table_row_count >= marker_count and marker_count > 0 else 0.0)
            + reference_coverage
            + unit_coverage
        ) / 3.0,
    )

    weak_reason: str | None = None
    if marker_count == 0:
        weak_reason = "no_usable_markers"
    elif marker_count <= 1 and (inspection.reference_count == 0 or inspection.meaningful_lines < 3):
        weak_reason = "too_few_markers_for_text"
    elif marker_count <= 2 and inspection.meaningful_lines < 3 and inspection.numeric_count < 8:
        weak_reason = "poor_text_structure"
    elif missing_value_count >= marker_count and inspection.garbage_ratio > 0.12:
        weak_reason = "garbled_text_output"

    return ExtractionAssessment(
        source="text",
        marker_count=marker_count,
        populated_ratio=populated_ratio,
        weak=weak_reason is not None,
        weak_reason=weak_reason,
        reference_coverage=reference_coverage,
        unit_coverage=unit_coverage,
        structural_consistency=structural_consistency,
    )


def _assess_vision_extraction(raw_values: dict[str, float | None]) -> ExtractionAssessment:
    total_keys = max(len(raw_values), 1)
    marker_count = _count_non_null_values(raw_values)
    populated_ratio = marker_count / total_keys

    weak_reason: str | None = None
    if marker_count == 0:
        weak_reason = "no_usable_markers"
    elif marker_count == 1:
        weak_reason = "single_marker_only"
    elif marker_count == 2 and populated_ratio < 0.04:
        weak_reason = "too_few_markers_from_vision"

    return ExtractionAssessment(
        source="vision",
        marker_count=marker_count,
        populated_ratio=populated_ratio,
        weak=weak_reason is not None,
        weak_reason=weak_reason,
        structural_consistency=1.0 if marker_count >= 3 else 0.5,
    )


def _build_confidence(
    *,
    inspection: TextInspection,
    final_source: SelectedSource,
    final_assessment: ExtractionAssessment,
    fallback_used: bool,
    fallback_reason: str | None,
    selection_reason: str,
) -> ConfidenceAssessment:
    score = 55
    reasons: list[str] = []

    if final_source == "text":
        score += 10
        reasons.append("source_text")
    else:
        reasons.append("source_vision")

    marker_count = final_assessment.marker_count
    if marker_count >= 10:
        score += 20
        reasons.append("marker_count_strong")
    elif marker_count >= 5:
        score += 12
        reasons.append("marker_count_good")
    elif marker_count >= 3:
        score += 4
        reasons.append("marker_count_limited")
    elif marker_count >= 1:
        score -= 18
        reasons.append("marker_count_low")
    else:
        score -= 35
        reasons.append("marker_count_empty")

    if final_source == "text":
        if final_assessment.reference_coverage >= 0.7:
            score += 8
            reasons.append("reference_coverage_strong")
        elif final_assessment.reference_coverage >= 0.4:
            score += 3
            reasons.append("reference_coverage_partial")
        elif marker_count >= 3:
            score -= 5
            reasons.append("reference_coverage_low")

        if final_assessment.unit_coverage >= 0.7:
            score += 4
            reasons.append("unit_coverage_strong")
        elif final_assessment.unit_coverage >= 0.4:
            score += 1
            reasons.append("unit_coverage_partial")

        if inspection.reference_count >= 3:
            score += 10
            reasons.append("references_present")
        elif inspection.reference_count >= 1:
            score += 4
            reasons.append("references_partial")
        else:
            score -= 10
            reasons.append("references_missing")

        if inspection.meaningful_lines >= 6:
            score += 8
            reasons.append("structure_strong")
        elif inspection.meaningful_lines >= 3:
            score += 3
            reasons.append("structure_acceptable")
        else:
            score -= 8
            reasons.append("structure_weak")

        if inspection.garbage_ratio > 0.12:
            score -= 12
            reasons.append("text_garbled")
        elif inspection.garbage_ratio > 0.05:
            score -= 5
            reasons.append("text_noisy")
    else:
        if marker_count >= 5:
            score += 6
            reasons.append("vision_marker_coverage_good")
        if "sparse_machine_text" in selection_reason or "image_heavy_pdf" in selection_reason:
            score += 2
            reasons.append("vision_preferred_for_document_type")
        if final_assessment.populated_ratio < 0.08:
            score -= 8
            reasons.append("vision_sparse_output")

    if final_assessment.structural_consistency >= 0.75:
        score += 6
        reasons.append("structure_consistent")
    elif final_assessment.structural_consistency >= 0.4:
        score += 2
        reasons.append("structure_partially_consistent")
    elif marker_count >= 3:
        score -= 5
        reasons.append("structure_inconsistent")

    if final_assessment.weak:
        score -= 15
        reasons.append("weak_output_signal")

    if fallback_used:
        score -= 12
        reasons.append("fallback_used")

    if fallback_reason:
        reasons.append(f"fallback_reason:{fallback_reason}")

    if "retained_after_vision_check" in selection_reason or "limited_vision_retained" in selection_reason:
        score -= 8
        reasons.append("parser_disagreement_or_limited_fallback")

    score = max(0, min(100, score))
    if score >= 80:
        level: ConfidenceLevel = "high"
        explanation = "Extraction quality looks strong and structurally consistent."
    elif score >= 55:
        level = "medium"
        explanation = "Extraction quality looks usable, but some signals are limited."
    else:
        level = "low"
        explanation = "Extraction quality is limited and should be reviewed carefully."

    return ConfidenceAssessment(
        score=score,
        level=level,
        reasons=reasons,
        explanation=explanation,
    )


def select_and_extract_lab_data(
    pdf_path: str,
    language: str = "en",
    max_pages: int | None = None,
) -> ParserSelectionResult:
    warnings: list[str] = []
    page_limit = resolve_pdf_page_limit(max_pages)
    inspection = _inspect_pdf_text(pdf_path, max_pages=page_limit)
    vision_available = extract_lab_data_via_vision is not None
    preferred_source, preferred_reason = _decide_source(inspection, vision_available)
    selected_reason = _build_selection_reason(preferred_reason, inspection)
    text_values = inspection.text_markers
    text_assessment = _assess_text_extraction(text_values, inspection)

    def build_result(
        *,
        raw_values: dict[str, float | None],
        marker_details: dict[str, MarkerDetail],
        source: str,
        selected_source: SelectedSource,
        fallback_used: bool,
        fallback_reason: str | None,
        selection_reason: str,
        final_assessment: ExtractionAssessment,
    ) -> ParserSelectionResult:
        confidence = _build_confidence(
            inspection=inspection,
            final_source=selected_source,
            final_assessment=final_assessment,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            selection_reason=selection_reason,
        )
        merged_values, merged_details = merge_canonical_markers(raw_values, marker_details)
        safe_reference_coverage = _normalize_fraction(final_assessment.reference_coverage, fallback=0.0)
        safe_unit_coverage = _normalize_fraction(final_assessment.unit_coverage, fallback=0.0)
        safe_structural_consistency = _normalize_fraction(final_assessment.structural_consistency, fallback=0.0)
        return ParserSelectionResult(
            raw_values=merged_values,
            marker_details=merged_details,
            source=source,
            selected_source=selected_source,
            selection_reason=selection_reason,
            initial_source=preferred_source,
            final_source=selected_source,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            confidence_score=confidence.score,
            confidence_level=confidence.level,
            confidence_reasons=confidence.reasons,
            confidence_explanation=confidence.explanation,
            reference_coverage=safe_reference_coverage,
            unit_coverage=safe_unit_coverage,
            structural_consistency=safe_structural_consistency,
            warnings=warnings,
        )

    if _is_text_rich_pdf(inspection):
        return build_result(
            raw_values=text_values,
            marker_details=inspection.text_marker_details,
            source="pdfplumber",
            selected_source="text",
            fallback_used=False,
            fallback_reason=None,
            selection_reason=f"canonical_text_path;initial={selected_reason}",
            final_assessment=text_assessment,
        )

    if preferred_source == "text":
        if not text_assessment.weak:
            return build_result(
                raw_values=text_values,
                marker_details=inspection.text_marker_details,
                source="pdfplumber",
                selected_source="text",
                fallback_used=False,
                fallback_reason=None,
                selection_reason=selected_reason,
                final_assessment=text_assessment,
            )

        if vision_available:
            vision_values = normalize_raw_values(extract_lab_data_via_vision(pdf_path, max_pages=page_limit, lang=language))
            vision_assessment = _assess_vision_extraction(vision_values)
            if not vision_assessment.weak:
                fallback_reason = f"text_weak:{text_assessment.weak_reason}"
                warnings.append("Text extraction was too weak; vision fallback was used.")
                return build_result(
                    raw_values=vision_values,
                    marker_details={},
                    source="vision",
                    selected_source="vision",
                    fallback_used=True,
                    fallback_reason=fallback_reason,
                    selection_reason=f"text_fallback_to_vision;initial={selected_reason}",
                    final_assessment=vision_assessment,
                )

            if _has_usable_values(text_values):
                warnings.append("Text extraction looked weak, but vision fallback was weaker; text output was kept.")
                return build_result(
                    raw_values=text_values,
                    marker_details=inspection.text_marker_details,
                    source="pdfplumber",
                    selected_source="text",
                    fallback_used=False,
                    fallback_reason=None,
                    selection_reason=f"text_retained_after_vision_check;initial={selected_reason}",
                    final_assessment=text_assessment,
                )

            if _has_usable_values(vision_values):
                warnings.append("Text extraction failed and vision fallback remained limited; vision output was kept.")
                return build_result(
                    raw_values=vision_values,
                    marker_details={},
                    source="vision",
                    selected_source="vision",
                    fallback_used=True,
                    fallback_reason=f"text_weak:{text_assessment.weak_reason}",
                    selection_reason=f"text_fallback_to_limited_vision;initial={selected_reason}",
                    final_assessment=vision_assessment,
                )

        return build_result(
            raw_values=text_values,
            marker_details=inspection.text_marker_details,
            source="pdfplumber",
            selected_source="text",
            fallback_used=False,
            fallback_reason=None,
            selection_reason=f"text_no_usable_markers;initial={selected_reason}",
            final_assessment=text_assessment,
        )

    vision_values = normalize_raw_values(extract_lab_data_via_vision(pdf_path, max_pages=page_limit, lang=language))
    vision_assessment = _assess_vision_extraction(vision_values)
    if not vision_assessment.weak:
        return build_result(
            raw_values=vision_values,
            marker_details={},
            source="vision",
            selected_source="vision",
            fallback_used=False,
            fallback_reason=None,
            selection_reason=selected_reason,
            final_assessment=vision_assessment,
        )

    if not text_assessment.weak:
        warnings.append("Vision extraction was too weak; PDF text fallback was used.")
        return build_result(
            raw_values=text_values,
            marker_details=inspection.text_marker_details,
            source="pdfplumber",
            selected_source="text",
            fallback_used=True,
            fallback_reason=f"vision_weak:{vision_assessment.weak_reason}",
            selection_reason=f"vision_fallback_to_text;initial={selected_reason}",
            final_assessment=text_assessment,
        )

    if _has_usable_values(vision_values):
        warnings.append("Vision extraction remained limited, and text fallback was not stronger; vision output was kept.")
        return build_result(
            raw_values=vision_values,
            source="vision",
            selected_source="vision",
            fallback_used=False,
            fallback_reason=None,
            selection_reason=f"limited_vision_retained;initial={selected_reason}",
            final_assessment=vision_assessment,
        )

    warnings.append("Vision extraction was selected but returned no usable markers; PDF text parsing fallback was used.")
    return build_result(
        raw_values=text_values,
        marker_details=inspection.text_marker_details,
        source="pdfplumber",
        selected_source="text",
        fallback_used=True,
        fallback_reason=f"vision_weak:{vision_assessment.weak_reason}",
        selection_reason=f"vision_fallback_to_text;initial={selected_reason}",
        final_assessment=text_assessment,
    )
