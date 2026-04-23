# Extraction Benchmark Report

## Benchmarked paths
- `text_inspection_snapshot`
- `direct_text_extract_pdf`
- `text_postprocess_pdfplumber_enriched`
- `source_selection_auto`
- `source_selection_forced_text`
- `source_selection_forced_vision`
- `direct_vision_extract`

## Synthetic PDFs created
- `synthetic_ru_clean`: `/opt/labsense/backend/tests/fixtures/generated/synthetic_ru_clean.pdf`
- `synthetic_en_clean`: `/opt/labsense/backend/tests/fixtures/generated/synthetic_en_clean.pdf`
- `synthetic_mixed_aliases`: `/opt/labsense/backend/tests/fixtures/generated/synthetic_mixed_aliases.pdf`
- `synthetic_decimal_comma`: `/opt/labsense/backend/tests/fixtures/generated/synthetic_decimal_comma.pdf`
- `synthetic_scientific_units`: `/opt/labsense/backend/tests/fixtures/generated/synthetic_scientific_units.pdf`

## Aggregate results
| Path | Exact fixtures | Exact match rate | Dropped markers | Malformed zeros | Warnings | Failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `text_inspection_snapshot` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `direct_text_extract_pdf` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `text_postprocess_pdfplumber_enriched` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `source_selection_auto` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `source_selection_forced_text` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `source_selection_forced_vision` | 7 | 100.00% | 0 | 0 | 0 | 0 |
| `direct_vision_extract` | 1 | 14.29% | 42 | 0 | 7 | 1 |

## Per-fixture results
### synthetic_ru_clean
- Kind: `synthetic`
- PDF: `/opt/labsense/backend/tests/fixtures/generated/synthetic_ru_clean.pdf`
- Notes: Clean Russian CBC + vitamin D + zinc.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### synthetic_en_clean
- Kind: `synthetic`
- PDF: `/opt/labsense/backend/tests/fixtures/generated/synthetic_en_clean.pdf`
- Notes: Clean English CBC with international aliases.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### synthetic_mixed_aliases
- Kind: `synthetic`
- PDF: `/opt/labsense/backend/tests/fixtures/generated/synthetic_mixed_aliases.pdf`
- Notes: Russian marker names mixed with Latin aliases.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### synthetic_decimal_comma
- Kind: `synthetic`
- PDF: `/opt/labsense/backend/tests/fixtures/generated/synthetic_decimal_comma.pdf`
- Notes: Decimal comma values without changing numeric meaning.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### synthetic_scientific_units
- Kind: `synthetic`
- PDF: `/opt/labsense/backend/tests/fixtures/generated/synthetic_scientific_units.pdf`
- Notes: Scientific-count units like 10^12/л and 10^9/л.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### real_123_pdf
- Kind: `real`
- PDF: `/opt/labsense/backend/tests/fixtures/123.pdf`
- Notes: Golden real-world fixture supplied in the repo.
- Expected key markers:
  - Гемоглобин: 148.1
  - Эритроциты: 4.98
  - Гематокрит: 41.6
  - Тромбоциты: 298.0
  - Лейкоциты: 4.19
  - Витамин D (25-OH): 29.0
  - Цинк: 8.5

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 7 | 148.1 | 4.98 | 41.6 | 298.0 | 4.19 | 29.0 | 8.5 | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | False | Direct vision extractor returned no usable markers. |

### uploaded_non_lab_pdf
- Kind: `non_lab_control`
- PDF: `/opt/labsense/backend/storage/uploads/cc5d183b651748118c59e89bb902668f.pdf`
- Notes: Available uploaded PDF, but not a text-rich lab report.
- Expected key markers:
  - Гемоглобин: None
  - Эритроциты: None
  - Гематокрит: None
  - Тромбоциты: None
  - Лейкоциты: None
  - Витамин D (25-OH): None
  - Цинк: None

| Path | Source | Selected | Marker count | Hb | RBC | HCT | PLT | WBC | Vit D | Zn | Exact | Warnings/Failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `text_inspection_snapshot` | `pdfplumber` | `vision` | 0 | None | None | None | None | None | None | None | True | - |
| `direct_text_extract_pdf` | `pdfplumber` | `text` | 0 | None | None | None | None | None | None | None | True | - |
| `text_postprocess_pdfplumber_enriched` | `pdfplumber` | `text` | 0 | None | None | None | None | None | None | None | True | - |
| `source_selection_auto` | `pdfplumber` | `text` | 0 | None | None | None | None | None | None | None | True | - |
| `source_selection_forced_text` | `pdfplumber` | `text` | 0 | None | None | None | None | None | None | None | True | - |
| `source_selection_forced_vision` | `pdfplumber` | `text` | 0 | None | None | None | None | None | None | None | True | - |
| `direct_vision_extract` | `vision` | `vision` | 0 | None | None | None | None | None | None | None | True | Direct vision extractor returned no usable markers.; vision_timeout:3s |

