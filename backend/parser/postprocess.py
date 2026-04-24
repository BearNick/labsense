from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency in test env
    pdfplumber = None

from parser.config import resolve_pdf_page_limit
from parser.extract_pdf import (
    _extract_simple_positional_override_value,
    _slice_after_alias,
    extract_lab_data_from_pdf,
    extract_reference_range,
    extract_unit,
    extract_value,
    match_indicator,
    match_indicator_with_alias,
)


logger = logging.getLogger(__name__)


_CANONICAL_GROUPS: dict[str, set[str]] = {
    "Гемоглобин": {"Гемоглобин", "Hemoglobin", "HGB", "Hb"},
    "Гематокрит": {"Гематокрит", "Hematocrit", "HCT", "Ht"},
    "Эритроциты": {"Эритроциты", "RBC"},
    "Лейкоциты": {"Лейкоциты", "WBC"},
    "Тромбоциты": {"Тромбоциты", "Platelets", "PLT"},
    "Глюкоза": {"Глюкоза", "Glucose"},
    "Натрий": {"Натрий", "Sodium", "Na"},
    "Калий": {"Калий", "Potassium", "K"},
    "Хлор": {"Хлор", "Chloride", "Cl"},
    "Мочевина": {"Мочевина", "Urea"},
    "Креатинин": {"Креатинин", "Creatinine"},
    "Кислота мочевая": {"Кислота мочевая", "Uric Acid", "Uric acid"},
    "eGFR": {"eGFR"},
    "ЛПНП": {"ЛПНП", "LDL"},
    "ЛПВП": {"ЛПВП", "HDL"},
    "CRP": {"CRP", "С-реактивный белок"},
    "Витамин D (25-OH)": {"Витамин D (25-OH)", "Vitamin D (25-OH)"},
    "HbA1c": {"HbA1c", "A1c"},
    "Urine Albumin": {"Urine Albumin"},
    "Urine Creatinine": {"Urine Creatinine"},
    "ACR": {"ACR"},
    "BUN": {"BUN"},
}

_ZERO_INVALID_MARKERS: set[str] = {
    "Гемоглобин",
    "Hemoglobin",
    "HGB",
    "Hb",
    "Гематокрит",
    "Hematocrit",
    "HCT",
    "Ht",
    "Эритроциты",
    "RBC",
    "Лейкоциты",
    "WBC",
    "Тромбоциты",
    "Platelets",
    "PLT",
}

_PLAUSIBLE_VALUE_RANGES: dict[str, tuple[float, float]] = {
    "Гемоглобин": (2.0, 250.0),
    "Hemoglobin": (2.0, 250.0),
    "HGB": (2.0, 250.0),
    "Hb": (2.0, 250.0),
    "Гематокрит": (1.0, 80.0),
    "Hematocrit": (1.0, 80.0),
    "HCT": (1.0, 80.0),
    "Ht": (1.0, 80.0),
    "Эритроциты": (0.1, 15.0),
    "RBC": (0.1, 15.0),
    "Лейкоциты": (0.1, 1000.0),
    "WBC": (0.1, 1000.0),
    "Тромбоциты": (1.0, 5000.0),
    "Platelets": (1.0, 5000.0),
    "PLT": (1.0, 5000.0),
    "Натрий": (90.0, 200.0),
    "Sodium": (90.0, 200.0),
    "Na": (90.0, 200.0),
    "Калий": (1.0, 10.0),
    "Potassium": (1.0, 10.0),
    "K": (1.0, 10.0),
    "Хлор": (50.0, 200.0),
    "Chloride": (50.0, 200.0),
    "Cl": (50.0, 200.0),
    "Мочевина": (0.1, 100.0),
    "Urea": (0.1, 100.0),
    "Креатинин": (1.0, 5000.0),
    "Creatinine": (1.0, 5000.0),
    "Кислота мочевая": (10.0, 3000.0),
    "Uric acid": (10.0, 3000.0),
    "Uric Acid": (10.0, 3000.0),
    "eGFR": (1.0, 300.0),
    "HbA1c": (1.0, 30.0),
    "A1c": (1.0, 30.0),
    "Urine Albumin": (0.0, 100000.0),
    "Urine Creatinine": (0.0, 100000.0),
    "ACR": (0.0, 100000.0),
    "BUN": (0.1, 200.0),
}


