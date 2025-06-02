"""Definition of FastAPI based web service."""

from fastapi import FastAPI
from app import routers
import version
from log import get_logger


logger = get_logger(__name__)


logger.info("Initializing app")

app = FastAPI(
    title="Lightspeed-core service - OpenAPI",
    description="Lightspeed-core service API specification.",
    version=version.__version__,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

logger.info("Including routers")
routers.include_routers(app)


@app.on_event("startup")
async def startup_event() -> None:
    """Perform logger setup on service startup."""
    get_logger("app.endpoints.handlers")
