"""Tests for the interactive web UI endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ui_root_endpoint(async_client: AsyncClient):
    """Test GET / serves the interactive single-page HTML interface."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Unlimited-OCR & LLM Parser" in response.text
    assert "dropzone" in response.text


@pytest.mark.asyncio
async def test_ui_alias_endpoint(async_client: AsyncClient):
    """Test GET /ui serves the same HTML interface."""
    response = await async_client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
