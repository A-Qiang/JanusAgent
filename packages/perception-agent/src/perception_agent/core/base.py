"""Base abstractions for all perceptors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MediaType(str, Enum):
    """Types of media that a perceptor can handle."""

    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"


@dataclass
class PerceptionResult:
    """Unified result produced by any perceptor."""

    source: str
    media_type: MediaType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source": self.source,
            "media_type": self.media_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "confidence": self.confidence,
        }


class BasePerceptor(ABC):
    """Abstract base for all perceptors.

    Each concrete perceptor implements :meth:`perceive` to transform a
    raw input (bytes | str | file path) into a structured ``PerceptionResult``.
    """

    @abstractmethod
    async def perceive(self, data: bytes | str, **kwargs: Any) -> PerceptionResult:
        """Perceive (analyse / understand) the given input.

        Args:
            data: Raw byte content *or* a string (e.g. file path or text).
            **kwargs: Perceiver-specific options.

        Returns:
            A structured ``PerceptionResult``.
        """
        ...

    async def batch_perceive(
        self,
        inputs: list[bytes | str],
        **kwargs: Any,
    ) -> list[PerceptionResult]:
        """Batch version — subclasses may override for efficiency."""
        return [await self.perceive(d, **kwargs) for d in inputs]
