import logging
import re
from functools import lru_cache
from typing import Optional, Tuple, List

from parser.config import resolve_pdf_page_limit
from parser.marker_metadata import get_marker_metadata

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency in test env
    pdfplumber = None


logger = logging.getLogger(__name__)

# Пытаемся подключить анонимайзер, если есть
try:
    from bot.utils.privacy import anonymize_text  # noqa: F401
    HAVE_PRIVACY = True
except Exception:
    HAVE_PRIVACY = False


# -----------------------
# Настройки и словари
# -----------------------

# Какие метрики «логично» чинить, если OCR пропустил точку (111 -> 11.1)
DECIMAL_FIX_WHITELIST = {
    "MCH", "MCHC", "MCV",
    "Глюкоза", "Glucose", "Glucosa",
    "Креатинин", "Creatinine", "Creatinina",
    "Мочевина", "Urea",
    "Билирубин общий", "Total bilirubin", "Bilirrubina total",
    "Билирубин прямой", "Direct bilirubin", "Bilirrubina directa",
    "АЛТ", "ALT",
    "АСТ", "AST",
    "ГГТ", "GGT",
    "АЛП", "ALP", "Alkaline phosphatase", "Fosfatasa alcalina",
    "Общий белок", "Total protein", "Proteína total",
    "Холестерин общий", "Total cholesterol", "Colesterol total",
    "ЛПНП", "LDL", "Colesterol LDL",
    "ЛПВП", "HDL", "Colesterol HDL",
}

DECIMAL_FIX_RANGES: dict[str, tuple[float, float]] = {
    "Глюкоза": (0.5, 30.0),
    "Glucose": (0.5, 30.0),
    "Glucosa": (0.5, 30.0),
    "Креатинин": (10.0, 1500.0),
    "Creatinine": (10.0, 1500.0),
    "Creatinina": (10.0, 1500.0),
    "АЛТ": (1.0, 1000.0),
    "ALT": (1.0, 1000.0),
    "АСТ": (1.0, 1000.0),
    "AST": (1.0, 1000.0),
    "ГГТ": (1.0, 1000.0),
    "GGT": (1.0, 1000.0),
    "ЛПНП": (0.1, 20.0),
    "LDL": (0.1, 20.0),
    "ЛПВП": (0.1, 20.0),
    "HDL": (0.1, 20.0),
    "Холестерин общий": (0.1, 30.0),
    "Total cholesterol": (0.1, 30.0),
    "Colesterol total": (0.1, 30.0),
    "MCH": (5.0, 60.0),
    "MCHC": (100.0, 500.0),
    "MCV": (20.0, 200.0),
}

