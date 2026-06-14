from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ValidationStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class LabelFields(BaseModel):
    brand_name: str | None = None
    class_type: str | None = None
    alcohol_content: str | None = None
    net_contents: str | None = None
    bottler_producer_name: str | None = None
    country_of_origin: str | None = None
    government_warning: str | None = None


class ExpectedApplication(BaseModel):
    application_id: str
    label_name: str
    fields: LabelFields


class FieldValidation(BaseModel):
    field: str
    expected: str | None = None
    extracted: str | None = None
    status: ValidationStatus
    confidence: float = Field(ge=0, le=1)
    message: str


class FormatObservations(BaseModel):
    government_warning_prefix_bold: bool | None = None
    source: str = "not_available"


class OCRResult(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)
    engine: str
    processing_ms: int
    fields: LabelFields
    format_observations: FormatObservations = Field(default_factory=FormatObservations)
    raw_blocks: list[dict[str, Any]] = Field(default_factory=list)


class LabelReviewResult(BaseModel):
    result_id: str
    filename: str
    application_id: str
    status: ValidationStatus
    uploaded_at: datetime
    image_url: str | None = None
    ocr: OCRResult
    validations: list[FieldValidation]


class BatchResponse(BaseModel):
    batch_id: str
    results: list[LabelReviewResult]
    summary: dict[str, int]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    ocr_engine: str
