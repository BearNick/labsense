from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MarkerKind = Literal["absolute", "percent", "concentration", "activity", "index"]


@dataclass(frozen=True)
class SemanticMarker:
    canonical_id: str
    display_name: str
    aliases: tuple[str, ...]
    kind: MarkerKind
    unit_family: tuple[str, ...]
    interpretation_slot: str
    merge_group: str
    must_not_merge_with: tuple[str, ...] = ()


SEMANTIC_MARKER_REGISTRY: dict[str, SemanticMarker] = {
    "hemoglobin": SemanticMarker(
        canonical_id="hemoglobin",
        display_name="Гемоглобин",
        aliases=("Гемоглобин", "Hemoglobin", "HGB", "Hb"),
        kind="concentration",
        unit_family=("g/L", "g/dL"),
        interpretation_slot="Гемоглобин",
        merge_group="hemoglobin",
    ),
    "hematocrit": SemanticMarker(
        canonical_id="hematocrit",
        display_name="Гематокрит",
        aliases=("Гематокрит", "Hematocrit", "HCT", "Ht"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Гематокрит",
        merge_group="hematocrit",
    ),
    "rbc": SemanticMarker(
        canonical_id="rbc",
        display_name="Эритроциты (RBC)",
        aliases=("Эритроциты", "RBC"),
        kind="concentration",
        unit_family=("x10^12/L",),
        interpretation_slot="Эритроциты",
        merge_group="rbc",
        must_not_merge_with=("nrbc",),
    ),
    "nrbc": SemanticMarker(
        canonical_id="nrbc",
        display_name="Нормобласты (NRBC)",
        aliases=("NRBC", "Нормобласты", "Нормобласты (NRBC)"),
        kind="percent",
        unit_family=("%", "x10^9/L"),
        interpretation_slot="NRBC",
        merge_group="nrbc",
        must_not_merge_with=("rbc",),
    ),
    "wbc": SemanticMarker(
        canonical_id="wbc",
        display_name="Лейкоциты (WBC)",
        aliases=("Лейкоциты", "WBC"),
        kind="concentration",
        unit_family=("x10^9/L",),
        interpretation_slot="Лейкоциты",
        merge_group="wbc",
    ),
    "platelets": SemanticMarker(
        canonical_id="platelets",
        display_name="Тромбоциты (PLT)",
        aliases=("Тромбоциты", "Platelets", "PLT"),
        kind="concentration",
        unit_family=("x10^9/L",),
        interpretation_slot="Тромбоциты",
        merge_group="platelets",
    ),
    "mcv": SemanticMarker(
        canonical_id="mcv",
        display_name="MCV",
        aliases=("MCV",),
        kind="index",
        unit_family=("fL",),
        interpretation_slot="MCV",
        merge_group="mcv",
    ),
    "mch": SemanticMarker(
        canonical_id="mch",
        display_name="MCH",
        aliases=("MCH",),
        kind="index",
        unit_family=("pg",),
        interpretation_slot="MCH",
        merge_group="mch",
    ),
    "mchc": SemanticMarker(
        canonical_id="mchc",
        display_name="MCHC",
        aliases=("MCHC",),
        kind="index",
        unit_family=("g/L", "g/dL"),
        interpretation_slot="MCHC",
        merge_group="mchc",
    ),
    "rdw": SemanticMarker(
        canonical_id="rdw",
        display_name="RDW",
        aliases=("RDW",),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="RDW",
        merge_group="rdw",
    ),
    "esr": SemanticMarker(
        canonical_id="esr",
        display_name="СОЭ (ESR)",
        aliases=("СОЭ", "ESR"),
        kind="activity",
        unit_family=("mm/h",),
        interpretation_slot="СОЭ",
        merge_group="esr",
    ),
    "lym_percent": SemanticMarker(
        canonical_id="lym_percent",
        display_name="Лимфоциты %",
        aliases=("Лимфоциты %", "Lymphocytes %", "LYM %", "LYM"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Лимфоциты %",
        merge_group="lym_percent",
        must_not_merge_with=("lym_absolute", "re_lymp_absolute", "re_lymp_percent", "as_lymp_absolute", "as_lymp_percent"),
    ),
    "lym_absolute": SemanticMarker(
        canonical_id="lym_absolute",
        display_name="Лимфоциты абс.",
        aliases=("Лимфоциты абс.", "Lymphocytes abs.", "LYM abs", "LYM ABS"),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="Лимфоциты абс.",
        merge_group="lym_absolute",
        must_not_merge_with=("lym_percent", "re_lymp_absolute", "as_lymp_absolute"),
    ),
    "neu_percent": SemanticMarker(
        canonical_id="neu_percent",
        display_name="Нейтрофилы %",
        aliases=("Нейтрофилы %", "Neutrophils %", "NEU %", "NEU"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Нейтрофилы %",
        merge_group="neu_percent",
    ),
    "neu_absolute": SemanticMarker(
        canonical_id="neu_absolute",
        display_name="Нейтрофилы абс.",
        aliases=("Нейтрофилы абс.", "Neutrophils abs.", "ANC", "NEU abs", "NEU ABS"),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="Нейтрофилы абс.",
        merge_group="neu_absolute",
    ),
    "mono_percent": SemanticMarker(
        canonical_id="mono_percent",
        display_name="Моноциты %",
        aliases=("Моноциты %", "Monocytes %", "MON %", "MON"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Моноциты %",
        merge_group="mono_percent",
    ),
    "mono_absolute": SemanticMarker(
        canonical_id="mono_absolute",
        display_name="Моноциты абс.",
        aliases=("Моноциты абс.", "Monocytes abs.", "MON abs", "MON ABS"),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="Моноциты абс.",
        merge_group="mono_absolute",
    ),
    "eos_percent": SemanticMarker(
        canonical_id="eos_percent",
        display_name="Эозинофилы %",
        aliases=("Эозинофилы %", "Eosinophils %", "EOS %", "EOS"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Эозинофилы %",
        merge_group="eos_percent",
    ),
    "eos_absolute": SemanticMarker(
        canonical_id="eos_absolute",
        display_name="Эозинофилы абс.",
        aliases=("Эозинофилы абс.", "Eosinophils abs.", "EOS abs", "EOS ABS"),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="Эозинофилы абс.",
        merge_group="eos_absolute",
    ),
    "baso_percent": SemanticMarker(
        canonical_id="baso_percent",
        display_name="Базофилы %",
        aliases=("Базофилы %", "Basophils %", "BASO %", "BASO"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="Базофилы %",
        merge_group="baso_percent",
    ),
    "baso_absolute": SemanticMarker(
        canonical_id="baso_absolute",
        display_name="Базофилы абс.",
        aliases=("Базофилы абс.", "Basophils abs.", "BASO abs", "BASO ABS"),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="Базофилы абс.",
        merge_group="baso_absolute",
    ),
    "re_lymp_absolute": SemanticMarker(
        canonical_id="re_lymp_absolute",
        display_name="RE-LYMP abs",
        aliases=("RE-LYMP abs", "RE-LYMP ABS", "RE-LYMP абс.", "RE-LYMP АБС."),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="RE-LYMP abs",
        merge_group="re_lymp_absolute",
        must_not_merge_with=("lym_percent", "lym_absolute", "as_lymp_absolute", "as_lymp_percent"),
    ),
    "re_lymp_percent": SemanticMarker(
        canonical_id="re_lymp_percent",
        display_name="RE-LYMP %",
        aliases=("RE-LYMP %", "RE-LYMP %%"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="RE-LYMP %",
        merge_group="re_lymp_percent",
        must_not_merge_with=("lym_percent", "re_lymp_absolute"),
    ),
    "as_lymp_absolute": SemanticMarker(
        canonical_id="as_lymp_absolute",
        display_name="AS-LYMP abs",
        aliases=("AS-LYMP abs", "AS-LYMP ABS", "AS-LYMP абс.", "AS-LYMP АБС."),
        kind="absolute",
        unit_family=("x10^9/L",),
        interpretation_slot="AS-LYMP abs",
        merge_group="as_lymp_absolute",
        must_not_merge_with=("lym_percent", "lym_absolute", "re_lymp_absolute", "re_lymp_percent"),
    ),
    "as_lymp_percent": SemanticMarker(
        canonical_id="as_lymp_percent",
        display_name="AS-LYMP %",
        aliases=("AS-LYMP %",),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="AS-LYMP %",
        merge_group="as_lymp_percent",
        must_not_merge_with=("lym_percent", "as_lymp_absolute"),
    ),
    "vitamin_d": SemanticMarker(
        canonical_id="vitamin_d",
        display_name="Витамин D (25-OH)",
        aliases=("Витамин D (25-OH)", "Vitamin D (25-OH)"),
        kind="concentration",
        unit_family=("ng/mL",),
        interpretation_slot="Витамин D (25-OH)",
        merge_group="vitamin_d",
    ),
    "zinc": SemanticMarker(
        canonical_id="zinc",
        display_name="Цинк",
        aliases=("Цинк", "Zinc"),
        kind="concentration",
        unit_family=("µmol/L", "umol/L"),
        interpretation_slot="Цинк",
        merge_group="zinc",
    ),
    "glucose": SemanticMarker(
        canonical_id="glucose",
        display_name="Глюкоза",
        aliases=("Глюкоза", "Glucose"),
        kind="concentration",
        unit_family=("mmol/L", "mg/dL"),
        interpretation_slot="Глюкоза",
        merge_group="glucose",
    ),
    "sodium": SemanticMarker(
        canonical_id="sodium",
        display_name="Натрий",
        aliases=("Натрий", "Sodium", "Na"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="Натрий",
        merge_group="sodium",
    ),
    "potassium": SemanticMarker(
        canonical_id="potassium",
        display_name="Калий",
        aliases=("Калий", "Potassium", "K"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="Калий",
        merge_group="potassium",
    ),
    "chloride": SemanticMarker(
        canonical_id="chloride",
        display_name="Хлор",
        aliases=("Хлор", "Chloride", "Cl"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="Хлор",
        merge_group="chloride",
    ),
    "urea": SemanticMarker(
        canonical_id="urea",
        display_name="Мочевина",
        aliases=("Мочевина", "Urea"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="Мочевина",
        merge_group="urea",
        must_not_merge_with=("bun",),
    ),
    "bun": SemanticMarker(
        canonical_id="bun",
        display_name="BUN",
        aliases=("BUN", "Blood urea nitrogen"),
        kind="concentration",
        unit_family=("mg/dL",),
        interpretation_slot="BUN",
        merge_group="bun",
        must_not_merge_with=("urea",),
    ),
    "creatinine": SemanticMarker(
        canonical_id="creatinine",
        display_name="Креатинин",
        aliases=("Креатинин", "Creatinine", "Cr"),
        kind="concentration",
        unit_family=("umol/L", "µmol/L"),
        interpretation_slot="Креатинин",
        merge_group="creatinine",
    ),
    "egfr": SemanticMarker(
        canonical_id="egfr",
        display_name="eGFR",
        aliases=("eGFR", "EGFR", "Estimated glomerular filtration rate"),
        kind="index",
        unit_family=("mL/min/1.73m2",),
        interpretation_slot="eGFR",
        merge_group="egfr",
    ),
    "crp": SemanticMarker(
        canonical_id="crp",
        display_name="CRP",
        aliases=("CRP", "С-реактивный белок"),
        kind="concentration",
        unit_family=("mg/L",),
        interpretation_slot="CRP",
        merge_group="crp",
    ),
    "alt": SemanticMarker(
        canonical_id="alt",
        display_name="ALT",
        aliases=("ALT", "АЛТ"),
        kind="activity",
        unit_family=("U/L",),
        interpretation_slot="ALT",
        merge_group="alt",
    ),
    "ast": SemanticMarker(
        canonical_id="ast",
        display_name="AST",
        aliases=("AST", "АСТ"),
        kind="activity",
        unit_family=("U/L",),
        interpretation_slot="AST",
        merge_group="ast",
    ),
    "uric_acid": SemanticMarker(
        canonical_id="uric_acid",
        display_name="Кислота мочевая",
        aliases=("Кислота мочевая", "Uric acid", "Uric Acid"),
        kind="concentration",
        unit_family=("umol/L", "µmol/L", "mg/dL"),
        interpretation_slot="Кислота мочевая",
        merge_group="uric_acid",
    ),
    "hba1c": SemanticMarker(
        canonical_id="hba1c",
        display_name="HbA1c",
        aliases=("HbA1c", "A1c", "Glycated hemoglobin"),
        kind="percent",
        unit_family=("%",),
        interpretation_slot="HbA1c",
        merge_group="hba1c",
    ),
    "urine_albumin": SemanticMarker(
        canonical_id="urine_albumin",
        display_name="Urine Albumin",
        aliases=("Urine Albumin", "Urinary Albumin", "Urine microalbumin", "Microalbumin, urine"),
        kind="concentration",
        unit_family=("mg/L", "mg/dL"),
        interpretation_slot="Urine Albumin",
        merge_group="urine_albumin",
    ),
    "urine_creatinine": SemanticMarker(
        canonical_id="urine_creatinine",
        display_name="Urine Creatinine",
        aliases=("Urine Creatinine", "Urinary Creatinine", "U-Creatinine"),
        kind="concentration",
        unit_family=("mmol/L", "mg/dL", "g/L"),
        interpretation_slot="Urine Creatinine",
        merge_group="urine_creatinine",
        must_not_merge_with=("creatinine",),
    ),
    "acr": SemanticMarker(
        canonical_id="acr",
        display_name="ACR",
        aliases=("ACR", "Albumin/Creatinine Ratio", "Albumin creatinine ratio"),
        kind="index",
        unit_family=("mg/mmol", "mg/g"),
        interpretation_slot="ACR",
        merge_group="acr",
    ),
    "ldl": SemanticMarker(
        canonical_id="ldl",
        display_name="ЛПНП (LDL)",
        aliases=("ЛПНП", "LDL"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="ЛПНП",
        merge_group="ldl",
    ),
    "hdl": SemanticMarker(
        canonical_id="hdl",
        display_name="ЛПВП (HDL)",
        aliases=("ЛПВП", "HDL"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="ЛПВП",
        merge_group="hdl",
    ),
    "total_cholesterol": SemanticMarker(
        canonical_id="total_cholesterol",
        display_name="Холестерин общий",
        aliases=("Холестерин общий", "Total cholesterol"),
        kind="concentration",
        unit_family=("mmol/L",),
        interpretation_slot="Холестерин общий",
        merge_group="total_cholesterol",
    ),
}


def normalize_marker_token(value: str) -> str:
    return " ".join(
        value.replace("\xa0", " ")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .strip()
        .lower()
        .split()
    )


def _build_alias_index() -> dict[str, str]:
    alias_index: dict[str, str] = {}
    for canonical_id, marker in SEMANTIC_MARKER_REGISTRY.items():
        candidates = {
            marker.canonical_id,
            marker.display_name,
            marker.interpretation_slot,
            *marker.aliases,
        }
        for alias in candidates:
            normalized_alias = normalize_marker_token(alias)
            existing = alias_index.get(normalized_alias)
            if existing is not None and existing != canonical_id:
                raise RuntimeError(f"Duplicate semantic marker alias: {alias!r}")
            alias_index[normalized_alias] = canonical_id
    return alias_index


SEMANTIC_ALIAS_INDEX = _build_alias_index()