# Отображение «разных» написаний показателей к **каноническому ключу** в нашем словаре
INDICATORS_MAP = {
    # Биохимия
    "ALT": ["alt", "аланинаминотрансфераза", "алт", "alanine aminotransferase", "transaminasa alt", "алат"],
    "AST": ["ast", "аспартатаминотрансфераза", "аст", "aspartate aminotransferase", "transaminasa ast", "асат"],
    "Глюкоза": ["глюкоза", "glucose", "glucosa"],
    "Натрий": ["натрий", "sodium", "na"],
    "Калий": ["калий", "potassium", "k"],
    "Хлор": ["хлор", "chloride", "chlorid", "cl"],
    "Креатинин": ["креатинин", "creatinine", "creatinina"],
    "eGFR": ["egfr", "estimated glomerular filtration rate"],
    "Мочевина": ["мочевина", "urea"],
    "BUN": ["bun", "blood urea nitrogen"],
    "Кислота мочевая": ["кислота мочевая", "uric acid", "urate"],
    "HbA1c": ["hba1c", "hb a1c", "a1c", "glycated hemoglobin", "glycosylated hemoglobin"],
    "Urine Albumin": [
        "urine albumin",
        "albumin urine",
        "urinary albumin",
        "microalbumin urine",
        "microalbumin, urine",
        "urine microalbumin",
        "u-albumin",
        "ualb",
    ],
    "Urine Creatinine": [
        "urine creatinine",
        "creatinine urine",
        "urinary creatinine",
        "u-creatinine",
        "u-creat",
        "ucreat",
    ],
    "ACR": [
        "acr",
        "albumin creatinine ratio",
        "albumin/creatinine ratio",
        "alb/creat ratio",
        "urine acr",
    ],
    "Билирубин общий": ["билирубин общий", "total bilirubin", "bilirrubina total"],
    "Билирубин прямой": ["билирубин прямой", "direct bilirubin", "bilirrubina directa"],
    "Холестерин общий": ["общий холестерин", "total cholesterol", "colesterol total", "cholesterol total"],
    "ЛПВП": ["лпвп", "hdl", "colesterol hdl", "hdl-c"],
    "ЛПНП": ["лпнп", "ldl", "colesterol ldl", "ldl-c"],
    "АЛП": ["щелочная фосфатаза", "алп", "alp", "alkaline phosphatase", "fosfatasa alcalina"],
    "ГГТ": ["ggt", "ггт", "gamma-gt", "gamma glutamyl transferase", "gammaglutamil transferasa"],
    "Общий белок": ["общий белок", "total protein", "proteína total", "protein total"],
    "CRP": ["c-reactive protein", "c reactive protein", "с-реактивный белок", "proteína c reactiva", "crp"],
    "Витамин D (25-OH)": [
        "25-oh vitamin d",
        "vitamin d 25-oh",
        "25 oh vitamina d",
        "vitamina d 25-oh",
        "витамин d (25-oh)",
        "витамин d 25-oh",
        "vitamin d",
        "vitamina d",
        "витамин d",
    ],
    "Цинк": ["цинк", "zinc", "zinc serum", "serum zinc"],

    # ОАК
    "Гемоглобин": ["гемоглобин", "hgb", "hemoglobin", "hemoglobina", "hb"],
    "Гематокрит": ["гематокрит", "hct", "hematocrit", "hematocrito", "ht"],
    "Нормобласты": [
        "nrbc",
        "nrbc %",
        "nrbc%",
        "нормобласты",
        "ядерные эритроциты",
        "эритроциты с ядром",
        "nucleated red blood cells",
    ],
    "Эритроциты": ["эритроциты", "rbc", "red blood cells", "eritrocitos"],
    "Лейкоциты": ["лейкоциты", "wbc", "white blood cells", "leucocitos"],
    "Тромбоциты": ["тромбоциты", "plt", "platelets", "plaquetas"],
    "СОЭ": ["соэ", "esr", "sedimentation rate", "vsg", "velocidad de sedimentación"],

    "MCV": ["mcv", "mean corpuscular volume", "volumen corpuscular medio"],
    "MCH": ["mch", "mean corpuscular hemoglobin", "hemoglobina corpuscular media"],
    "MCHC": ["mchc", "mean corpuscular hemoglobin concentration",
             "concentración de hemoglobina corpuscular media"],
    "RDW": ["rdw", "red cell distribution width", "amplitud de distribución eritrocitaria"],

    "Нейтрофилы %": ["нейтрофилы %", "neutrophils %", "neutrófilos %", "нейтрофилы", "neutrophils", "neutrófilos", "neu %", "neu%", "neu"],
    "Лимфоциты %": ["лимфоциты %", "lymphocytes %", "linfocitos %", "lym %", "lym%", "лимфоциты", "lymphocytes", "linfocitos", "lym"],
    "Моноциты %": ["моноциты %", "monocytes %", "monocitos %", "моноциты", "monocytes", "monocitos", "mon %", "mon%", "mon"],
    "Эозинофилы %": ["эозинофилы %", "eosinophils %", "eosinófilos %", "эозинофилы", "eosinophils", "eosinófilos", "eos %", "eos%", "eos"],
    "Базофилы %": ["базофилы %", "basophils %", "basófilos %", "базофилы", "basophils", "basófilos", "baso %", "baso%", "baso"],

    # Абсолюты (часто встречаются)
    "Нейтрофилы абс.": ["neutrophils abs", "neutrophils abs.", "нейтрофилы абс", "нейтрофилы абс.", "neu abs", "neut abs", "neu#", "neut#", "anc"],
    "Лимфоциты абс.": ["lymphocytes abs", "lymphocytes abs.", "лимфоциты абс", "лимфоциты абс.", "lym abs", "lym abs.", "lym#", "lym #", "lym"],
    "Моноциты абс.": ["monocytes abs", "monocytes abs.", "моноциты абс", "моноциты абс.", "mon abs", "mon#", "mon #", "mon"],
    "Эозинофилы абс.": ["eosinophils abs", "eosinophils abs.", "эозинофилы абс", "эозинофилы абс.", "eos abs", "eos#", "eos #", "eos"],
    "Базофилы абс.": ["basophils abs", "basophils abs.", "базофилы абс", "базофилы абс.", "baso abs", "baso#", "baso #", "baso"],
    "RE-LYMP abs": [
        "re-lymp abs",
        "re lymp abs",
        "re-lymp абс",
        "re-lymp",
        "re lymp",
        "re-lymph",
        "reactive lymphocytes",
        "reactive lymphocyte",
        "реактивные лимфоциты",
    ],
    "RE-LYMP %": ["re-lymp %", "re lymp %", "re-lymph %"],
    "AS-LYMP abs": [
        "as-lymp abs",
        "as lymp abs",
        "as-lymp абс",
        "as-lymp",
        "as lymp",
        "atypical lymphocytes",
        "atypical lymphocyte",
        "plasma cells",
        "plasma cell",
        "плазматические клетки",
    ],
    "AS-LYMP %": ["as-lymp %", "as lymp %"],

    # --- Антитела / иммуноглобулины ---
    # Иммуноглобулины (частые варианты записи и локализации)
    "IgA": [
        "iga", "immunoglobulin a", "immunoglobulina a",
        "игa", "иг а", "иммуноглобулин a"
    ],
    "IgG": [
        "igg", "immunoglobulin g", "immunoglobulina g",
        "игg", "иг г", "иммуноглобулин g"
    ],
    "IgM": [
        "igm", "immunoglobulin m", "immunoglobulina m",
        "игm", "иг м", "иммуноглобулин m"
    ],
    "IgE": [
        "ige", "immunoglobulin e", "immunoglobulina e",
        "игe", "иг е", "иммуноглобулин e"
    ],
    "IgD": [
        "igd", "immunoglobulin d", "immunoglobulina d",
        "игd", "иг д", "иммуноглобулин d"
    ],

    # Anti-TPO (антитела к тиреопероксидазе)
    "anti-TPO": [
        "anti-tpo", "anti tpo", "anti-tpo", "anti–tpo",
        "антитела к тпо", "антитела к тиреопероксидазе", "ато", "ат к тпо", "ат-тпо",
        "anti-thyroid peroxidase", "anticuerpos anti tpo", "anticuerpos contra la peroxidasa tiroidea"
    ],

    # Anti-TG (антитела к тиреоглобулину)
    "anti-TG": [
        "anti-tg", "anti tg", "anti-tg", "anti–tg",
        "антитела к тг", "антитела к тиреоглобулину", "ат к тг", "ат-тг",
        "anti-thyroglobulin", "anticuerpos anti tg", "anticuerpos contra la tiroglobulina"
    ],

    # ANA (антинуклеарные антитела)
    "ANA": [
        "ana", "anti-nuclear", "antinuclear", "antinucleares",
        "антинуклеарные антитела", "анти-нуклеарные", "анти нуклеарные"
    ],
}

