import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["OCR_ENGINE"] = "demo"

TEST_DATA_DIR = Path(__file__).resolve().parents[2] / "sample_data"

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_demo_label() -> None:
    sample = TEST_DATA_DIR / "labels" / "valid_old_tom.png"
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files={"files": ("valid_old_tom.png", sample.read_bytes(), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 1
    assert payload["results"][0]["status"] == "PASS"
    assert payload["results"][0]["ocr"]["engine"] == "sample-fixture"


def test_upload_invalid_warning_label_fails() -> None:
    sample = TEST_DATA_DIR / "labels" / "invalid_warning.png"
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files={"files": ("invalid_warning.png", sample.read_bytes(), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["status"] == "FAIL"
    assert payload["results"][0]["ocr"]["engine"] == "sample-fixture"


def test_bundled_sample_batch_produces_documented_summary() -> None:
    samples = [
        TEST_DATA_DIR / "labels" / "valid_old_tom.png",
        TEST_DATA_DIR / "labels" / "invalid_warning.png",
        TEST_DATA_DIR / "labels" / "rotated_blurry.png",
    ]
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files=[
            ("files", (sample.name, sample.read_bytes(), "image/png"))
            for sample in samples
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {"total": 3, "pass": 2, "warning": 0, "fail": 1}
    assert {result["ocr"]["engine"] for result in payload["results"]} == {"sample-fixture"}


def test_run_sample_batch_endpoint_produces_documented_summary() -> None:
    response = client.post("/api/samples/demo", data={"application_id": "APP-OLD-TOM-001"})
    assert response.status_code == 200
    assert response.json()["summary"] == {"total": 3, "pass": 2, "warning": 0, "fail": 1}


def test_generated_ten_file_batch_produces_documented_summary() -> None:
    samples = sorted((TEST_DATA_DIR / "generated_labels").glob("*.png"))
    assert len(samples) == 10
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files=[
            ("files", (sample.name, sample.read_bytes(), "image/png"))
            for sample in samples
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {"total": 10, "pass": 5, "warning": 1, "fail": 4}
    assert {result["ocr"]["engine"] for result in payload["results"]} == {"sample-fixture"}


def test_demo_mode_does_not_substitute_valid_text_for_unknown_upload() -> None:
    sample = TEST_DATA_DIR / "labels" / "valid_old_tom.png"
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files={"files": ("unknown_submission.png", sample.read_bytes(), "image/png")},
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "FAIL"
    assert result["ocr"]["engine"] == "demo-unrecognized"
    assert result["ocr"]["text"] == ""


def test_modified_file_named_like_sample_is_not_trusted_as_fixture() -> None:
    response = client.post(
        "/api/labels/upload",
        data={"application_id": "APP-OLD-TOM-001"},
        files={"files": ("valid_old_tom.png", b"not the controlled sample", "image/png")},
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["ocr"]["engine"] == "demo-unrecognized"
    assert result["status"] == "FAIL"
