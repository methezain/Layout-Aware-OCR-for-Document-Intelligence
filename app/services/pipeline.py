import logging
import threading
from pathlib import Path

from openai import OpenAI

from app.config import Settings
from app.schemas import DocumentExtraction
from app.services.cropper import crop_pdf_regions
from app.services.extraction import extract_contract
from app.services.store import DocumentStore

logger = logging.getLogger(__name__)


class MissingApiKeyError(Exception):
    """GROQ_API_KEY is required before a document can be processed."""


class PipelineError(Exception):
    """The document could not be processed."""


class Pipeline:
    """Layout, crop, OCR, then field extraction. Models are loaded once."""

    def __init__(self, settings: Settings):
        # Imported here so the API process can start without loading Docling and Paddle.
        from app.services.layout import PDFLayoutExtractor
        from app.services.ocr import OcrEngine

        self.settings = settings
        self.store = DocumentStore(settings)
        self._lock = threading.Lock()
        self.layout = PDFLayoutExtractor(render_scale=settings.render_scale)
        self.ocr = OcrEngine()
        self.client = (
            OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
            if settings.groq_api_key
            else None
        )

    def run(self, pdf_path: Path) -> DocumentExtraction:
        client = self.client
        if client is None:
            raise MissingApiKeyError("GROQ_API_KEY is not set")
        with self._lock:
            return self._run(pdf_path, client)

    def _run(self, pdf_path: Path, client: OpenAI) -> DocumentExtraction:
        pdf_path = Path(pdf_path)
        stem = pdf_path.stem
        logger.info("Processing %s", pdf_path.name)

        try:
            layout = self.layout.process(pdf_path)
            layout.save(
                self.settings.json_dir,
                self.settings.markdown_dir,
                self.settings.processed_pdf_dir,
                stem,
            )
            crops = crop_pdf_regions(
                pdf_path=pdf_path,
                pages_blocks=layout.to_json_dict()["pages"],
                output_base_dir=self.settings.crops_dir,
                scale=self.settings.render_scale,
            )
            crop_paths = [path for paths in crops.values() for path in paths]
            ocr_blocks = self.ocr.extract(crop_paths)
            ocr_text = "\n".join(block["raw_text"] for block in ocr_blocks if block["raw_text"])
            extracted = extract_contract(ocr_text, client, self.settings.groq_model)
            payload = DocumentExtraction(
                file_name=pdf_path.name,
                extracted_data=extracted,
                raw_ocr_blocks=ocr_blocks,
            )
        except Exception as exc:
            logger.exception("Failed to process %s", pdf_path.name)
            raise PipelineError(f"Could not process {pdf_path.name}") from exc

        output = self.store.save_extraction(stem, payload)
        logger.info("Saved %s", output.name)
        return payload
