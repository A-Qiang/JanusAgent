"""Router that picks the right engine backend based on config."""

from __future__ import annotations

from typing import Literal

from inference_service.engine.base import EngineConfig, ServiceEngine
from inference_service.engine.sglang_engine import SglangEngine
from inference_service.engine.transformers_engine import TransformersEngine
from inference_service.engine.vllm_engine import VllmEngine

BackendType = Literal["sglang", "vllm", "transformers"]


def create_engine(
    backend: BackendType,
    config: EngineConfig,
    **kwargs: object,
) -> ServiceEngine:
    """Factory — instantiate an engine for *backend*.

    Extra keyword arguments are forwarded to the engine constructor.
    """
    match backend:
        case "sglang":
            return SglangEngine(config, **kwargs)  # type: ignore[arg-type]
        case "vllm":
            return VllmEngine(config, **kwargs)  # type: ignore[arg-type]
        case "transformers":
            return TransformersEngine(config, **kwargs)  # type: ignore[arg-type]
        case _:
            msg = f"Unknown backend: {backend!r} (expected sglang | vllm | transformers)"
            raise ValueError(msg)
