"""Standalone serving script for MiMo-V2.5 model via transformers + FastAPI."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from typing import Any

import torch
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import gc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("serve_mimo")

app = FastAPI(title="MiMo-V2 Inference", version="0.1.0")


# ── State -------------------------------------------------------------------

class ModelState:
    model: Any = None
    tokenizer: Any = None
    model_path: str = ""
    device: str = "cuda"


state = ModelState()


# ── API Models --------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    model: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


# ── Routes ------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    if state.model is None:
        return HealthResponse(status="loading", model=state.model_path)

    gpu_info = []
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(i)
            gpu_info.append({
                "gpu": i,
                "name": torch.cuda.get_device_properties(i).name,
                "free_gb": round(free / 1e9, 1),
                "total_gb": round(total / 1e9, 1),
                "used_pct": round((1 - free / total) * 100, 1),
            })

    return HealthResponse(status="healthy", model=state.model_path)


@app.get("/v1/models")
async def list_models() -> dict:
    return {
        "object": "list",
        "data": [{"id": state.model_path, "object": "model", "backend": "transformers"}],
    }


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest) -> dict:
    if state.model is None:
        return {"error": "Model not loaded yet", "status": "loading"}

    loop = asyncio.get_running_loop()

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    inputs = await loop.run_in_executor(
        None,
        lambda: state.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ),
    )

    device = next(state.model.parameters()).device
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    gen_kwargs = {
        "max_new_tokens": body.max_tokens,
        "temperature": body.temperature,
        "do_sample": body.temperature > 0,
        "pad_token_id": state.tokenizer.pad_token_id or state.tokenizer.eos_token_id,
    }

    with torch.no_grad():
        outputs = await loop.run_in_executor(
            None,
            lambda: state.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **gen_kwargs,
            ),
        )

    input_len = input_ids.shape[1]
    generated = outputs[0][input_len:]
    text = state.tokenizer.decode(generated, skip_special_tokens=True)

    return {
        "id": "chatcmpl-mimo",
        "object": "chat.completion",
        "created": int(time.time()),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": input_len,
            "completion_tokens": len(generated),
            "total_tokens": input_len + len(generated),
        },
    }


# ── Lifespan ----------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    logger.info("Loading model from %s …", model_path)
    state.model_path = model_path

    loop = asyncio.get_running_loop()

    state.tokenizer = await loop.run_in_executor(
        None,
        lambda: AutoTokenizer.from_pretrained(model_path, trust_remote_code=True),
    )

    load_kwargs: dict[str, Any] = {
        "trust_remote_code": True,
        "torch_dtype": dtype,
    }

    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        load_kwargs["device_map"] = "auto"
        logger.info("Using device_map=auto with %d GPUs", torch.cuda.device_count())
    elif torch.cuda.is_available():
        load_kwargs["device_map"] = "cuda"

    if gpu_memory_fraction < 1.0:
        for i in range(torch.cuda.device_count()):
            torch.cuda.set_per_process_memory_fraction(gpu_memory_fraction, i)

    t0 = time.time()
    logger.info("Starting model load (this will take several minutes) …")
    state.model = await loop.run_in_executor(
        None,
        lambda: AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs),
    )
    state.model.eval()
    elapsed = time.time() - t0
    logger.info("Model loaded in %.1fs", elapsed)

    # Print GPU memory after load
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(i)
            used = total - free
            logger.info("GPU %d: %.1f / %.1f GiB used (%.0f%%)", 
                        i, used / 1e9, total / 1e9, used / total * 100)

    logger.info("Service ready on port %d", port)


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Shutting down …")
    if state.model is not None:
        del state.model
        state.model = None
    if state.tokenizer is not None:
        del state.tokenizer
        state.tokenizer = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ── Entry point -------------------------------------------------------------

parser = argparse.ArgumentParser(description="Serve MiMo-V2.5 via transformers")
parser.add_argument("--model-path", default="/data/models/MiMo-V2.5/")
parser.add_argument("--port", type=int, default=31001)
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--dtype", default="auto")
parser.add_argument("--gpu-memory-fraction", type=float, default=0.95)

args = parser.parse_args()
model_path = args.model_path
port = args.port
dtype = args.dtype
gpu_memory_fraction = args.gpu_memory_fraction

if __name__ == "__main__":
    uvicorn.run(app, host=args.host, port=port, log_level="info")
