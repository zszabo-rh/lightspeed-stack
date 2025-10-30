"""Integration tests for the /config endpoint."""

import pytest

from fastapi import Request

from configuration import AppConfig, LogicError
from app.endpoints.config import config_endpoint_handler


@pytest.mark.asyncio
async def test_config_endpoint_returns_config(
    test_config: AppConfig,
    test_request: Request,
    test_auth: tuple[str, str, bool, str],
) -> None:
    """Test that config endpoint returns test configuration.

    This integration test verifies:
    - Endpoint handler integrates with configuration system
    - Configuration values are correctly accessed
    - Real noop authentication is used
    - Response structure matches expected format

    Args:
        test_config: Loads test configuration
        test_request: FastAPI request
        test_auth: noop authentication tuple
    """
    response = await config_endpoint_handler(auth=test_auth, request=test_request)

    # Verify that response matches the real configuration
    assert response == test_config.configuration


@pytest.mark.asyncio
async def test_config_endpoint_returns_current_config(
    current_config: AppConfig,
    test_request: Request,
    test_auth: tuple[str, str, bool, str],
) -> None:
    """Test that config endpoint returns current configuration (from root).

    This integration test verifies:
    - Endpoint handler integrates with configuration system
    - Configuration values are correctly accessed
    - Real noop authentication is used
    - Response structure matches expected format

    Args:
        current_config: Loads root configuration
        test_request: FastAPI request
        test_auth: noop authentication tuple
    """
    response = await config_endpoint_handler(auth=test_auth, request=test_request)

    # Verify that response matches the root configuration
    assert response == current_config.configuration


@pytest.mark.asyncio
async def test_config_endpoint_fails_without_configuration(
    test_request: Request,
    test_auth: tuple[str, str, bool, str],
) -> None:
    """Test that authorization fails when configuration is not loaded.

    This integration test verifies:
    - LogicError is raised when configuration is not loaded
    - Error message indicates configuration is not loaded

    Args:
        test_request: FastAPI request
        test_auth: noop authentication tuple
    """

    # Verify that LogicError is raised when authorization tries to access config
    with pytest.raises(LogicError) as exc_info:
        await config_endpoint_handler(auth=test_auth, request=test_request)

    # Verify error message
    assert "configuration is not loaded" in str(exc_info.value)
