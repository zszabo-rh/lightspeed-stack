"""REST API routers."""

from fastapi import FastAPI

from app.endpoints import (
    info,
)


def include_routers(app: FastAPI) -> None:
    """Include FastAPI routers for different endpoints.

    Args:
        app: The `FastAPI` app instance.
    """
    app.include_router(info.router, prefix="/v1")
