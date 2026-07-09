"""Document ingestor — parses PDF, HTML, Markdown, TXT into structured content."""

from __future__ import annotations

from typing import Any

from perception_agent.core.base import BasePerceptor, MediaType, PerceptionResult


class DocumentIngestor(BasePerceptor):
    """Ingest and extract text content from documents.

    Handles: PDF (via PyMuPDF/pdfplumber), HTML, Markdown, plain text.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".md", ".txt", ".rst"}

    async def perceive(self, data: bytes | str, **kwargs: Any) -> PerceptionResult:
        # TODO: implement parsing logic
        _ = data
        return PerceptionResult(
            source=str(data)[:128],
            media_type=MediaType.DOCUMENT,
            content="",
            metadata={"extension_hint": kwargs.get("ext", "")},
        )
