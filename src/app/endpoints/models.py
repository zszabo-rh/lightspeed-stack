"""Handler for REST API call to provide info."""

import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, Request
from llama_stack_client import Agent, AgentEventLogger, RAGDocument, LlamaStackClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["models"])


@router.get("/models")
def models_endpoint_handler(request: Request) -> list[dict]:
    client = LlamaStackClient(base_url="http://localhost:8321")
    models = client.models.list()
    return [dict(m) for m in models]