@dataclass(frozen=True)
class MarkerDetail:
    name: str
    value: float | None
    unit: str | None = None
    reference_range: str | None = None
    source_kind: str = "line"
    source_text: str = ""
    reference_recovered: bool = False
    unit_recovered: bool = False
    confidence: float = 0.0


@dataclass(frozen=True)
class TextPostprocessResult:
    raw_values: dict[str, float | None]
    marker_details: dict[str, MarkerDetail]
    table_count: int = 0
    table_row_count: int = 0


def extract_legacy_text_with_details(pdf_path: str, max_pages: int | None = None) -> TextPostprocessResult:
    page_limit = resolve_pdf_page_limit(max_pages)
    raw_values = {str(name): value for name, value in extract_lab_data_from_pdf(pdf_path, max_pages=page_limit).items()}
    if pdfplumber is None:
        merged_values, merged_details = merge_canonical_markers(raw_values, {})
        return TextPostprocessResult(raw_values=merged_values, marker_details=merged_details)

    details: dict[str, MarkerDetail] = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_read = min(len(pdf.pages), page_limit)
            for index in range(pages_to_read):
                page = pdf.pages[index]
                page_text = page.extract_text() or ""
                for line in [line.strip() for line in page_text.splitlines() if line.strip()]:
                    candidate = build_marker_detail_from_text(line, source_kind="line")
                    if candidate:
                        details[candidate.name] = _prefer_detail(details.get(candidate.name), candidate)
    except Exception:
        pass

    merged_values, merged_details = merge_canonical_markers(raw_values, details)
    return TextPostprocessResult(raw_values=merged_values, marker_details=merged_details)


def extract_text_with_details(pdf_path: str, max_pages: int | None = None) -> TextPostprocessResult:
    page_limit = resolve_pdf_page_limit(max_pages)
    raw_values = {str(name): value for name, value in extract_lab_data_from_pdf(pdf_path, max_pages=page_limit).items()}
    if pdfplumber is None:
        merged_values, merged_details = merge_canonical_markers(raw_values, {})
        return TextPostprocessResult(raw_values=merged_values, marker_details=merged_details)

    details: dict[str, MarkerDetail] = {}
    table_count = 0
    table_row_count = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_read = min(len(pdf.pages), page_limit)
            for index in range(pages_to_read):
                page = pdf.pages[index]
                page_text = page.extract_text() or ""
                for line in [line.strip() for line in page_text.splitlines() if line.strip()]:
                    candidate = build_marker_detail_from_text(line, source_kind="line")
                    if candidate:
                        details[candidate.name] = _prefer_detail(details.get(candidate.name), candidate)

                tables = page.extract_tables() or []
                table_count += len(tables)
                for table in tables:
                    rows = [[(cell or "").strip() for cell in row] for row in (table or []) if row]
                    table_row_count += len(rows)
                    for row_index, row in enumerate(rows):
                        candidate = build_marker_detail_from_row(rows, row_index)
                        if candidate:
                            details[candidate.name] = _prefer_detail(details.get(candidate.name), candidate)
    except Exception:
        pass

    merged_values, merged_details = merge_canonical_markers(raw_values, details)
    return TextPostprocessResult(
        raw_values=merged_values,
        marker_details=merged_details,
        table_count=table_count,
        table_row_count=table_row_count,
    )


def build_marker_detail_from_text(text: str, source_kind: str = "line") -> MarkerDetail | None:
    matched = match_indicator_with_alias(text)
    if matched is None:
        return None

    name, alias = matched
    value = extract_value(text, name, alias)
    return MarkerDetail(
        name=name,
        value=value,
        unit=extract_unit(text),
        reference_range=extract_reference_range(text),
        source_kind=source_kind,
        source_text=text,
        confidence=_detail_score(
            value=value,
            unit=extract_unit(text),
            reference_range=extract_reference_range(text),
            source_kind=source_kind,
            recovered=False,
        ),
    )


