import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.documents import router
from app.config import get_settings
from app.schemas import HealthResponse
from app.services.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_dirs()
    logger.info("Loading layout and OCR models")
    app.state.pipeline = Pipeline(settings)
    yield


app = FastAPI(
    title="Layout Aware OCR for Contract Data Extraction",
    version="1.0.0",
    lifespan=lifespan,
    description=(
        "Upload a PDF with POST /process-pdf. Copy the stem from that response "
        "(or from GET /stems) and use it to download the annotated PDF, the raw OCR text, "
        "or the LLM structured fields.\n\n"
        "Developed with 💖 by Ali Zain (www.linkedin.com/in/alizain-technologist)"
    ),
)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok")
