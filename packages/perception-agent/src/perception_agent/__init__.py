"""perception-agent: 多模感知层 — Multi-modal Perception & Knowledge Ingestion."""

from perception_agent.core.base import BasePerceptor, PerceptionResult
from perception_agent.core.pipeline import PerceptionPipeline

__all__ = [
    "BasePerceptor",
    "PerceptionPipeline",
    "PerceptionResult",
]


def main() -> None:
    """CLI entry point."""
    print("perception-agent: multi-modal perception layer for JanusAgent")
