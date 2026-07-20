"""vLLM backend — connects to an existing vLLM server via its OpenAI-compatible API.

This engine operates in **proxy mode**: it assumes a vLLM server is already
running (or will be started externally) and communicates through HTTP.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from inference_service.engine.base import EngineConfig, EngineState, ServiceEngine

logger = logging.getLogger(__name__)


class VllmEngine(ServiceEngine):
    """Proxies inference requests to a remote vLLM server.

    The vLLM server must already expose an OpenAI-compatible ``/v1/*`` API.
    """

    def __init__(
        self,
        config: EngineConfig,
        *,
        base_url: str = "http://127.0.0.1:8000",
        api_key: str | None = None,
    ) -> None:
        super().__init__(config)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._http_client: httpx.AsyncClient | None = None

    # ── Lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        self.state = EngineState.LOADING
        logger.info("Connecting to vLLM server at %s …", self._base_url)

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        self._http_client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=120,
        )

        # Verify the server is alive.
        await self._ping_or_raise()
        self.state = EngineState.READY
        logger.info("vLLM engine ready at %s", self._base_url)

    async def stop(self) -> None:
        logger.info("Stopping vLLM proxy engine …")
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        self.state = EngineState.SHUTDOWN
        logger.info("vLLM proxy engine stopped.")

    # ── Health --------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        try:
            ok_payload = await self._get_json("/health", timeout=5)
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            return {"status": "unhealthy", "error": str(exc)}
        else:
            return {"status": "healthy", "model": self.model_path, **ok_payload}

    # ── Internal ------------------------------------------------------------

    async def _ping_or_raise(self) -> None:
        resp = await self._http_client.get("/health", timeout=10)  # type: ignore[union-attr]
        if resp.status_code >= 500:
            msg = f"vLLM server at {self._base_url} returned {resp.status_code}"
            raise RuntimeError(msg)
        payload = resp.json()
        logger.debug("vLLM health response: %s", payload)

    async def _get_json(self, path: str, request_timeout: int = 30) -> Any:
        resp = await self._http_client.get(path, timeout=request_timeout)  # type: ignore[union-attr]
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
