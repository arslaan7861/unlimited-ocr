"""Service for streaming PDF page rendering and OCR extraction."""

import asyncio
import time

import fitz  # PyMuPDF
from fastapi import UploadFile
from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import (
    BadRequestException,
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)
from app.core.logger import get_logger
from app.schemas.ocr import PDFOCRResponse, PDFPageResult
from app.services.model_service import ModelService

logger = get_logger(__name__)


def validate_pdf_bytes(data: bytes) -> None:
    """Validate PDF magic bytes (%PDF-).

    Args:
        data (bytes): Raw binary data of the uploaded file.

    Raises:
        UnsupportedMediaTypeException: If file does not start with %PDF header.
    """
    if len(data) < 5 or not data.startswith(b"%PDF"):
        raise UnsupportedMediaTypeException(
            message="Uploaded file is not a valid PDF document",
            field="file.content_type",
        )


def _render_page_to_pil(doc: fitz.Document, page_index: int, dpi: int) -> Image.Image:
    """Render a single PDF page into a PIL Image.

    Args:
        doc (fitz.Document): Open PyMuPDF document.
        page_index (int): 0-indexed page number.
        dpi (int): DPI resolution for rendering.

    Returns:
        Image.Image: Rendered RGB PIL Image.
    """
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return image


async def process_pdf_ocr(
    file: UploadFile,
    model_service: ModelService,
    semaphore: asyncio.Semaphore,
    settings: Settings,
) -> PDFOCRResponse:
    """Stream and render PDF pages one at a time and extract text using OCR.

    Args:
        file (UploadFile): Uploaded multipart PDF document.
        model_service (ModelService): OCR model service instance.
        semaphore (asyncio.Semaphore): Concurrency limiting semaphore.
        settings (Settings): Active application configuration.

    Returns:
        PDFOCRResponse: Structured response with per-page text and aggregated text.

    Raises:
        PayloadTooLargeException: If upload exceeds maximum allowed byte limit.
        UnsupportedMediaTypeException: If magic bytes do not match PDF signature.
        BadRequestException: If PDF is corrupt or page count exceeds MAX_PDF_PAGES.
        InferenceException: If OCR model prediction fails.
    """
    start_time = time.perf_counter()

    # Read binary content
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

    # Validate PDF signature
    validate_pdf_bytes(contents)

    doc: fitz.Document | None = None
    try:
        try:
            doc = fitz.open(stream=contents, filetype="pdf")
        except Exception as exc:
            logger.warning("Corrupt or invalid PDF uploaded: %s", exc)
            raise BadRequestException(
                message="Uploaded PDF file is corrupt or unreadable",
                field="file",
            ) from exc

        page_count = len(doc)
        if page_count == 0:
            raise BadRequestException(
                message="Uploaded PDF contains no pages",
                field="file.pages",
            )

        if page_count > settings.max_pdf_pages:
            raise BadRequestException(
                message=(
                    f"PDF page count ({page_count}) exceeds "
                    f"maximum allowed limit of {settings.max_pdf_pages} pages"
                ),
                field="file.pages",
            )

        pages_results: list[PDFPageResult] = []

        # Process each page sequentially to keep memory usage flat
        for page_idx in range(page_count):
            page_num = page_idx + 1

            # Render page to PIL image
            pil_page = _render_page_to_pil(doc, page_idx, settings.pdf_dpi)

            # Run inference in worker thread protected by semaphore
            async with semaphore:
                page_text = await asyncio.to_thread(model_service.predict_image, pil_page)

            # Explicitly dereference image to assist memory collection
            del pil_page

            pages_results.append(PDFPageResult(page_number=page_num, text=page_text))

        aggregated_text = "\n\n".join(p.text for p in pages_results)
        elapsed_time = round(time.perf_counter() - start_time, 2)

        return PDFOCRResponse(
            success=True,
            filename=file.filename or "unknown.pdf",
            page_count=page_count,
            pages=pages_results,
            text=aggregated_text,
            processing_time_seconds=elapsed_time,
        )

    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
