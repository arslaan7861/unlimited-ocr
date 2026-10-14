"""Tests for the LLM document parser and structured endpoints."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient

from app.config.settings import Settings
from app.services.llm_parser import LLMDocumentParser


def test_clean_ocr_tags():
    """Test stripping Baidu Unlimited-OCR layout grounding tags."""
    from app.services.model_service import clean_ocr_tags

    raw_output = (
        "<|det|>title [117, 106, 250, 122]<|/det|>Arslaan Ansari "
        "<|det|>text [116, 128, 692, 146]<|/det|>Najibabad, India | +91-8273553959\n"
        "<|ref|>Ref text<|/ref|><｜end of sentence｜>"
    )
    cleaned = clean_ocr_tags(raw_output)
    assert "<|det|>" not in cleaned
    assert "[117, 106, 250, 122]" not in cleaned
    assert "<|ref|>" not in cleaned
    assert "Arslaan Ansari" in cleaned
    assert "Najibabad, India" in cleaned


@pytest.mark.asyncio
async def test_llm_parser_success(test_settings: Settings):
    """Test LLM document parser successfully processes raw text with mocked API."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": "# Invoice Document\n\n| Item | Cost |\n|---|---|\n| Service | $500 |\n\n**Total Due:** $500"
                }
            }
        ]
    }

    parser = LLMDocumentParser(test_settings)

    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json = lambda: mock_payload

    with patch("app.services.llm_parser.httpx.AsyncClient.post", return_value=mock_resp):
        cleaned_md, structured = await parser.parse_document(
            raw_text="INVOICE Total $500", document_type="auto"
        )

    assert "# Invoice Document" in cleaned_md
    assert "| Item | Cost |" in cleaned_md
    assert structured == {}


@pytest.mark.asyncio
async def test_llm_parser_fallback_on_api_error(test_settings: Settings):
    """Test LLM document parser gracefully falls back to raw text if API fails."""
    parser = LLMDocumentParser(test_settings)

    with patch(
        "app.services.llm_parser.httpx.AsyncClient.post",
        side_effect=httpx.ConnectError("Connection failed"),
    ):
        cleaned_md, structured = await parser.parse_document(
            raw_text="Raw OCR Content", document_type="general"
        )

    assert cleaned_md == "Raw OCR Content"
    assert structured == {}


@pytest.mark.asyncio
async def test_image_parse_endpoint(async_client: AsyncClient, sample_png_bytes: bytes):
    """Test POST /api/v1/ocr/image/parse returns structured response."""
    files = {"file": ("test.png", sample_png_bytes, "image/png")}
    data = {"document_type": "receipt", "custom_prompt": "Extract amount"}

    with patch(
        "app.services.llm_parser.LLMDocumentParser.parse_document",
        new_callable=AsyncMock,
        return_value=("### Clean Document", {"type": "receipt", "amount": 100}),
    ):
        response = await async_client.post("/api/v1/ocr/image/parse", files=files, data=data)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["document_type"] == "receipt"
    assert "Clean Document" in res_data["cleaned_markdown"]
    assert res_data["structured_data"]["amount"] == 100
    assert res_data["total_time_seconds"] >= 0.0


@pytest.mark.asyncio
async def test_pdf_parse_endpoint(async_client: AsyncClient, sample_multipage_pdf_bytes: bytes):
    """Test POST /api/v1/ocr/pdf/parse returns structured response."""
    files = {"file": ("test.pdf", sample_multipage_pdf_bytes, "application/pdf")}
    data = {"document_type": "invoice"}

    with patch(
        "app.services.llm_parser.LLMDocumentParser.parse_document",
        new_callable=AsyncMock,
        return_value=(
            "### Invoice Document\nInvoice: INV-1024",
            {"invoice_number": "INV-1024"},
        ),
    ):
        response = await async_client.post("/api/v1/ocr/pdf/parse", files=files, data=data)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["structured_data"]["invoice_number"] == "INV-1024"
    assert res_data["metadata"]["page_count"] == 2
