import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.analysis import AnalysisRecord, LabValuePayload
from parser.marker_metadata import get_marker_metadata
from parser.postprocess import MarkerDetail


class LocalAnalysisStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        raw_values: dict[str, float | None],
        marker_details: dict[str, MarkerDetail] | None = None,
    ) -> AnalysisRecord:
        marker_details = marker_details or {}
        record = AnalysisRecord(
            id=uuid4().hex,
            created_at=datetime.now(UTC),
            status="parsed",
            values=[
                LabValuePayload(
                    name=name,
                    value=value,
                    unit=(
                        marker_details.get(name).unit
                        if marker_details.get(name) and marker_details.get(name).unit
                        else (metadata.get("unit") if metadata else None)
                    ),
                    reference_range=(
                        marker_details.get(name).reference_range
                        if marker_details.get(name) and marker_details.get(name).reference_range
                        else (metadata.get("reference_range") if metadata else None)
                    ),
                )
                for name, value in raw_values.items()
                for metadata in [get_marker_metadata(name)]
            ]
        )
        self._write(record)
        return record

    def save_interpretation(self, analysis_id: str, summary: str) -> AnalysisRecord:
        record = self.get(analysis_id)
        record.status = "interpreted"
        record.interpretation = summary
        self._write(record)
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        path = self.base_dir / f"{analysis_id}.json"
        return AnalysisRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def _write(self, record: AnalysisRecord) -> None:
        path = self.base_dir / f"{record.id}.json"
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
