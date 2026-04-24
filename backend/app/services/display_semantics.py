from __future__ import annotations

from parser.marker_metadata import get_marker_metadata
from parser.postprocess import MarkerDetail
from app.services.interpretation_payload import resolve_semantic_marker


def resolve_lab_value_display(
    name: str,
    detail: MarkerDetail | None = None,
) -> tuple[str | None, str | None]:
    metadata = get_marker_metadata(name) or {}
    marker = resolve_semantic_marker(name)

    unit = detail.unit if detail and detail.unit else None
    reference_range = detail.reference_range if detail and detail.reference_range else None

    if marker is not None and marker.kind in {"percent", "absolute"}:
        allowed_units = set(marker.unit_family)
        if unit and unit not in allowed_units:
            unit = None
            reference_range = None

        if unit is None:
            unit = metadata.get("unit") or (marker.unit_family[0] if marker.unit_family else None)
        if reference_range is None:
            reference_range = metadata.get("reference_range")
        return unit, reference_range

    return unit or metadata.get("unit"), reference_range or metadata.get("reference_range")
