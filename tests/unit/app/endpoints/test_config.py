"""Unit tests for the /config REST API endpoint."""

from typing import Any
import pytest
from pytest_mock import MockerFixture

from fastapi import HTTPException, Request, status
from authentication.interface import AuthTuple
from app.endpoints.config import config_endpoint_handler
from configuration import AppConfig
from tests.unit.utils.auth_helpers import mock_authorization_resolvers


@pytest.mark.asyncio
async def test_config_endpoint_handler_configuration_not_loaded(
    mocker: MockerFixture,
) -> None:
    """Test the config endpoint handler when configuration is not loaded."""
    mock_authorization_resolvers(mocker)

    # mock for missing configuration
    mocker.patch(
        "app.endpoints.config.configuration._configuration",
        new=None,
    )
    mocker.patch("app.endpoints.config.configuration", None)

    # HTTP request mock required by URL endpoint handler
    request = Request(
        scope={
            "type": "http",
        }
    )

    # authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as exc_info:
        await config_endpoint_handler(
            auth=auth, request=request  # pyright:ignore[reportArgumentType]
        )
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    detail = exc_info.value.detail
    assert isinstance(detail, dict)
    assert detail["response"] == "Configuration is not loaded"


@pytest.mark.asyncio
async def test_config_endpoint_handler_configuration_loaded(
    mocker: MockerFixture,
) -> None:
    """Test the config endpoint handler when configuration is loaded."""
    mock_authorization_resolvers(mocker)

    # configuration to be loaded
    config_dict: dict[Any, Any] = {
        "name": "foo",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "feedback_enabled": False,
        },
        "authentication": {
            "module": "noop",
        },
        "authorization": {"access_rules": []},
        "customization": None,
    }

    # load the configuration
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # Mock configuration
    mocker.patch("app.endpoints.config.configuration", cfg)

    # HTTP request mock required by URL endpoint handler
    request = Request(
        scope={
            "type": "http",
        }
    )

    # authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    response = await config_endpoint_handler(
        auth=auth, request=request  # pyright:ignore[reportArgumentType]
    )
    assert response is not None
    assert response == cfg.configuration
