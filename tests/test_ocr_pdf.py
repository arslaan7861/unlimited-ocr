"""Tests for scanned PDF OCR endpoint."""

import pytest
from httpx import AsyncClient

from tests.conftest import MockModelService


@pytest.mark.asyncio
async def test_ocr_pdf_multipage(async_client: AsyncClient, sample_multipage_pdf_bytes: bytes):
    """Test OCR extraction on valid 2-page PDF document."""
    files = {"file": ("invoice.pdf", sample_multipage_pdf_bytes, "application/pdf")}
    response = await async_client.post("/api/v1/ocr/pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "invoice.pdf"
    assert data["page_count"] == 2
    assert len(data["pages"]) == 2
    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][1]["page_number"] == 2
    assert "Mock OCR Extracted Text" in data["text"]
    assert data["processing_time_seconds"] >= 0.0
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_ocr_pdf_model_unready(
    app, async_client: AsyncClient, sample_multipage_pdf_bytes: bytes
):
    """Test PDF OCR returns HTTP 503 when model is not ready."""
    app.state.is_ready = False
    app.state.model_service = MockModelService(is_loaded=False)

    files = {"file": ("invoice.pdf", sample_multipage_pdf_bytes, "application/pdf")}
    response = await async_client.post("/api/v1/ocr/pdf", files=files)

    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0
    assert data["errors"][0]["field"] == "model"
