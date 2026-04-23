from __future__ import annotations

import math
from typing import Any

from app.services.semantic_markers import (
    SEMANTIC_ALIAS_INDEX,
    SEMANTIC_MARKER_REGISTRY,
    SemanticMarker,
    normalize_marker_token,
)


def normalize_interpretation_markers(marker_values: dict[str, object]) -> dict[str, float | None]:
    semantic_values: dict[str, float | None] = {}
    passthrough_values: dict[str, float | None] = {}

    for raw_name, raw_value in marker_values.items():
        name = str(raw_name).strip()
        if not name:
            continue

        numeric_value = _coerce_numeric_value(raw_value)
        marker = resolve_semantic_marker(name)
        if marker is None:
            if name in passthrough_values and passthrough_values[name] is not None:
                continue
            passthrough_values[name] = numeric_value
            continue

        existing_value = semantic_values.get(marker.canonical_id)
        if existing_value is not None:
            continue
        semantic_values[marker.canonical_id] = numeric_value

    payload = {
        marker.interpretation_slot: semantic_values.get(canonical_id)
        for canonical_id, marker in SEMANTIC_MARKER_REGISTRY.items()
        if canonical_id in semantic_values
    }
    for raw_name, numeric_value in passthrough_values.items():
        if raw_name in payload and payload[raw_name] is not None:
            continue
        payload[raw_name] = numeric_value

    return dict(sorted(payload.items(), key=lambda item: item[0].lower()))


def resolve_semantic_marker(raw_name: str) -> SemanticMarker | None:
    canonical_id = SEMANTIC_ALIAS_INDEX.get(normalize_marker_token(raw_name))
    if canonical_id is None:
        return None
    return SEMANTIC_MARKER_REGISTRY[canonical_id]


def _coerce_numeric_value(raw_value: Any) -> float | None:
    if raw_value is None or isinstance(raw_value, bool):
        return None

    if isinstance(raw_value, (int, float)):
        numeric = float(raw_value)
        return numeric if math.isfinite(numeric) else None

    text = str(raw_value).strip()
    if not text:
        return None

    normalized = (
        text.replace("\xa0", " ")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace(",", ".")
    )

    try:
        numeric = float(normalized)
    except ValueError:
        return None

    return numeric if math.isfinite(numeric) else None
