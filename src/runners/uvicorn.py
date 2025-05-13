"""Uvicorn runner."""

import logging

import uvicorn

logger: logging.Logger = logging.getLogger(__name__)


def start_uvicorn() -> None:
    """Start Uvicorn-based REST API service."""
    logger.info("Starting Uvicorn")

    host = "localhost"
    port = 8080
    workers = 1
    log_level = logging.INFO

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
    )
