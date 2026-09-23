from typing import Any

from pydantic import BaseModel, Field


class ContractExtraction(BaseModel):
    contractor_name: str = Field(description="Name of contractor or individual")
    contractor_no: str = Field(description="Contractor ID or reference number")
    vat_number: str = Field(description="VAT or Tax registration number")
    process_date: str = Field(description="Date processed or document date")
    gross_pay: float = Field(description="Total gross payment this period")
    net_pay: float = Field(description="Total net pay amount")


class OcrLine(BaseModel):
    text: str
    confidence: float
    local_box: list[Any]


class OcrBlock(BaseModel):
    crop_file: str
    raw_text: str
    lines: list[OcrLine]


class DocumentExtraction(BaseModel):
    file_name: str
    extracted_data: ContractExtraction
    raw_ocr_blocks: list[OcrBlock]


class StemRecord(BaseModel):
    stem: str = Field(
        description="PDF file name without .pdf. Copy this into the other endpoints."
    )
    file_name: str


class RawExtractedText(BaseModel):
    stem: str
    file_name: str
    raw_ocr_blocks: list[OcrBlock]


class LlmStructuredJson(BaseModel):
    stem: str
    file_name: str
    extracted_data: ContractExtraction


class HealthResponse(BaseModel):
    status: str
