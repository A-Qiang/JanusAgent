"""Perception pipeline — compose multiple perceptors into a chain."""

from __future__ import annotations

from typing import Any

from perception_agent.core.base import BasePerceptor, PerceptionResult


class PerceptionPipeline:
    """Orchestrate a sequence of perceptors over the same input.

    Example::

        pipeline = PerceptionPipeline([
            ocr_perceptor,
            layout_analysis_perceptor,
            summary_perceptor,
        ])
        results = await pipeline.run(document_bytes)
    """

    def __init__(self, perceptors: list[BasePerceptor]) -> None:
        self._perceptors = perceptors

    async def run(
        self,
        data: bytes | str,
        **kwargs: Any,
    ) -> list[PerceptionResult]:
        """Feed *data* through every registered perceptor in order.

        Returns one ``PerceptionResult`` per perceptor.
        """
        results: list[PerceptionResult] = []
        for perceptor in self._perceptors:
            result = await perceptor.perceive(data, **kwargs)
            results.append(result)
        return results

    @property
    def perceptors(self) -> list[BasePerceptor]:
        """Read-only view of registered perceptors."""
        return list(self._perceptors)
