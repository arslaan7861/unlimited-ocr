"""LLM document parsing service using OpenRouter for autonomous markdown reconstruction."""

import logging
import re
from typing import Any

import httpx

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class LLMDocumentParser:
    """Service to understand raw OCR text and reconstruct it into meaningful Markdown.

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
        document_type: str = "auto",
        custom_prompt: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Understand raw OCR text and reconstruct it into meaningful Markdown.

        Args:
            raw_text (str): Raw text extracted by Unlimited-OCR.
            document_type (str): Optional hint or 'auto' for autonomous deduction.
            custom_prompt (str | None): Optional specific instructions for extraction.

        Returns:
            tuple[str, dict[str, Any]]: (cleaned_markdown, empty_dict).
        """
        if not self.settings.llm_enabled or not self.settings.llm_api_key:
            logger.info("LLM parsing is disabled or unconfigured; returning raw text.")
            return raw_text, {}

        system_instruction = (
            "You are an expert AI document understanding and restructuring assistant. You are given "
            "raw OCR text extracted from an image or scanned document by Baidu Unlimited-OCR.\n\n"
            "Your objective:\n"
            "1. Read and understand the text autonomously to deduce the document's type and intent "
            "(e.g. resume, cover letter, invoice, receipt, legal contract, report, article, form, table).\n"
            "2. Strip away any residual OCR noise, bounding box coordinates, or tags "
            "(such as <|det|>...<|/det|> or <|ref|>...<|/ref|>).\n"
            "3. Reconstruct the document into clean, meaningful, highly structured GitHub-Flavored Markdown:\n"
            "   - Establish a logical heading hierarchy (# Title, ## Section, ### Sub-section).\n"
            "   - Reconnect fragmented sentences and broken line breaks naturally.\n"
            "   - Convert tabular data, columnar numbers, and itemized rows into clean, aligned Markdown tables.\n"
            "   - Use clean bullet points or numbered lists where appropriate.\n"
            "   - Emphasize key metadata (names, dates, totals, contact info) with bold formatting or blockquotes.\n"
            "4. Output ONLY the meaningful markdown document itself. Do not wrap your response in an outer "
            "```markdown code block, and do not add conversational pleasantries or preamble."
        )

        user_content = f"Raw OCR Input:\n\n{raw_text}"
        if custom_prompt:
            user_content += f"\n\nUser Focus / Instructions:\n{custom_prompt}"

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
            raw_content = data["choices"][0]["message"]["content"].strip()

            # Strip any outer markdown fences if the model included them
            cleaned_markdown = raw_content
            if cleaned_markdown.startswith("```"):
                cleaned_markdown = re.sub(r"^```(?:markdown)?\s*\n?", "", cleaned_markdown)
                cleaned_markdown = re.sub(r"\n?```$", "", cleaned_markdown).strip()

            return cleaned_markdown, {}

        except Exception as exc:
            logger.warning(
                "Failed to parse document with LLM (%s); falling back to raw OCR.",
                exc,
                exc_info=True,
            )
            return raw_text, {}
