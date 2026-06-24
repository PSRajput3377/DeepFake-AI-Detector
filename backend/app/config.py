"""Centralized runtime configuration."""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Loaded from env vars (prefixed with `DEEPFAKE_`) and from a .env file."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_prefix="DEEPFAKE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Demo mode → no model weights required, deterministic verdicts.
    demo_mode: bool = True

    # Use a HuggingFace pretrained deepfake image classifier instead of the
    # locally trained checkpoint. This works on arbitrary in-the-wild videos
    # because the pretrained models were trained on diverse datasets (FF++,
    # DFDC, etc.). Setting this to True takes precedence over `demo_mode`.
    use_pretrained_hf: bool = False
    hf_model_id: str = "prithivMLmods/Deep-Fake-Detector-Model"

    # Storage paths.
    media_dir: Path = ROOT_DIR / "media"
    models_dir: Path = ROOT_DIR / "models"
    hf_cache_dir: Path = ROOT_DIR / ".hf_cache"

    # Upload limits.
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB
    allowed_extensions: List[str] = Field(
        default_factory=lambda: [
            "mp4", "mov", "webm", "mkv", "avi", "3gp", "wmv", "flv", "gif",
        ]
    )

    # CORS (the React dev server + a couple of preview ports).
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    cors_allow_all: bool = True  # convenient for local dev / demos

    # Pipeline defaults.
    default_sequence_length: int = 20
    max_sequence_length: int = 100
    preview_frame_count: int = 12
    face_preview_count: int = 8

    @property
    def uploaded_videos_dir(self) -> Path:
        return self.media_dir / "uploaded_videos"

    @property
    def uploaded_images_dir(self) -> Path:
        return self.media_dir / "uploaded_images"

    def ensure_dirs(self) -> None:
        for path in (
            self.media_dir,
            self.uploaded_videos_dir,
            self.uploaded_images_dir,
            self.models_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
