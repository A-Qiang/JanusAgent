"""Ingestion providers — concrete perceptors for each media type."""

from perception_agent.ingestors.audio import AudioIngestor
from perception_agent.ingestors.document import DocumentIngestor
from perception_agent.ingestors.image import ImageIngestor
from perception_agent.ingestors.video import VideoIngestor

__all__ = [
    "AudioIngestor",
    "DocumentIngestor",
    "ImageIngestor",
    "VideoIngestor",
]