_GENERIC_ALIAS_EXCLUSIONS = {
    "эритроциты": ("нормобласт", "nrbc", "с ядром", "ядерн"),
    "rbc": ("nrbc",),
    "red blood cells": ("nucleated", "nrbc"),
    "нейтрофилы": ("абс", "abs", "#"),
    "neutrophils": ("abs", "#"),
    "neutrófilos": ("abs", "#"),
    "лимфоциты": ("абс", "abs", "#", "реактив", "reactive", "re-lymp", "as-lymp", "plasma"),
    "lymphocytes": ("abs", "#", "reactive", "re-lymp", "as-lymp", "plasma"),
    "linfocitos": ("abs", "#", "reactiv"),
    "моноциты": ("абс", "abs", "#"),
    "monocytes": ("abs", "#"),
    "monocitos": ("abs", "#"),
    "эозинофилы": ("абс", "abs", "#"),
    "eosinophils": ("abs", "#"),
    "eosinófilos": ("abs", "#"),
    "базофилы": ("абс", "abs", "#"),
    "basophils": ("abs", "#"),
    "basófilos": ("abs", "#"),
}

_DIFFERENTIAL_PERCENT_MARKERS = {
    "Нейтрофилы %",
    "Лимфоциты %",
    "Моноциты %",
    "Эозинофилы %",
    "Базофилы %",
}

_PERCENTAGE_RESULT_MARKERS = _DIFFERENTIAL_PERCENT_MARKERS | {
    "RE-LYMP %",
    "AS-LYMP %",
}

_DIFFERENTIAL_ABSOLUTE_MARKERS = {
    "Нейтрофилы абс.",
    "Лимфоциты абс.",
    "Моноциты абс.",
    "Эозинофилы абс.",
    "Базофилы абс.",
}

_DIFFERENTIAL_SLOT_PAIRS = {
    "Нейтрофилы %": "Нейтрофилы абс.",
    "Лимфоциты %": "Лимфоциты абс.",
    "Моноциты %": "Моноциты абс.",
    "Эозинофилы %": "Эозинофилы абс.",
    "Базофилы %": "Базофилы абс.",
}

_ABSOLUTE_TO_PERCENT_DIFFERENTIAL_MARKERS = {
    absolute: percent for percent, absolute in _DIFFERENTIAL_SLOT_PAIRS.items()
}

_UNIT_ALIASES = {
    "µmol/l": "umol/L",
    "μmol/l": "umol/L",
    "umol/l": "umol/L",
    "мкмоль/л": "umol/L",
    "mmol/l": "mmol/L",
    "ммоль/л": "mmol/L",
    "mmol/mol": "mmol/mol",
    "mol/l": "mol/L",
    "mg/l": "mg/L",
    "мг/л": "mg/L",
    "mg/dl": "mg/dL",
    "mg alb/mmol": "mg Alb/mmol",
    "ng/ml": "ng/mL",
    "нг/мл": "ng/mL",
    "fl": "fL",
    "pg": "pg",
    "pg/ml": "pg/mL",
    "iu/ml": "IU/mL",
    "ме/мл": "IU/mL",
    "u/l": "U/L",
    "ед/л": "U/L",
    "g/l": "g/L",
    "г/л": "g/L",
    "g/dl": "g/dL",
    "ml/min/1.73m2": "mL/min/1.73m2",
    "ml/min/1.73 m2": "mL/min/1.73m2",
    "mg/mmol": "mg/mmol",
    "mg/g": "mg/g",
    "k/ul": "K/uL",
    "k/µl": "K/uL",
    "k/μl": "K/uL",
    "m/ul": "M/uL",
    "m/µl": "M/uL",
    "m/μl": "M/uL",
    "mm/h": "mm/h",
    "мм/ч": "mm/h",
    "10^9/l": "x10^9/L",
    "10^12/l": "x10^12/L",
    "x10^9/l": "x10^9/L",
    "x10^12/l": "x10^12/L",
    "109/l": "x10^9/L",
    "1012/l": "x10^12/L",
    "x109/l": "x10^9/L",
    "x1012/l": "x10^12/L",
    "10^9/л": "x10^9/L",
    "10^12/л": "x10^12/L",
    "x10^9/л": "x10^9/L",
    "x10^12/л": "x10^12/L",
}

_UNIT_PATTERN = re.compile(
    r"\b(?:g/l|г/л|g/dl|mg/l|мг/л|mg/dl|mg\s+alb/mmol|mg/mmol|mg/g|mmol/l|ммоль/л|"
    r"mmol/mol|mol/l|umol/l|µmol/l|μmol/l|мкмоль/л|ng/ml|нг/мл|fl|pg|pg/ml|iu/ml|"
    r"ме/мл|u/l|ед/л|ml/min/1\.73 ?m2|mm/h|мм/ч|k/[uµμ]l|m/[uµμ]l|%|x10\^?9/[lл]|"
    r"x10\^?12/[lл]|10\^9/[lл]|10\^12/[lл]|x10[⁹9]/[lл]|x10[¹1][²2]/[lл]|"
    r"10[⁹9]/[lл]|10[¹1][²2]/[lл])\b",
    flags=re.IGNORECASE,
)

# -----------------------
# Публичная функция
# -----------------------

