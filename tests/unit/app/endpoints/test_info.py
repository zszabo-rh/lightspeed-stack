"""Unit tests for the /info REST API endpoint."""

import pytest
from fastapi import Request, HTTPException, status

from llama_stack_client import APIConnectionError
from llama_stack_client.types import VersionInfo

from app.endpoints.info import info_endpoint_handler
from configuration import AppConfig
from tests.unit.utils.auth_helpers import mock_authorization_resolvers


@pytest.mark.asyncio
async def test_info_endpoint(mocker):
    """Test the info endpoint handler."""
    mock_authorization_resolvers(mocker)

    # configuration for tests
    config_dict = {
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
        "customization": None,
        "authorization": {"access_rules": []},
        "authentication": {"module": "noop"},
    }
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # Mock the LlamaStack client
    mock_client = mocker.AsyncMock()
    mock_client.inspect.version.return_value = VersionInfo(version="0.1.2")
    mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_lsc.return_value = mock_client
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.models.configuration", mock_config)

    # Mock configuration
    mocker.patch("configuration.configuration", cfg)

    mock_authorization_resolvers(mocker)

    request = Request(
        scope={
            "type": "http",
        }
    )
    auth = ("test_user", "token", {})
    response = await info_endpoint_handler(auth=auth, request=request)
    assert response is not None
    assert response.name is not None
    assert response.service_version is not None
    assert response.llama_stack_version == "0.1.2"


@pytest.mark.asyncio
async def test_info_endpoint_connection_error(mocker):
    """Test the info endpoint handler."""
    mock_authorization_resolvers(mocker)

    # configuration for tests
    config_dict = {
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
        "customization": None,
        "authorization": {"access_rules": []},
        "authentication": {"module": "noop"},
    }
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # Mock the LlamaStack client
    mock_client = mocker.AsyncMock()
    mock_client.inspect.version.side_effect = APIConnectionError(request=None)
    mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_lsc.return_value = mock_client
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.models.configuration", mock_config)

    # Mock configuration
    mocker.patch("configuration.configuration", cfg)

    mock_authorization_resolvers(mocker)

    request = Request(
        scope={
            "type": "http",
        }
    )
    auth = ("test_user", "token", {})

    with pytest.raises(HTTPException) as e:
        await info_endpoint_handler(auth=auth, request=request)
        assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert e.detail["response"] == "Unable to connect to Llama Stack"
