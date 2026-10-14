"""Model service encapsulating Baidu Unlimited-OCR lifecycle and inference."""

import logging
import os
import tempfile
from typing import Any

from PIL import Image

from app.config.settings import Settings
from app.core.exceptions import InferenceException

logger = logging.getLogger(__name__)


class ModelService:
    """Manages loading and running inference with Baidu Unlimited-OCR.

    Attributes:
        settings (Settings): Active application configuration.
        device (str): Resolved compute device ('cuda' or 'cpu').
        is_loaded (bool): Indicates if model weights are successfully loaded.
        model (Any): The underlying PyTorch / HuggingFace model instance.
        tokenizer (Any): The associated tokenizer instance.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize ModelService with application settings.

        Args:
            settings (Settings): Application configuration.
        """
        self.settings = settings
        self.device = self._resolve_device(settings.device)
        self.is_loaded = False
        self.model: Any = None
        self.tokenizer: Any = None

    def _resolve_device(self, target_device: str) -> str:
        """Determine optimal compute device based on hardware availability.

        Args:
            target_device (str): Configured target device ('cpu', 'cuda', 'auto').

        Returns:
            str: Resolved device ('cuda' or 'cpu').
        """
        try:
            import torch

            if target_device == "cuda":
                if torch.cuda.is_available():
                    return "cuda"
                logger.warning("CUDA requested but not available; falling back to CPU")
                return "cpu"
            if target_device == "auto":
                return "cuda" if torch.cuda.is_available() else "cpu"
            return "cpu"
        except ImportError:
            return "cpu"

    def load(self) -> None:
        """Load tokenizer and model weights into memory.

        Attempts loading from local directory or Hugging Face repository.
        If loading fails (e.g. missing weights or missing dependencies), logs
        a detailed error and flags service as not ready without raising an unhandled exception.
        """
        model_path = self.settings.model_path
        logger.info(
            "Initializing Baidu Unlimited-OCR model from '%s' on device '%s'",
            model_path,
            self.device,
        )

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            dtype_map = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32,
            }
            torch_dtype = dtype_map.get(
                self.settings.torch_dtype,
                torch.float32 if self.device == "cpu" else torch.bfloat16,
            )

            # Ensure CPU execution doesn't fail with bfloat16 if unsupported
            if self.device == "cpu" and torch_dtype == torch.bfloat16:
                torch_dtype = torch.float32

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
            )

            self.model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                use_safetensors=True,
                torch_dtype=torch_dtype,
            )

            self.model = self.model.eval()
            if self.device == "cuda":
                self.model = self.model.cuda()
            else:
                self.model = self.model.cpu()

            self.is_loaded = True
            logger.info("Baidu Unlimited-OCR successfully loaded on %s", self.device)

        except Exception as exc:
            self.is_loaded = False
            self.model = None
            self.tokenizer = None
            logger.error(
                "Failed to load Unlimited-OCR model from '%s': %s. "
                "Service will start in unready state (HTTP 503 on readiness checks).",
                model_path,
                exc,
                exc_info=True,
            )

    def is_ready(self) -> bool:
        """Check if model is loaded and ready for prediction.

        Returns:
            bool: True if model is initialized and ready, False otherwise.
        """
        return self.is_loaded and self.model is not None and self.tokenizer is not None

    def predict_image(self, image: Image.Image) -> str:
        """Run OCR extraction on a single PIL Image.

        Args:
            image (Image.Image): Input raster image.

        Returns:
            str: Extracted text content.

        Raises:
            InferenceException: If model is not loaded or inference execution fails.
        """
        if not self.is_ready():
            raise InferenceException(
                message="OCR model is not loaded or ready for inference",
                status_code=503,
                field="model",
            )

        temp_file_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_file_path = tmp.name
                image.save(tmp, format="PNG")

            # Call Unlimited-OCR model infer method
            result = self.model.infer(
                self.tokenizer,
                prompt="<image>document parsing.",
                image_file=temp_file_path,
                eval_mode=True,
                base_size=1024,
                image_size=640,
                crop_mode=True,
                max_length=32768,
                no_repeat_ngram_size=35,
                ngram_window=128,
            )

            if result is None:
                return ""

            cleaned = str(result).replace("<｜end▁of▁sentence｜>", "").strip()
            return cleaned

        except Exception as exc:
            if isinstance(exc, InferenceException):
                raise
            logger.error("Inference execution failed on image: %s", exc, exc_info=True)
            raise InferenceException(
                message=f"Model inference failed: {exc}",
                status_code=500,
                field="model.inference",
            ) from exc
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass

    def predict_images(self, images: list[Image.Image]) -> list[str]:
        """Run OCR extraction sequentially across a list of PIL Images.

        Streaming approach to prevent memory ballooning on constrained machines.

        Args:
            images (list[Image.Image]): List of page images.

        Returns:
            list[str]: Extracted text corresponding to each input image.

        Raises:
            InferenceException: If model is not loaded or inference fails.
        """
        results: list[str] = []
        for img in images:
            text = self.predict_image(img)
            results.append(text)
        return results
