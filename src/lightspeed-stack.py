"""Lightspeed stack."""

import logging
from runners.uvicorn import start_uvicorn
from models.config import Configuration
from configuration import configuration

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Lightspeed stack startup")
    configuration.load_configuration("lightspeed-stack.yaml")
    logger.info("Configuration: %s", configuration.configuration)
    logger.info(
        "Llama stack configuration: %s", configuration.llama_stack_configuration
    )
    start_uvicorn()
    logger.info("Lightspeed stack finished")
