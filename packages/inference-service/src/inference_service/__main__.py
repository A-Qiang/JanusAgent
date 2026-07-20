"""Entry-point: ``python -m inference_service`` or ``inference-service`` CLI."""

from __future__ import annotations

import logging
import sys

import uvicorn

from inference_service.server.app import create_app
from inference_service.server.config import ServiceConfig


def main() -> None:
    config = ServiceConfig()  # type: ignore[call-arg]

    logging.basicConfig(
        level=getattr(logging, config.model_config.get("log_level", "INFO").upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    app = create_app(config)

    uvicorn.run(
        app,
        host=config.host,
        port=config.management_port,
        log_level=config.model_config.get("log_level", "info").lower(),
    )


if __name__ == "__main__":
    main()
