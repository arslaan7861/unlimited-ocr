"""Tests for health and readiness probes."""

import pytest
from httpx import AsyncClient

from tests.conftest import MockModelService


@pytest.mark.asyncio
async def test_health_endpoint_model_loaded(async_client: AsyncClient):
    """Test /health returns healthy status when model is loaded."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["device"] == "cpu"


@pytest.mark.asyncio
async def test_health_endpoint_model_not_loaded(app, async_client: AsyncClient):
    """Test /health returns model_loaded=false when model is not initialized."""
    app.state.model_service = MockModelService(is_loaded=False)
    app.state.is_ready = False

    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is False


@pytest.mark.asyncio
async def test_readiness_endpoint_ready(async_client: AsyncClient):
    """Test /health/ready returns HTTP 200 when service is ready."""
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True


@pytest.mark.asyncio
async def test_readiness_endpoint_not_ready(app, async_client: AsyncClient):
    """Test /health/ready returns HTTP 503 when service is not initialized."""
    app.state.is_ready = False
    app.state.model_service = MockModelService(is_loaded=False)

    response = await async_client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert "not ready" in data["message"].lower()
    assert len(data["errors"]) > 0
    assert data["errors"][0]["field"] == "model"
