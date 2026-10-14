"""Application startup and lifecycle routines."""

from app.startup.lifespan import lifespan

__all__ = ["lifespan"]
