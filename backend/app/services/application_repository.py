import json
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.models.schemas import ExpectedApplication


@lru_cache
def load_expected_applications() -> dict[str, ExpectedApplication]:
    configured_path = get_settings().expected_data_path
    path = configured_path if configured_path.exists() else Path("sample_data/expected/mock_applications.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["application_id"]: ExpectedApplication.model_validate(item)
        for item in data["applications"]
    }


def get_expected_application(application_id: str) -> ExpectedApplication:
    applications = load_expected_applications()
    if application_id not in applications:
        raise KeyError(f"Unknown application_id '{application_id}'")
    return applications[application_id]
