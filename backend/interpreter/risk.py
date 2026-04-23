from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


ColorKey = Literal["green", "yellow", "red"]
RiskLevel = Literal["NORMAL", "BORDERLINE", "SIGNIFICANT"]


class RiskStatus(TypedDict):
    label: str
    color_key: ColorKey
    explanation: str
    priority_notes: list[str]


class RiskRule(TypedDict, total=False):
    min: float
    max: float
    severe_min: float
    severe_max: float


@dataclass(frozen=True)
class RiskDeviation:
    marker: str
    direction: Literal["high", "low"]
    severity: Literal["mild", "severe"]
    note: str
    clinically_relevant: bool


@dataclass(frozen=True)
class RiskAssessmentDetails:
    risk_level: RiskLevel
    priority_notes: list[str]
    all_notes: list[str]
    abnormal_markers: list[str]
    deviations: list[RiskDeviation]


RISK_RULES: dict[str, RiskRule] = {
    "Гемоглобин": {"min": 120, "max": 170, "severe_min": 100, "severe_max": 180},
    "Hemoglobin": {"min": 120, "max": 170, "severe_min": 100, "severe_max": 180},
    "Лейкоциты": {"min": 4, "max": 10, "severe_min": 3, "severe_max": 15},
    "WBC": {"min": 4, "max": 10, "severe_min": 3, "severe_max": 15},
    "Тромбоциты": {"min": 150, "max": 400, "severe_min": 100, "severe_max": 500},
    "Platelets": {"min": 150, "max": 400, "severe_min": 100, "severe_max": 500},
    "Глюкоза": {"min": 3.9, "max": 5.5, "severe_min": 3.0, "severe_max": 7.0},
    "Glucose": {"min": 3.9, "max": 5.5, "severe_min": 3.0, "severe_max": 7.0},
    "Креатинин": {"min": 53, "max": 115, "severe_max": 150},
    "Creatinine": {"min": 53, "max": 115, "severe_max": 150},
    "Холестерин общий": {"max": 5.2, "severe_max": 7.0},
    "Total Cholesterol": {"max": 5.2, "severe_max": 7.0},
    "ЛПНП": {"max": 3.0, "severe_max": 4.9},
    "LDL": {"max": 3.0, "severe_max": 4.9},
    "ЛПВП": {"min": 1.0, "severe_min": 0.8},
    "HDL": {"min": 1.0, "severe_min": 0.8},
    "С-реактивный белок": {"min": 0, "max": 5, "severe_max": 10},
    "CRP": {"min": 0, "max": 5, "severe_max": 10},
    "ALT": {"max": 55, "severe_max": 120},
    "AST": {"max": 40, "severe_max": 100},
    "Гематокрит": {"min": 36, "max": 50, "severe_min": 30, "severe_max": 55},
    "Hematocrit": {"min": 36, "max": 50, "severe_min": 30, "severe_max": 55},
    "Эритроциты": {"min": 3.8, "max": 5.8, "severe_min": 3.0, "severe_max": 6.2},
    "RBC": {"min": 3.8, "max": 5.8, "severe_min": 3.0, "severe_max": 6.2},
    "Лимфоциты %": {"min": 20, "max": 45, "severe_min": 15, "severe_max": 55},
    "Lymphocytes %": {"min": 20, "max": 45, "severe_min": 15, "severe_max": 55},
    "Эозинофилы %": {"min": 0, "max": 5, "severe_max": 10},
    "Eosinophils %": {"min": 0, "max": 5, "severe_max": 10},
    "Базофилы %": {"min": 0, "max": 1.5, "severe_max": 3},
    "Basophils %": {"min": 0, "max": 1.5, "severe_max": 3},
    "СОЭ": {"max": 20, "severe_max": 40},
    "ESR": {"max": 20, "severe_max": 40},
    "Витамин D (25-OH)": {"min": 30, "max": 100, "severe_min": 20},
    "Vitamin D (25-OH)": {"min": 30, "max": 100, "severe_min": 20},
    "Цинк": {"min": 10.7, "max": 18.4, "severe_min": 7.0},
    "Zinc": {"min": 10.7, "max": 18.4, "severe_min": 7.0},
}

CLINICALLY_RELEVANT_MARKERS = {
    "Гемоглобин",
    "Hemoglobin",
    "Лейкоциты",
    "WBC",
    "Тромбоциты",
    "Platelets",
    "Глюкоза",
    "Glucose",
    "Креатинин",
    "Creatinine",
    "С-реактивный белок",
    "CRP",
    "ALT",
    "AST",
    "Гематокрит",
    "Hematocrit",
    "Эритроциты",
    "RBC",
    "Лимфоциты %",
    "Lymphocytes %",
    "Эозинофилы %",
    "Eosinophils %",
    "СОЭ",
    "ESR",
}

MAJOR_SIGNIFICANT_MARKERS = {
    "Гемоглобин",
    "Hemoglobin",
    "Глюкоза",
    "Glucose",
    "Креатинин",
    "Creatinine",
    "С-реактивный белок",
    "CRP",
    "ALT",
    "AST",
}


