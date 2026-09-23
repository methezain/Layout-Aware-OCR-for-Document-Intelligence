"""Process every PDF already sitting in raw_pdfs. Uses the same pipeline as the API."""

import logging

from app.config import get_settings
from app.services.pipeline import Pipeline

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    settings.ensure_dirs()
    pipeline = Pipeline(settings)
    pdfs = sorted(settings.raw_pdfs.glob("*.pdf"))
    if not pdfs:
        logger.info("No PDFs in %s", settings.raw_pdfs)
        return
    for pdf_path in pdfs:
        pipeline.run(pdf_path)


if __name__ == "__main__":
    main()
