"""
SafeSkin AI – Application Configuration
Uses pydantic-settings to load and validate all environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.
    Values are read from environment variables (or .env file).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Supabase
    # ------------------------------------------------------------------ #
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_anon_key: str = "placeholder-anon-key"
    supabase_service_role_key: str = "placeholder-service-role-key"

    # ------------------------------------------------------------------ #
    # API Security
    # ------------------------------------------------------------------ #
    api_secret_key: str = "dev-secret-change-in-production"

    # ------------------------------------------------------------------ #
    # CORS – stored as a comma-separated string, parsed to list
    # ------------------------------------------------------------------ #
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return CORS origins as a Python list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #
    model_dir: str = "./models"
    max_image_size_mb: int = 10

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def model_dir_path(self) -> Path:
        return Path(self.model_dir)

    # ------------------------------------------------------------------ #
    # Image Quality
    # ------------------------------------------------------------------ #
    image_quality_threshold: int = 40  # 0-100

    # ------------------------------------------------------------------ #
    # AI Confidence Thresholds (0.0 – 1.0)
    # ------------------------------------------------------------------ #
    confidence_threshold_high: float = 0.75
    confidence_threshold_moderate: float = 0.50

    # ------------------------------------------------------------------ #
    # Runtime
    # ------------------------------------------------------------------ #
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    # ------------------------------------------------------------------ #
    # Derived constants
    # ------------------------------------------------------------------ #
    # Supabase storage bucket names
    skin_images_bucket: str = "skin-images"
    avatars_bucket: str = "avatars"

    # Signed URL expiry in seconds
    signed_url_expiry: int = 3600  # 1 hour

    # Supported upload MIME types
    allowed_image_types: List[str] = ["image/jpeg", "image/jpg", "image/png"]
    allowed_image_extensions: List[str] = [".jpg", ".jpeg", ".png"]

    # Model filenames (expected inside model_dir)
    screener_model_file: str = "healthy_screener.h5"
    classifier_model_file: str = "condition_classifier.h5"
    class_labels_file: str = "class_labels.json"

    # ------------------------------------------------------------------ #
    # Medical disclaimer (appended to every response)
    # ------------------------------------------------------------------ #
    disclaimer: str = (
        "This analysis is provided for informational purposes only and does NOT "
        "constitute medical advice, diagnosis, or treatment. Always consult a "
        "qualified dermatologist or healthcare professional for skin concerns."
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