def _localize(language: str, key: str) -> str:
    messages = {
        "en": {
            "green_label": "Normal",
            "yellow_label": "Needs observation",
            "red_label": "Significant deviation",
            "green_explanation": "All detected markers are within range.",
            "yellow_explanation_one": "A mild deviation is present and should be observed.",
            "yellow_explanation_many": "Mild deviations are present and should be observed.",
            "red_explanation": "Clinically relevant deviations are present and should be reviewed.",
            "high_note": "{name} is above range.",
            "low_note": "{name} is below range.",
        },
        "ru": {
            "green_label": "Норма",
            "yellow_label": "Нужно наблюдение",
            "red_label": "Значимое отклонение",
            "green_explanation": "Все обнаруженные маркеры находятся в пределах референса.",
            "yellow_explanation_one": "Есть легкое отклонение, за которым стоит наблюдать.",
            "yellow_explanation_many": "Есть легкие отклонения, за которыми стоит наблюдать.",
            "red_explanation": "Есть клинически значимые отклонения, которые стоит обсудить с врачом.",
            "high_note": "{name} выше референса.",
            "low_note": "{name} ниже референса.",
        },
        "es": {
            "green_label": "Normal",
            "yellow_label": "Necesita observación",
            "red_label": "Desviación significativa",
            "green_explanation": "Todos los marcadores detectados están dentro de rango.",
            "yellow_explanation_one": "Hay una desviación leve que conviene observar.",
            "yellow_explanation_many": "Hay desviaciones leves que conviene observar.",
            "red_explanation": "Hay desviaciones clínicamente relevantes que conviene revisar.",
            "high_note": "{name} está por encima del rango.",
            "low_note": "{name} está por debajo del rango.",
        },
    }
    selected = messages.get(language, messages["en"])
    return selected[key]


def _build_note(language: str, name: str, direction: Literal["high", "low"]) -> str:
    template_key = "high_note" if direction == "high" else "low_note"
    return _localize(language, template_key).format(name=name)


def _classify_marker(name: str, value: float) -> tuple[Literal["normal", "mild", "severe"], str | None]:
    rule = RISK_RULES.get(name)
    if not rule:
        return "normal", None

    min_value = rule.get("min")
    max_value = rule.get("max")
    severe_min = rule.get("severe_min")
    severe_max = rule.get("severe_max")

    if min_value is not None and value < min_value:
        if severe_min is not None and value < severe_min:
            return "severe", "low"
        return "mild", "low"

    if max_value is not None and value > max_value:
        if severe_max is not None and value > severe_max:
            return "severe", "high"
        return "mild", "high"

    return "normal", None


def assess_risk_details(raw_values: dict[str, object], language: str = "en") -> RiskAssessmentDetails:
    mild_minor_deviations: list[RiskDeviation] = []
    mild_relevant_deviations: list[RiskDeviation] = []
    severe_deviations: list[RiskDeviation] = []
    mild_relevant_markers: list[str] = []

    for name, raw_value in raw_values.items():
        if name in {"language", "age", "gender"} or raw_value is None:
            continue

        if not isinstance(raw_value, (int, float)):
            continue

        severity, direction = _classify_marker(name, float(raw_value))
        if severity == "normal" or direction is None:
            continue

        clinically_relevant = name in CLINICALLY_RELEVANT_MARKERS
        deviation = RiskDeviation(
            marker=name,
            direction=direction,
            severity=severity,
            note=_build_note(language, name, direction),
            clinically_relevant=clinically_relevant,
        )

        if severity == "severe":
            severe_deviations.append(deviation)
            continue

        if clinically_relevant:
            mild_relevant_deviations.append(deviation)
            mild_relevant_markers.append(name)
        else:
            mild_minor_deviations.append(deviation)

    deviations = [*severe_deviations, *mild_relevant_deviations, *mild_minor_deviations]
    all_notes = [deviation.note for deviation in deviations]
    abnormal_markers = [deviation.marker for deviation in deviations]
    has_major_relevant_abnormality = any(name in MAJOR_SIGNIFICANT_MARKERS for name in mild_relevant_markers)

    if severe_deviations:
        risk_level: RiskLevel = "SIGNIFICANT"
    elif has_major_relevant_abnormality or len(mild_relevant_deviations) >= 2:
        risk_level = "SIGNIFICANT"
    elif mild_relevant_deviations or mild_minor_deviations:
        risk_level = "BORDERLINE"
    else:
        risk_level = "NORMAL"

    return RiskAssessmentDetails(
        risk_level=risk_level,
        priority_notes=all_notes[:2],
        all_notes=all_notes,
        abnormal_markers=abnormal_markers,
        deviations=deviations,
    )


def assess_risk(raw_values: dict[str, object], language: str = "en") -> tuple[RiskLevel, list[str], list[str]]:
    details = assess_risk_details(raw_values, language)
    return details.risk_level, details.priority_notes, details.all_notes


def compute_risk_status(raw_values: dict[str, object], language: str = "en") -> RiskStatus:
    details = assess_risk_details(raw_values, language)
    risk_level = details.risk_level
    priority_notes = details.priority_notes
    all_notes = details.all_notes

    if risk_level == "SIGNIFICANT":
        return {
            "label": _localize(language, "red_label"),
            "color_key": "red",
            "explanation": _localize(language, "red_explanation"),
            "priority_notes": priority_notes,
        }

    if risk_level == "BORDERLINE":
        explanation_key = "yellow_explanation_one" if len(all_notes) == 1 else "yellow_explanation_many"
        return {
            "label": _localize(language, "yellow_label"),
            "color_key": "yellow",
            "explanation": _localize(language, explanation_key),
            "priority_notes": priority_notes,
        }

    return {
        "label": _localize(language, "green_label"),
        "color_key": "green",
        "explanation": _localize(language, "green_explanation"),
        "priority_notes": [],
    }
