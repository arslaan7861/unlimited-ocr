"""Web interface endpoint serving interactive document parsing single-page application."""

from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
INDEX_FILE = TEMPLATES_DIR / "index.html"


@router.get(
    "/",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.get(
    "/ui",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def serve_ui() -> HTMLResponse:
    """Serve the interactive HTML web application for document upload and parsing.

    Returns:
        HTMLResponse: Rendered single-page application HTML.
    """
    if not INDEX_FILE.exists():
        return HTMLResponse(
            content="<h1>UI Template not found</h1>",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    html_content = INDEX_FILE.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