def extract_lab_data_from_pdf(filepath: str, max_pages: int | None = None) -> dict:
    """
    Извлекает метрики из PDF. Возвращает словарь {канонический_показатель: float|None}.
    Читает до max_pages страниц. Пытается фиксить частые OCR-ошибки.
    """
    lab_data: dict = {}
    if pdfplumber is None:
        return {}
    page_limit = resolve_pdf_page_limit(max_pages)

    try:
        with pdfplumber.open(filepath) as pdf:
            text_chunks: List[str] = []
            pages_to_read = min(len(pdf.pages), page_limit)
            for i in range(pages_to_read):
                page = pdf.pages[i]
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)

        raw_text = "\n".join(text_chunks)

        # Анонимизация (если есть модуль)
        if HAVE_PRIVACY:
            try:
                raw_text = anonymize_text(raw_text)  # type: ignore
            except Exception:
                pass

        # По строкам
        lines = [l for l in raw_text.split("\n") if l.strip()]

        for line in lines:
            key, val = match_indicator(line)
            if key:
                lab_data[key] = val

        return lab_data

    except Exception as e:
        # Без лишней болтологии: просто вернём пусто.
        # Если нужно логировать — логи уже настраиваются в main/logging.
        return {}


# -----------------------
# Внутренняя логика
# -----------------------

