from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Path as StemPath, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.config import document_stem
from app.schemas import DocumentExtraction, LlmStructuredJson, RawExtractedText, StemRecord
from app.services.pipeline import MissingApiKeyError, Pipeline, PipelineError

router = APIRouter()

STEM = StemPath(
    ...,
    description="PDF file name without .pdf. Copy it from POST /process-pdf or GET /stems.",
    examples=["Distributor Agreement"],
)


def get_pipeline(request: Request) -> Pipeline:
    return request.app.state.pipeline


def _require_stem(stem: str) -> str:
    if stem in {".", ".."} or stem != Path(stem).name or not stem.strip():
        raise HTTPException(status_code=400, detail="Invalid stem")
    return stem


def _load_extraction(pipeline: Pipeline, stem: str) -> tuple[str, DocumentExtraction]:
    stem = _require_stem(stem)
    payload = pipeline.store.load_extraction(stem)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail="No processed PDF for that stem. Call GET /stems to see valid values.",
        )
    return stem, payload


@router.post(
    "/process-pdf",
    response_model=StemRecord,
    status_code=201,
    summary="Upload a PDF and process it",
    tags=["1. Process"],
)
async def process_pdf(
    file: UploadFile = File(..., description="The contract PDF to process."),
    pipeline: Pipeline = Depends(get_pipeline),
) -> StemRecord:
    """Runs layout detection, OCR, and LLM extraction. Save the returned stem."""
    data = await file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Upload a PDF file")

    stem = document_stem(file.filename)
    pdf_path = pipeline.store.save_upload(stem, data)
    try:
        await run_in_threadpool(pipeline.run, pdf_path)
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StemRecord(stem=stem, file_name=pdf_path.name)


@router.get(
    "/stems",
    response_model=list[StemRecord],
    summary="Get the stem of every processed PDF",
    tags=["2. Stem"],
)
def get_stems(pipeline: Pipeline = Depends(get_pipeline)) -> list[StemRecord]:
    """Lists the stem to paste into the download endpoints."""
    return pipeline.store.list_stems()


@router.get(
    "/annotated-pdf/{stem}",
    summary="Download the annotated PDF",
    tags=["3. Download"],
    responses={200: {"content": {"application/pdf": {}}}},
)
def download_annotated_pdf(
    stem: str = STEM,
    pipeline: Pipeline = Depends(get_pipeline),
) -> FileResponse:
    """PDF with layout boxes drawn on each page."""
    path = pipeline.store.annotated_pdf_path(_require_stem(stem))
    if path is None:
        raise HTTPException(
            status_code=404,
            detail="No annotated PDF for that stem. Call GET /stems to see valid values.",
        )
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get(
    "/raw-extracted-text/{stem}",
    response_model=RawExtractedText,
    summary="Get the raw OCR text JSON",
    tags=["3. Download"],
)
def get_raw_extracted_text(
    stem: str = STEM,
    pipeline: Pipeline = Depends(get_pipeline),
) -> RawExtractedText:
    """Text read off the page, before the LLM turns it into fields."""
    stem, payload = _load_extraction(pipeline, stem)
    return RawExtractedText(
        stem=stem,
        file_name=payload.file_name,
        raw_ocr_blocks=payload.raw_ocr_blocks,
    )


@router.get(
    "/llm-structured-json/{stem}",
    response_model=LlmStructuredJson,
    summary="Get the LLM structured JSON",
    tags=["3. Download"],
)
def get_llm_structured_json(
    stem: str = STEM,
    pipeline: Pipeline = Depends(get_pipeline),
) -> LlmStructuredJson:
    """Contract fields extracted by the LLM: name, VAT, dates, and pay."""
    stem, payload = _load_extraction(pipeline, stem)
    return LlmStructuredJson(
        stem=stem,
        file_name=payload.file_name,
        extracted_data=payload.extracted_data,
    )
