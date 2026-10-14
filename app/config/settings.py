"""Application configuration settings using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Unlimited-OCR microservice.

    Attributes:
        host (str): Listening IP address.
        port (int): Listening port number.
        environment (str): Runtime environment (development, staging, production).
        log_level (str): Application logging level.
        model_path (str): File path or Hugging Face repository ID for Unlimited-OCR.
        device (str): Compute device for inference ('cpu', 'cuda', 'auto').
        torch_dtype (str): Torch data type for model weights ('bfloat16', 'float16', 'float32').
        max_upload_size_mb (int): Maximum upload size permitted in megabytes.
        max_pdf_pages (int): Maximum allowed pages per PDF document.
        max_concurrent_inferences (int): Maximum concurrent OCR inference executions.
        pdf_dpi (int): DPI resolution when rendering PDF pages into raster images.
        cors_origins (list[str]): Permitted origins for Cross-Origin Resource Sharing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    host: str = Field(default="0.0.0.0", description="Host address to bind to")
    port: int = Field(default=8000, description="Port number to bind to")
    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development", description="Environment stage"
    )
    log_level: str = Field(default="INFO", description="Logging level")

    model_path: str = Field(
        default="models/unlimited-ocr",
        description="Path to model weights or HuggingFace ID",
        validation_alias=None,
    )
    model_dir: str | None = Field(
        default=None,
        description="Legacy alias for model_path",
    )
    model_id_or_path: str | None = Field(
        default=None,
        description="Legacy alias for model_path",
    )

    device: Literal["cpu", "cuda", "auto"] = Field(
        default="cpu", description="Execution target device"
    )
    torch_dtype: Literal["bfloat16", "float16", "float32"] = Field(
        default="bfloat16", description="PyTorch tensor datatype"
    )

    max_upload_size_mb: int = Field(
        default=25, ge=1, le=100, description="Max allowed file size in MB"
    )
    max_pdf_pages: int = Field(
        default=50, ge=1, le=500, description="Max allowed PDF pages to process"
    )
    max_concurrent_inferences: int = Field(
        default=2, ge=1, le=16, description="Max concurrent inference jobs"
    )
    pdf_dpi: int = Field(default=300, ge=72, le=600, description="DPI for PDF page rasterization")

    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origin hosts")

    @field_validator("model_path", mode="before")
    @classmethod
    def resolve_model_path(cls, v: str | None) -> str:
        """Resolve model path from fallback environment variables if set.

        Args:
            v (str | None): Original model_path value.

        Returns:
            str: Resolved model path.
        """
        if v:
            return v
        return os.getenv("MODEL_DIR") or os.getenv("MODEL_ID_OR_PATH") or "models/unlimited-ocr"

    @property
    def max_upload_size_bytes(self) -> int:
        """Calculate max upload size in bytes.

        Returns:
            int: Maximum upload size in bytes.
        """
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached application settings instance.

    Returns:
        Settings: Singleton instance of application configuration.
    """
    return Settings()
