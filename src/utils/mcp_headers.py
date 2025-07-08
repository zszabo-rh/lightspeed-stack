"""MCP headers handling."""

import json
import logging
from fastapi import Request

logger = logging.getLogger("app.endpoints.dependencies")


async def mcp_headers_dependency(_request: Request) -> dict[str, dict[str, str]]:
    """Get the mcp headers dependency to passed to mcp servers.

    mcp headers is a json dictionary or mcp url paths and their respective headers

    Args:
        request (Request): The FastAPI request object.

    Returns:
        The mcp headers dictionary, or empty dictionary if not found or on json decoding error
    """
    return extract_mcp_headers(_request)


def extract_mcp_headers(request: Request) -> dict[str, dict[str, str]]:
    """Extract mcp headers from MCP-HEADERS header.

    Args:
        request: The FastAPI request object

    Returns:
        The mcp headers dictionary, or empty dictionary if not found or on json decoding error
    """
    mcp_headers_string = request.headers.get("MCP-HEADERS", "")
    mcp_headers = {}
    if mcp_headers_string:
        try:
            mcp_headers = json.loads(mcp_headers_string)
        except json.decoder.JSONDecodeError as e:
            logger.error("MCP headers decode error: %s", e)

        if not isinstance(mcp_headers, dict):
            logger.error(
                "MCP headers wrong type supplied (mcp headers must be a dictionary), "
                "but type %s was supplied",
                type(mcp_headers),
            )
            mcp_headers = {}
    return mcp_headers
