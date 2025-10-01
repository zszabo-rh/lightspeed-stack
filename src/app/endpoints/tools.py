"""Handler for REST API call to list available tools from MCP servers."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends
from llama_stack_client import APIConnectionError

from authentication import get_auth_dependency
from authentication.interface import AuthTuple
from authorization.middleware import authorize
from client import AsyncLlamaStackClientHolder
from configuration import configuration
from models.config import Action
from models.responses import ToolsResponse
from utils.endpoints import check_configuration_loaded
from utils.tool_formatter import format_tools_list

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tools"])


tools_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "tools": [
                        {
                            "identifier": "filesystem_read",
                            "description": "Read contents of a file from the filesystem",
                            "parameters": [
                                {
                                    "name": "path",
                                    "description": "Path to the file to read",
                                    "parameter_type": "string",
                                    "required": True
                                }
                            ],
                            "provider_id": "model-context-protocol",
                            "toolgroup_id": "filesystem-tools",
                            "server_source": "http://localhost:3000",
                            "type": "tool",
                            "metadata": {}
                        }
                    ]
                }
            }
        }
    },
    500: {"description": "Connection to Llama Stack is broken or MCP server error"},
}


@router.get("/tools", responses=tools_responses)
@authorize(Action.GET_TOOLS)
async def tools_endpoint_handler(
    request: Request,
    auth: Annotated[AuthTuple, Depends(get_auth_dependency())],
) -> ToolsResponse:
    """
    Handle requests to the /tools endpoint.

    Process GET requests to the /tools endpoint, returning a consolidated list of 
    available tools from all configured MCP servers.

    Raises:
        HTTPException: If unable to connect to the Llama Stack server or if
        tool retrieval fails for any reason.

    Returns:
        ToolsResponse: An object containing the consolidated list of available tools
        with metadata including tool name, description, parameters, and server source.
    """
    # Used only by the middleware
    _ = auth

    # Nothing interesting in the request
    _ = request

    check_configuration_loaded(configuration)

    try:
        # Get Llama Stack client
        client = AsyncLlamaStackClientHolder().get_client()
        
        consolidated_tools = []
        
        # First, get built-in tools from Llama Stack (like RAG tools)
        try:
            logger.debug("Retrieving built-in tools from Llama Stack")
            # Get all available toolgroups
            toolgroups_response = await client.toolgroups.list()
            
            for toolgroup in toolgroups_response:
                try:
                    # Get tools for each toolgroup
                    tools_response = await client.tools.list(toolgroup_id=toolgroup.identifier)
                    
                    # Convert tools to dict format
                    for tool in tools_response:
                        tool_dict = dict(tool)
                        # Add source information for built-in tools
                        tool_dict["server_source"] = "builtin"
                        consolidated_tools.append(tool_dict)
                        
                    logger.debug(
                        "Retrieved %d tools from built-in toolgroup %s", 
                        len(tools_response), 
                        toolgroup.identifier
                    )
                    
                except Exception as e:
                    logger.warning(
                        "Failed to retrieve tools from toolgroup %s: %s", 
                        toolgroup.identifier, 
                        e
                    )
                    continue
                    
        except Exception as e:
            logger.warning("Failed to retrieve built-in tools: %s", e)
        
        # Then, iterate through each configured MCP server (if any)
        if configuration.mcp_servers:
            for mcp_server in configuration.mcp_servers:
                try:
                    logger.debug("Retrieving tools from MCP server: %s", mcp_server.name)
                    
                    # Get tools for this specific toolgroup (MCP server)
                    tools_response = await client.tools.list(toolgroup_id=mcp_server.name)
                    
                    # Convert tools to dict format and add server source information
                    for tool in tools_response:
                        tool_dict = dict(tool)
                        # Add server source information
                        tool_dict["server_source"] = mcp_server.url
                        consolidated_tools.append(tool_dict)
                        
                    logger.debug(
                        "Retrieved %d tools from MCP server %s", 
                        len(tools_response), 
                        mcp_server.name
                    )
                    
                except Exception as e:
                    logger.warning(
                        "Failed to retrieve tools from MCP server %s: %s", 
                        mcp_server.name, 
                        e
                    )
                    # Continue with other servers even if one fails
                    continue
        
        logger.info("Retrieved total of %d tools (%d from built-in toolgroups, %d from MCP servers)", 
                   len(consolidated_tools), 
                   len([t for t in consolidated_tools if t.get("server_source") == "builtin"]),
                   len([t for t in consolidated_tools if t.get("server_source") != "builtin"]))
        
        # Format tools with structured description parsing
        formatted_tools = format_tools_list(consolidated_tools)
        
        return ToolsResponse(tools=formatted_tools)

    # Connection to Llama Stack server
    except APIConnectionError as e:
        logger.error("Unable to connect to Llama Stack: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "response": "Unable to connect to Llama Stack",
                "cause": str(e),
            },
        ) from e
    # Any other exception that can occur during tool listing
    except Exception as e:
        logger.error("Unable to retrieve list of tools: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "response": "Unable to retrieve list of tools",
                "cause": str(e),
            },
        ) from e
