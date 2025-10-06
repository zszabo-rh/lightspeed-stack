"""Utility functions for formatting and parsing MCP tool descriptions."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def format_tool_response(tool_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a tool dictionary to include only required fields.

    Args:
        tool_dict: Raw tool dictionary from Llama Stack

    Returns:
        Formatted tool dictionary with only required fields
    """
    # Clean up description if it contains structured metadata
    description = tool_dict.get("description", "")
    if description and ("TOOL_NAME=" in description or "DISPLAY_NAME=" in description):
        # Extract clean description from structured metadata
        clean_description = extract_clean_description(description)
        description = clean_description

    # Extract only the required fields
    formatted_tool = {
        "identifier": tool_dict.get("identifier", ""),
        "description": description,
        "parameters": tool_dict.get("parameters", []),
        "provider_id": tool_dict.get("provider_id", ""),
        "toolgroup_id": tool_dict.get("toolgroup_id", ""),
        "server_source": tool_dict.get("server_source", ""),
        "type": tool_dict.get("type", ""),
    }

    return formatted_tool


def extract_clean_description(description: str) -> str:
    """
    Extract a clean description from structured metadata format.

    Args:
        description: Raw description with structured metadata

    Returns:
        Clean description without metadata
    """
    try:
        # Look for the main description after all the metadata
        description_parts = description.split("\n\n")
        for part in description_parts:
            if not any(
                part.strip().startswith(prefix)
                for prefix in [
                    "TOOL_NAME=",
                    "DISPLAY_NAME=",
                    "USECASE=",
                    "INSTRUCTIONS=",
                    "INPUT_DESCRIPTION=",
                    "OUTPUT_DESCRIPTION=",
                    "EXAMPLES=",
                    "PREREQUISITES=",
                    "AGENT_DECISION_CRITERIA=",
                ]
            ):
                if (
                    part.strip() and len(part.strip()) > 20
                ):  # Reasonable description length
                    return part.strip()

        # If no clean description found, try to extract from USECASE
        lines = description.split("\n")
        for line in lines:
            if line.startswith("USECASE="):
                return line.replace("USECASE=", "").strip()

        # Fallback to first 200 characters
        return description[:200] + "..." if len(description) > 200 else description

    except (ValueError, AttributeError) as e:
        logger.warning("Failed to extract clean description: %s", e)
        return description[:200] + "..." if len(description) > 200 else description


def format_tools_list(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format a list of tools with structured description parsing.

    Args:
        tools: List of raw tool dictionaries

    Returns:
        List of formatted tool dictionaries
    """
    return [format_tool_response(tool) for tool in tools]
