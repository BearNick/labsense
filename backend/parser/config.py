from __future__ import annotations

import os


DEFAULT_MAX_PDF_PAGES = 20


def _read_int_env(key: str, default: int) -> int:
    raw_value = os.getenv(key)
    if raw_value is None or raw_value == "":
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default

    return max(1, value)


MAX_PDF_PAGES = _read_int_env("MAX_PDF_PAGES", DEFAULT_MAX_PDF_PAGES)


def resolve_pdf_page_limit(max_pages: int | None = None) -> int:
    if max_pages is None:
        return MAX_PDF_PAGES
    return max(1, int(max_pages))