def build_marker_detail_from_row(rows: list[list[str]], row_index: int) -> MarkerDetail | None:
    row = rows[row_index]
    row_text = _join_cells(row)
    matched = match_indicator_with_alias(row_text)
    if matched is None:
        return None

    name, alias = matched
    value = _extract_value_from_row(row, name, alias)
    if value is None:
        value = extract_value(row_text, name, alias)

    unit = _extract_unit_from_cells(row) or extract_unit(row_text)
    reference = _extract_reference_from_cells(row) or extract_reference_range(row_text)

    reference_recovered = False
    unit_recovered = False
    if reference is None:
        recovered_reference = _recover_from_adjacent_rows(rows, row_index, extractor=_extract_reference_from_cells)
        if recovered_reference is None:
            recovered_reference = _recover_from_adjacent_columns(rows, row_index, extractor=_extract_reference_from_cells)
        if recovered_reference is not None:
            reference = recovered_reference
            reference_recovered = True

    if unit is None:
        recovered_unit = _recover_from_adjacent_rows(rows, row_index, extractor=_extract_unit_from_cells)
        if recovered_unit is None:
            recovered_unit = _recover_from_adjacent_columns(rows, row_index, extractor=_extract_unit_from_cells)
        if recovered_unit is not None:
            unit = recovered_unit
            unit_recovered = True

    return MarkerDetail(
        name=name,
        value=value,
        unit=unit,
        reference_range=reference,
        source_kind="table",
        source_text=row_text,
        reference_recovered=reference_recovered,
        unit_recovered=unit_recovered,
        confidence=_detail_score(
            value=value,
            unit=unit,
            reference_range=reference,
            source_kind="table",
            recovered=reference_recovered or unit_recovered,
        ),
    )


def merge_canonical_markers(
    raw_values: dict[str, float | None],
    marker_details: dict[str, MarkerDetail | dict[str, object]],
) -> tuple[dict[str, float | None], dict[str, MarkerDetail]]:
    values_out = dict(raw_values)
    details_out = dict(marker_details)

    for preferred_name, group in _CANONICAL_GROUPS.items():
        present_value_names = [name for name in values_out if name in group]
        present_detail_names = [name for name in details_out if name in group]
        if len(set(present_value_names + present_detail_names)) <= 1:
            continue

        chosen_name = _choose_best_candidate_name(
            preferred_name,
            list(dict.fromkeys(present_value_names + present_detail_names)),
            values_out,
            details_out,
        )
        chosen_value = values_out.get(chosen_name)
        chosen_detail = details_out.get(chosen_name)
        if chosen_value is None:
            chosen_value = _detail_numeric_value(chosen_detail)
        best_detail = _build_canonical_detail(preferred_name, chosen_value, chosen_detail)

        for name in list(values_out):
            if name in group:
                del values_out[name]
        for name in list(details_out):
            if name in group:
                del details_out[name]

        values_out[preferred_name] = chosen_value
        details_out[preferred_name] = best_detail

    return (
        dict(sorted(values_out.items(), key=lambda item: item[0].lower())),
        dict(sorted(details_out.items(), key=lambda item: item[0].lower())),
    )


def _choose_best_candidate_name(
    preferred_name: str,
    names: list[str],
    raw_values: dict[str, float | None],
    details: dict[str, MarkerDetail | dict[str, object]],
) -> str:
    if not names:
        return preferred_name

    chosen_name: str | None = None
    chosen_rank: tuple[int, int, int, int, int, float] | None = None

    for name in names:
        detail = details.get(name)
        rank = _candidate_rank(preferred_name, raw_values.get(name), detail)
        if chosen_rank is None or rank > chosen_rank:
            chosen_name = name
            chosen_rank = rank

    return chosen_name if chosen_name is not None else names[0]


