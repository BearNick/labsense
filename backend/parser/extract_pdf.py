import re
from functools import lru_cache
from typing import Optional, Tuple, List

from parser.config import resolve_pdf_page_limit
from parser.marker_metadata import get_marker_metadata

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency in test env
    pdfplumber = None

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
    "10^9/л": "x10^9/L",
    "10^12/л": "x10^12/L",
    "x10^9/л": "x10^9/L",
    "x10^12/л": "x10^12/L",
}

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
    primary_candidates = _extract_primary_result_candidates(source_text)
    source_candidates = _parse_candidates(source_text)
    candidates = source_candidates or _parse_candidates(line)

    if not primary_candidates and not candidates:
        return None

    detected_unit = extract_unit(line)
    reference_range = extract_reference_range(line)
    raw = primary_candidates[0] if primary_candidates else candidates[0]

    if _is_percentage_metric(metric_name):
        percentage_primary = _select_percentage_primary_result(primary_candidates)
        if percentage_primary is not None:
            raw = percentage_primary

    if primary_candidates and candidates and _looks_like_layout_concatenated_value(
        parsed_value=candidates[0],
        primary_value=primary_candidates[0],
        metric_name=metric_name,
        detected_unit=detected_unit,
        reference_range=reference_range,
    ):
        raw = primary_candidates[0]

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
    normalized_line = _normalize_unit_text(line)
    unit_match = re.search(
        r"\b(?:g/l|г/л|g/dl|mg/l|мг/л|mg/dl|mg\s+alb/mmol|mg/mmol|mg/g|mmol/l|ммоль/л|mmol/mol|mol/l|umol/l|µmol/l|μmol/l|мкмоль/л|ng/ml|нг/мл|fl|pg|pg/ml|iu/ml|u/l|ед/л|ml/min/1\.73 ?m2|mm/h|мм/ч|k/[uµμ]l|m/[uµμ]l|%|x10\^?9/[lл]|x10\^?12/[lл]|10\^9/[lл]|10\^12/[lл])\b",
        normalized_line,
        flags=re.IGNORECASE,
    )
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
    return (
        normalized.replace("×", "x")
        .replace("х", "x")
        .replace("Х", "x")
        .replace("⁹", "^9")
        .replace("¹²", "^12")
        .replace("мкмоль/л", "umol/l")
        .replace("ммоль/л", "mmol/l")
        .replace("мг/л", "mg/l")
        .replace("нг/мл", "ng/ml")
        .replace("ед/л", "u/l")
        .replace("г/л", "g/l")
        .replace("мм/ч", "mm/h")
        .replace("/л", "/l")
    )


def _find_unit_start(text: str) -> int | None:
    normalized_text = _normalize_unit_text(text)
    unit_match = re.search(
        r"\b(?:g/l|г/л|g/dl|mg/l|мг/л|mg/dl|mg\s+alb/mmol|mg/mmol|mg/g|mmol/l|ммоль/л|mmol/mol|mol/l|umol/l|µmol/l|μmol/l|мкмоль/л|ng/ml|нг/мл|fl|pg|pg/ml|iu/ml|u/l|ед/л|ml/min/1\.73 ?m2|mm/h|мм/ч|k/[uµμ]l|m/[uµμ]l|%|x10\^?9/[lл]|x10\^?12/[lл]|10\^9/[lл]|10\^12/[lл])\b",
        normalized_text,
        flags=re.IGNORECASE,
    )
    if unit_match is None:
        return None
    return unit_match.start()


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
