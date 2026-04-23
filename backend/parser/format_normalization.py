from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any

from parser.extract_pdf import extract_reference_range, extract_unit
from parser.postprocess import MarkerDetail


@dataclass(frozen=True)
class FormatProfile:
    region: str
    decimal_separator: str
    unit_style: str
    mixed: bool = False


_UNIT_ONLY_RE = re.compile(
    r"^\s*(?:"
    r"g/l|г/л|g/dl|mg/l|мг/л|mg/dl|mg\s+alb/mmol|mg/mmol|mg/g|"
    r"mmol/l|ммоль/л|mmol/mol|mol/l|umol/l|µmol/l|μmol/l|мкмоль/л|"
    r"ng/ml|нг/мл|fl|pg|pg/ml|iu/ml|u/l|ед/л|ml/min/1\.73 ?m2|mm/h|мм/ч|"
    r"k/[uµμ]l|m/[uµμ]l|%|x?10\^?9/[lл]|x?10\^?12/[lл]"
    r")\s*$",
    flags=re.IGNORECASE,
)
_SCIENTIFIC_COUNT_RE = re.compile(r"^\s*x?\s*10\^?(?:9|12)\s*/\s*[lл]\s*$", flags=re.IGNORECASE)
_SAFE_NUMBER_RE = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
_SCIENTIFIC_VALUE_RE = re.compile(
    r"([+-]?\d+(?:[.,]\d+)?)\s+(x?\s*10\^?(?:9|12)\s*/\s*[lл])(?:\s|$)",
    flags=re.IGNORECASE,
)
_UNIT_LABEL_NORMALIZATION = {
    "umol/L": "µmol/L",
    "µmol/L": "µmol/L",
    "K/uL": "K/uL",
    "M/uL": "M/uL",
    "mg Alb/mmol": "mg Alb/mmol",
    "mmol/mol": "mmol/mol",
    "fL": "fL",
    "pg": "pg",
}


def detect_report_format(
    *,
    raw_text: str = "",
    marker_details: dict[str, MarkerDetail] | None = None,
    language_hint: str | None = None,
) -> FormatProfile:
    samples: list[str] = []
    if raw_text:
        samples.append(raw_text)
    if marker_details:
        for detail in marker_details.values():
            if detail.source_text:
                samples.append(detail.source_text)
            if detail.unit:
                samples.append(detail.unit)
            if detail.reference_range:
                samples.append(detail.reference_range)

    joined = "\n".join(samples).lower()
    joined = joined.replace("\xa0", " ")

    comma_score = sum(token in joined for token in [",", "г/л", "ммоль/л", "нг/мл", "мкмоль/л", "10^12/л", "10^9/л"])
    dot_score = sum(token in joined for token in [".", "g/dl", "mg/dl", "mmol/l", "ng/ml", "umol/l", "x10^12/l", "x10^9/l"])
    cyrillic_score = sum(token in joined for token in ["г/л", "ммоль/л", "нг/мл", "мкмоль/л", "10^12/л", "10^9/л"])
    us_unit_score = sum(token in joined for token in ["g/dl", "mg/dl"])

    hint = (language_hint or "").lower()
    if hint == "ru":
        comma_score += 2
        cyrillic_score += 2
    elif hint == "en":
        dot_score += 1

    mixed = comma_score > 0 and dot_score > 0
    if cyrillic_score > 0 or comma_score > dot_score + 1:
        return FormatProfile(
            region="ru_eu" if not mixed else "mixed",
            decimal_separator=",",
            unit_style="cyrillic" if cyrillic_score > 0 else "latin",
            mixed=mixed,
        )
    if us_unit_score > 0 or dot_score > 0:
        return FormatProfile(
            region="us" if not mixed else "mixed",
            decimal_separator=".",
            unit_style="latin",
            mixed=mixed,
        )
    return FormatProfile(region="mixed", decimal_separator=".", unit_style="latin", mixed=True)


