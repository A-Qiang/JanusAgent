"""Client SDK for other JanusAgent packages to consume the inference service."""

from __future__ import annotations

from typing import Any

import httpx


class InferenceClient:
    """Async HTTP client for the Janus inference service.

    Usage::

        client = InferenceClient("http://inference-service:31001")
        health = await client.health()
        reply = await client.chat([
            {"role": "user", "content": "Hello!"},
        ])
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:31001",
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

    # ── Lifecycle -----------------------------------------------------------

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> InferenceClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ── Health --------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        resp = await self._client.get("/health")
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ── Chat (OpenAI-compatible) -------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs,
        }
        if model is not None:
            body["model"] = model
        resp = await self._client.post("/v1/chat/completions", json=body)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ── Completions --------------------------------------------------------

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        if model is not None:
            body["model"] = model
        resp = await self._client.post("/v1/completions", json=body)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
