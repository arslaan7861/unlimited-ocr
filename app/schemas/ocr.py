"""Schemas for image and PDF OCR requests and responses."""

from pydantic import BaseModel, ConfigDict, Field


class ImageMetadata(BaseModel):
    """Metadata describing an uploaded image.

    Attributes:
        format (str): Image format (e.g. 'PNG', 'JPEG', 'WEBP').
        width (int): Image width in pixels.
        height (int): Image height in pixels.
    """

    model_config = ConfigDict(extra="forbid")

    format: str = Field(..., description="Image format (e.g. PNG, JPEG, WEBP)")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")


class ImageOCRResponse(BaseModel):
    """Structured response for single image OCR processing.

    Attributes:
        success (bool): Always true on successful processing.
        filename (str): Name of the processed image file.
        text (str): Extracted text content from the image.
        processing_time_seconds (float): Time taken to process the image in seconds.
        metadata (ImageMetadata): Format and dimension details.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=True, description="Success indicator")
    filename: str = Field(..., description="Original filename")
    text: str = Field(..., description="Extracted text from image")
    processing_time_seconds: float = Field(
        ..., ge=0.0, description="Processing duration in seconds"
    )
    metadata: ImageMetadata = Field(..., description="Image dimensional metadata")


class PDFPageResult(BaseModel):
    """Extracted text result for a single PDF page.

    Attributes:
        page_number (int): 1-indexed page number.
        text (str): Extracted text from this specific page.
    """

    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(..., description="Text extracted from this page")


class PDFOCRResponse(BaseModel):
    """Structured response for scanned PDF OCR processing.

    Attributes:
        success (bool): Always true on successful processing.
        filename (str): Name of the processed PDF file.
        page_count (int): Total number of processed pages.
        pages (list[PDFPageResult]): Breakdown of text per page.
        text (str): Concatenated text of all pages separated by double newlines.
        processing_time_seconds (float): Time taken to process the entire PDF in seconds.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=True, description="Success indicator")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., ge=1, description="Total number of pages")
    pages: list[PDFPageResult] = Field(..., description="Ordered list of page extraction results")
    text: str = Field(..., description="Aggregated text from all pages")
    processing_time_seconds: float = Field(
        ..., ge=0.0, description="Total processing duration in seconds"
    )
