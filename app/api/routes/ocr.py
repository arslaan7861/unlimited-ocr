"""OCR endpoints for image and scanned PDF processing."""

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.config.settings import Settings, get_settings
from app.core.exceptions import InferenceException
from app.schemas.ocr import ImageOCRResponse, PDFOCRResponse
from app.services.image_ocr import process_image_ocr
from app.services.pdf_ocr import process_pdf_ocr

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post(
    "/image",
    response_model=ImageOCRResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from an image",
)
async def ocr_image(
    request: Request,
    file: UploadFile = File(..., description="Image file (PNG, JPEG, WEBP)"),
    settings: Settings = Depends(get_settings),
) -> ImageOCRResponse:
    """Extract text from an uploaded raster image.

    Args:
        request (Request): Active HTTP request.
        file (UploadFile): Uploaded multipart image file.
        settings (Settings): Active application configuration.

    Returns:
        ImageOCRResponse: Structured extraction output with text and metadata.

    Raises:
        InferenceException: If the model is not loaded.
    """
    model_service = getattr(request.app.state, "model_service", None)
    if not model_service or not model_service.is_ready():
        raise InferenceException(
            message="OCR model is not loaded or ready to accept requests",
            status_code=503,
            field="model",
        )

    semaphore = request.app.state.semaphore
    return await process_image_ocr(
        file=file,
        model_service=model_service,
        semaphore=semaphore,
        settings=settings,
    )


@router.post(
    "/pdf",
    response_model=PDFOCRResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from a scanned PDF document",
)
async def ocr_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF document (application/pdf)"),
    settings: Settings = Depends(get_settings),
) -> PDFOCRResponse:
    """Extract text from an uploaded scanned PDF document page by page.

    Args:
        request (Request): Active HTTP request.
        file (UploadFile): Uploaded multipart PDF file.
        settings (Settings): Active application configuration.

    Returns:
        PDFOCRResponse: Structured extraction output with per-page text breakdown.

    Raises:
        InferenceException: If the model is not loaded.
    """
    model_service = getattr(request.app.state, "model_service", None)
    if not model_service or not model_service.is_ready():
        raise InferenceException(
            message="OCR model is not loaded or ready to accept requests",
            status_code=503,
            field="model",
        )

    semaphore = request.app.state.semaphore
    return await process_pdf_ocr(
        file=file,
        model_service=model_service,
        semaphore=semaphore,
        settings=settings,
    )
