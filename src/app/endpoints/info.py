"""Handler for REST API call to provide info."""

import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["info"])


@router.get("/info")
def info_endpoint_handler(request: Request) -> dict:
    return {
        "foo": 1,
        "bar": 2,
    }
