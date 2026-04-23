from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import fitz

ROOT = Path("/opt/labsense")
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from parser.extract_pdf import extract_lab_data_from_pdf
from parser.postprocess import MarkerDetail, extract_text_with_details
from parser.source_selection import (
    ParserSelectionResult,
    _assess_text_extraction,
    _assess_vision_extraction,
    _build_selection_reason,
    _decide_source,
    _inspect_pdf_text,
    normalize_raw_values,
    select_and_extract_lab_data,
)
from parser.vision_extract import extract_lab_data_via_vision


KEY_MARKERS = [
    "Гемоглобин",
    "Эритроциты",
    "Гематокрит",
    "Тромбоциты",
    "Лейкоциты",
    "Витамин D (25-OH)",
    "Цинк",
]

FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FIXTURE_DIR = BACKEND_ROOT / "tests" / "fixtures"
GENERATED_DIR = FIXTURE_DIR / "generated"
ARTIFACT_DIR = BACKEND_ROOT / "tests" / "artifacts"
JSON_REPORT = ARTIFACT_DIR / "extraction_benchmark_report.json"
MARKDOWN_REPORT = ARTIFACT_DIR / "extraction_benchmark_report.md"
BENCH_PYTHON = os.environ.get("LABSENSE_BENCH_PYTHON", sys.executable)
VISION_TIMEOUT_SECONDS = int(os.environ.get("LABSENSE_BENCH_VISION_TIMEOUT_SECONDS", "20"))
_VISION_CACHE: dict[str, tuple[dict[str, float | None], list[str]]] = {}


@dataclass(frozen=True)
class Fixture:
    name: str
    pdf_path: Path
    expected: dict[str, float | None]
    kind: str
    notes: str = ""


def _round_number(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _marker_snapshot(values: dict[str, float | None]) -> dict[str, float | None]:
    return {marker: _round_number(values.get(marker)) for marker in KEY_MARKERS}


def _marker_count(values: dict[str, float | None]) -> int:
    return sum(1 for value in values.values() if value is not None)


def _compare(expected: dict[str, float | None], observed: dict[str, float | None]) -> dict[str, Any]:
    exact_matches = 0
    dropped_markers: list[str] = []
    malformed_zero_markers: list[str] = []
    mismatches: dict[str, dict[str, float | None]] = {}

    for marker, expected_value in expected.items():
        observed_value = observed.get(marker)
        normalized_expected = _round_number(expected_value)
        normalized_observed = _round_number(observed_value)
        if normalized_expected == normalized_observed:
            exact_matches += 1
            continue
        if observed_value is None:
            dropped_markers.append(marker)
        if normalized_expected not in (None, 0.0) and normalized_observed == 0.0:
            malformed_zero_markers.append(marker)
        mismatches[marker] = {
            "expected": normalized_expected,
            "observed": normalized_observed,
        }

    return {
        "exact_matches": exact_matches,
        "expected_marker_total": len(expected),
        "all_exact": exact_matches == len(expected),
        "dropped_markers": dropped_markers,
        "malformed_zero_markers": malformed_zero_markers,
        "mismatches": mismatches,
    }


def _detail_to_dict(detail: MarkerDetail) -> dict[str, Any]:
    payload = asdict(detail)
    payload["value"] = _round_number(detail.value)
    payload["confidence"] = round(float(detail.confidence), 4)
    return payload


def _selection_result_to_dict(result: ParserSelectionResult) -> dict[str, Any]:
    return {
        "raw_values": {key: _round_number(value) for key, value in result.raw_values.items()},
        "source": result.source,
        "selected_source": result.selected_source,
        "selection_reason": result.selection_reason,
        "initial_source": result.initial_source,
        "final_source": result.final_source,
        "fallback_used": result.fallback_used,
        "fallback_reason": result.fallback_reason,
        "confidence_score": result.confidence_score,
        "confidence_level": result.confidence_level,
        "confidence_reasons": result.confidence_reasons,
        "confidence_explanation": result.confidence_explanation,
        "reference_coverage": round(float(result.reference_coverage), 4),
        "unit_coverage": round(float(result.unit_coverage), 4),
        "structural_consistency": round(float(result.structural_consistency), 4),
        "warnings": list(result.warnings),
        "marker_details": {name: _detail_to_dict(detail) for name, detail in result.marker_details.items()},
    }


def _run_vision_subprocess(pdf_path: Path) -> tuple[dict[str, float | None], list[str]]:
    cache_key = str(pdf_path)
    cached = _VISION_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached[0]), list(cached[1])

    command = [
        BENCH_PYTHON,
        "-c",
        (
            "import json, sys; "
            "sys.path.insert(0, '/opt/labsense/backend'); "
            "from parser.vision_extract import extract_lab_data_via_vision; "
            "result = extract_lab_data_via_vision(sys.argv[1], max_pages=5, lang='ru'); "
            "print(json.dumps(result, ensure_ascii=False))"
        ),
        str(pdf_path),
    ]
    failures: list[str] = []
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=VISION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        failures.append(f"vision_timeout:{VISION_TIMEOUT_SECONDS}s")
        _VISION_CACHE[cache_key] = ({}, list(failures))
        return {}, failures

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or f"exit_code={completed.returncode}"
        failures.append(f"vision_subprocess_error:{stderr}")
        _VISION_CACHE[cache_key] = ({}, list(failures))
        return {}, failures

    stdout = completed.stdout.strip()
    if not stdout:
        _VISION_CACHE[cache_key] = ({}, list(failures))
        return {}, failures

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        failures.append(f"vision_json_decode_error:{exc}")
        _VISION_CACHE[cache_key] = ({}, list(failures))
        return {}, failures

    if not isinstance(payload, dict):
        failures.append("vision_payload_not_dict")
        _VISION_CACHE[cache_key] = ({}, list(failures))
        return {}, failures

    values = normalize_raw_values(payload)
    _VISION_CACHE[cache_key] = (dict(values), list(failures))
    return values, failures


