from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-Powered Alcohol Label Verification App"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./ttb_label_review.db"
    upload_dir: Path = Path("./uploads")
    max_upload_mb: int = 20
    persist_results: bool = True
    delete_uploads_after_processing: bool = True
    ocr_engine: str = "tesseract"
    easyocr_languages: str = "en"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    expected_data_path: Path = Path("../sample_data/expected/mock_applications.json")
    frontend_dist_dir: Path | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
