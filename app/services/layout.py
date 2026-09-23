"""PDF layout extraction with Docling: reading order, markdown, and an annotated PDF."""

import json
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

LABEL_COLORS = {
    "title": "#1E40AF",
    "section_header": "#2563EB",
    "paragraph": "#DC2626",
    "text": "#DC2626",
    "table": "#16A34A",
    "list_item": "#D97706",
}
DEFAULT_COLOR = "#4B5563"


@dataclass
class PageResult:
    page_number: int
    reading_sequence: list
    annotated_image: Image.Image = field(repr=False)


@dataclass
class DocumentResult:
    file_name: str
    markdown: str
    pages: list[PageResult]

    def to_json_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "pages": [
                {"page_number": page.page_number, "reading_sequence": page.reading_sequence}
                for page in self.pages
            ],
        }

    def annotated_pdf_bytes(self) -> bytes:
        buf = BytesIO()
        if self.pages:
            images = [page.annotated_image for page in self.pages]
            images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
        return buf.getvalue()

    def save(self, json_dir: Path, md_dir: Path, pdf_dir: Path, stem: str) -> None:
        for directory in (json_dir, md_dir, pdf_dir):
            directory.mkdir(parents=True, exist_ok=True)

        (md_dir / f"{stem}.md").write_text(self.markdown, encoding="utf-8")
        (json_dir / f"{stem}.json").write_text(
            json.dumps(self.to_json_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if self.pages:
            images = [page.annotated_image for page in self.pages]
            images[0].save(
                pdf_dir / f"{stem}_annotated.pdf",
                save_all=True,
                append_images=images[1:],
            )


class PDFLayoutExtractor:
    """Extracts text, tables, and corrected reading order from a PDF via Docling."""

    def __init__(
        self,
        table_mode: TableFormerMode = TableFormerMode.ACCURATE,
        render_scale: float = 2.0,
    ):
        self.render_scale = render_scale
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = table_mode
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )

    @staticmethod
    def _sort_reading_order(blocks: list, page_w: float) -> list:
        """Column-first sort: left column, then right column, each top-to-bottom."""
        mid_x = page_w / 2.0
        left_col, right_col = [], []
        for block in blocks:
            center_x = (block["bbox"]["l"] + block["bbox"]["r"]) / 2.0
            (left_col if center_x < mid_x else right_col).append(block)

        # Docling's origin is bottom-left, so a larger `t` is higher on the page.
        left_col.sort(key=lambda item: item["bbox"]["t"], reverse=True)
        right_col.sort(key=lambda item: item["bbox"]["t"], reverse=True)
        return left_col + right_col

    @staticmethod
    def _extract_blocks(doc) -> dict:
        raw_page_blocks: dict = {}
        for item, _ in doc.iterate_items():
            if not getattr(item, "prov", None):
                continue

            label = str(item.label).lower().replace("docitemlabel.", "")
            text = getattr(item, "text", "")
            table_html = (
                item.export_to_html(doc)
                if label == "table" and hasattr(item, "export_to_html")
                else None
            )
            for prov in item.prov:
                page_idx = prov.page_no - 1
                raw_page_blocks.setdefault(page_idx, []).append({
                    "label": label,
                    "text": text,
                    "table_html": table_html,
                    "bbox": {
                        "l": prov.bbox.l,
                        "t": prov.bbox.t,
                        "r": prov.bbox.r,
                        "b": prov.bbox.b,
                    },
                })
        return raw_page_blocks

    def _annotate_page(self, img: Image.Image, ordered_blocks: list) -> Image.Image:
        draw = ImageDraw.Draw(img)
        img_h = img.height
        for seq_idx, block in enumerate(ordered_blocks, start=1):
            bbox = block["bbox"]
            color = LABEL_COLORS.get(block["label"], DEFAULT_COLOR)
            x0 = bbox["l"] * self.render_scale
            x1 = bbox["r"] * self.render_scale
            y0 = img_h - (bbox["t"] * self.render_scale)
            y1 = img_h - (bbox["b"] * self.render_scale)
            draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
            draw.text((x0, max(0, y0 - 12)), f"#{seq_idx} [{block['label']}]", fill=color)
        return img.convert("RGB")

    def process(self, pdf_path: Path) -> DocumentResult:
        pdf_path = Path(pdf_path)
        doc = self.converter.convert(pdf_path).document
        raw_page_blocks = self._extract_blocks(doc)
        pdf = pdfium.PdfDocument(str(pdf_path))
        pages: list[PageResult] = []

        for page_idx, page in enumerate(pdf):
            image = page.render(scale=self.render_scale).to_pil()
            page_w = image.width / self.render_scale
            ordered_blocks = self._sort_reading_order(raw_page_blocks.get(page_idx, []), page_w)
            pages.append(PageResult(
                page_number=page_idx + 1,
                reading_sequence=ordered_blocks,
                annotated_image=self._annotate_page(image, ordered_blocks),
            ))

        return DocumentResult(
            file_name=pdf_path.name,
            markdown=doc.export_to_markdown(),
            pages=pages,
        )
