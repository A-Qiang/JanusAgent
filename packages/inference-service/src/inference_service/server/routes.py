"""API routes exposed by the Janus inference service."""

from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Health ------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    engine_state: str
    model: str = ""
    endpoint: str | None = None
    error: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    engine = request.app.state.engine
    eng_state = engine.state.name.lower() if engine.state else "unknown"

    try:
        h = await engine.health()
    except RuntimeError as exc:
        return HealthResponse(status="unhealthy", engine_state=eng_state, error=str(exc))

    return HealthResponse(
        status=h.get("status", "unknown"),
        engine_state=eng_state,
        model=engine.model_path,
        endpoint=getattr(engine, "endpoint", None),
    )


# ── Models ------------------------------------------------------------------


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    backend: str


@router.get("/v1/models")
async def list_models(request: Request) -> dict:
    engine = request.app.state.engine
    backend = request.app.state.config.backend
    return {
        "object": "list",
        "data": [ModelInfo(id=engine.model_path, backend=backend).model_dump()],
    }


# ── Chat completions --------------------------------------------------------


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, body: ChatCompletionRequest) -> dict:
    engine = request.app.state.engine
    # Only the transformers engine has a native generate() method;
    # for sglang/vllm the request is proxied to the underlying endpoint.
    if hasattr(engine, "generate") and callable(getattr(engine, "generate")):
        messages = [m.model_dump() for m in body.messages]
        return await engine.generate(messages, temperature=body.temperature, max_new_tokens=body.max_tokens)  # type: ignore[no-any-return]
    msg = "Chat completions are not supported by the current engine backend."
    raise NotImplementedError(msg)


# ── Registration ------------------------------------------------------------


def register_routes(app: FastAPI) -> None:
    app.include_router(router, tags=["management"])
