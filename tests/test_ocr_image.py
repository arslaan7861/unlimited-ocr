"""Tests for image OCR endpoint."""

import pytest
from httpx import AsyncClient

from tests.conftest import MockModelService


@pytest.mark.asyncio
async def test_ocr_image_png(async_client: AsyncClient, sample_png_bytes: bytes):
    """Test OCR extraction on valid PNG upload."""
    files = {"file": ("document.png", sample_png_bytes, "image/png")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "document.png"
    assert data["text"] == "Mock OCR Extracted Text"
    assert data["processing_time_seconds"] >= 0.0
    assert data["metadata"]["format"] == "PNG"
    assert data["metadata"]["width"] == 200
    assert data["metadata"]["height"] == 100
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_ocr_image_jpeg(async_client: AsyncClient, sample_jpeg_bytes: bytes):
    """Test OCR extraction on valid JPEG upload."""
    files = {"file": ("scan.jpg", sample_jpeg_bytes, "image/jpeg")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "scan.jpg"
    assert data["metadata"]["format"] == "JPEG"


@pytest.mark.asyncio
async def test_ocr_image_webp(async_client: AsyncClient, sample_webp_bytes: bytes):
    """Test OCR extraction on valid WebP upload."""
    files = {"file": ("receipt.webp", sample_webp_bytes, "image/webp")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "receipt.webp"
    assert data["metadata"]["format"] == "WEBP"


@pytest.mark.asyncio
async def test_ocr_image_model_unready(app, async_client: AsyncClient, sample_png_bytes: bytes):
    """Test image OCR returns HTTP 503 when model is not ready."""
    app.state.is_ready = False
    app.state.model_service = MockModelService(is_loaded=False)

    files = {"file": ("document.png", sample_png_bytes, "image/png")}
    response = await async_client.post("/api/v1/ocr/image", files=files)

    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0
    assert data["errors"][0]["field"] == "model"
