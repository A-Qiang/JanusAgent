"""FastAPI application factory for the Janus inference service."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from inference_service.engine.base import EngineConfig, ServiceEngine
from inference_service.engine.sglang_engine import SglangEngine
from inference_service.engine.transformers_engine import TransformersEngine
from inference_service.engine.vllm_engine import VllmEngine
from inference_service.server.config import ServiceConfig
from inference_service.server.middleware import register_middleware
from inference_service.server.routes import register_routes

logger = logging.getLogger(__name__)


def create_app(config: ServiceConfig) -> FastAPI:
    """Build a fully-configured FastAPI application.

    The returned app manages an inference engine over its whole lifetime.
    Callers typically hand it to ``uvicorn.run(app)``.
    """
    engine = _build_engine(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "Starting inference service (backend=%s, model=%s) …",
            config.backend,
            config.model_path,
        )
        await engine.start()
        yield
        await engine.stop()

    app = FastAPI(
        title="Janus Inference Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.config = config

    register_middleware(app)
    register_routes(app)

    return app


def _build_engine(config: ServiceConfig) -> ServiceEngine:
    """Instantiate the engine based on *config*."""
    engine_cfg = EngineConfig(
        model_path=config.resolved_model_path,
        dtype=config.dtype,
        max_model_len=config.max_model_len,
        gpu_memory_utilization=config.gpu_memory_utilization,
        seed=config.seed,
    )

    if config.backend == "vllm":
        return VllmEngine(
            engine_cfg,
            base_url=config.vllm_base_url or "http://127.0.0.1:8000",
            api_key=config.vllm_api_key,
        )

    if config.backend == "transformers":
        return TransformersEngine(engine_cfg)

    # Default: SGLang
    return SglangEngine(
        engine_cfg,
        host=config.host,
        port=config.port,
    )