def _candidate_rank(
    preferred_name: str,
    value: float | None,
    detail: MarkerDetail | dict[str, object] | None,
) -> tuple[int, int, int, int, int, float]:
    detail_value = _detail_numeric_value(detail)
    candidate_value = value if value is not None else detail_value
    return (
        _numeric_value_quality(preferred_name, candidate_value),
        _plausibility_score(preferred_name, candidate_value),
        1 if _has_reference(detail) else 0,
        1 if _has_unit(detail) else 0,
        1 if detail is not None else 0,
        _detail_confidence(detail),
    )


def _build_canonical_detail(
    preferred_name: str,
    chosen_value: float | None,
    detail: MarkerDetail | dict[str, object] | None,
) -> MarkerDetail:
    if detail is None:
        return MarkerDetail(name=preferred_name, value=chosen_value)

    coerced = _coerce_marker_detail(preferred_name, detail)
    if _numeric_value_quality(preferred_name, chosen_value) > _numeric_value_quality(preferred_name, coerced.value):
        return MarkerDetail(
            name=preferred_name,
            value=chosen_value,
            unit=coerced.unit,
            reference_range=coerced.reference_range,
            source_kind=coerced.source_kind,
            source_text=coerced.source_text,
            reference_recovered=coerced.reference_recovered,
            unit_recovered=coerced.unit_recovered,
            confidence=coerced.confidence,
        )
    return coerced


def _detail_field(detail: MarkerDetail | dict[str, object], field: str) -> object | None:
    if isinstance(detail, dict):
        return detail.get(field)
    return getattr(detail, field, None)


def _detail_confidence(detail: MarkerDetail | dict[str, object] | None) -> float:
    if detail is None:
        return 0.0
    confidence = _detail_field(detail, "confidence")
    return confidence if isinstance(confidence, (int, float)) else 0.0


def _detail_numeric_value(detail: MarkerDetail | dict[str, object] | None) -> float | None:
    if detail is None:
        return None
    value = _detail_field(detail, "value")
    return value if isinstance(value, (int, float)) else None


def _has_reference(detail: MarkerDetail | dict[str, object] | None) -> bool:
    reference_range = _detail_field(detail, "reference_range") if detail is not None else None
    return isinstance(reference_range, str) and bool(reference_range.strip())


def _has_unit(detail: MarkerDetail | dict[str, object] | None) -> bool:
    unit = _detail_field(detail, "unit") if detail is not None else None
    return isinstance(unit, str) and bool(unit.strip())


def _numeric_value_quality(marker_name: str, value: object) -> int:
    if not isinstance(value, (int, float)):
        return 0
    if value == 0 and marker_name in _ZERO_INVALID_MARKERS:
        return 1
    if value == 0:
        return 2
    return 3


def _plausibility_score(marker_name: str, value: object) -> int:
    if not isinstance(value, (int, float)):
        return 1
    plausible_range = _PLAUSIBLE_VALUE_RANGES.get(marker_name)
    if plausible_range is None:
        return 1
    lower, upper = plausible_range
    return 1 if lower <= value <= upper else 0


def _coerce_marker_detail(preferred_name: str, detail: MarkerDetail | dict[str, object]) -> MarkerDetail:
    value = _detail_field(detail, "value")
    unit = _detail_field(detail, "unit")
    reference_range = _detail_field(detail, "reference_range")
    source_kind = _detail_field(detail, "source_kind")
    source_text = _detail_field(detail, "source_text")

    return MarkerDetail(
        name=preferred_name,
        value=value if isinstance(value, (int, float)) else None,
        unit=unit if isinstance(unit, str) else None,
        reference_range=reference_range if isinstance(reference_range, str) else None,
        source_kind=source_kind if isinstance(source_kind, str) else "line",
        source_text=source_text if isinstance(source_text, str) else "",
        reference_recovered=bool(_detail_field(detail, "reference_recovered")),
        unit_recovered=bool(_detail_field(detail, "unit_recovered")),
        confidence=_detail_confidence(detail),
    )


def _prefer_detail(current: MarkerDetail | None, candidate: MarkerDetail) -> MarkerDetail:
    if current is None:
        return candidate
    return candidate if candidate.confidence >= current.confidence else current


