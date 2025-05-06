"""Handler for the / endpoint."""

import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["root"])


@router.get("/", response_class=HTMLResponse)
def root_endpoint_handler(request: Request) -> HTMLResponse:
    return "<html>foo</html>"
