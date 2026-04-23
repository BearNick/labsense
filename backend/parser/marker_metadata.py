from __future__ import annotations

from typing import TypedDict


class MarkerMetadata(TypedDict, total=False):
    unit: str
    reference_range: str


METRIC_METADATA: dict[str, MarkerMetadata] = {
    "Гемоглобин": {"unit": "g/L", "reference_range": "120 - 170"},
    "Hemoglobin": {"unit": "g/L", "reference_range": "120 - 170"},
    "Лейкоциты": {"unit": "x10^9/L", "reference_range": "4.0 - 10.0"},
    "Тромбоциты": {"unit": "x10^9/L", "reference_range": "150 - 400"},
    "Глюкоза": {"unit": "mmol/L", "reference_range": "3.9 - 5.5"},
    "Glucose": {"unit": "mmol/L", "reference_range": "3.9 - 5.5"},
    "Натрий": {"unit": "mmol/L", "reference_range": "135 - 145"},
    "Калий": {"unit": "mmol/L", "reference_range": "3.5 - 5.1"},
    "Хлор": {"unit": "mmol/L", "reference_range": "98 - 107"},
    "Креатинин": {"unit": "umol/L", "reference_range": "53 - 115"},
    "Мочевина": {"unit": "mmol/L", "reference_range": "2.5 - 8.3"},
    "BUN": {"unit": "mg/dL", "reference_range": "7 - 20"},
    "eGFR": {"unit": "mL/min/1.73m2", "reference_range": ">= 60"},
    "Кислота мочевая": {"unit": "umol/L", "reference_range": "150 - 420"},
    "Холестерин общий": {"unit": "mmol/L", "reference_range": "< 5.2"},
    "ЛПНП": {"unit": "mmol/L", "reference_range": "< 3.0"},
    "LDL": {"unit": "mmol/L", "reference_range": "< 3.0"},
    "ЛПВП": {"unit": "mmol/L", "reference_range": ">= 1.0"},
    "HDL": {"unit": "mmol/L", "reference_range": ">= 1.0"},
    "С-реактивный белок": {"unit": "mg/L", "reference_range": "0 - 5"},
    "CRP": {"unit": "mg/L", "reference_range": "0 - 5"},
    "ALT": {"unit": "U/L", "reference_range": "< 55"},
    "AST": {"unit": "U/L", "reference_range": "< 40"},
    "HbA1c": {"unit": "%", "reference_range": "< 5.7"},
    "Urine Albumin": {"unit": "mg/L"},
    "Urine Creatinine": {"unit": "mmol/L"},
    "ACR": {"unit": "mg/mmol"},
    "Гематокрит": {"unit": "%", "reference_range": "36 - 50"},
    "Эритроциты": {"unit": "x10^12/L", "reference_range": "3.8 - 5.8"},
    "СОЭ": {"unit": "mm/h", "reference_range": "< 20"},
    "Витамин D (25-OH)": {"unit": "ng/mL", "reference_range": "30 - 100"},
}


def get_marker_metadata(name: str) -> MarkerMetadata | None:
    return METRIC_METADATA.get(name)
