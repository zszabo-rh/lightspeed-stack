"""Handler for REST API call to provide answer to query."""

import logging
from typing import Any

from fastapi import APIRouter, Request

from models.responses import QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["models"])


query_response: dict[int | str, dict[str, Any]] = {
    200: {
        "query": "User query",
        "answer": "LLM ansert",
    },
}


@router.get("/query", responses=query_response)
def info_endpoint_handler(request: Request) -> QueryResponse:
    return QueryResponse(query="foo", response="bar")
