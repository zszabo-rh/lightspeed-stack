"""Unit tests for the /providers REST API endpoints."""

import pytest
from pytest_mock import MockerFixture
from fastapi import HTTPException, Request, status
from llama_stack_client import APIConnectionError

from authentication.interface import AuthTuple

from app.endpoints.providers import (
    get_provider_endpoint_handler,
    providers_endpoint_handler,
)


@pytest.mark.asyncio
async def test_providers_endpoint_configuration_not_loaded(
    mocker: MockerFixture,
) -> None:
    """Test that /providers endpoint raises HTTP 500 if configuration is not loaded."""
    mocker.patch("app.endpoints.providers.configuration", None)
    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as e:
        await providers_endpoint_handler(request=request, auth=auth)
    assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_providers_endpoint_connection_error(mocker: MockerFixture) -> None:
    """Test that /providers endpoint raises HTTP 500 if Llama Stack connection fails."""
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.side_effect = APIConnectionError(request=None)  # type: ignore
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as e:
        await providers_endpoint_handler(request=request, auth=auth)
    assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = e.value.detail
    assert isinstance(detail, dict)
    assert "Unable to connect to Llama Stack" in detail["response"]


@pytest.mark.asyncio
async def test_providers_endpoint_success(mocker: MockerFixture) -> None:
    """Test that /providers endpoint returns a grouped list of providers on success."""
    provider_list = [
        {
            "api": "inference",
            "provider_id": "openai",
            "provider_type": "remote::openai",
        },
        {
            "api": "inference",
            "provider_id": "st",
            "provider_type": "inline::sentence-transformers",
        },
        {
            "api": "datasetio",
            "provider_id": "huggingface",
            "provider_type": "remote::huggingface",
        },
    ]
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.return_value = provider_list
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    response = await providers_endpoint_handler(request=request, auth=auth)
    assert "inference" in response.providers
    assert len(response.providers["inference"]) == 2
    assert "datasetio" in response.providers


@pytest.mark.asyncio
async def test_get_provider_not_found(mocker: MockerFixture) -> None:
    """Test that /providers/{provider_id} endpoint raises HTTP 404 if the provider is not found."""
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.return_value = []
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as e:
        await get_provider_endpoint_handler(
            request=request, provider_id="openai", auth=auth
        )
    assert e.value.status_code == status.HTTP_404_NOT_FOUND
    detail = e.value.detail
    assert isinstance(detail, dict)
    assert "not found" in detail["response"]


@pytest.mark.asyncio
async def test_get_provider_success(mocker: MockerFixture) -> None:
    """Test that /providers/{provider_id} endpoint returns provider details on success."""
    provider = {
        "api": "inference",
        "provider_id": "openai",
        "provider_type": "remote::openai",
        "config": {"api_key": "*****"},
        "health": {"status": "OK", "message": "Healthy"},
    }
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.return_value = [provider]
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    response = await get_provider_endpoint_handler(
        request=request, provider_id="openai", auth=auth
    )
    assert response.provider_id == "openai"
    assert response.api == "inference"


@pytest.mark.asyncio
async def test_get_provider_connection_error(mocker: MockerFixture) -> None:
    """Test that /providers/{provider_id} raises HTTP 500 if Llama Stack connection fails."""
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.side_effect = APIConnectionError(request=None)  # type: ignore
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as e:
        await get_provider_endpoint_handler(
            request=request, provider_id="openai", auth=auth
        )
    assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = e.value.detail
    assert isinstance(detail, dict)
    assert "Unable to connect to Llama Stack" in detail["response"]


@pytest.mark.asyncio
async def test_get_provider_unexpected_exception(mocker: MockerFixture) -> None:
    """Test that /providers/{provider_id} endpoint raises HTTP 500 for unexpected exceptions."""
    mock_client = mocker.AsyncMock()
    mock_client.providers.list.side_effect = Exception("boom")
    mocker.patch(
        "app.endpoints.providers.AsyncLlamaStackClientHolder"
    ).return_value.get_client.return_value = mock_client

    request = Request(scope={"type": "http"})

    # Authorization tuple required by URL endpoint handler
    auth: AuthTuple = ("test_user_id", "test_user", True, "test_token")

    with pytest.raises(HTTPException) as e:
        await get_provider_endpoint_handler(
            request=request, provider_id="openai", auth=auth
        )
    assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = e.value.detail
    assert isinstance(detail, dict)
    assert "Unable to retrieve list of providers" in detail["response"]
