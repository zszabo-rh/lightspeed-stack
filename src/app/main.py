"""Definition of FastAPI based web service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from app import routers

import version
from log import get_logger
from configuration import configuration
from utils.common import register_mcp_servers

logger = get_logger(__name__)

logger.info("Initializing app")

service_name = configuration.configuration.name


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle app lifespan events."""
    # Startup
    logger.info("Starting up: registering MCP servers")
    register_mcp_servers(logger, configuration.configuration)
    logger.info("Including routers")
    routers.include_routers(fastapi_app)

    # Setup logger for handlers
    get_logger("app.endpoints.handlers")

    yield

    # Shutdown (if needed)
    logger.info("Shutting down")


app = FastAPI(
    title=f"{service_name} service - OpenAPI",
    description=f"{service_name} service API specification.",
    version=version.__version__,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    lifespan=lifespan,
)
