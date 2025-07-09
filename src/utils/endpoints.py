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


def get_system_prompt(query_request: QueryRequest, configuration: AppConfig) -> str:
    """Get the system prompt: the provided one, configured one, or default one."""
    # system prompt defined in query request has precendence
    if query_request.system_prompt:
        return query_request.system_prompt

    # customized system prompt should be used when query request
    # does not contain one
    if (
        configuration.customization is not None
        and configuration.customization.system_prompt is not None
    ):
        return configuration.customization.system_prompt

    # default system prompt has the lowest precedence
    return constants.DEFAULT_SYSTEM_PROMPT
