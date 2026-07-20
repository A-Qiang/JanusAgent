"""SGLang backend — wraps sglang.Runtime for sub-process HTTP serving."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any

import httpx

from inference_service.engine.base import EngineConfig, EngineState, ServiceEngine

logger = logging.getLogger(__name__)


class SglangEngine(ServiceEngine):
    """Manages an SGLang SRT server as a subprocess.

    Starts ``sglang.Runtime`` in a child process and proxies the
    OpenAI-compatible HTTP API it exposes.
    """

    _runtime: Any  # sglang.Runtime (lazy import to keep core deps light)
    _http_client: httpx.AsyncClient | None = None
    _endpoint: str | None = None
    _shutdown_event: asyncio.Event | None = None

    def __init__(self, config: EngineConfig, *, host: str = "127.0.0.1", port: int = 0) -> None:
        super().__init__(config)
        self._host = host
        self._port = port or self._pick_free_port()

    # ── Lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        self.state = EngineState.LOADING
        logger.info("Starting SGLang engine for %s …", self.config.model_path)

        loop = asyncio.get_running_loop()
        self._runtime = await loop.run_in_executor(None, self._launch_runtime)

        self._endpoint = self._runtime.url.rstrip("/")
        self._http_client = httpx.AsyncClient(base_url=self._endpoint, timeout=120)
        self._shutdown_event = asyncio.Event()

        self.state = EngineState.READY
        logger.info("SGLang engine ready at %s", self._endpoint)

    def _launch_runtime(self) -> Any:
        """Import sglang and create Runtime (blocking – runs in thread pool)."""
        # Late import so `pip install inference-service` without sglang succeeds.
        from sglang import Runtime  # noqa: PLC0415  # type: ignore[import-untyped]

        kwargs: dict[str, Any] = {
            "model_path": self.config.model_path,
            "host": self._host,
            "port": self._port,
            "dtype": self.config.dtype,
            "mem_fraction_static": self.config.gpu_memory_utilization,
            "seed": self.config.seed,
        }
        if self.config.max_model_len is not None:
            kwargs["max_model_len"] = self.config.max_model_len
        kwargs.update(self.config.extra)

        return Runtime(**kwargs)  # type: ignore[no-any-return]

    async def stop(self) -> None:
        logger.info("Stopping SGLang engine …")
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        if self._runtime is not None:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._runtime.shutdown)
            self._runtime = None
        if self._shutdown_event is not None:
            self._shutdown_event.set()
        self.state = EngineState.SHUTDOWN
        logger.info("SGLang engine stopped.")

    # ── Inference helpers ---------------------------------------------------

    @property
    def endpoint(self) -> str | None:
        return self._endpoint

    @property
    def client(self) -> httpx.AsyncClient:
        assert self._http_client is not None, "engine not started"
        return self._http_client

    async def generate(self, prompt: str, **sampling_params: Any) -> dict[str, Any]:
        resp = await self.client.post(
            "/generate",
            json={"text": prompt, "sampling_params": sampling_params},
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ── Health --------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self.client.get("/health", timeout=5)
            ok = resp.status_code < 500
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            return {"status": "unhealthy", "error": str(exc)}

        return {
            "status": "healthy" if ok else "degraded",
            "model": self.model_path,
            "endpoint": self._endpoint,
        }

    # ── Private helpers -----------------------------------------------------

    @staticmethod
    def _pick_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return int(s.getsockname()[1])

    @property
    def env_vars(self) -> dict[str, str]:
        """Environment variables forwarded to the SGLang sub-process."""
        return dict(os.environ)