def _write_pdf(lines: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_font(fontname="dejavu", fontfile=str(FONT_PATH))
    y = 60
    for line in lines:
        page.insert_text((50, y), line, fontname="dejavu", fontsize=12)
        y += 20
    document.save(output_path)
    document.close()


def generate_synthetic_fixtures() -> list[Fixture]:
    fixtures: list[Fixture] = []

    synthetic_specs = [
        {
            "name": "synthetic_ru_clean",
            "notes": "Clean Russian CBC + vitamin D + zinc.",
            "lines": [
                "Общий анализ крови",
                "Гемоглобин 148,10 г/л 130 - 170",
                "Эритроциты 4,98 10^12/л 4,30 - 5,70",
                "Гематокрит 41,60 % 39,0 - 49,0",
                "Тромбоциты 298 10^9/л 150 - 400",
                "Лейкоциты 4,19 10^9/л 4,00 - 9,00",
                "Витамин D (25-OH) 29 нг/мл 30 - 100",
                "Цинк 8,5 мкмоль/л 8,4 - 23,0",
            ],
            "expected": {
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
        },
        {
            "name": "synthetic_en_clean",
            "notes": "Clean English CBC with international aliases.",
            "lines": [
                "Complete Blood Count",
                "Hemoglobin 148.10 g/L 130 - 170",
                "RBC 4.98 x10^12/L 4.30 - 5.70",
                "Hematocrit 41.60 % 39.0 - 49.0",
                "Platelets 298 x10^9/L 150 - 400",
                "WBC 4.19 x10^9/L 4.00 - 9.00",
                "Vitamin D 25-OH 29 ng/mL 30 - 100",
                "Zinc 8.5 umol/L 8.4 - 23.0",
            ],
            "expected": {
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
        },
        {
            "name": "synthetic_mixed_aliases",
            "notes": "Russian marker names mixed with Latin aliases.",
            "lines": [
                "CBC mixed aliases",
                "Гемоглобин (Hb) 148,10 г/л 130 - 170",
                "Эритроциты (RBC) 4,98 10^12/л 4,30 - 5,70",
                "Гематокрит (HCT) 41,60 % 39,0 - 49,0",
                "Тромбоциты (PLT) 298 10^9/л 150 - 400",
                "Лейкоциты (WBC) 4,19 10^9/л 4,00 - 9,00",
                "Витамин D 25-OH 29 нг/мл 30 - 100",
                "Цинк / Zinc 8,5 мкмоль/л 8,4 - 23,0",
            ],
            "expected": {
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
        },
        {
            "name": "synthetic_decimal_comma",
            "notes": "Decimal comma values without changing numeric meaning.",
            "lines": [
                "Decimal comma stress test",
                "Гемоглобин 148,10 г/л 130 - 170",
                "Эритроциты 4,98 10^12/л 4,30 - 5,70",
                "Гематокрит 41,60 % 39,0 - 49,0",
                "Тромбоциты 298 10^9/л 150 - 400",
                "Лейкоциты 4,19 10^9/л 4,00 - 9,00",
                "Витамин D (25-OH) 29,0 нг/мл 30,0 - 100,0",
                "Цинк 8,50 мкмоль/л 8,40 - 23,00",
            ],
            "expected": {
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
        },
        {
            "name": "synthetic_scientific_units",
            "notes": "Scientific-count units like 10^12/л and 10^9/л.",
            "lines": [
                "Scientific units stress test",
                "Гемоглобин 148,10 г/л 130 - 170",
                "Эритроциты 4,98 10^12/л 4,30 - 5,70",
                "Гематокрит 41,60 % 39,0 - 49,0",
                "Тромбоциты 298 10^9/л 150 - 400",
                "Лейкоциты 4,19 10^9/л 4,00 - 9,00",
                "RBC 4,98 10^12/л 4,30 - 5,70",
                "PLT 298 10^9/л 150 - 400",
                "WBC 4,19 10^9/л 4,00 - 9,00",
                "Витамин D (25-OH) 29 нг/мл 30 - 100",
                "Цинк 8,5 мкмоль/л 8,4 - 23,0",
            ],
            "expected": {
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
        },
    ]

    for spec in synthetic_specs:
        pdf_path = GENERATED_DIR / f"{spec['name']}.pdf"
        _write_pdf(spec["lines"], pdf_path)
        fixtures.append(
            Fixture(
                name=spec["name"],
                pdf_path=pdf_path,
                expected=spec["expected"],
                kind="synthetic",
                notes=spec["notes"],
            )
        )

    return fixtures


def build_real_fixtures() -> list[Fixture]:
    fixtures = [
        Fixture(
            name="real_123_pdf",
            pdf_path=FIXTURE_DIR / "123.pdf",
            expected={
                "Гемоглобин": 148.10,
                "Эритроциты": 4.98,
                "Гематокрит": 41.60,
                "Тромбоциты": 298.0,
                "Лейкоциты": 4.19,
                "Витамин D (25-OH)": 29.0,
                "Цинк": 8.5,
            },
            kind="real",
            notes="Golden real-world fixture supplied in the repo.",
        )
    ]

    uploaded_candidate = BACKEND_ROOT / "storage" / "uploads" / "cc5d183b651748118c59e89bb902668f.pdf"
    if uploaded_candidate.exists():
        fixtures.append(
            Fixture(
                name="uploaded_non_lab_pdf",
                pdf_path=uploaded_candidate,
                expected={marker: None for marker in KEY_MARKERS},
                kind="non_lab_control",
                notes="Available uploaded PDF, but not a text-rich lab report.",
            )
        )

    return fixtures


def run_direct_text_path(pdf_path: Path) -> dict[str, Any]:
    raw_values = normalize_raw_values(extract_lab_data_from_pdf(str(pdf_path), max_pages=5))
    return {
        "path": "direct_text_extract_pdf",
        "raw_values": {key: _round_number(value) for key, value in raw_values.items()},
        "selected_source": "text",
        "source": "pdfplumber",
        "marker_count": _marker_count(raw_values),
        "key_markers": _marker_snapshot(raw_values),
        "warnings": [],
        "failures": [],
    }


def run_text_postprocess_path(pdf_path: Path) -> dict[str, Any]:
    result = extract_text_with_details(str(pdf_path), max_pages=5)
    raw_values = normalize_raw_values(result.raw_values)
    return {
        "path": "text_postprocess_pdfplumber_enriched",
        "raw_values": {key: _round_number(value) for key, value in raw_values.items()},
        "selected_source": "text",
        "source": "pdfplumber",
        "marker_count": _marker_count(raw_values),
        "key_markers": _marker_snapshot(raw_values),
        "warnings": [],
        "failures": [],
        "table_count": result.table_count,
        "table_row_count": result.table_row_count,
        "marker_details": {name: _detail_to_dict(detail) for name, detail in result.marker_details.items()},
    }


def run_selector_auto_path(pdf_path: Path) -> dict[str, Any]:
    vision_failures: list[str] = []

    def benchmark_vision_wrapper(path: str, max_pages: int | None = None, lang: str = "ru") -> dict[str, float | None]:
        values, failures = _run_vision_subprocess(Path(path))
        vision_failures.extend(failures)
        return values

    with patch("parser.source_selection.extract_lab_data_via_vision", side_effect=benchmark_vision_wrapper):
        result = select_and_extract_lab_data(str(pdf_path), language="ru", max_pages=5)
    return {
        "path": "source_selection_auto",
        **_selection_result_to_dict(result),
        "marker_count": _marker_count(result.raw_values),
        "key_markers": _marker_snapshot(result.raw_values),
        "failures": vision_failures,
    }


def _run_forced_selector_path(pdf_path: Path, forced_source: str, reason: str) -> dict[str, Any]:
    vision_failures: list[str] = []

    def benchmark_vision_wrapper(path: str, max_pages: int | None = None, lang: str = "ru") -> dict[str, float | None]:
        values, failures = _run_vision_subprocess(Path(path))
        vision_failures.extend(failures)
        return values

    with (
        patch("parser.source_selection._decide_source", return_value=(forced_source, reason)),
        patch("parser.source_selection.extract_lab_data_via_vision", side_effect=benchmark_vision_wrapper),
    ):
        result = select_and_extract_lab_data(str(pdf_path), language="ru", max_pages=5)
    return {
        "path": f"source_selection_forced_{forced_source}",
        **_selection_result_to_dict(result),
        "marker_count": _marker_count(result.raw_values),
        "key_markers": _marker_snapshot(result.raw_values),
        "failures": vision_failures,
    }


def run_direct_vision_path(pdf_path: Path) -> dict[str, Any]:
    warnings: list[str] = []
    raw_values, failures = _run_vision_subprocess(pdf_path)

    if not raw_values:
        warnings.append("Direct vision extractor returned no usable markers.")

    assessment = _assess_vision_extraction(raw_values)
    return {
        "path": "direct_vision_extract",
        "raw_values": {key: _round_number(value) for key, value in raw_values.items()},
        "selected_source": "vision",
        "source": "vision",
        "marker_count": _marker_count(raw_values),
        "key_markers": _marker_snapshot(raw_values),
        "warnings": warnings,
        "failures": failures,
        "weak": assessment.weak,
        "weak_reason": assessment.weak_reason,
        "populated_ratio": round(float(assessment.populated_ratio), 4),
    }


def run_text_inspection_path(pdf_path: Path) -> dict[str, Any]:
    inspection = _inspect_pdf_text(str(pdf_path), max_pages=5)
    preferred_source, preferred_reason = _decide_source(
        inspection,
        vision_available=True,
    )
    assessment = _assess_text_extraction(inspection.text_markers, inspection)
    return {
        "path": "text_inspection_snapshot",
        "raw_values": {key: _round_number(value) for key, value in inspection.text_markers.items()},
        "selected_source": preferred_source,
        "source": "pdfplumber",
        "selection_reason": _build_selection_reason(preferred_reason, inspection),
        "marker_count": _marker_count(inspection.text_markers),
        "key_markers": _marker_snapshot(inspection.text_markers),
        "warnings": [],
        "failures": [],
        "char_count": inspection.char_count,
        "word_count": inspection.word_count,
        "meaningful_lines": inspection.meaningful_lines,
        "numeric_count": inspection.numeric_count,
        "reference_count": inspection.reference_count,
        "garbage_ratio": round(float(inspection.garbage_ratio), 4),
        "text_pages": inspection.text_pages,
        "image_pages": inspection.image_pages,
        "total_pages": inspection.total_pages,
        "table_count": inspection.table_count,
        "table_row_count": inspection.table_row_count,
        "weak": assessment.weak,
        "weak_reason": assessment.weak_reason,
    }


def benchmark_fixture(fixture: Fixture) -> dict[str, Any]:
    path_runs = [
        run_text_inspection_path(fixture.pdf_path),
        run_direct_text_path(fixture.pdf_path),
        run_text_postprocess_path(fixture.pdf_path),
        run_selector_auto_path(fixture.pdf_path),
        _run_forced_selector_path(fixture.pdf_path, "text", "benchmark_forced_text"),
        _run_forced_selector_path(fixture.pdf_path, "vision", "benchmark_forced_vision"),
        run_direct_vision_path(fixture.pdf_path),
    ]

    for run in path_runs:
        run["comparison"] = _compare(fixture.expected, run.get("raw_values", {}))

    return {
        "fixture": {
            "name": fixture.name,
            "pdf_path": str(fixture.pdf_path),
            "kind": fixture.kind,
            "notes": fixture.notes,
            "expected": {key: _round_number(value) for key, value in fixture.expected.items()},
        },
        "path_runs": path_runs,
    }


def summarize_results(benchmarks: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate: dict[str, dict[str, Any]] = {}
    for benchmark in benchmarks:
        fixture_name = benchmark["fixture"]["name"]
        for run in benchmark["path_runs"]:
            path_name = run["path"]
            bucket = aggregate.setdefault(
                path_name,
                {
                    "fixtures": [],
                    "exact_fixture_count": 0,
                    "total_exact_matches": 0,
                    "total_expected_markers": 0,
                    "total_dropped_markers": 0,
                    "total_malformed_zero_markers": 0,
                    "warnings": 0,
                    "failures": 0,
                },
            )
            comparison = run["comparison"]
            bucket["fixtures"].append(
                {
                    "fixture": fixture_name,
                    "all_exact": comparison["all_exact"],
                    "exact_matches": comparison["exact_matches"],
                    "expected_marker_total": comparison["expected_marker_total"],
                    "dropped_markers": comparison["dropped_markers"],
                    "malformed_zero_markers": comparison["malformed_zero_markers"],
                }
            )
            bucket["exact_fixture_count"] += int(bool(comparison["all_exact"]))
            bucket["total_exact_matches"] += comparison["exact_matches"]
            bucket["total_expected_markers"] += comparison["expected_marker_total"]
            bucket["total_dropped_markers"] += len(comparison["dropped_markers"])
            bucket["total_malformed_zero_markers"] += len(comparison["malformed_zero_markers"])
            bucket["warnings"] += len(run.get("warnings", []))
            bucket["failures"] += len(run.get("failures", []))

    for payload in aggregate.values():
        total = max(payload["total_expected_markers"], 1)
        payload["exact_match_rate"] = round(payload["total_exact_matches"] / total, 4)

    return aggregate


def render_markdown_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Extraction Benchmark Report")
    lines.append("")
    lines.append("## Benchmarked paths")
    for path_name in report["aggregate"]:
        lines.append(f"- `{path_name}`")
    lines.append("")
    lines.append("## Synthetic PDFs created")
    for fixture in report["fixtures"]:
        if fixture["kind"] == "synthetic":
            lines.append(f"- `{fixture['name']}`: `{fixture['pdf_path']}`")
    lines.append("")
    lines.append("## Aggregate results")
    lines.append("| Path | Exact fixtures | Exact match rate | Dropped markers | Malformed zeros | Warnings | Failures |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for path_name, payload in report["aggregate"].items():
        lines.append(
            f"| `{path_name}` | {payload['exact_fixture_count']} | {payload['exact_match_rate']:.2%} | "
            f"{payload['total_dropped_markers']} | {payload['total_malformed_zero_markers']} | "
            f"{payload['warnings']} | {payload['failures']} |"
        )
    lines.append("")
    lines.append("## Per-fixture results")
    for benchmark in report["benchmarks"]:
        fixture = benchmark["fixture"]
        lines.append(f"### {fixture['name']}")
        lines.append(f"- Kind: `{fixture['kind']}`")
        lines.append(f"- PDF: `{fixture['pdf_path']}`")
        lines.append(f"- Notes: {fixture['notes']}")
        lines.append("- Expected key markers:")
        for marker in KEY_MARKERS:
            lines.append(f"  - {marker}: {fixture['expected'].get(marker)}")
        lines.append("")
        lines.append("| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |")
        lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
        for run in benchmark["path_runs"]:
            key_markers = run["key_markers"]
            comparison = run["comparison"]
            issues = "; ".join(run.get("warnings", []) + run.get("failures", [])) or "-"
            lines.append(
                f"| `{run['path']}` | `{run.get('source', '-')}` | `{run.get('selected_source', '-')}` | "
                f"{run['marker_count']} | {key_markers['Гемоглобин']} | {key_markers['Эритроциты']} | "
                f"{key_markers['Гематокрит']} | {key_markers['Тромбоциты']} | {key_markers['Лейкоциты']} | "
                f"{key_markers['Витамин D (25-OH)']} | {key_markers['Цинк']} | {comparison['all_exact']} | {issues} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = generate_synthetic_fixtures() + build_real_fixtures()
    benchmarks = [benchmark_fixture(fixture) for fixture in fixtures]
    aggregate = summarize_results(benchmarks)

    report = {
        "fixtures": [benchmark["fixture"] for benchmark in benchmarks],
        "benchmarks": benchmarks,
        "aggregate": aggregate,
        "environment": {
            "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
            "font_path": str(FONT_PATH),
        },
    }

    JSON_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MARKDOWN_REPORT.write_text(render_markdown_report(report), encoding="utf-8")
    print(json.dumps({"json_report": str(JSON_REPORT), "markdown_report": str(MARKDOWN_REPORT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
