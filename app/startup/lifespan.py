"""Application lifespan managing model lifecycle and concurrency limits."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import get_settings
from app.core.logger import get_logger, setup_logging
from app.services.model_service import ModelService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown events.

    On startup:
    - Configures structured logging.
    - Instantiates and loads the ModelService singleton into `app.state.model_service`.
    - Sets `app.state.is_ready` based on model load status.
    - Creates `app.state.semaphore` with configured concurrency limit.

    On shutdown:
    - Cleans up model references and resources.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control back to the running FastAPI server.
    """
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Starting Unlimited-OCR microservice in %s mode", settings.environment)

    # Initialize concurrency limiter
    app.state.semaphore = asyncio.Semaphore(settings.max_concurrent_inferences)

    # Initialize model service singleton
    model_service = ModelService(settings)
    app.state.model_service = model_service

    # Load model synchronously in thread to avoid blocking loop on startup
    await asyncio.to_thread(model_service.load)
    app.state.is_ready = model_service.is_ready()

    if app.state.is_ready:
        logger.info(
            "Service is ready to accept OCR requests on device '%s'",
            model_service.device,
        )
    else:
        logger.warning(
            "Service started in unready state. /health/ready will return HTTP 503 "
            "until model weights are properly configured."
        )

    try:
        yield
    finally:
        logger.info("Shutting down Unlimited-OCR microservice")
        app.state.is_ready = False
        app.state.model_service = None