def _extract_value_from_row(row: list[str], name: str, alias: str) -> Optional[float]:
    alias_cell_index = -1
    for index, cell in enumerate(row):
        matched = match_indicator_with_alias(cell)
        if matched and matched[0] == name:
            alias_cell_index = index
            break

    if alias_cell_index == -1:
        return None

    linear_row_text = " ".join(cell.strip() for cell in row[alias_cell_index:] if cell.strip())
    if linear_row_text:
        source_text = _slice_after_alias(linear_row_text, alias)
        positional_override = _extract_simple_positional_override_value(
            line=linear_row_text,
            source_text=source_text,
            metric_name=name,
            matched_alias=alias,
        )
        if positional_override is not None:
            logger.debug(
                "value_selection marker=%s path=simple_scalar_early_return value=%s",
                name,
                positional_override,
            )
            return positional_override

    for cell in row[alias_cell_index + 1:]:
        if not cell.strip():
            continue
        cell_reference = extract_reference_range(cell)
        if cell_reference and cell_reference.replace(" ", "") == cell.replace(" ", "").replace("–", "-").replace("—", "-"):
            continue
        value = extract_value(cell, name, alias)
        if value is not None:
            return value

    for index, cell in enumerate(row):
        if index == alias_cell_index or not cell.strip():
            continue
        value = extract_value(cell, name, alias)
        if value is not None:
            return value
    return None


def _extract_reference_from_cells(row: list[str]) -> str | None:
    inline_candidates: list[str] = []
    standalone_candidates: list[str] = []
    for cell in row:
        reference = extract_reference_range(cell)
        if not reference:
            continue
        normalized_cell = cell.strip().replace("–", "-").replace("—", "-")
        normalized_reference = reference.replace("–", "-").replace("—", "-")
        if normalized_reference.replace(" ", "") == normalized_cell.replace(" ", ""):
            standalone_candidates.append(reference)
            continue
        inline_candidates.append(reference)
    if standalone_candidates:
        return standalone_candidates[0]
    if inline_candidates:
        return inline_candidates[0]
    return None


def _extract_unit_from_cells(row: list[str]) -> str | None:
    for cell in row:
        unit = extract_unit(cell)
        if unit:
            return unit
    return None


def _recover_from_adjacent_rows(
    rows: list[list[str]],
    row_index: int,
    extractor,
) -> str | None:
    for neighbor_index in (row_index - 1, row_index + 1):
        if neighbor_index < 0 or neighbor_index >= len(rows):
            continue
        neighbor = rows[neighbor_index]
        neighbor_text = _join_cells(neighbor)
        if not neighbor_text:
            continue
        if match_indicator(neighbor_text)[0] is not None:
            continue
        recovered = extractor(neighbor)
        if recovered is None:
            continue
        non_empty_cells = [cell for cell in neighbor if cell.strip()]
        if len(non_empty_cells) > 2:
            continue
        return recovered
    return None


def _recover_from_adjacent_columns(
    rows: list[list[str]],
    row_index: int,
    extractor,
) -> str | None:
    row = rows[row_index]
    for cell_index in range(len(row)):
        current = row[cell_index].strip()
        if not current:
            continue
        candidate = extractor([current])
        if candidate is not None:
            return candidate

        for neighbor_index in (cell_index - 1, cell_index + 1):
            if neighbor_index < 0 or neighbor_index >= len(row):
                continue
            neighbor = row[neighbor_index].strip()
            if not neighbor:
                continue
            recovered = extractor([neighbor])
            if recovered is not None:
                return recovered
    return None


def _join_cells(row: list[str]) -> str:
    return " | ".join(cell for cell in row if cell)


def _detail_score(
    *,
    value: float | None,
    unit: str | None,
    reference_range: str | None,
    source_kind: str,
    recovered: bool,
) -> float:
    score = 0.0
    if value is not None:
        score += 4.0
    if unit:
        score += 1.5
    if reference_range:
        score += 2.0
    if source_kind == "table":
        score += 1.0
    if recovered:
        score -= 0.5
    return score
