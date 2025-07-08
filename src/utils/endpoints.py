"""Utility functions for endpoint handlers."""

from fastapi import HTTPException, status

import constants
from models.requests import QueryRequest
from configuration import AppConfig


def check_configuration_loaded(configuration: AppConfig) -> None:
    """Check that configuration is loaded and raise exception when it is not."""
    if configuration is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"response": "Configuration is not loaded"},
        )


def get_system_prompt(query_request: QueryRequest, _configuration: AppConfig) -> str:
    """Get the system prompt: the provided one, configured one, or default one."""
    return (
        query_request.system_prompt
        if query_request.system_prompt
        else constants.DEFAULT_SYSTEM_PROMPT
    )
