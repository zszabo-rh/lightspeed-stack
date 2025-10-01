"""Utility functions for formatting and parsing MCP tool descriptions."""

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_mcp_tool_description(description: str) -> Dict[str, Any]:
    """
    Parse MCP tool description to extract structured information.
    
    Args:
        description: Raw description string from MCP tool
        
    Returns:
        Dictionary with parsed structured information
    """
    parsed = {
        "tool_name": None,
        "display_name": None,
        "use_case": None,
        "instructions": None,
        "input_description": None,
        "output_description": None,
        "examples": [],
        "prerequisites": [],
        "agent_decision_criteria": None,
        "clean_description": None
    }
    
    try:
        # Split description into lines for parsing
        lines = description.split('\n')
        
        # Extract structured fields using regex
        for line in lines:
            line = line.strip()
            
            if line.startswith('TOOL_NAME='):
                parsed["tool_name"] = line.replace('TOOL_NAME=', '').strip()
            elif line.startswith('DISPLAY_NAME='):
                parsed["display_name"] = line.replace('DISPLAY_NAME=', '').strip()
            elif line.startswith('USECASE='):
                parsed["use_case"] = line.replace('USECASE=', '').strip()
            elif line.startswith('INSTRUCTIONS='):
                parsed["instructions"] = line.replace('INSTRUCTIONS=', '').strip()
            elif line.startswith('INPUT_DESCRIPTION='):
                parsed["input_description"] = line.replace('INPUT_DESCRIPTION=', '').strip()
            elif line.startswith('OUTPUT_DESCRIPTION='):
                parsed["output_description"] = line.replace('OUTPUT_DESCRIPTION=', '').strip()
            elif line.startswith('EXAMPLES='):
                examples_text = line.replace('EXAMPLES=', '').strip()
                # Split examples by common separators
                parsed["examples"] = [ex.strip() for ex in re.split(r'[;,]', examples_text) if ex.strip()]
            elif line.startswith('PREREQUISITES='):
                prereq_text = line.replace('PREREQUISITES=', '').strip()
                # Split prerequisites by common separators
                parsed["prerequisites"] = [pr.strip() for pr in re.split(r'[;,]', prereq_text) if pr.strip()]
            elif line.startswith('AGENT_DECISION_CRITERIA='):
                parsed["agent_decision_criteria"] = line.replace('AGENT_DECISION_CRITERIA=', '').strip()
        
        # Extract clean description (everything after the structured metadata)
        # Look for the main description after all the metadata
        description_parts = description.split('\n\n')
        for part in description_parts:
            if not any(part.strip().startswith(prefix) for prefix in [
                'TOOL_NAME=', 'DISPLAY_NAME=', 'USECASE=', 'INSTRUCTIONS=', 
                'INPUT_DESCRIPTION=', 'OUTPUT_DESCRIPTION=', 'EXAMPLES=', 
                'PREREQUISITES=', 'AGENT_DECISION_CRITERIA='
            ]):
                if part.strip() and len(part.strip()) > 20:  # Reasonable description length
                    parsed["clean_description"] = part.strip()
                    break
        
        # If no clean description found, use the use_case or display_name
        if not parsed["clean_description"]:
            parsed["clean_description"] = parsed["use_case"] or parsed["display_name"] or "No description available"
            
    except Exception as e:
        logger.warning("Failed to parse MCP tool description: %s", e)
        parsed["clean_description"] = description[:200] + "..." if len(description) > 200 else description
    
    return parsed


def format_tool_response(tool_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a tool dictionary with structured description parsing.
    
    Args:
        tool_dict: Raw tool dictionary from Llama Stack
        
    Returns:
        Formatted tool dictionary with structured information
    """
    formatted_tool = tool_dict.copy()
    
    # Parse description if it exists and looks like MCP format
    description = tool_dict.get("description", "")
    if description and ("TOOL_NAME=" in description or "DISPLAY_NAME=" in description):
        parsed_desc = parse_mcp_tool_description(description)
        
        # Add structured fields
        formatted_tool.update({
            "display_name": parsed_desc["display_name"] or tool_dict.get("identifier", "Unknown Tool"),
            "use_case": parsed_desc["use_case"],
            "instructions": parsed_desc["instructions"],
            "examples": parsed_desc["examples"],
            "prerequisites": parsed_desc["prerequisites"],
            "agent_decision_criteria": parsed_desc["agent_decision_criteria"],
            "description": parsed_desc["clean_description"]  # Replace with clean description
        })
        
        # Add metadata section for additional info
        formatted_tool["metadata"] = formatted_tool.get("metadata", {})
        formatted_tool["metadata"].update({
            "input_description": parsed_desc["input_description"],
            "output_description": parsed_desc["output_description"],
            "original_tool_name": parsed_desc["tool_name"]
        })
    
    return formatted_tool


def format_tools_list(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format a list of tools with structured description parsing.
    
    Args:
        tools: List of raw tool dictionaries
        
    Returns:
        List of formatted tool dictionaries
    """
    return [format_tool_response(tool) for tool in tools]

