import json
from pathlib import Path

from app.config import Settings
from app.schemas import DocumentExtraction, StemRecord


class DocumentStore:
    """Paths for the on-disk artifacts. Every name stays inside its own directory."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def save_upload(self, stem: str, data: bytes) -> Path:
        path = self._child(self.settings.raw_pdfs, f"{stem}.pdf")
        path.write_bytes(data)
        return path

    def save_extraction(self, stem: str, payload: DocumentExtraction) -> Path:
        path = self._child(self.settings.json_dir, f"{stem}_extracted.json")
        path.write_text(
            json.dumps(payload.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def list_stems(self) -> list[StemRecord]:
        records = []
        for path in sorted(self.settings.json_dir.glob("*_extracted.json")):
            stem = path.name.removesuffix("_extracted.json")
            records.append(StemRecord(stem=stem, file_name=f"{stem}.pdf"))
        return records

    def load_extraction(self, stem: str) -> DocumentExtraction | None:
        path = self._child(self.settings.json_dir, f"{stem}_extracted.json")
        if not path.is_file():
            return None
        return DocumentExtraction.model_validate_json(path.read_text(encoding="utf-8"))

    def markdown_path(self, stem: str) -> Path | None:
        return self._existing(self.settings.markdown_dir, f"{stem}.md")

    def layout_path(self, stem: str) -> Path | None:
        return self._existing(self.settings.json_dir, f"{stem}.json")

    def annotated_pdf_path(self, stem: str) -> Path | None:
        return self._existing(self.settings.processed_pdf_dir, f"{stem}_annotated.pdf")

    def _existing(self, directory: Path, name: str) -> Path | None:
        path = self._child(directory, name)
        return path if path.is_file() else None

    @staticmethod
    def _child(directory: Path, name: str) -> Path:
        path = (directory / name).resolve()
        if path.parent != directory.resolve():
            raise ValueError("invalid document name")
        return path
