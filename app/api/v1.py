"""API version 1 router aggregation."""

from fastapi import APIRouter

from app.api.routes import ocr

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(ocr.router)

__all__ = ["v1_router"]
