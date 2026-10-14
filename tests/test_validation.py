"""Tests for input validation, file size limits, magic bytes, and error contracts."""

import fitz
import pytest
from httpx import AsyncClient

from app.schemas.common import ErrorResponse


def assert_unified_error_contract(response_json: dict) -> None:
    """Validate that response dictionary matches the ErrorResponse schema.

    Args:
        response_json (dict): Parsed JSON body.
    """
    validated = ErrorResponse.model_validate(response_json)
    assert validated.success is False
    assert len(validated.message) > 0
    assert len(validated.errors) > 0
    for err in validated.errors:
        assert len(err.field) > 0
        assert len(err.message) > 0


@pytest.mark.asyncio
async def test_oversized_image_upload_rejected(async_client: AsyncClient):
    """Test that image upload exceeding MAX_UPLOAD_SIZE_MB returns HTTP 413."""
    # Test settings have max_upload_size_mb=5. Send 6MB.
    large_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * (6 * 1024 * 1024)
    files = {"file": ("large.png", large_payload, "image/png")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 413
    data = response.json()
    assert_unified_error_contract(data)
    assert data["errors"][0]["field"] == "file.size"


@pytest.mark.asyncio
async def test_oversized_pdf_upload_rejected(async_client: AsyncClient):
    """Test that PDF upload exceeding MAX_UPLOAD_SIZE_MB returns HTTP 413."""
    large_payload = b"%PDF-1.4" + b"\x00" * (6 * 1024 * 1024)
    files = {"file": ("large.pdf", large_payload, "application/pdf")}
    response = await async_client.post("/api/v1/ocr/pdf", files=files)

    assert response.status_code == 413
    data = response.json()
    assert_unified_error_contract(data)
    assert data["errors"][0]["field"] == "file.size"


@pytest.mark.asyncio
async def test_unsupported_image_magic_bytes(async_client: AsyncClient):
    """Test that file with false PNG extension but text content returns HTTP 415."""
    fake_png = b"This is plain text disguised as a PNG file"
    files = {"file": ("fake.png", fake_png, "image/png")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 415
    data = response.json()
    assert_unified_error_contract(data)
    assert data["errors"][0]["field"] == "file.content_type"


@pytest.mark.asyncio
async def test_unsupported_pdf_magic_bytes(async_client: AsyncClient):
    """Test that non-PDF file sent to /pdf returns HTTP 415."""
    fake_pdf = b"Plain text file"
    files = {"file": ("fake.pdf", fake_pdf, "application/pdf")}
    response = await async_client.post("/api/v1/ocr/pdf", files=files)

    assert response.status_code == 415
    data = response.json()
    assert_unified_error_contract(data)
    assert data["errors"][0]["field"] == "file.content_type"


@pytest.mark.asyncio
async def test_pdf_exceeding_max_pages(async_client: AsyncClient):
    """Test that PDF with more pages than MAX_PDF_PAGES returns HTTP 400."""
    # Test settings have max_pdf_pages=5. Create 6-page document.
    doc = fitz.open()
    for _ in range(6):
        doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("too_many_pages.pdf", pdf_bytes, "application/pdf")}
    response = await async_client.post("/api/v1/ocr/pdf", files=files)

    assert response.status_code == 400
    data = response.json()
    assert_unified_error_contract(data)
    assert data["errors"][0]["field"] == "file.pages"


@pytest.mark.asyncio
async def test_missing_file_validation_error(async_client: AsyncClient):
    """Test that missing required file upload field returns HTTP 422 with unified format."""
    response = await async_client.post("/api/v1/ocr/image", data={})

    assert response.status_code == 422
    data = response.json()
    assert_unified_error_contract(data)
    # Ensure root 'body.' prefix is stripped in field name
    assert data["errors"][0]["field"] == "file"
