"""Definition of FastAPI based web service."""

from typing import Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route, WebSocketRoute
from app import routers
from app.database import initialize_database, create_tables
from configuration import configuration
from log import get_logger
from models.config import CORSConfiguration
import metrics
from utils.common import register_mcp_servers_async
import version

logger = get_logger(__name__)

logger.info("Initializing app")

# Use a default service name when configuration is not available
def get_service_name():
    """Get service name with fallback for when configuration is not loaded."""
    try:
        return configuration.configuration.name
    except (AttributeError, ImportError, Exception):
        return "lightspeed-stack"  # Fallback name

service_name = get_service_name()


app = FastAPI(
    title=f"{service_name} service - OpenAPI",
    summary=f"{service_name} service API specification.",
    description=f"{service_name} service API specification.",
    version=version.__version__,
    contact={
        "name": "Pavel Tisnovsky",
        "url": "https://github.com/tisnik/",
        "email": "ptisnovs@redhat.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    servers=[
        {"url": "http://localhost:8080/", "description": "Locally running service"}
    ],
)

def get_cors_config():
    """Get CORS configuration with fallback defaults."""
    try:
        return configuration.service_configuration.cors
    except (AttributeError, ImportError, Exception):
        # Fallback CORS configuration for minimal mode
        return CORSConfiguration()

# Initialize CORS configuration
cors = get_cors_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors.allow_origins,
    allow_credentials=cors.allow_credentials,
    allow_methods=cors.allow_methods,
    allow_headers=cors.allow_headers,
)


@app.middleware("")
async def rest_api_metrics(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware with REST API counter update logic."""
    path = request.url.path
    logger.debug("Received request for path: %s", path)

    # ignore paths that are not part of the app routes
    if path not in app_routes_paths:
        return await call_next(request)

    logger.debug("Processing API request for path: %s", path)

    # measure time to handle duration + update histogram
    with metrics.response_duration_seconds.labels(path).time():
        response = await call_next(request)

    # ignore /metrics endpoint that will be called periodically
    if not path.endswith("/metrics"):
        # just update metrics
        metrics.rest_api_calls_total.labels(path, response.status_code).inc()
    return response


logger.info("Including routers")
routers.include_routers(app)

app_routes_paths = [
    route.path
    for route in app.routes
    if isinstance(route, (Mount, Route, WebSocketRoute))
]


@app.on_event("startup")
async def startup_event() -> None:
    """Perform setup on service startup and track initialization state."""
    # Import app_state here to avoid circular imports
    from app.endpoints.health import app_state
    
    try:
        logger.info("Registering MCP servers")
        # Try to access configuration for MCP servers
        try:
            config = configuration.configuration
            await register_mcp_servers_async(logger, config)
            app_state.mark_check_complete('mcp_servers_registered', True)
        except (AttributeError, ImportError, ValueError) as config_error:
            # Configuration not available - skip MCP server registration
            logger.info("Skipping MCP server registration - configuration not available")
            app_state.mark_check_complete('mcp_servers_registered', False, f"Configuration not available: {str(config_error)}")
        
        get_logger("app.endpoints.handlers")
        logger.info("App startup complete")

        initialize_database()
        create_tables()
        
        # Mark full initialization complete
        app_state.mark_initialization_complete()
        logger.info("Application fully initialized and ready to accept traffic")
        
    except Exception as e:
        error_msg = f"Startup event failed: {str(e)}"
        logger.error(error_msg)
        app_state.mark_check_complete('mcp_servers_registered', False, error_msg)
