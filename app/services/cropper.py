from pathlib import Path

import pypdfium2 as pdfium


def crop_pdf_regions(
    pdf_path: Path,
    pages_blocks: list,
    output_base_dir: Path,
    scale: float = 2.0,
) -> dict[int, list[str]]:
    """Render each page and crop the layout blocks. Returns page number to crop paths."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    pdf_out_dir = output_base_dir / pdf_path.stem / "crops"
    pdf_out_dir.mkdir(parents=True, exist_ok=True)
    crops_per_page: dict[int, list[str]] = {}

    for page_idx, page in enumerate(pdf):
        image = page.render(scale=scale).to_pil()
        img_h = image.height
        page_num = page_idx + 1
        crops_per_page[page_num] = []

        page_data = next((item for item in pages_blocks if item["page_number"] == page_num), None)
        if not page_data:
            continue

        for idx, block in enumerate(page_data["reading_sequence"], start=1):
            bbox = block["bbox"]
            # PDF origin is bottom-left; PIL origin is top-left.
            x0 = int(bbox["l"] * scale)
            x1 = int(bbox["r"] * scale)
            y0 = int(img_h - (bbox["t"] * scale))
            y1 = int(img_h - (bbox["b"] * scale))
            crop_path = pdf_out_dir / f"p{page_num}_block{idx}_{block['label']}.png"
            image.crop((x0, y0, x1, y1)).save(crop_path)
            crops_per_page[page_num].append(str(crop_path))

    return crops_per_page
