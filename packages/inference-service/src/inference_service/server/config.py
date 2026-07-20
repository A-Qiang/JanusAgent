"""Top-level service configuration, parsed from CLI / env / file."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings, cli_parse_args=True):
    """Configuration for the inference service.

    Priority: CLI flags > environment variables > defaults.
    """

    # ── Backend selection --------------------------------------------------
    backend: Literal["sglang", "vllm", "transformers"] = Field(
        default="sglang",
        alias="backend",
        description="Inference engine backend (sglang | vllm | transformers).",
    )

    # ── Model --------------------------------------------------------------
    model_path: str = Field(
        default="",
        description="HuggingFace model ID or local path.",
    )
    dtype: str = Field(default="auto", description="Model weight dtype.")
    max_model_len: int | None = Field(
        default=None,
        description="Maximum sequence length (backend default if unset).",
    )
    gpu_memory_utilization: float = Field(
        default=0.90,
        ge=0.1,
        le=1.0,
        description="Fraction of GPU memory to reserve for the model.",
    )
    seed: int = Field(default=42, description="Random seed for reproducibility.")

    # ── Networking ---------------------------------------------------------
    host: str = Field(default="0.0.0.0", description="Bind address.")  # noqa: S104
    port: int = Field(default=30001, ge=1024, le=65535, description="Bind port.")
    management_port: int = Field(
        default=31001,
        ge=1024,
        le=65535,
        description="Port for the Janus management API.",
    )

    # ── vLLM proxy --------------------------------------------------------
    vllm_base_url: str | None = Field(
        default=None,
        description="Remote vLLM server URL (only used when backend=vllm).",
    )
    vllm_api_key: str | None = Field(
        default=None,
        description="API key for the remote vLLM server.",
    )

    # ── Docker / convenience ----------------------------------------------
    model_download_dir: str | None = Field(
        default=None,
        description="Local directory to cache downloaded models.",
    )

    model_config = {"env_prefix": "INFERENCE_"}

    @property
    def resolved_model_path(self) -> str:
        if self.model_path:
            return self.model_path
        msg = "--model-path (or INFERENCE_MODEL_PATH env) is required unless started via the OEM image with a baked-in model."
        raise ValueError(msg)
