"""Pytest fixtures for offline testing with mocked OCR services."""

import asyncio
import io
from collections.abc import AsyncGenerator

import fitz
import httpx
import pytest
from PIL import Image

from app.config.settings import Settings, get_settings
from app.core.exceptions import InferenceException
from app.main import create_application


class MockModelService:
    """Mock implementation of ModelService for fast offline testing.

    Attributes:
        is_loaded (bool): Simulated loaded status.
        device (str): Simulated hardware device.
        canned_text (str): Pre-configured OCR text output.
    """

    def __init__(
        self,
        is_loaded: bool = True,
        device: str = "cpu",
        canned_text: str = "Mock OCR Extracted Text",
    ) -> None:
        """Initialize MockModelService.

        Args:
            is_loaded (bool): Whether model is ready. Defaults to True.
            device (str): Device name. Defaults to 'cpu'.
            canned_text (str): OCR response text. Defaults to 'Mock OCR Extracted Text'.
        """
        self.is_loaded = is_loaded
        self.device = device
        self.canned_text = canned_text
        self.model = object() if is_loaded else None
        self.tokenizer = object() if is_loaded else None

    def load(self) -> None:
        """Simulate loading model weights."""
        self.is_loaded = True
        self.model = object()
        self.tokenizer = object()

    def is_ready(self) -> bool:
        """Return readiness status."""
        return self.is_loaded and self.model is not None

    def predict_image(self, image: Image.Image) -> str:
        """Simulate image inference."""
        if not self.is_ready():
            raise InferenceException(
                message="OCR model is not loaded or ready for inference",
                status_code=503,
                field="model",
            )
        return self.canned_text

    def predict_images(self, images: list[Image.Image]) -> list[str]:
        """Simulate sequential image inference."""
        return [self.predict_image(img) for img in images]


@pytest.fixture
def mock_model_service() -> MockModelService:
    """Fixture providing a ready MockModelService instance.

    Returns:
        MockModelService: Initialized ready mock service.
    """
    return MockModelService(is_loaded=True)


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing test configuration settings.

    Returns:
        Settings: Test settings with strict limits.
    """
    return Settings(
        environment="testing",
        model_path="models/unlimited-ocr",
        device="cpu",
        max_upload_size_mb=5,
        max_pdf_pages=5,
        max_concurrent_inferences=2,
        pdf_dpi=150,
    )


@pytest.fixture
def app(mock_model_service: MockModelService, test_settings: Settings):
    """Fixture providing a test application with attached mock services.

    Args:
        mock_model_service (MockModelService): Mocked model service.
        test_settings (Settings): Test configuration settings.

    Returns:
        FastAPI: Configured application instance.
    """
    application = create_application()
    application.state.model_service = mock_model_service
    application.state.is_ready = True
    application.state.semaphore = asyncio.Semaphore(test_settings.max_concurrent_inferences)
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


@pytest.fixture
async def async_client(app) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture providing an async HTTP client for endpoint testing.

    Args:
        app (FastAPI): Test FastAPI application.

    Yields:
        httpx.AsyncClient: Configured async client.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate a valid PNG image byte sequence."""
    img = Image.new("RGB", (200, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate a valid JPEG image byte sequence."""
    img = Image.new("RGB", (200, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_webp_bytes() -> bytes:
    """Generate a valid WebP image byte sequence."""
    img = Image.new("RGB", (200, 100), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP")
    return buffer.getvalue()


@pytest.fixture
def sample_multipage_pdf_bytes() -> bytes:
    """Generate a 2-page valid PDF byte sequence using PyMuPDF."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Invoice Number: INV-1024")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Total Amount: INR 12500")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
