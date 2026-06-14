import base64
import csv
import hashlib
import io
import json
import mimetypes
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.models import database
from app.models.schemas import BatchResponse, HealthResponse, LabelReviewResult
from app.services.application_repository import get_expected_application
from app.services.ocr import OCRService
from app.services.validation import ValidationEngine

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_name=settings.app_name, ocr_engine=settings.ocr_engine)


@router.post("/labels/upload", response_model=BatchResponse)
async def upload_labels(
    files: list[UploadFile] = File(...),
    application_id: str = Form("APP-OLD-TOM-001"),
) -> BatchResponse:
    settings = get_settings()
    batch_id = str(uuid4())
    results: list[LabelReviewResult] = []
    for upload in files:
        _validate_upload(upload)
        saved_path = await _save_upload(upload, settings.upload_dir / batch_id)
        results.append(_process_file(batch_id, saved_path, upload.filename or saved_path.name, application_id))
    return BatchResponse(batch_id=batch_id, results=results, summary=_summary(results))


@router.post("/samples/demo", response_model=BatchResponse)
def run_sample_batch(application_id: str = Form("APP-OLD-TOM-001")) -> BatchResponse:
    settings = get_settings()
    batch_id = str(uuid4())
    source_dir = settings.expected_data_path.resolve().parent.parent / "labels"
    fixture_names = ("valid_old_tom.png", "invalid_warning.png", "rotated_blurry.png")
    results: list[LabelReviewResult] = []
    for filename in fixture_names:
        source_path = source_dir / filename
        if not source_path.exists():
            raise HTTPException(status_code=500, detail=f"Bundled sample not found: {filename}")
        saved_path = settings.upload_dir / batch_id / filename
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, saved_path)
        results.append(_process_file(batch_id, saved_path, filename, application_id))
    return BatchResponse(batch_id=batch_id, results=results, summary=_summary(results))


@router.post("/ocr/extract")
async def extract_ocr(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    _validate_upload(file)
    saved_path = await _save_upload(file, settings.upload_dir / "adhoc")
    try:
        fixture = _controlled_sample_record(saved_path, file.filename or saved_path.name)
        if fixture:
            return OCRService("sample-fixture").extract_fixture(
                saved_path,
                fixture["ocr_text"],
                fixture.get("government_warning_prefix_bold"),
            ).model_dump()
        return OCRService(settings.ocr_engine).extract(saved_path).model_dump()
    finally:
        _cleanup_upload(saved_path)


@router.get("/results", response_model=list[LabelReviewResult])
def results() -> list[dict]:
    if not get_settings().persist_results:
        return []
    return database.list_results()


@router.get("/batches/{batch_id}", response_model=BatchResponse)
def batch(batch_id: str) -> BatchResponse:
    if not get_settings().persist_results:
        raise HTTPException(status_code=404, detail="Batch history is disabled")
    items = [LabelReviewResult.model_validate(item) for item in database.list_batch(batch_id)]
    if not items:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchResponse(batch_id=batch_id, results=items, summary=_summary(items))


@router.get("/exports/results.csv")
def export_results() -> StreamingResponse:
    rows = database.list_results() if get_settings().persist_results else []
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["result_id", "filename", "application_id", "status", "field", "expected", "extracted", "field_status", "confidence", "message"])
    for row in rows:
        for validation in row["validations"]:
            writer.writerow([
                row["result_id"],
                row["filename"],
                row["application_id"],
                row["status"],
                validation["field"],
                validation.get("expected"),
                validation.get("extracted"),
                validation["status"],
                validation["confidence"],
                validation["message"],
            ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ttb-label-review-results.csv"},
    )


def _process_file(batch_id: str, path: Path, filename: str, application_id: str) -> LabelReviewResult:
    settings = get_settings()
    try:
        expected = get_expected_application(application_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        fixture = _controlled_sample_record(path, filename)
        if fixture:
            ocr_result = OCRService("sample-fixture").extract_fixture(
                path,
                fixture["ocr_text"],
                fixture.get("government_warning_prefix_bold"),
            )
        elif settings.ocr_engine.lower() == "demo":
            ocr_result = OCRService("reject-unrecognized-demo").extract(path)
        else:
            ocr_result = OCRService(settings.ocr_engine).extract(path)
        validations = ValidationEngine().validate(expected, ocr_result.fields, ocr_result.format_observations)
        status = ValidationEngine().summarize(validations)
        result = LabelReviewResult(
            result_id=str(uuid4()),
            filename=filename,
            application_id=application_id,
            status=status,
            uploaded_at=datetime.now(UTC),
            image_url=_build_image_url(path),
            ocr=ocr_result,
            validations=validations,
        )
        if settings.persist_results:
            database.save_result(batch_id, result.model_dump(mode="json"))
        return result
    finally:
        _cleanup_upload(path)


async def _save_upload(upload: UploadFile, folder: Path) -> Path:
    settings = get_settings()
    folder.mkdir(parents=True, exist_ok=True)
    source = Path(upload.filename or "label.png")
    suffix = source.suffix.lower() or ".png"
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", source.stem).strip("_") or "label"
    path = folder / f"{safe_stem}_{uuid4()}{suffix}"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    bytes_written = 0
    try:
        with path.open("wb") as buffer:
            while chunk := await upload.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
                    )
                buffer.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _validate_upload(upload: UploadFile) -> None:
    if upload.content_type and not upload.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {upload.content_type}")


def _build_image_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _controlled_sample_record(upload_path: Path, filename: str) -> dict | None:
    sample_name = Path(filename).name
    manifest_path = get_settings().expected_data_path.resolve().parent / "controlled_fixtures.json"
    if not manifest_path.exists():
        return None
    fixture_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture = next(
        (record for record in fixture_data.get("fixtures", []) if record["filename"] == sample_name),
        None,
    )
    if not fixture or fixture.get("sha256") != _sha256(upload_path):
        return None
    return fixture


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cleanup_upload(path: Path) -> None:
    if not get_settings().delete_uploads_after_processing:
        return
    path.unlink(missing_ok=True)
    path.with_name(f"{path.stem}.processed.png").unlink(missing_ok=True)


def _summary(results: list[LabelReviewResult]) -> dict[str, int]:
    return {
        "total": len(results),
        "pass": sum(1 for item in results if item.status == "PASS"),
        "warning": sum(1 for item in results if item.status == "WARNING"),
        "fail": sum(1 for item in results if item.status == "FAIL"),
    }
