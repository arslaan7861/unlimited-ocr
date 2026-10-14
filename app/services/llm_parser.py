"""LLM document parsing service using OpenRouter for markdown cleanup and JSON structuring."""

import json
import logging
from typing import Any

import httpx

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class LLMDocumentParser:
    """Service to clean up and structure raw OCR text into markdown and JSON entities.

    Attributes:
        settings (Settings): Active application configuration.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize LLMDocumentParser with configuration settings.

        Args:
            settings (Settings): Application configuration instance.
        """
        self.settings = settings

    async def parse_document(
        self,
        raw_text: str,
        document_type: str = "general",
        custom_prompt: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Parse raw OCR text into cleaned Markdown and structured JSON.

        Args:
            raw_text (str): Raw text extracted by Unlimited-OCR.
            document_type (str): Type of document (e.g. 'general', 'invoice', 'receipt', 'table').
            custom_prompt (str | None): Optional specific instructions for extraction.

        Returns:
            tuple[str, dict[str, Any]]: (cleaned_markdown, structured_data_dict).
        """
        if not self.settings.llm_enabled or not self.settings.llm_api_key:
            logger.info("LLM parsing is disabled or unconfigured; returning raw text.")
            return raw_text, {}

        system_instruction = (
            "You are an expert AI document parsing assistant. You are given raw OCR text extracted "
            "from a scanned document or image by Baidu Unlimited-OCR.\n"
            "Your task is to:\n"
            "1. Clean up and format the document text into crisp, readable GitHub-flavored Markdown. "
            "Fix OCR misspellings, restore proper paragraph line-breaks, and format tables accurately.\n"
            "2. Extract structured key-value entities, numbers, dates, organizations, and line items "
            "into a clean JSON structure.\n\n"
            f"Document classification context: {document_type.upper()}\n"
            "You MUST respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "cleaned_markdown": "Full cleaned and formatted markdown representation of the document",\n'
            '  "structured_data": {\n'
            '    "document_type": "' + document_type + '",\n'
            '    "summary": "1-2 sentence summary",\n'
            '    "entities": { ... key fields, totals, dates, names ... },\n'
            '    "tables": [ ... any table data as array of objects ... ]\n'
            "  }\n"
            "}"
        )

        user_content = f"Raw OCR Input:\n```\n{raw_text}\n```"
        if custom_prompt:
            user_content += f"\n\nAdditional User Request:\n{custom_prompt}"

        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "HTTP-Referer": "https://github.com/arslaan7861/unlimited-ocr",
            "X-Title": "Unlimited-OCR Microservice",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "temperature": self.settings.llm_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.warning(
                    "OpenRouter LLM request failed [HTTP %s]: %s",
                    response.status_code,
                    response.text,
                )
                return raw_text, {}

            data = response.json()
            message_content = data["choices"][0]["message"]["content"]
            parsed_result = json.loads(message_content)

            cleaned_markdown = parsed_result.get("cleaned_markdown", raw_text)
            structured_data = parsed_result.get("structured_data", {})
            return cleaned_markdown, structured_data

        except Exception as exc:
            logger.warning(
                "Failed to parse document with LLM (%s); falling back to raw OCR.",
                exc,
                exc_info=True,
            )
            return raw_text, {}
