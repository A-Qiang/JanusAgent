"""Abstract engine interface for model inference backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EngineState(Enum):
    """Lifecycle states of an inference engine."""

    CREATED = auto()
    LOADING = auto()
    READY = auto()
    BUSY = auto()
    DEGRADED = auto()
    SHUTDOWN = auto()
    ERROR = auto()


@dataclass
class EngineConfig:
    """Common configuration shared across engine backends."""

    model_path: str
    dtype: str = "auto"
    max_model_len: int | None = None
    gpu_memory_utilization: float = 0.90
    seed: int = 42
    extra: dict[str, Any] = field(default_factory=dict)


class ServiceEngine(ABC):
    """Abstract inference engine that can be managed by the service layer.

    Subclasses wrap a specific backend (SGLang Runtime, vLLM AsyncLLMEngine, …)
    and expose a uniform lifecycle + inference API.
    """

    def __init__(self, config: EngineConfig) -> None:
        self._config = config
        self._state = EngineState.CREATED

    # ── Lifecycle -----------------------------------------------------------

    @abstractmethod
    async def start(self) -> None:
        """Start the engine (download model, allocate GPU memory, warm up)."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the engine and free resources."""

    @property
    def state(self) -> EngineState:
        return self._state

    @state.setter
    def state(self, value: EngineState) -> None:
        self._state = value

    @property
    def config(self) -> EngineConfig:
        return self._config

    # ── Health --------------------------------------------------------------

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return a snapshot of engine health & metrics."""

    # ── Convenience ---------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._state is EngineState.READY

    @property
    def model_path(self) -> str:
        return self._config.model_path
