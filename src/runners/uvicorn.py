"""Uvicorn runner."""

import logging

import uvicorn

from models.config import ServiceConfiguration

logger: logging.Logger = logging.getLogger(__name__)


def start_uvicorn(configuration: ServiceConfiguration) -> None:
    """Start Uvicorn-based REST API service."""
    logger.info("Starting Uvicorn")

    log_level = logging.INFO

    uvicorn.run(
        "app.main:app",
        host=configuration.host,
        port=configuration.port,
        workers=configuration.workers,
        log_level=log_level,
        use_colors=True,
        access_log=True,
    )