def match_indicator(line: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Пытаемся сопоставить строку конкретному показателю и извлечь значение.
    """
    matched = match_indicator_with_alias(line)
    if matched is None:
        return None, None

    canonical, alias = _resolve_differential_slot_by_unit(line, matched)
    value = extract_value(line, canonical, alias)
    return canonical, value

    return None, None


def match_indicator_with_alias(line: str) -> Optional[Tuple[str, str]]:
    """
    Возвращает (канонический_ключ, alias), если строка совпала с показателем.
    """
    line_low = _normalize_for_match(line)
    matches: List[Tuple[str, str]] = []

    for canonical, aliases in INDICATORS_MAP.items():
        for alias in aliases:
            if _alias_matches(line_low, alias) and not _alias_conflicts(line_low, alias):
                matches.append((canonical, alias))

    if not matches:
        return None

    disambiguated = _disambiguate_differential_aliases(line_low, matches)
    if disambiguated is not None:
        return disambiguated

    return max(matches, key=lambda item: (_alias_specificity(item[1]), len(item[0])))


def _disambiguate_differential_aliases(
    line_low: str,
    matches: List[Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    percent_matches = [item for item in matches if item[0] in _DIFFERENTIAL_PERCENT_MARKERS]
    absolute_matches = [item for item in matches if item[0] in _DIFFERENTIAL_ABSOLUTE_MARKERS]
    if not percent_matches or not absolute_matches:
        return None

    if "%" in line_low:
        return max(percent_matches, key=lambda item: (_alias_specificity(item[1]), len(item[0])))

    if any(token in line_low for token in (" abs", "абс", "#", "x10^9/", "10^9/", "/л", "/l", "anc")):
        return max(absolute_matches, key=lambda item: (_alias_specificity(item[1]), len(item[0])))

    return None


def _resolve_differential_slot_by_unit(line: str, matched: Tuple[str, str]) -> Tuple[str, str]:
    canonical, alias = matched
    detected_unit = extract_unit(line)

    if detected_unit in {"x10^9/L", "K/uL"}:
        absolute_marker = _DIFFERENTIAL_SLOT_PAIRS.get(canonical)
        if absolute_marker is not None:
            return absolute_marker, alias
        if canonical in _DIFFERENTIAL_ABSOLUTE_MARKERS:
            return canonical, alias

    if detected_unit == "%":
        percent_marker = _ABSOLUTE_TO_PERCENT_DIFFERENTIAL_MARKERS.get(canonical)
        if percent_marker is not None:
            return percent_marker, alias
        if canonical in _DIFFERENTIAL_PERCENT_MARKERS:
            return canonical, alias

    return canonical, alias


def extract_value(line: str, metric_name: str, matched_alias: str | None = None) -> Optional[float]:
    """
    Извлекаем число из строки, исправляем типичные OCR-ошибки (по whitelists),
    мягко нормализуем.
    """
    source_text = _slice_after_alias(line, matched_alias) if matched_alias else line
    positional_override = _extract_simple_positional_override_value(
        line=line,
        source_text=source_text,
        metric_name=metric_name,
        matched_alias=matched_alias,
    )
    if positional_override is not None:
        logger.debug(
            "value_selection marker=%s path=simple_scalar_early_return value=%s",
            metric_name,
            positional_override,
        )
        return positional_override

    first_standalone_value = _extract_first_standalone_value(source_text)
    primary_candidates = _extract_primary_result_candidates(source_text)
    source_candidates = _parse_candidates(source_text)
    candidates = source_candidates or _parse_candidates(line)

    if not primary_candidates and not candidates:
        return None

    detected_unit = extract_unit(line)
    reference_range = extract_reference_range(line)
    simple_positional_value = _extract_simple_positional_value(source_text)
    raw = simple_positional_value if simple_positional_value is not None else first_standalone_value
    if raw is None:
        raw = primary_candidates[0] if primary_candidates else candidates[0]

    if simple_positional_value is None and _is_percentage_metric(metric_name):
        percentage_primary = _select_percentage_primary_result(primary_candidates)
        if percentage_primary is not None:
            raw = percentage_primary

    if simple_positional_value is None and primary_candidates and candidates and _looks_like_layout_concatenated_value(
        parsed_value=candidates[0],
        primary_value=primary_candidates[0],
        metric_name=metric_name,
        detected_unit=detected_unit,
        reference_range=reference_range,
    ):
        raw = primary_candidates[0]

    if simple_positional_value is None and first_standalone_value is not None and _looks_like_corrupted_primary_value(
        parsed_value=raw,
        fallback_value=first_standalone_value,
    ):
        raw = first_standalone_value

    # Decimal-fix is only allowed when the corrected value is the only clearly plausible reading.
    fixed = _choose_value_with_decimal_fix(
        raw,
        metric_name,
        source_text=line,
        detected_unit=detected_unit,
        reference_range=reference_range,
    )

    # Нормализация единиц при явном контексте (очень мягкая)
    fixed = _unit_adjust_if_needed(fixed, line, metric_name)

    logger.debug(
        "value_selection marker=%s path=smart value=%s",
        metric_name,
        fixed,
    )

    return fixed


def convert_value_safely(name: str, raw_val: str | float | int | None) -> Optional[float]:
    try:
        if raw_val is None:
            return None
        if isinstance(raw_val, (int, float)):
            value = float(raw_val)
            should_fix_decimal = True
        else:
            raw = str(raw_val).strip()
            if name == "ANA" and ":" in raw:
                tail = raw.split(":")[-1].strip()
                if tail.isdigit():
                    return float(tail)
            candidates = _parse_candidates(raw)
            if not candidates:
                return None
            value = candidates[0]
            should_fix_decimal = not bool(re.search(r"[A-Za-zА-Яа-яЁё/%]", raw))

        if should_fix_decimal:
            value = _choose_value_with_decimal_fix(value, name, source_text=str(raw_val) if raw_val is not None else None)
        return value if value == value else None
    except Exception:
        return None


def _parse_candidates(line: str) -> List[float]:
    """
    Находим все числа в строке и приводим к float:
    - '7,5' -> 7.5
    - '7 500' -> 7500
    - '7•5', '7·5' -> 7.5
    """
    clean = _normalize_numeric_text(line)
    raw_nums = re.findall(r"(?<![\w/])[-+]?\d[\d\s.,]*", clean)

    nums: List[float] = []
    for token in raw_nums:
        t = token.strip()
        normalized = _normalize_number_token(t)
        if normalized is None:
            continue
        try:
            nums.append(float(normalized))
        except Exception:
            continue

    return nums


def extract_reference_range(line: str) -> Optional[str]:
    clean = _normalize_numeric_text(line)
    inline_parenthetical = _extract_inline_parenthetical_reference(clean)

    standalone_patterns = [
        r"^\s*([<>≤≥]=?\s*\d+(?:[.,]\d+)?)\s*$",
        r"^\s*(\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?)\s*$",
    ]
    for pattern in standalone_patterns:
        match = re.search(pattern, clean)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).replace(",", ".").strip()

    trailing_comparator = re.search(r"([<>≤≥]=?\s*\d+(?:[.,]\d+)?)\s*$", clean)
    if trailing_comparator:
        return re.sub(r"\s+", " ", trailing_comparator.group(1)).replace(",", ".").strip()

    patterns = [
        r"(\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).replace(",", ".").strip()

    compact_pair = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*", clean)
    if compact_pair:
        low, high = compact_pair.groups()
        return f"{low.replace(',', '.')} - {high.replace(',', '.')}"

    trailing_pair = re.search(r"(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", clean)
    if trailing_pair:
        low, high = trailing_pair.groups()
        return f"{low.replace(',', '.')} - {high.replace(',', '.')}"

    if inline_parenthetical:
        return inline_parenthetical
    return None


def extract_unit(line: str) -> Optional[str]:
    normalized_line = _normalize_unit_search_text(line)
    unit_match = _UNIT_PATTERN.search(normalized_line)
    if not unit_match:
        return None

    unit = unit_match.group(0)
    return _UNIT_ALIASES.get(unit.lower(), unit)


def _slice_after_alias(line: str, alias: str) -> str:
    normalized_line = _normalize_for_match(line)
    match = _alias_pattern(alias).search(normalized_line)
    if not match:
        return line
    return line[match.end():]


def _extract_primary_result_candidates(text: str) -> List[float]:
    primary_segment = _extract_primary_result_segment(text)
    if not primary_segment:
        return []
    return _parse_candidates(primary_segment)


def _extract_first_standalone_value(text: str) -> float | None:
    match = _extract_first_standalone_value_match(text)
    if match is None:
        return None
    return match[0]


def _extract_first_standalone_value_match(text: str) -> tuple[float, int, int] | None:
    if not text:
        return None

    primary_segment = _extract_primary_result_segment(text) or text
    clean = _normalize_numeric_text(primary_segment)

    for match in re.finditer(r"(?<![\w/])[-+]?\d+(?:[.,]\d+)?", clean):
        token = match.group(0)
        tail = clean[match.end():]
        joined, consumed = _maybe_extend_numeric_token_with_consumed(token, tail)
        normalized = _normalize_number_token(joined)
        if normalized is None:
            continue
        try:
            return float(normalized), match.start(), match.end() + consumed
        except Exception:
            continue

    return None


def _select_simple_scalar_value_match(text: str) -> tuple[float, int, int] | None:
    if not text:
        return None

    unit_span = _find_unit_span(text)
    if unit_span is None:
        return None

    unit_start, _ = unit_span
    clean = _normalize_numeric_text(text)
    selected_match: tuple[float, int, int] | None = None

    search_start = 0
    pattern = re.compile(r"(?<![\w/])[-+]?\d+(?:[.,]\d+)?")
    while True:
        match = pattern.search(clean, search_start)
        if match is None:
            break

        token = match.group(0)
        tail = clean[match.end():]
        joined, consumed = _maybe_extend_numeric_token_with_consumed(token, tail)
        normalized = _normalize_number_token(joined)
        next_search_start = match.end() + max(consumed, 0)
        if next_search_start <= search_start:
            next_search_start = match.end()

        if normalized is None:
            search_start = next_search_start
            continue

        try:
            candidate = float(normalized), match.start(), match.end() + consumed
        except Exception:
            search_start = next_search_start
            continue

        _, _, value_end = candidate
        if value_end <= unit_start:
            if _is_ignorable_value_to_unit_gap(text[value_end:unit_start]):
                selected_match = candidate

        search_start = next_search_start

    return selected_match


def _maybe_extend_numeric_token(token: str, tail: str) -> str:
    return _maybe_extend_numeric_token_with_consumed(token, tail)[0]


def _maybe_extend_numeric_token_with_consumed(token: str, tail: str) -> tuple[str, int]:
    continuation = re.match(r"\s+(\d+)(?!\s*[\^/])", tail)
    if continuation is None:
        return token, 0

    next_part = continuation.group(1)
    remainder = tail[continuation.end():]
    remainder_lstrip = remainder.lstrip()

    if re.match(r"[-–—]\s*\d", remainder_lstrip):
        return token, 0

    if len(next_part) == 3 and token.lstrip("+-").isdigit():
        return f"{token} {next_part}", continuation.end()

    unsigned = token.lstrip("+-")
    if "." not in unsigned and "," not in unsigned and len(next_part) <= 2:
        return f"{token} {next_part}", continuation.end()

    return token, 0


def _extract_simple_positional_value(text: str) -> float | None:
    if not text:
        return None

    value_match = _extract_first_standalone_value_match(text)
    unit_span = _find_unit_span(text)
    if value_match is None or unit_span is None:
        return None

    value, _, value_end = value_match
    unit_start, unit_end = unit_span
    if value_end > unit_start:
        return None

    if not _is_ignorable_value_to_unit_gap(text[value_end:unit_start]):
        return None

    trailing = text[unit_end:]
    if not _looks_like_simple_reference_tail(trailing):
        return None

    return value


def _extract_simple_positional_override_value(
    line: str,
    source_text: str,
    metric_name: str,
    matched_alias: str | None,
) -> float | None:
    del matched_alias

    if not _is_simple_scalar_row(
        line=line,
        source_text=source_text,
        metric_name=metric_name,
    ):
        return None

    unit_span = _find_unit_span(source_text)
    if unit_span is None:
        return None

    value_match = _select_simple_scalar_value_match(source_text)
    if value_match is None:
        return None

    value, _, value_end = value_match
    unit_start, unit_end = unit_span
    if value_end > unit_start:
        return None

    if not _is_ignorable_value_to_unit_gap(source_text[value_end:unit_start]):
        return None

    trailing = source_text[unit_end:]
    if not _looks_like_simple_reference_tail(trailing):
        return None

    return value


def _is_simple_scalar_row(line: str, source_text: str, metric_name: str) -> bool:
    if not _is_structurally_simple_linear_row(line):
        return False

    metric = metric_name.strip()
    if metric in _DIFFERENTIAL_ABSOLUTE_MARKERS or metric in _PERCENTAGE_RESULT_MARKERS:
        return False
    if metric in {"RE-LYMP abs", "AS-LYMP abs", "Нормобласты"}:
        return False

    value_match = _select_simple_scalar_value_match(source_text)
    if value_match is None:
        return False

    _, _, value_end = value_match
    unit_span = _find_unit_span(source_text)
    if unit_span is None:
        return False

    unit_start, unit_end = unit_span
    if value_end > unit_start:
        return False

    if not _is_ignorable_value_to_unit_gap(source_text[value_end:unit_start]):
        return False

    detected_unit = extract_unit(source_text) or extract_unit(line)
    if detected_unit == "%":
        return False

    trailing = source_text[unit_end:]
    return _looks_like_simple_reference_tail(trailing)


def _extract_primary_result_segment(text: str) -> str:
    if not text:
        return text

    cutoff = len(text)
    reference_start = _find_reference_start(text)
    unit_start = _find_unit_start(text)

    if reference_start is not None:
        cutoff = min(cutoff, reference_start)
    if unit_start is not None:
        cutoff = min(cutoff, unit_start)

    return text[:cutoff]


def _is_structurally_simple_linear_row(text: str) -> bool:
    normalized = _normalize_for_match(text)
    if "\n" in text or "\r" in text:
        return False
    if _scientific_notation_present(text):
        return False
    if any(token in normalized for token in ("смотри текст", "see text", "refer to comment")):
        return False
    return True


def _find_simple_override_unit_span(text: str, value_end: int) -> tuple[int, int] | None:
    unit_span = _find_unit_span(text)
    if unit_span is not None and unit_span[0] >= value_end:
        return unit_span

    tail = text[value_end:]
    fallback_match = re.match(r"\s*([A-Za-zА-Яа-яЁёµμ%][A-Za-zА-Яа-яЁё0-9µμ/%.^-]*)", tail)
    if fallback_match is None:
        return None

    unit_text = fallback_match.group(1)
    if not re.search(r"[A-Za-zА-Яа-яЁёµμ%]", unit_text):
        return None

    start = value_end + fallback_match.start(1)
    end = value_end + fallback_match.end(1)
    return start, end


def _normalize_for_match(value: str) -> str:
    return value.lower().replace("–", "-").replace("—", "-")


@lru_cache(maxsize=512)
def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(_normalize_for_match(alias))
    return re.compile(rf"(?<![a-zа-яё0-9]){escaped}(?![a-zа-яё0-9])")


def _alias_matches(line_low: str, alias: str) -> bool:
    return _alias_pattern(alias).search(line_low) is not None


def _alias_conflicts(line_low: str, alias: str) -> bool:
    exclusion_tokens = _GENERIC_ALIAS_EXCLUSIONS.get(_normalize_for_match(alias), ())
    return any(token in line_low for token in exclusion_tokens)


def _alias_specificity(alias: str) -> tuple[int, int]:
    normalized = _normalize_for_match(alias)
    token_bonus = sum(1 for token in ("%", "abs", "#", "-", ".", " ") if token in normalized)
    return (len(normalized), token_bonus)


def _is_percentage_metric(metric_name: str) -> bool:
    return metric_name.strip() in _PERCENTAGE_RESULT_MARKERS


def _select_percentage_primary_result(primary_candidates: List[float]) -> float | None:
    for candidate in primary_candidates:
        if 0.0 <= candidate <= 100.0:
            return candidate
    return None


def _looks_like_layout_concatenated_value(
    parsed_value: float,
    primary_value: float,
    metric_name: str,
    detected_unit: str | None,
    reference_range: str | None,
) -> bool:
    if parsed_value == primary_value:
        return False

    if reference_range is None:
        return False

    if float(int(parsed_value)) != parsed_value:
        return False

    primary_plausible = _is_plausible_value_for_metric(primary_value, metric_name, detected_unit)
    parsed_plausible = _is_plausible_value_for_metric(parsed_value, metric_name, detected_unit)
    if not primary_plausible or parsed_plausible:
        return False

    parsed_digits = str(abs(int(parsed_value)))
    primary_digits = str(abs(int(primary_value)))
    if len(parsed_digits) <= len(primary_digits):
        return False

    return parsed_digits.startswith(primary_digits)


def _looks_like_corrupted_primary_value(parsed_value: float, fallback_value: float) -> bool:
    if parsed_value == fallback_value:
        return False

    parsed_text = format(parsed_value, ".15g")
    fallback_text = format(fallback_value, ".15g")
    parsed_digits = re.sub(r"\D", "", parsed_text)
    fallback_digits = re.sub(r"\D", "", fallback_text)

    if not parsed_digits or not fallback_digits:
        return False

    if len(parsed_digits) >= max(len(fallback_digits) + 3, 7):
        return True

    if len(parsed_digits) > len(fallback_digits) and fallback_digits in parsed_digits:
        return True

    return False


def _value_matches_reference_range(value: float, reference_range: str | None) -> bool:
    if not reference_range:
        return False

    normalized = reference_range.strip().replace(",", ".")
    between = re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", normalized)
    if between:
        low, high = (float(part) for part in between.groups())
        return low <= value <= high

    upper = re.fullmatch(r"(?:<|<=|≤)\s*(\d+(?:\.\d+)?)", normalized)
    if upper:
        return value <= float(upper.group(1))

    lower = re.fullmatch(r"(?:>|>=|≥)\s*(\d+(?:\.\d+)?)", normalized)
    if lower:
        return value >= float(lower.group(1))

    return False


def _scientific_notation_present(text: str | None) -> bool:
    if not text:
        return False
    normalized = _normalize_unit_text(text)
    return re.search(r"\d+(?:[.,]\d+)?\s+(?:x\s*)?10\^?(?:9|12)\s*/\s*[lл]\b", normalized, flags=re.IGNORECASE) is not None


def _decimal_fix_candidate(value: float) -> float | None:
    if float(int(value)) != value:
        return None
    if not (10 <= value < 10000):
        return None
    return value / 10.0


def _line_reference_supports_decimal_fix(
    original_value: float,
    candidate_value: float,
    reference_range: str | None,
) -> bool:
    if not reference_range:
        return True
    original_matches = _value_matches_reference_range(original_value, reference_range)
    candidate_matches = _value_matches_reference_range(candidate_value, reference_range)
    return candidate_matches and not original_matches


def _line_suggests_decimal_loss(text: str | None) -> bool:
    if not text:
        return False
    normalized = _normalize_numeric_text(text)
    return re.search(r"\b\d{1,2}\s+\d(?:\D|$)", normalized) is not None


def _should_apply_decimal_fix(
    original_value: float,
    candidate_value: float,
    metric_name: str,
    detected_unit: str | None,
    reference_range: str | None,
    source_text: str | None,
) -> bool:
    if _scientific_notation_present(source_text):
        return False

    original_plausible = _is_plausible_value_for_metric(original_value, metric_name, detected_unit)
    candidate_plausible = _is_plausible_value_for_metric(candidate_value, metric_name, detected_unit)

    if original_plausible or not candidate_plausible:
        return False

    if not _line_reference_supports_decimal_fix(original_value, candidate_value, reference_range):
        if detected_unit is not None:
            return False

    if detected_unit is not None:
        return _line_suggests_decimal_loss(source_text)

    return True


def _choose_value_with_decimal_fix(
    value: float,
    metric_name: str,
    source_text: str | None = None,
    detected_unit: str | None = None,
    reference_range: str | None = None,
) -> float:
    candidate = _decimal_fix_candidate(value)
    if candidate is None:
        return value

    fixed = _smart_decimal_fix(value, metric_name, source_text=source_text, detected_unit=detected_unit)
    if fixed == value:
        return value

    if _should_apply_decimal_fix(
        original_value=value,
        candidate_value=fixed,
        metric_name=metric_name,
        detected_unit=detected_unit,
        reference_range=reference_range,
        source_text=source_text,
    ):
        return fixed

    return value


def _is_plausible_value_for_metric(value: float, metric_name: str, detected_unit: str | None = None) -> bool:
    if _is_percentage_metric(metric_name):
        return 0.0 <= value <= 100.0

    metadata = get_marker_metadata(metric_name.strip()) or {}
    expected_unit = metadata.get("unit")
    if detected_unit and expected_unit and detected_unit != expected_unit:
        return False

    if _value_matches_reference_range(value, metadata.get("reference_range")):
        return True

    expected_range = DECIMAL_FIX_RANGES.get(metric_name.strip())
    if expected_range is None:
        return False

    low, high = expected_range
    return low <= value <= high


def _smart_decimal_fix(
    value: float,
    metric_name: str,
    source_text: str | None = None,
    detected_unit: str | None = None,
) -> float:
    """
    Пробуем аккуратно восстановить «пропавшую» точку только для действительно
    неоднозначных чисел без явной десятичной части. Membership в whitelist сам по себе
    не приводит к изменению значения: окончательное решение принимает plausibility gate.
    """
    name = metric_name.strip()

    if name not in DECIMAL_FIX_WHITELIST:
        return value

    candidate = _decimal_fix_candidate(value)
    if candidate is None:
        return value

    return candidate


def _unit_adjust_if_needed(value: float, line: str, metric_name: str) -> float:
    """
    Queue 2 is unit-recognition-only: retain source numeric values exactly.
    Unit metadata may be normalized by spelling, but no value conversion happens here.
    """
    del line, metric_name
    return value


def _normalize_numeric_text(value: str) -> str:
    return (
        value.replace("•", ".")
        .replace("·", ".")
        .replace("…", ".")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("\xa0", " ")
    )


def _normalize_unit_text(value: str) -> str:
    normalized = _normalize_numeric_text(value)
    normalized = (
        normalized.replace("×", "x")
        .replace("х", "x")
        .replace("Х", "x")
        .replace("⁹", "^9")
        .replace("¹²", "^12")
    )
    localized_unit_patterns = (
        (r"(?i)\bмкмоль\s*/\s*л\b", "umol/l"),
        (r"(?i)\bммоль\s*/\s*л\b", "mmol/l"),
        (r"(?i)\bмг\s*/\s*л\b", "mg/l"),
        (r"(?i)\bнг\s*/\s*мл\b", "ng/ml"),
        (r"(?i)\bг\s*/\s*л\b", "g/l"),
        (r"(?i)\bед\s*/\s*л\b", "u/l"),
        (r"(?i)\bме\s*/\s*мл\b", "iu/ml"),
    )
    for pattern, replacement in localized_unit_patterns:
        normalized = re.sub(pattern, replacement, normalized)
    normalized = normalized.replace("мм/ч", "mm/h").replace("/л", "/l")
    return normalized


def _normalize_unit_search_text(value: str) -> str:
    return (
        _normalize_numeric_text(value)
        .replace("×", "x")
        .replace("х", "x")
        .replace("Х", "x")
        .replace("⁹", "9")
        .replace("¹", "1")
        .replace("²", "2")
    )


def _find_unit_start(text: str) -> int | None:
    unit_span = _find_unit_span(text)
    if unit_span is None:
        return None
    return unit_span[0]


def _find_unit_span(text: str) -> tuple[int, int] | None:
    normalized_text = _normalize_unit_search_text(text)
    unit_match = _UNIT_PATTERN.search(normalized_text)
    if unit_match is None:
        return None
    return unit_match.start(), unit_match.end()


def _find_reference_start(text: str) -> int | None:
    clean = _normalize_numeric_text(text)
    patterns = [
        r"([<>≤≥]=?\s*\d+(?:[.,]\d+)?)\s*$",
        r"(\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?)",
        r"(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$",
    ]
    starts: List[int] = []

    for pattern in patterns:
        match = re.search(pattern, clean)
        if match is not None:
            starts.append(match.start())

    parenthetical_matches = [
        match.start()
        for match in re.finditer(r"\(([^()]*)\)", clean)
        if _extract_inline_parenthetical_reference(match.group(0)) is not None
    ]
    starts.extend(parenthetical_matches)

    if not starts:
        return None

    return min(starts)


def _extract_inline_parenthetical_reference(line: str) -> str | None:
    for content in re.findall(r"\(([^()]*)\)", line):
        candidate = content.strip()
        if not candidate:
            continue
        if re.fullmatch(r"[<>≤≥]=?\s*\d+(?:[.,]\d+)?", candidate):
            return re.sub(r"\s+", " ", candidate).replace(",", ".").strip()
        if re.fullmatch(r"\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?", candidate):
            return re.sub(r"\s+", " ", candidate).replace(",", ".").strip()
    return None


def _looks_like_simple_reference_tail(text: str) -> bool:
    clean = _normalize_numeric_text(text).strip()
    if not clean:
        return True

    allowed_patterns = (
        r"[<>≤≥]=?\s*\d+(?:[.,]\d+)?",
        r"\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?",
        r"\(\s*[<>≤≥]=?\s*\d+(?:[.,]\d+)?\s*\)",
        r"\(\s*\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?\s*\)",
        r"\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?",
    )
    return any(re.fullmatch(pattern, clean) for pattern in allowed_patterns)


def _is_ignorable_value_to_unit_gap(text: str) -> bool:
    clean = _normalize_numeric_text(text).strip()
    if not clean:
        return True
    return re.fullmatch(r"(?:\+\+?|\-\-?)", clean) is not None


def _normalize_number_token(token: str) -> str | None:
    token = token.strip()
    if not token:
        return None

    token = _normalize_numeric_text(token)
    token = re.sub(r"(?<=\d)\s+(?=\d{3}\b)", "", token)
    token = re.sub(r"(?<=\d)\s+(?=\d[.,])", "", token)

    if " " in token:
        parts = [part for part in token.split() if part]
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            left, right = parts
            if len(right) == 3:
                token = left + right
            elif len(right) == 1 and len(left) <= 2:
                token = f"{left}.{right}"
            else:
                token = left
        else:
            token = parts[0]

    has_comma = "," in token
    has_dot = "." in token
    if has_comma and has_dot:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif has_comma:
        if token.count(",") == 1 and len(token.split(",")[-1]) in {1, 2}:
            token = token.replace(",", ".")
        else:
            token = token.replace(",", "")
    elif has_dot and token.count(".") > 1:
        parts = token.split(".")
        if len(parts[-1]) in {1, 2}:
            token = "".join(parts[:-1]) + "." + parts[-1]
        else:
            token = "".join(parts)

    token = re.sub(r"[^0-9.+-]", "", token)
    if not token or token in {"+", "-", ".", "+.", "-."}:
        return None
    return token