def preprocess_extracted_data(
    *,
    raw_values: dict[str, Any],
    marker_details: dict[str, MarkerDetail] | None = None,
    raw_text: str = "",
    language_hint: str | None = None,
) -> tuple[dict[str, float | None], dict[str, MarkerDetail], FormatProfile]:
    details = marker_details or {}
    profile = detect_report_format(raw_text=raw_text, marker_details=details, language_hint=language_hint)

    normalized_values: dict[str, float | None] = {}
    normalized_details: dict[str, MarkerDetail] = {}

    for name, raw_value in raw_values.items():
        normalized_values[str(name).strip()] = _normalize_value(str(name).strip(), raw_value)

    for name, detail in details.items():
        normalized = _normalize_marker_detail(detail)
        normalized_details[name] = normalized
        if normalized.value is not None:
            normalized_values[name] = normalized.value

    return (
        dict(sorted(normalized_values.items(), key=lambda item: item[0].lower())),
        dict(sorted(normalized_details.items(), key=lambda item: item[0].lower())),
        profile,
    )


def _normalize_value(name: str, raw_value: Any) -> float | None:
    del name
    return _safe_parse_numeric_value(raw_value)


def _normalize_marker_detail(detail: MarkerDetail) -> MarkerDetail:
    source_text = detail.source_text or ""
    parsed_value, scientific_unit = _extract_value_and_unit_from_source(source_text)
    unit = detail.unit or scientific_unit or extract_unit(source_text)
    if detail.unit:
        unit = extract_unit(detail.unit) or unit or detail.unit
    unit = _normalize_unit_label(unit)

    reference_range = detail.reference_range or extract_reference_range(source_text)
    if detail.reference_range:
        reference_range = extract_reference_range(detail.reference_range) or reference_range or detail.reference_range
    reference_range = _normalize_reference_range(reference_range)

    value = _coerce_finite_float(detail.value)
    if value is None and parsed_value is not None:
        value = parsed_value

    return MarkerDetail(
        name=detail.name,
        value=value,
        unit=unit,
        reference_range=reference_range,
        source_kind=detail.source_kind,
        source_text=detail.source_text,
        reference_recovered=detail.reference_recovered,
        unit_recovered=detail.unit_recovered,
        confidence=detail.confidence,
    )


def _safe_parse_numeric_value(raw_value: Any) -> float | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, bool):
        return None

    if isinstance(raw_value, (int, float)):
        value = float(raw_value)
        return value if math.isfinite(value) else None

    text = str(raw_value).strip()
    if not text:
        return None

    text = (
        text.replace("\xa0", " ")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("•", ".")
        .replace("·", ".")
        .replace("…", ".")
    )
    text = re.sub(r"\s+", " ", text)

    scientific_match = re.fullmatch(r"([+-]?\d+(?:[.,]\d+)?)\s+(x?\s*10\^?(?:9|12)\s*/\s*[lл])", text, flags=re.IGNORECASE)
    if scientific_match:
        return _parse_single_number_token(scientific_match.group(1))

    parts = text.split(" ", 1)
    if len(parts) == 2 and _SAFE_NUMBER_RE.fullmatch(parts[0]) and _UNIT_ONLY_RE.fullmatch(parts[1]):
        return _parse_single_number_token(parts[0])

    if _SAFE_NUMBER_RE.fullmatch(text):
        return _parse_single_number_token(text)

    return None


def _parse_single_number_token(token: str) -> float | None:
    normalized = token.replace(",", ".")
    if normalized.count(".") > 1:
        return None

    try:
        value = float(normalized)
    except ValueError:
        return None

    return value if math.isfinite(value) else None


def _coerce_finite_float(raw_value: Any) -> float | None:
    if raw_value is None:
        return None
    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        return None
    return numeric_value if math.isfinite(numeric_value) else None


def _extract_value_and_unit_from_source(source_text: str) -> tuple[float | None, str | None]:
    if not source_text:
        return None, None

    scientific_match = _SCIENTIFIC_VALUE_RE.search(source_text.replace("\xa0", " "))
    if scientific_match:
        return _parse_single_number_token(scientific_match.group(1)), _normalize_unit_label(extract_unit(scientific_match.group(2)))

    return None, None


def _normalize_unit_label(unit: str | None) -> str | None:
    if unit is None:
        return None
    return _UNIT_LABEL_NORMALIZATION.get(unit, unit)


def _normalize_reference_range(reference_range: str | None) -> str | None:
    if reference_range is None:
        return None

    text = reference_range.strip()
    if not text:
        return None

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace(",", ".")
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s*([<>≤≥])\s*", r"\1 ", text)
    return text.strip()
