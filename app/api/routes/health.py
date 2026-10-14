"""Health and readiness check endpoints."""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service liveness and model status",
)
async def check_health(request: Request) -> HealthResponse:
    """Check service liveness and current model load status.

    Args:
        request (Request): Active HTTP request to access application state.

    Returns:
        HealthResponse: Status including model loaded flag and compute device.
    """
    model_service = getattr(request.app.state, "model_service", None)
    is_loaded = bool(model_service and model_service.is_loaded)
    device = getattr(model_service, "device", "unknown") if model_service else "unknown"

    return HealthResponse(
        status="healthy",
        model_loaded=is_loaded,
        device=device,
    )


@router.get(
    "/health/ready",
    summary="Readiness probe for upstream pipelines",
)
async def check_readiness(request: Request) -> JSONResponse:
    """Readiness probe indicating whether model is ready for inference.

    Args:
        request (Request): Active HTTP request to access application state.

    Returns:
        JSONResponse: HTTP 200 if ready, HTTP 503 if not ready.
    """
    is_ready = getattr(request.app.state, "is_ready", False)
    model_service = getattr(request.app.state, "model_service", None)

    if is_ready and model_service and model_service.is_ready():
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "model_loaded": True},
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "Service is not ready to process OCR requests",
            "errors": [
                {
                    "field": "model",
                    "message": "Unlimited-OCR model weights are not loaded or initialized",
                }
            ],
        },
    )
