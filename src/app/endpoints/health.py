"""Handlers for health REST API endpoints.

These endpoints are used to check if service is live and prepared to accept
requests. Note that these endpoints can be accessed using GET or HEAD HTTP
methods. For HEAD HTTP method, just the HTTP response code is used.
"""

import logging
from typing import Any

from fastapi import APIRouter

from models.responses import ReadinessResponse, LivenessResponse, NotAvailableResponse


router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


get_readiness_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Service is ready",
        "model": ReadinessResponse,
    },
    503: {
        "description": "Service is not ready",
        "model": NotAvailableResponse,
    },
}


@router.get("/readiness", responses=get_readiness_responses)
def readiness_probe_get_method() -> ReadinessResponse:
    """Ready status of service."""
    return ReadinessResponse(ready=True, reason="service is ready")


get_liveness_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Service is alive",
        "model": LivenessResponse,
    },
    503: {
        "description": "Service is not alive",
        "model": LivenessResponse,
    },
}


@router.get("/liveness", responses=get_liveness_responses)
def liveness_probe_get_method() -> LivenessResponse:
    """Live status of service."""
    return LivenessResponse(alive=True)
