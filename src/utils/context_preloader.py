"""Agent context preloading utilities.

This module provides functionality for preloading agent context by executing
configured MCP tools and formatting their results for injection into the
conversation history.
"""

import json
from typing import Any

from llama_stack_client import AsyncLlamaStackClient

from log import get_logger
from models.config import AgentContextPreloading, ContextPreloadingTool

logger = get_logger(__name__)

# Marker prefix to identify context preloading turns
CONTEXT_PRELOAD_MARKER = "CONTEXT_PRELOAD:"


async def execute_preloading_tools(
    client: AsyncLlamaStackClient,
    config: AgentContextPreloading,
    mcp_headers: dict[str, dict[str, str]],
) -> str:
    """Execute configured tools and return formatted context.

    Args:
        client: AsyncLlamaStackClient instance for tool execution.
        config: AgentContextPreloading configuration with tools to execute.
        mcp_headers: MCP server authentication headers.

    Returns:
        Formatted context string containing results from all tools.
    """
    if not config.enabled or not config.tools:
        logger.debug("Context preloading disabled or no tools configured")
        return ""

    logger.info("Executing %d context preloading tools", len(config.tools))
    
    context_parts = [CONTEXT_PRELOAD_MARKER]
    context_parts.append(config.intro_message)
    context_parts.append("")

    for tool_config in config.tools:
        try:
            result = await execute_single_tool(client, tool_config, mcp_headers)
            if result:
                formatted = format_tool_result(tool_config, result)
                context_parts.append(formatted)
                context_parts.append("")  # Empty line between tools
        except Exception as e:
            logger.warning(
                "Failed to execute context preloading tool %s: %s",
                tool_config.tool_name,
                str(e),
            )
            # Continue with other tools even if one fails

    if len(context_parts) <= 3:  # Only header and marker
        logger.warning("No successful tool executions for context preloading")
        return ""

    # Add explicit instruction for the agent to acknowledge and use this data
    context_parts.append("---")
    context_parts.append("Please acknowledge that you have received and will use this information. "
                        "When answering questions, always check this data first before calling tools.")

    return "\n".join(context_parts)


async def execute_single_tool(
    client: AsyncLlamaStackClient,
    tool_config: ContextPreloadingTool,
    mcp_headers: dict[str, dict[str, str]],
) -> Any:
    """Execute a single MCP tool and return its result.

    Args:
        client: AsyncLlamaStackClient instance.
        tool_config: Configuration for the tool to execute.
        mcp_headers: MCP server authentication headers.

    Returns:
        The tool execution result.

    Raises:
        Exception: If tool execution fails.
    """
    logger.debug(
        "Executing tool %s on MCP server %s",
        tool_config.tool_name,
        tool_config.mcp_server,
    )

    # Get the toolgroup for the MCP server
    toolgroups = await client.toolgroups.list()
    matching_toolgroup = None
    
    for toolgroup in toolgroups:
        # Match by provider_resource_id which corresponds to MCP server name
        if toolgroup.provider_resource_id == tool_config.mcp_server:
            matching_toolgroup = toolgroup
            break
    
    if not matching_toolgroup:
        raise ValueError(
            f"MCP server toolgroup '{tool_config.mcp_server}' not found. "
            f"Available toolgroups: {[tg.provider_resource_id for tg in toolgroups]}"
        )

    # Get available tools for this toolgroup
    tools = await client.tools.list(toolgroup_id=matching_toolgroup.identifier)
    matching_tool = None
    
    for tool in tools:
        if tool.identifier == tool_config.tool_name:
            matching_tool = tool
            break
    
    if not matching_tool:
        available_tools = [t.identifier for t in tools]
        raise ValueError(
            f"Tool '{tool_config.tool_name}' not found in MCP server "
            f"'{tool_config.mcp_server}'. Available tools: {available_tools}"
        )

    # Execute the tool through the tool runtime
    # Note: We use the client's tool runtime API with proper headers
    logger.debug("Invoking tool %s", tool_config.tool_name)
    
    # Build the provider data header for MCP
    provider_data = {"mcp_headers": mcp_headers}
    extra_headers = {"X-LlamaStack-Provider-Data": json.dumps(provider_data)}
    
    # Execute tool via tool runtime
    result = await client.tool_runtime.invoke_tool(
        tool_name=tool_config.tool_name,
        kwargs={},  # Most preloading tools don't require arguments
        extra_headers=extra_headers,
    )
    
    logger.debug("Tool %s executed successfully", tool_config.tool_name)
    return result


def format_tool_result(tool_config: ContextPreloadingTool, result: Any) -> str:
    """Format tool result with optional label.

    Args:
        tool_config: Tool configuration including optional label and empty message.
        result: The raw tool execution result.

    Returns:
        Formatted string representation of the result.
    """
    # Extract content from tool runtime response
    result_text = extract_result_text(result)
    
    # Check if result is empty and use custom empty message if configured
    if not result_text or result_text.strip() in ["[]", "{}", "null", ""]:
        if tool_config.empty_message:
            label = tool_config.label or tool_config.tool_name
            return f"**{label}**: {tool_config.empty_message}"
        # If no custom empty message, skip this tool
        return ""
    
    # Return the raw result with label
    label = tool_config.label or tool_config.tool_name
    return f"**{label}**:\n{result_text}"


def extract_result_text(result: Any) -> str:
    """Extract text content from tool execution result.

    Args:
        result: The tool execution result.

    Returns:
        String representation of the result content.
    """
    if hasattr(result, "content"):
        content = result.content
        # Handle different content types
        if isinstance(content, list) and len(content) > 0:
            # Extract text from content items
            if hasattr(content[0], "text"):
                return content[0].text
            else:
                return str(content[0])
        elif isinstance(content, str):
            return content
        else:
            return str(content)
    else:
        return str(result)


def is_context_preloading_turn(turn_content: str) -> bool:
    """Check if a turn contains context preloading data.

    Args:
        turn_content: The content of a turn message.

    Returns:
        True if this is a context preloading turn, False otherwise.
    """
    if isinstance(turn_content, str):
        return turn_content.startswith(CONTEXT_PRELOAD_MARKER)
    return False

