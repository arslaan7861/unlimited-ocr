"""Main FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, ui
from app.api.v1 import v1_router
from app.config.settings import get_settings
from app.core.error_handlers import register_error_handlers
from app.middlewares.request_id import RequestIdMiddleware
from app.startup.lifespan import lifespan


def create_application() -> FastAPI:
    """Create and configure the FastAPI microservice instance.

    Returns:
        FastAPI: Fully configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Baidu Unlimited-OCR Microservice",
        description="Production-ready OCR microservice powered by Baidu Unlimited-OCR",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request Correlation ID Middleware
    app.add_middleware(RequestIdMiddleware)

    # 3. Standardized Error Handlers
    register_error_handlers(app)

    # 4. Include Routers
    app.include_router(ui.router)
    app.include_router(health.router)
    app.include_router(v1_router)

    return app


app = create_application()
