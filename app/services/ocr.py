from pathlib import Path

from paddleocr import PaddleOCR


def _as_box(poly_box):
    if hasattr(poly_box, "tolist"):
        return poly_box.tolist()
    return poly_box


def _iter_ocr_lines(ocr_result):
    """Yield (text, score, box) from PaddleOCR 2.x or 3.x results."""
    if not ocr_result:
        return

    first = ocr_result[0]
    if isinstance(first, list):
        for line in first:
            poly_box, (text, score) = line
            yield text, score, poly_box
        return

    for page in ocr_result:
        texts = page.get("rec_texts") or []
        scores = page.get("rec_scores") or []
        polys = page.get("rec_polys")
        if polys is None:
            polys = page.get("dt_polys") or []
        for text, score, poly in zip(texts, scores, polys):
            yield text, score, poly


class OcrEngine:
    def __init__(self) -> None:
        # use_angle_cls is the 2.x name; PaddleOCR 3.x maps it to use_textline_orientation.
        self._ocr = PaddleOCR(use_angle_cls=True, lang="en", enable_mkldnn=False)

    def extract(self, crop_paths: list[str]) -> list[dict]:
        results = []
        for path_str in crop_paths:
            path = Path(path_str)
            # 3.x ocr() forwards kwargs into predict(), which rejects the old cls= flag.
            if hasattr(self._ocr, "predict"):
                ocr_result = self._ocr.predict(str(path))
            else:
                ocr_result = self._ocr.ocr(str(path), cls=True)

            lines = []
            combined_text = []
            for text, score, poly_box in _iter_ocr_lines(ocr_result):
                combined_text.append(text)
                lines.append({
                    "text": text,
                    "confidence": round(float(score), 4),
                    "local_box": _as_box(poly_box),
                })
            results.append({
                "crop_file": path.name,
                "raw_text": " ".join(combined_text),
                "lines": lines,
            })
        return results
