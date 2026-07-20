"""Native Transformers engine — loads models directly via transformers for custom architectures."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from inference_service.engine.base import EngineConfig, EngineState, ServiceEngine

logger = logging.getLogger(__name__)


class TransformersEngine(ServiceEngine):
    """Loads and runs a model directly via ``transformers``.

    Designed for custom model architectures (e.g. MiMoV2) that are not
    supported by SGLang / vLLM but ship their own modeling code and can
    be loaded with ``trust_remote_code=True``.
    """

    _model: Any = None
    _tokenizer: Any = None
    _device: str = "cuda"

    def __init__(self, config: EngineConfig, **kwargs: Any) -> None:
        super().__init__(config)
        self._device = kwargs.pop("device", "cuda")
        self._extra_kwargs = kwargs

    # ── Lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        self.state = EngineState.LOADING
        logger.info("Loading model %s with transformers …", self.config.model_path)

        loop = asyncio.get_running_loop()

        self._tokenizer = await loop.run_in_executor(
            None,
            lambda: AutoTokenizer.from_pretrained(
                self.config.model_path,
                trust_remote_code=True,
            ),
        )

        self._model = await loop.run_in_executor(
            None,
            self._load_model,
        )

        self.state = EngineState.READY
        logger.info("Transformers engine ready — model=%s device=%s", self.config.model_path, self._device)

    def _load_model(self) -> Any:
        kwargs: dict[str, Any] = {
            "trust_remote_code": True,
            "torch_dtype": self.config.dtype if self.config.dtype != "auto" else "auto",
        }

        # Determine device map for multi-GPU
        gpu_count = torch.cuda.device_count()
        if gpu_count > 1:
            kwargs["device_map"] = "auto"
        else:
            kwargs["device_map"] = self._device if torch.cuda.is_available() else "cpu"

        if self.config.gpu_memory_utilization < 1.0:
            for i in range(gpu_count):
                free = torch.cuda.mem_get_info(i)[0]
                total = torch.cuda.get_device_properties(i).total_memory
                frac = self.config.gpu_memory_utilization
                torch.cuda.set_per_process_memory_fraction(frac, i)
                logger.info("GPU %d: set memory fraction to %.0f%% (%s / %s)", i, frac * 100,
                            _format_bytes(int(free * frac)), _format_bytes(total))

        if self.config.max_model_len is not None:
            kwargs["max_position_embeddings"] = self.config.max_model_len

        kwargs.update(self.config.extra)

        model = AutoModelForCausalLM.from_pretrained(
            self.config.model_path,
            **kwargs,
        )
        model.eval()
        return model

    async def stop(self) -> None:
        logger.info("Stopping Transformers engine …")
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.state = EngineState.SHUTDOWN
        logger.info("Transformers engine stopped.")

    # ── Health --------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        if self._model is None or self.state != EngineState.READY:
            return {"status": "not_ready", "model": self.config.model_path}

        gpu_info: dict[str, Any] = {}
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                free, total = torch.cuda.mem_get_info(i)
                gpu_info[f"gpu_{i}"] = {
                    "name": torch.cuda.get_device_properties(i).name,
                    "free_bytes": free,
                    "total_bytes": total,
                    "used_percent": round((1 - free / total) * 100, 1),
                }

        return {
            "status": "healthy",
            "model": self.config.model_path,
            "state": "transformers",
            "gpus": gpu_info,
        }

    # ── Inference -----------------------------------------------------------

    @property
    def model(self) -> Any:
        assert self._model is not None, "engine not started"
        return self._model

    @property
    def tokenizer(self) -> Any:
        assert self._tokenizer is not None, "engine not started"
        return self._tokenizer

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_new_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()

        inputs = await loop.run_in_executor(
            None,
            lambda: self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            ),
        )

        inputs = {k: v.to(self._model.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}

        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            **kwargs,
        }

        with torch.no_grad():
            outputs = await loop.run_in_executor(
                None,
                lambda: self._model.generate(**inputs, **gen_kwargs),
            )

        input_len = inputs["input_ids"].shape[1]
        generated = outputs[0][input_len:]
        text = self.tokenizer.decode(generated, skip_special_tokens=True)

        return {
            "id": "chatcmpl-transformers",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": input_len,
                "completion_tokens": len(generated),
                "total_tokens": input_len + len(generated),
            },
        }


def _format_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"
