from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.config.settings import Settings, get_settings
from app.core.exceptions import InferenceException
from app.schemas.ocr import ImageOCRResponse, PDFOCRResponse, StructuredDocumentResponse
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


@router.post(
    "/image/parse",
    response_model=StructuredDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and structure text from an image using LLM",
)
async def ocr_image_parse(
    request: Request,
    file: UploadFile = File(..., description="Image file (PNG, JPEG, WEBP)"),
    document_type: str = Form(default="general", description="Document type"),
    custom_prompt: str | None = Form(default=None, description="Custom prompt"),
    settings: Settings = Depends(get_settings),
) -> StructuredDocumentResponse:
    """Extract and semantically structure image text using Unlimited-OCR and LLM.

    Args:
        request (Request): Active HTTP request.
        file (UploadFile): Uploaded multipart image file.
        document_type (str): Type of document (general, invoice, receipt, contract, table).
        custom_prompt (str | None): Optional specific extraction instructions.
        settings (Settings): Active application configuration.

    Returns:
        StructuredDocumentResponse: Raw OCR, cleaned markdown, and structured JSON.
    """
    model_service = getattr(request.app.state, "model_service", None)
    if not model_service or not model_service.is_ready():
        raise InferenceException(
            message="OCR model is not loaded or ready to accept requests",
            status_code=503,
            field="model",
        )

    semaphore = request.app.state.semaphore
    ocr_result = await process_image_ocr(
        file=file,
        model_service=model_service,
        semaphore=semaphore,
        settings=settings,
    )

    # Run LLM semantic structuring
    import time

    llm_start = time.perf_counter()
    from app.services.llm_parser import LLMDocumentParser

    parser = LLMDocumentParser(settings)
    cleaned_md, structured_data = await parser.parse_document(
        raw_text=ocr_result.text,
        document_type=document_type,
        custom_prompt=custom_prompt,
    )
    llm_time = round(time.perf_counter() - llm_start, 2)
    total_time = round(ocr_result.processing_time_seconds + llm_time, 2)

    return StructuredDocumentResponse(
        success=True,
        filename=ocr_result.filename,
        document_type=document_type,
        raw_text=ocr_result.text,
        cleaned_markdown=cleaned_md,
        structured_data=structured_data,
        ocr_time_seconds=ocr_result.processing_time_seconds,
        llm_time_seconds=llm_time,
        total_time_seconds=total_time,
        metadata={
            "format": ocr_result.metadata.format,
            "width": ocr_result.metadata.width,
            "height": ocr_result.metadata.height,
        },
    )


@router.post(
    "/pdf/parse",
    response_model=StructuredDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and structure text from a scanned PDF using LLM",
)
async def ocr_pdf_parse(
    request: Request,
    file: UploadFile = File(..., description="PDF document (application/pdf)"),
    document_type: str = Form(default="general", description="Document type"),
    custom_prompt: str | None = Form(default=None, description="Custom prompt"),
    settings: Settings = Depends(get_settings),
) -> StructuredDocumentResponse:
    """Extract and semantically structure scanned PDF text using Unlimited-OCR and LLM.

    Args:
        request (Request): Active HTTP request.
        file (UploadFile): Uploaded multipart PDF document.
        document_type (str): Type of document (general, invoice, receipt, contract, table).
        custom_prompt (str | None): Optional specific extraction instructions.
        settings (Settings): Active application configuration.

    Returns:
        StructuredDocumentResponse: Raw OCR, cleaned markdown, and structured JSON.
    """
    model_service = getattr(request.app.state, "model_service", None)
    if not model_service or not model_service.is_ready():
        raise InferenceException(
            message="OCR model is not loaded or ready to accept requests",
            status_code=503,
            field="model",
        )

    semaphore = request.app.state.semaphore
    ocr_result = await process_pdf_ocr(
        file=file,
        model_service=model_service,
        semaphore=semaphore,
        settings=settings,
    )

    # Run LLM semantic structuring
    import time

    llm_start = time.perf_counter()
    from app.services.llm_parser import LLMDocumentParser

    parser = LLMDocumentParser(settings)
    cleaned_md, structured_data = await parser.parse_document(
        raw_text=ocr_result.text,
        document_type=document_type,
        custom_prompt=custom_prompt,
    )
    llm_time = round(time.perf_counter() - llm_start, 2)
    total_time = round(ocr_result.processing_time_seconds + llm_time, 2)

    return StructuredDocumentResponse(
        success=True,
        filename=ocr_result.filename,
        document_type=document_type,
        raw_text=ocr_result.text,
        cleaned_markdown=cleaned_md,
        structured_data=structured_data,
        ocr_time_seconds=ocr_result.processing_time_seconds,
        llm_time_seconds=llm_time,
        total_time_seconds=total_time,
        metadata={
            "page_count": ocr_result.page_count,
        },
    )
