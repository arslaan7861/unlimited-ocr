"""Service for image validation, preprocessing, and OCR extraction."""

import asyncio
import io
import time

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config.settings import Settings
from app.core.exceptions import (
    BadRequestException,
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)
from app.core.logger import get_logger
from app.schemas.ocr import ImageMetadata, ImageOCRResponse
from app.services.model_service import ModelService

logger = get_logger(__name__)

# Magic byte signatures for supported image types
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/webp": [b"RIFF"],  # also validated with WEBP header at byte offset 8
}


def validate_image_bytes(data: bytes) -> str:
    """Validate image magic bytes to ensure allowed MIME format.

    Args:
        data (bytes): Raw binary data of the uploaded file.

    Returns:
        str: Detected MIME type ('image/png', 'image/jpeg', 'image/webp').

    Raises:
        UnsupportedMediaTypeException: If file header does not match allowed signatures.
    """
    if len(data) < 12:
        raise UnsupportedMediaTypeException(
            message="Uploaded file is too small or truncated",
            field="file",
        )

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"

    raise UnsupportedMediaTypeException(
        message="Unsupported image format. Allowed formats: PNG, JPEG, WEBP",
        field="file.content_type",
    )


async def process_image_ocr(
    file: UploadFile,
    model_service: ModelService,
    semaphore: asyncio.Semaphore,
    settings: Settings,
) -> ImageOCRResponse:
    """Validate, preprocess, and run OCR on an uploaded image file.

    Args:
        file (UploadFile): Uploaded multipart image file.
        model_service (ModelService): OCR model service instance.
        semaphore (asyncio.Semaphore): Concurrency limiting semaphore.
        settings (Settings): Active configuration settings.

    Returns:
        ImageOCRResponse: Structured response with extracted text and timing.

    Raises:
        PayloadTooLargeException: If upload exceeds configured size limit.
        UnsupportedMediaTypeException: If file MIME/magic bytes are unsupported.
        BadRequestException: If image file is corrupt or unreadable.
        InferenceException: If model prediction fails.
    """
    start_time = time.perf_counter()

    # Read uploaded file content
    contents = await file.read()
    file_size = len(contents)

    if file_size > settings.max_upload_size_bytes:
        raise PayloadTooLargeException(
            message=(
                f"File size ({round(file_size / (1024 * 1024), 2)}MB) exceeds "
                f"maximum allowed limit of {settings.max_upload_size_mb}MB"
            ),
            field="file.size",
        )

    # Validate magic bytes
    validate_image_bytes(contents)

    # Open with PIL
    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.load()  # Verify integrity
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Corrupt or invalid image uploaded: %s", exc)
        raise BadRequestException(
            message="Uploaded file is not a valid or readable image",
            field="file",
        ) from exc

    metadata = ImageMetadata(
        format=pil_image.format or "UNKNOWN",
        width=pil_image.width,
        height=pil_image.height,
    )

    # Convert to RGB if needed (e.g. RGBA or palette)
    if pil_image.mode not in ("RGB", "L"):
        pil_image = pil_image.convert("RGB")

    # Run non-blocking model inference with concurrency control
    async with semaphore:
        text = await asyncio.to_thread(model_service.predict_image, pil_image)

    elapsed_time = round(time.perf_counter() - start_time, 2)

    return ImageOCRResponse(
        success=True,
        filename=file.filename or "unknown.png",
        text=text,
        processing_time_seconds=elapsed_time,
        metadata=metadata,
    )
