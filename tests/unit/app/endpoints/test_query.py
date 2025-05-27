from fastapi import HTTPException, status
import pytest

from app.endpoints.query import (
    query_endpoint_handler,
    select_model_id,
    retrieve_response,
    validate_attachments_metadata,
)
from models.requests import QueryRequest, Attachment
from llama_stack_client.types import UserMessage  # type: ignore


def test_query_endpoint_handler(mocker):
    """Test the query endpoint handler."""
    mock_client = mocker.Mock()
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
        mocker.Mock(identifier="model2", model_type="llm", provider_id="provider2"),
    ]

    mocker.patch(
        "app.endpoints.query.configuration",
        return_value=mocker.Mock(),
    )
    mocker.patch("app.endpoints.query.get_llama_stack_client", return_value=mock_client)
    mocker.patch("app.endpoints.query.retrieve_response", return_value="LLM answer")
    mocker.patch("app.endpoints.query.select_model_id", return_value="fake_model_id")

    query_request = QueryRequest(query="What is OpenStack?")

    response = query_endpoint_handler(None, query_request)

    assert response.response == "LLM answer"


def test_select_model_id(mocker):
    """Test the select_model_id function."""
    mock_client = mocker.Mock()
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
        mocker.Mock(identifier="model2", model_type="llm", provider_id="provider2"),
    ]

    query_request = QueryRequest(
        query="What is OpenStack?", model="model1", provider="provider1"
    )

    model_id = select_model_id(mock_client, query_request)

    assert model_id == "model1"


def test_select_model_id_no_model(mocker):
    """Test the select_model_id function when no model is specified."""
    mock_client = mocker.Mock()
    mock_client.models.list.return_value = [
        mocker.Mock(
            identifier="not_llm_type", model_type="embedding", provider_id="provider1"
        ),
        mocker.Mock(
            identifier="first_model", model_type="llm", provider_id="provider1"
        ),
        mocker.Mock(
            identifier="second_model", model_type="llm", provider_id="provider2"
        ),
    ]

    query_request = QueryRequest(query="What is OpenStack?")

    model_id = select_model_id(mock_client, query_request)

    # Assert return the first available LLM model
    assert model_id == "first_model"


def test_select_model_id_invalid_model(mocker):
    """Test the select_model_id function with an invalid model."""
    mock_client = mocker.Mock()
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
    ]

    query_request = QueryRequest(
        query="What is OpenStack?", model="invalid_model", provider="provider1"
    )

    with pytest.raises(Exception) as exc_info:
        select_model_id(mock_client, query_request)

    assert (
        "Model invalid_model from provider provider1 not found in available models"
        in str(exc_info.value)
    )


def test_validate_attachments_metadata():
    """Test the validate_attachments_metadata function."""
    attachments = [
        Attachment(
            attachment_type="log",
            content_type="text/plain",
            content="this is attachment",
        ),
        Attachment(
            attachment_type="configuration",
            content_type="application/yaml",
            content="kind: Pod\n metadata:\n name:    private-reg",
        ),
    ]

    # If no exception is raised, the test passes
    validate_attachments_metadata(attachments)


def test_validate_attachments_metadata_invalid_type():
    """Test the validate_attachments_metadata function with invalid attachment type."""
    attachments = [
        Attachment(
            attachment_type="invalid_type",
            content_type="text/plain",
            content="this is attachment",
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        validate_attachments_metadata(attachments)
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "Attachment with improper type invalid_type detected"
        in exc_info.value.detail["cause"]
    )


def test_validate_attachments_metadata_invalid_content_type():
    """Test the validate_attachments_metadata function with invalid attachment type."""
    attachments = [
        Attachment(
            attachment_type="log",
            content_type="text/invalid_content_type",
            content="this is attachment",
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        validate_attachments_metadata(attachments)
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "Attachment with improper content type text/invalid_content_type detected"
        in exc_info.value.detail["cause"]
    )


def test_retrieve_response(mocker):
    """Test the retrieve_response function."""
    mock_agent = mocker.Mock()
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client = mocker.Mock()
    mock_client.shields.list.return_value = []

    mocker.patch("app.endpoints.query.Agent", return_value=mock_agent)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"

    response = retrieve_response(mock_client, model_id, query_request)

    assert response == "LLM answer"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user", context=None)],
        session_id=mocker.ANY,
        documents=[],
        stream=False,
    )
