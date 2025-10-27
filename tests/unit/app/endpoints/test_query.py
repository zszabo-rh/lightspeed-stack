# pylint: disable=redefined-outer-name

"""Unit tests for the /query REST API endpoint."""

# pylint: disable=too-many-lines

import json

import pytest
from fastapi import HTTPException, Request, status
from llama_stack_client import APIConnectionError
from llama_stack_client.types import UserMessage  # type: ignore
from llama_stack_client.types.agents.turn import Turn
from llama_stack_client.types.shared.interleaved_content_item import TextContentItem
from llama_stack_client.types.tool_execution_step import ToolExecutionStep
from llama_stack_client.types.tool_response import ToolResponse
from pydantic import AnyUrl

from app.endpoints.query import (
    evaluate_model_hints,
    get_topic_summary,
    get_rag_toolgroups,
    is_transcripts_enabled,
    parse_metadata_from_text_item,
    parse_referenced_documents,
    query_endpoint_handler,
    retrieve_response,
    select_model_and_provider_id,
    validate_attachments_metadata,
)
from authorization.resolvers import NoopRolesResolver
from configuration import AppConfig
from models.config import Action, ModelContextProtocolServer
from models.database.conversations import UserConversation
from models.requests import Attachment, QueryRequest
from models.responses import ReferencedDocument
from tests.unit.app.endpoints.test_streaming_query import (
    SAMPLE_KNOWLEDGE_SEARCH_RESULTS,
)
from utils.types import ToolCallSummary, TurnSummary
from utils.token_counter import TokenCounter

# User ID must be proper UUID
MOCK_AUTH = (
    "00000001-0001-0001-0001-000000000001",
    "mock_username",
    False,
    "mock_token",
)


@pytest.fixture
def dummy_request() -> Request:
    """Dummy request fixture for testing."""
    req = Request(
        scope={
            "type": "http",
        }
    )

    req.state.authorized_actions = set(Action)
    return req


def mock_metrics(mocker) -> None:
    """Helper function to mock metrics operations for query endpoints."""
    mocker.patch(
        "app.endpoints.query.extract_and_update_token_metrics",
        return_value=TokenCounter(),
    )
    # Mock the metrics that are called inside extract_and_update_token_metrics
    mocker.patch("metrics.llm_token_sent_total")
    mocker.patch("metrics.llm_token_received_total")
    mocker.patch("metrics.llm_calls_total")


def mock_database_operations(mocker) -> None:
    """Helper function to mock database operations for query endpoints."""
    mocker.patch(
        "app.endpoints.query.validate_conversation_ownership", return_value=True
    )
    mocker.patch("app.endpoints.query.persist_user_conversation_details")

    # Mock the database session and query
    mock_session = mocker.Mock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    mock_session.__enter__ = mocker.Mock(return_value=mock_session)
    mock_session.__exit__ = mocker.Mock(return_value=None)
    mocker.patch("app.endpoints.query.get_session", return_value=mock_session)


@pytest.fixture(name="setup_configuration")
def setup_configuration_fixture():
    """Set up configuration for tests."""
    config_dict = {
        "name": "test",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "test-key",
            "url": "http://test.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "transcripts_enabled": False,
        },
        "mcp_servers": [],
        "customization": None,
        "conversation_cache": {
            "type": "noop",
        },
    }
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)
    return cfg


@pytest.mark.asyncio
async def test_query_endpoint_handler_configuration_not_loaded(
    mocker, dummy_request
) -> None:
    """Test the query endpoint handler if configuration is not loaded."""
    # simulate state when no configuration is loaded
    mocker.patch(
        "app.endpoints.query.configuration",
        return_value=mocker.Mock(),
    )
    mocker.patch("app.endpoints.query.configuration", None)

    query = "What is OpenStack?"
    query_request = QueryRequest(query=query)
    with pytest.raises(HTTPException) as e:
        await query_endpoint_handler(
            query_request=query_request,
            request=dummy_request,
            auth=("test-user", "", False, "token"),
        )
    assert e.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert e.value.detail["response"] == "Configuration is not loaded"


def test_is_transcripts_enabled(setup_configuration, mocker) -> None:
    """Test that is_transcripts_enabled returns True when transcripts is not disabled."""
    # Override the transcripts_enabled setting
    mocker.patch.object(
        setup_configuration.user_data_collection_configuration,
        "transcripts_enabled",
        True,
    )
    mocker.patch("app.endpoints.query.configuration", setup_configuration)

    assert is_transcripts_enabled() is True, "Transcripts should be enabled"


def test_is_transcripts_disabled(setup_configuration, mocker) -> None:
    """Test that is_transcripts_enabled returns False when transcripts is disabled."""
    # Use default transcripts_enabled=False from setup
    mocker.patch("app.endpoints.query.configuration", setup_configuration)

    assert is_transcripts_enabled() is False, "Transcripts should be disabled"


async def _test_query_endpoint_handler(
    mocker, dummy_request: Request, store_transcript_to_file=False
) -> None:
    """Test the query endpoint handler."""
    mock_client = mocker.AsyncMock()
    mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_lsc.return_value = mock_client
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
        mocker.Mock(identifier="model2", model_type="llm", provider_id="provider2"),
    ]

    mock_config = mocker.Mock()
    mock_config.user_data_collection_configuration.transcripts_enabled = (
        store_transcript_to_file
    )
    mocker.patch("app.endpoints.query.configuration", mock_config)

    summary = TurnSummary(
        llm_response="LLM answer",
        tool_calls=[
            ToolCallSummary(
                id="123",
                name="test-tool",
                args="testing",
                response="tool response",
            )
        ],
    )
    conversation_id = "00000000-0000-0000-0000-000000000000"
    query = "What is OpenStack?"
    referenced_documents: list[ReferencedDocument] = []

    mocker.patch(
        "app.endpoints.query.retrieve_response",
        return_value=(summary, conversation_id, referenced_documents, TokenCounter()),
    )
    mocker.patch(
        "app.endpoints.query.select_model_and_provider_id",
        return_value=("fake_model_id", "fake_model_id", "fake_provider_id"),
    )
    mocker.patch(
        "app.endpoints.query.is_transcripts_enabled",
        return_value=store_transcript_to_file,
    )
    mock_transcript = mocker.patch("app.endpoints.query.store_transcript")

    # Mock get_topic_summary function
    mocker.patch(
        "app.endpoints.query.get_topic_summary", return_value="Test topic summary"
    )

    # Mock database operations
    mock_database_operations(mocker)

    query_request = QueryRequest(query=query)

    response = await query_endpoint_handler(
        request=dummy_request, query_request=query_request, auth=MOCK_AUTH
    )

    # Assert the response is as expected
    assert response.response == summary.llm_response
    assert response.conversation_id == conversation_id

    # Note: metrics are now handled inside extract_and_update_token_metrics() which is mocked

    # Assert the store_transcript function is called if transcripts are enabled
    if store_transcript_to_file:
        mock_transcript.assert_called_once_with(
            user_id="00000001-0001-0001-0001-000000000001",
            conversation_id=conversation_id,
            model_id="fake_model_id",
            provider_id="fake_provider_id",
            query_is_valid=True,
            query=query,
            query_request=query_request,
            summary=summary,
            attachments=[],
            rag_chunks=[],
            truncated=False,
        )
    else:
        mock_transcript.assert_not_called()


@pytest.mark.asyncio
async def test_query_endpoint_handler_transcript_storage_disabled(
    mocker, dummy_request
) -> None:
    """Test the query endpoint handler with transcript storage disabled."""
    await _test_query_endpoint_handler(
        mocker, dummy_request, store_transcript_to_file=False
    )


@pytest.mark.asyncio
async def test_query_endpoint_handler_store_transcript(mocker, dummy_request) -> None:
    """Test the query endpoint handler with transcript storage enabled."""
    await _test_query_endpoint_handler(
        mocker, dummy_request, store_transcript_to_file=True
    )


def test_select_model_and_provider_id_from_request(mocker) -> None:
    """Test the select_model_and_provider_id function."""
    mocker.patch(
        "metrics.utils.configuration.inference.default_provider",
        "default_provider",
    )
    mocker.patch(
        "metrics.utils.configuration.inference.default_model",
        "default_model",
    )

    model_list = [
        mocker.Mock(
            identifier="provider1/model1", model_type="llm", provider_id="provider1"
        ),
        mocker.Mock(
            identifier="provider2/model2", model_type="llm", provider_id="provider2"
        ),
        mocker.Mock(
            identifier="default_provider/default_model",
            model_type="llm",
            provider_id="default_provider",
        ),
    ]

    # Create a query request with model and provider specified
    query_request = QueryRequest(
        query="What is OpenStack?", model="model2", provider="provider2"
    )

    # Assert the model and provider from request take precedence from the configuration one
    llama_stack_model_id, model_id, provider_id = select_model_and_provider_id(
        model_list, query_request.model, query_request.provider
    )

    assert llama_stack_model_id == "provider2/model2"
    assert model_id == "model2"
    assert provider_id == "provider2"


def test_select_model_and_provider_id_from_configuration(mocker) -> None:
    """Test the select_model_and_provider_id function."""
    mocker.patch(
        "metrics.utils.configuration.inference.default_provider",
        "default_provider",
    )
    mocker.patch(
        "metrics.utils.configuration.inference.default_model",
        "default_model",
    )

    model_list = [
        mocker.Mock(
            identifier="provider1/model1", model_type="llm", provider_id="provider1"
        ),
        mocker.Mock(
            identifier="default_provider/default_model",
            model_type="llm",
            provider_id="default_provider",
        ),
    ]

    # Create a query request without model and provider specified
    query_request = QueryRequest(
        query="What is OpenStack?",
    )

    llama_stack_model_id, model_id, provider_id = select_model_and_provider_id(
        model_list, query_request.model, query_request.provider
    )

    # Assert that the default model and provider from the configuration are returned
    assert llama_stack_model_id == "default_provider/default_model"
    assert model_id == "default_model"
    assert provider_id == "default_provider"


def test_select_model_and_provider_id_first_from_list(mocker) -> None:
    """Test the select_model_and_provider_id function when no model is specified."""
    model_list = [
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

    llama_stack_model_id, model_id, provider_id = select_model_and_provider_id(
        model_list, query_request.model, query_request.provider
    )

    # Assert return the first available LLM model when no model/provider is
    # specified in the request or in the configuration
    assert llama_stack_model_id == "first_model"
    assert model_id == "first_model"
    assert provider_id == "provider1"


def test_select_model_and_provider_id_invalid_model(mocker) -> None:
    """Test the select_model_and_provider_id function with an invalid model."""
    mock_client = mocker.Mock()
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
    ]

    query_request = QueryRequest(
        query="What is OpenStack?", model="invalid_model", provider="provider1"
    )

    with pytest.raises(HTTPException) as exc_info:
        select_model_and_provider_id(
            mock_client.models.list(), query_request.model, query_request.provider
        )

    assert (
        "Model invalid_model from provider provider1 not found in available models"
        in str(exc_info.value)
    )


def test_select_model_and_provider_id_no_available_models(mocker) -> None:
    """Test the select_model_and_provider_id function with no available models."""
    mock_client = mocker.Mock()
    # empty list of models
    mock_client.models.list.return_value = []

    query_request = QueryRequest(query="What is OpenStack?", model=None, provider=None)

    with pytest.raises(HTTPException) as exc_info:
        select_model_and_provider_id(
            mock_client.models.list(), query_request.model, query_request.provider
        )

    assert "No LLM model found in available models" in str(exc_info.value)


def test_validate_attachments_metadata() -> None:
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


def test_validate_attachments_metadata_invalid_type() -> None:
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


def test_validate_attachments_metadata_invalid_content_type() -> None:
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


@pytest.mark.asyncio
async def test_retrieve_response_no_returned_message(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message = None
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    response, _, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    # fallback mechanism: check that the response is empty
    assert response.llm_response == ""


@pytest.mark.asyncio
async def test_retrieve_response_message_without_content(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = None
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    response, _, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    # fallback mechanism: check that the response is empty
    assert response.llm_response == ""


@pytest.mark.asyncio
async def test_retrieve_response_vector_db_available(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_metric = mocker.patch("metrics.llm_calls_validation_errors_total")
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    # Assert that the metric for validation errors is NOT incremented
    mock_metric.inc.assert_not_called()
    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=get_rag_toolgroups(["VectorDB-1"]),
    )


@pytest.mark.asyncio
async def test_retrieve_response_no_available_shields(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_one_available_shield(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""

    class MockShield:
        """Mock for Llama Stack shield to be used."""

        def __init__(self, identifier):
            self.identifier = identifier

        def __str__(self):
            return "MockShield"

        def __repr__(self):
            return "MockShield"

    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = [MockShield("shield1")]
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_two_available_shields(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""

    class MockShield:
        """Mock for Llama Stack shield to be used."""

        def __init__(self, identifier):
            self.identifier = identifier

        def __str__(self):
            return "MockShield"

        def __repr__(self):
            return "MockShield"

    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = [
        MockShield("shield1"),
        MockShield("shield2"),
    ]
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_four_available_shields(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""

    class MockShield:
        """Mock for Llama Stack shield to be used."""

        def __init__(self, identifier):
            self.identifier = identifier

        def __str__(self):
            return "MockShield"

        def __repr__(self):
            return "MockShield"

    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = [
        MockShield("shield1"),
        MockShield("input_shield2"),
        MockShield("output_shield3"),
        MockShield("inout_shield4"),
    ]
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mock_get_agent = mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify get_agent was called with the correct parameters
    mock_get_agent.assert_called_once_with(
        mock_client,
        model_id,
        mocker.ANY,  # system_prompt
        ["shield1", "input_shield2", "inout_shield4"],  # available_input_shields
        ["output_shield3", "inout_shield4"],  # available_output_shields
        None,  # conversation_id
        False,  # no_tools
        {},  # mcp_headers
        mocker.ANY,  # agent_context_preloading
    )

    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_with_one_attachment(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)

    attachments = [
        Attachment(
            attachment_type="log",
            content_type="text/plain",
            content="this is attachment",
        ),
    ]
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?", attachments=attachments)
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        stream=False,
        documents=[
            {
                "content": "this is attachment",
                "mime_type": "text/plain",
            },
        ],
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_with_two_attachments(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)

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
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?", attachments=attachments)
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        stream=False,
        documents=[
            {
                "content": "this is attachment",
                "mime_type": "text/plain",
            },
            {
                "content": "kind: Pod\n" " metadata:\n" " name:    private-reg",
                "mime_type": "application/yaml",
            },
        ],
        toolgroups=None,
    )


def test_parse_metadata_from_text_item_valid(mocker) -> None:
    """Test parsing metadata from a TextContentItem."""
    text = """
    Some text...
    Metadata: {"docs_url": "https://redhat.com", "title": "Example Doc"}
    """
    mock_item = mocker.Mock(spec=TextContentItem)
    mock_item.text = text

    doc = parse_metadata_from_text_item(mock_item)

    assert isinstance(doc, ReferencedDocument)
    assert doc.doc_url == AnyUrl("https://redhat.com")
    assert doc.doc_title == "Example Doc"


def test_parse_metadata_from_text_item_missing_title(mocker) -> None:
    """Test parsing metadata from a TextContentItem with missing title."""
    mock_item = mocker.Mock(spec=TextContentItem)
    mock_item.text = """Metadata: {"docs_url": "https://redhat.com"}"""
    doc = parse_metadata_from_text_item(mock_item)
    assert doc is None


def test_parse_metadata_from_text_item_missing_url(mocker) -> None:
    """Test parsing metadata from a TextContentItem with missing url."""
    mock_item = mocker.Mock(spec=TextContentItem)
    mock_item.text = """Metadata: {"title": "Example Doc"}"""
    doc = parse_metadata_from_text_item(mock_item)
    assert doc is None


def test_parse_metadata_from_text_item_malformed_url(mocker) -> None:
    """Test parsing metadata from a TextContentItem with malformed url."""
    mock_item = mocker.Mock(spec=TextContentItem)
    mock_item.text = (
        """Metadata: {"docs_url": "not a valid url", "title": "Example Doc"}"""
    )
    doc = parse_metadata_from_text_item(mock_item)
    assert doc is None


def test_parse_referenced_documents_single_doc(mocker) -> None:
    """Test parsing metadata from a Turn containing a single doc."""
    text_item = mocker.Mock(spec=TextContentItem)
    text_item.text = (
        """Metadata: {"docs_url": "https://redhat.com", "title": "Example Doc"}"""
    )

    tool_response = mocker.Mock(spec=ToolResponse)
    tool_response.tool_name = "knowledge_search"
    tool_response.content = [text_item]

    step = mocker.Mock(spec=ToolExecutionStep)
    step.tool_responses = [tool_response]

    response = mocker.Mock(spec=Turn)
    response.steps = [step]

    docs = parse_referenced_documents(response)

    assert len(docs) == 1
    assert docs[0].doc_url == AnyUrl("https://redhat.com")
    assert docs[0].doc_title == "Example Doc"


def test_parse_referenced_documents_multiple_docs(mocker) -> None:
    """Test parsing metadata from a Turn containing multiple docs."""
    text_item = mocker.Mock(spec=TextContentItem)
    text_item.text = SAMPLE_KNOWLEDGE_SEARCH_RESULTS

    tool_response = ToolResponse(
        call_id="c1",
        tool_name="knowledge_search",
        content=[
            TextContentItem(text=s, type="text")
            for s in SAMPLE_KNOWLEDGE_SEARCH_RESULTS
        ],
    )

    step = mocker.Mock(spec=ToolExecutionStep)
    step.tool_responses = [tool_response]

    response = mocker.Mock(spec=Turn)
    response.steps = [step]

    docs = parse_referenced_documents(response)

    assert len(docs) == 2
    assert docs[0].doc_url == AnyUrl("https://example.com/doc1")
    assert docs[0].doc_title == "Doc1"
    assert docs[1].doc_url == AnyUrl("https://example.com/doc2")
    assert docs[1].doc_title == "Doc2"


def test_parse_referenced_documents_ignores_other_tools(mocker) -> None:
    """Test parsing metadata from a Turn with the wrong tool name."""
    text_item = mocker.Mock(spec=TextContentItem)
    text_item.text = (
        """Metadata: {"docs_url": "https://redhat.com", "title": "Example Doc"}"""
    )

    tool_response = mocker.Mock(spec=ToolResponse)
    tool_response.tool_name = "not rag tool"
    tool_response.content = [text_item]

    step = mocker.Mock(spec=ToolExecutionStep)
    step.tool_responses = [tool_response]

    response = mocker.Mock()
    response.steps = [step]

    docs = parse_referenced_documents(response)

    assert not docs


@pytest.mark.asyncio
async def test_retrieve_response_with_mcp_servers(prepare_agent_mocks, mocker) -> None:
    """Test the retrieve_response function with MCP servers configured."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with MCP servers
    mcp_servers = [
        ModelContextProtocolServer(
            name="filesystem-server", url="http://localhost:3000"
        ),
        ModelContextProtocolServer(
            name="git-server",
            provider_id="custom-git",
            url="https://git.example.com/mcp",
        ),
    ]
    mock_config = mocker.Mock()
    mock_config.mcp_servers = mcp_servers
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mock_get_agent = mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = "test_token_123"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify get_agent was called with the correct parameters
    mock_get_agent.assert_called_once_with(
        mock_client,
        model_id,
        mocker.ANY,  # system_prompt
        [],  # available_input_shields
        [],  # available_output_shields
        None,  # conversation_id
        False,  # no_tools
        {
            "http://localhost:3000": {"Authorization": "Bearer test_token_123"},
            "https://git.example.com/mcp": {"Authorization": "Bearer test_token_123"},
        },  # mcp_headers
        mocker.ANY,  # agent_context_preloading
    )

    # Check that the agent's extra_headers property was set correctly
    expected_extra_headers = {
        "X-LlamaStack-Provider-Data": json.dumps(
            {
                "mcp_headers": {
                    "http://localhost:3000": {"Authorization": "Bearer test_token_123"},
                    "https://git.example.com/mcp": {
                        "Authorization": "Bearer test_token_123"
                    },
                }
            }
        )
    }
    assert mock_agent.extra_headers == expected_extra_headers

    # Check that create_turn was called with the correct parameters
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(role="user", content="What is OpenStack?")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=[mcp_server.name for mcp_server in mcp_servers],
    )


@pytest.mark.asyncio
async def test_retrieve_response_with_mcp_servers_empty_token(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function with MCP servers and empty access token."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with MCP servers
    mcp_servers = [
        ModelContextProtocolServer(name="test-server", url="http://localhost:8080"),
    ]
    mock_config = mocker.Mock()
    mock_config.mcp_servers = mcp_servers
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mock_get_agent = mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = ""  # Empty token

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify get_agent was called with the correct parameters
    mock_get_agent.assert_called_once_with(
        mock_client,
        model_id,
        mocker.ANY,  # system_prompt
        [],  # available_input_shields
        [],  # available_output_shields
        None,  # conversation_id
        False,  # no_tools
        {},  # mcp_headers (empty because token is empty)
        mocker.ANY,  # agent_context_preloading
    )

    # Check that create_turn was called with the correct parameters
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(role="user", content="What is OpenStack?")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=[mcp_server.name for mcp_server in mcp_servers],
    )


@pytest.mark.asyncio
async def test_retrieve_response_with_mcp_servers_and_mcp_headers(
    prepare_agent_mocks, mocker
) -> None:
    """Test the retrieve_response function with MCP servers configured."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_client.vector_dbs.list.return_value = []

    # Mock configuration with MCP servers
    mcp_servers = [
        ModelContextProtocolServer(
            name="filesystem-server", url="http://localhost:3000"
        ),
        ModelContextProtocolServer(
            name="git-server",
            provider_id="custom-git",
            url="https://git.example.com/mcp",
        ),
    ]
    mock_config = mocker.Mock()
    mock_config.mcp_servers = mcp_servers
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mock_get_agent = mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")
    model_id = "fake_model_id"
    access_token = ""
    mcp_headers = {
        "filesystem-server": {"Authorization": "Bearer test_token_123"},
        "git-server": {"Authorization": "Bearer test_token_456"},
        "http://another-server-mcp-server:3000": {
            "Authorization": "Bearer test_token_789"
        },
        "unknown-mcp-server": {
            "Authorization": "Bearer test_token_for_unknown-mcp-server"
        },
    }

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client,
        model_id,
        query_request,
        access_token,
        mcp_headers=mcp_headers,
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify get_agent was called with the correct parameters
    expected_mcp_headers = {
        "http://localhost:3000": {"Authorization": "Bearer test_token_123"},
        "https://git.example.com/mcp": {"Authorization": "Bearer test_token_456"},
        "http://another-server-mcp-server:3000": {
            "Authorization": "Bearer test_token_789"
        },
        # we do not put "unknown-mcp-server" url as it's unknown to lightspeed-stack
    }
    
    mock_get_agent.assert_called_once_with(
        mock_client,
        model_id,
        mocker.ANY,  # system_prompt
        [],  # available_input_shields
        [],  # available_output_shields
        None,  # conversation_id
        False,  # no_tools
        expected_mcp_headers,  # mcp_headers
        mocker.ANY,  # agent_context_preloading
    )

    # Check that the agent's extra_headers property was set correctly
    expected_extra_headers = {
        "X-LlamaStack-Provider-Data": json.dumps(
            {
                "mcp_headers": expected_mcp_headers,
            }
        )
    }

    assert mock_agent.extra_headers == expected_extra_headers

    # Check that create_turn was called with the correct parameters
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(role="user", content="What is OpenStack?")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=[mcp_server.name for mcp_server in mcp_servers],
    )


@pytest.mark.asyncio
async def test_retrieve_response_shield_violation(prepare_agent_mocks, mocker) -> None:
    """Test the retrieve_response function."""
    mock_metric = mocker.patch("metrics.llm_calls_validation_errors_total")
    mock_client, mock_agent = prepare_agent_mocks
    # Mock the agent's create_turn method to return a response with a shield violation
    steps = [
        mocker.Mock(
            step_type="shield_call",
            violation=True,
        ),
    ]
    mock_agent.create_turn.return_value.steps = steps
    mock_agent.create_turn.return_value.output_message.content = TextContentItem(
        text="LLM answer", type="text"
    )
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with empty MCP servers
    mock_config = mocker.Mock()
    mock_config.mcp_servers = []
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?")

    _, conversation_id, _, _ = await retrieve_response(
        mock_client, "fake_model_id", query_request, "test_token"
    )

    # Assert that the metric for validation errors is incremented
    mock_metric.inc.assert_called_once()

    assert conversation_id == "00000000-0000-0000-0000-000000000000"
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=get_rag_toolgroups(["VectorDB-1"]),
    )


def test_get_rag_toolgroups() -> None:
    """Test get_rag_toolgroups function."""
    vector_db_ids: list[str] = []
    result = get_rag_toolgroups(vector_db_ids)
    assert result is None

    vector_db_ids = ["Vector-DB-1", "Vector-DB-2"]
    result = get_rag_toolgroups(vector_db_ids)
    assert result is not None
    assert len(result) == 1
    assert result[0]["name"] == "builtin::rag/knowledge_search"
    assert result[0]["args"]["vector_db_ids"] == vector_db_ids


@pytest.mark.asyncio
async def test_query_endpoint_handler_on_connection_error(
    mocker, dummy_request
) -> None:
    """Test the query endpoint handler."""
    mock_metric = mocker.patch("metrics.llm_calls_failures_total")

    mocker.patch(
        "app.endpoints.query.configuration",
        return_value=mocker.Mock(),
    )

    query_request = QueryRequest(query="What is OpenStack?")

    # simulate situation when it is not possible to connect to Llama Stack
    mock_get_client = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_get_client.side_effect = APIConnectionError(request=query_request)

    with pytest.raises(HTTPException) as exc_info:
        await query_endpoint_handler(
            query_request=query_request, request=dummy_request, auth=MOCK_AUTH
        )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Unable to connect to Llama Stack" in str(exc_info.value.detail)
    mock_metric.inc.assert_called_once()


@pytest.mark.asyncio
async def test_auth_tuple_unpacking_in_query_endpoint_handler(
    mocker, dummy_request
) -> None:
    """Test that auth tuple is correctly unpacked in query endpoint handler."""
    # Mock dependencies
    mock_config = mocker.Mock()
    mock_config.llama_stack_configuration = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    mock_client = mocker.AsyncMock()
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1")
    ]
    mocker.patch(
        "client.AsyncLlamaStackClientHolder.get_client", return_value=mock_client
    )

    summary = TurnSummary(
        llm_response="LLM answer",
        tool_calls=[
            ToolCallSummary(
                id="123",
                name="test-tool",
                args="testing",
                response="tool response",
            )
        ],
    )
    mock_retrieve_response = mocker.patch(
        "app.endpoints.query.retrieve_response",
        return_value=(
            summary,
            "00000000-0000-0000-0000-000000000000",
            [],
            TokenCounter(),
        ),
    )

    mocker.patch(
        "app.endpoints.query.select_model_and_provider_id",
        return_value=("test_model", "test_model", "test_provider"),
    )
    mocker.patch("app.endpoints.query.is_transcripts_enabled", return_value=False)
    # Mock get_topic_summary function
    mocker.patch(
        "app.endpoints.query.get_topic_summary", return_value="Test topic summary"
    )
    # Mock database operations
    mock_database_operations(mocker)

    _ = await query_endpoint_handler(
        request=dummy_request,
        query_request=QueryRequest(query="test query"),
        auth=("user123", "username", False, "auth_token_123"),
        mcp_headers={},
    )

    assert mock_retrieve_response.call_args[0][3] == "auth_token_123"


@pytest.mark.asyncio
async def test_query_endpoint_handler_no_tools_true(mocker, dummy_request) -> None:
    """Test the query endpoint handler with no_tools=True."""
    mock_client = mocker.AsyncMock()
    mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_lsc.return_value = mock_client
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
    ]

    mock_config = mocker.Mock()
    mock_config.user_data_collection_configuration.transcripts_disabled = True
    mocker.patch("app.endpoints.query.configuration", mock_config)

    summary = TurnSummary(
        llm_response="LLM answer",
        tool_calls=[
            ToolCallSummary(
                id="123",
                name="test-tool",
                args="testing",
                response="tool response",
            )
        ],
    )
    conversation_id = "00000000-0000-0000-0000-000000000000"
    query = "What is OpenStack?"
    referenced_documents: list[ReferencedDocument] = []

    mocker.patch(
        "app.endpoints.query.retrieve_response",
        return_value=(summary, conversation_id, referenced_documents, TokenCounter()),
    )
    mocker.patch(
        "app.endpoints.query.select_model_and_provider_id",
        return_value=("fake_model_id", "fake_model_id", "fake_provider_id"),
    )
    mocker.patch("app.endpoints.query.is_transcripts_enabled", return_value=False)
    # Mock get_topic_summary function
    mocker.patch(
        "app.endpoints.query.get_topic_summary", return_value="Test topic summary"
    )
    # Mock database operations
    mock_database_operations(mocker)

    query_request = QueryRequest(query=query, no_tools=True)

    response = await query_endpoint_handler(
        request=dummy_request, query_request=query_request, auth=MOCK_AUTH
    )

    # Assert the response is as expected
    assert response.response == summary.llm_response
    assert response.conversation_id == conversation_id


@pytest.mark.asyncio
async def test_query_endpoint_handler_no_tools_false(mocker, dummy_request) -> None:
    """Test the query endpoint handler with no_tools=False (default behavior)."""
    mock_client = mocker.AsyncMock()
    mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")
    mock_lsc.return_value = mock_client
    mock_client.models.list.return_value = [
        mocker.Mock(identifier="model1", model_type="llm", provider_id="provider1"),
    ]

    mock_config = mocker.Mock()
    mock_config.user_data_collection_configuration.transcripts_disabled = True
    mocker.patch("app.endpoints.query.configuration", mock_config)

    summary = TurnSummary(
        llm_response="LLM answer",
        tool_calls=[
            ToolCallSummary(
                id="123",
                name="test-tool",
                args="testing",
                response="tool response",
            )
        ],
    )
    conversation_id = "00000000-0000-0000-0000-000000000000"
    query = "What is OpenStack?"
    referenced_documents: list[ReferencedDocument] = []

    mocker.patch(
        "app.endpoints.query.retrieve_response",
        return_value=(summary, conversation_id, referenced_documents, TokenCounter()),
    )
    mocker.patch(
        "app.endpoints.query.select_model_and_provider_id",
        return_value=("fake_model_id", "fake_model_id", "fake_provider_id"),
    )
    mocker.patch("app.endpoints.query.is_transcripts_enabled", return_value=False)
    # Mock get_topic_summary function
    mocker.patch(
        "app.endpoints.query.get_topic_summary", return_value="Test topic summary"
    )
    # Mock database operations
    mock_database_operations(mocker)

    query_request = QueryRequest(query=query, no_tools=False)

    response = await query_endpoint_handler(
        request=dummy_request, query_request=query_request, auth=MOCK_AUTH
    )

    # Assert the response is as expected
    assert response.response == summary.llm_response
    assert response.conversation_id == conversation_id


@pytest.mark.asyncio
async def test_retrieve_response_no_tools_bypasses_mcp_and_rag(
    prepare_agent_mocks, mocker
) -> None:
    """Test that retrieve_response bypasses MCP servers and RAG when no_tools=True."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with MCP servers
    mcp_servers = [
        ModelContextProtocolServer(
            name="filesystem-server", url="http://localhost:3000"
        ),
    ]
    mock_config = mocker.Mock()
    mock_config.mcp_servers = mcp_servers
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?", no_tools=True)
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify that agent.extra_headers is empty (no MCP headers)
    assert mock_agent.extra_headers == {}

    # Verify that create_turn was called with toolgroups=None
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_retrieve_response_no_tools_false_preserves_functionality(
    prepare_agent_mocks, mocker
) -> None:
    """Test that retrieve_response preserves normal functionality when no_tools=False."""
    mock_client, mock_agent = prepare_agent_mocks
    mock_agent.create_turn.return_value.output_message.content = "LLM answer"
    mock_client.shields.list.return_value = []
    mock_vector_db = mocker.Mock()
    mock_vector_db.identifier = "VectorDB-1"
    mock_client.vector_dbs.list.return_value = [mock_vector_db]

    # Mock configuration with MCP servers
    mcp_servers = [
        ModelContextProtocolServer(
            name="filesystem-server", url="http://localhost:3000"
        ),
    ]
    mock_config = mocker.Mock()
    mock_config.mcp_servers = mcp_servers
    mocker.patch("app.endpoints.query.configuration", mock_config)
    mocker.patch(
        "app.endpoints.query.get_agent",
        return_value=(
            mock_agent,
            "00000000-0000-0000-0000-000000000000",
            "fake_session_id",
        ),
    )
    mock_metrics(mocker)

    query_request = QueryRequest(query="What is OpenStack?", no_tools=False)
    model_id = "fake_model_id"
    access_token = "test_token"

    summary, conversation_id, _, _ = await retrieve_response(
        mock_client, model_id, query_request, access_token
    )

    assert summary.llm_response == "LLM answer"
    assert conversation_id == "00000000-0000-0000-0000-000000000000"

    # Verify that agent.extra_headers contains MCP headers
    expected_extra_headers = {
        "X-LlamaStack-Provider-Data": json.dumps(
            {
                "mcp_headers": {
                    "http://localhost:3000": {"Authorization": "Bearer test_token"},
                }
            }
        )
    }
    assert mock_agent.extra_headers == expected_extra_headers

    # Verify that create_turn was called with RAG and MCP toolgroups
    expected_toolgroups = get_rag_toolgroups(["VectorDB-1"]) + ["filesystem-server"]
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(content="What is OpenStack?", role="user")],
        session_id="fake_session_id",
        documents=[],
        stream=False,
        toolgroups=expected_toolgroups,
    )


def test_no_tools_parameter_backward_compatibility() -> None:
    """Test that default behavior is unchanged when no_tools parameter is not specified."""
    # This test ensures that existing code that doesn't specify no_tools continues to work
    query_request = QueryRequest(query="What is OpenStack?")

    # Verify default value
    assert query_request.no_tools is False

    # Test that QueryRequest can be created without no_tools parameter
    query_request_minimal = QueryRequest(query="Simple query")
    assert query_request_minimal.no_tools is False


@pytest.mark.parametrize(
    "user_conversation,request_values,expected_values",
    [
        # No user conversation, no request values
        (
            None,
            (None, None),
            # Expect no values to be used
            (None, None),
        ),
        # No user conversation, request values provided
        (
            None,
            ("foo", "bar"),
            # Expect request values to be used
            ("foo", "bar"),
        ),
        # User conversation exists, no request values
        (
            UserConversation(
                id="conv1",
                user_id="user1",
                last_used_provider="foo",
                last_used_model="bar",
                message_count=1,
            ),
            (
                None,
                None,
            ),
            # Expect conversation values to be used
            (
                "foo",
                "bar",
            ),
        ),
        # Request matches user conversation
        (
            UserConversation(
                id="conv1",
                user_id="user1",
                last_used_provider="foo",
                last_used_model="bar",
                message_count=1,
            ),
            (
                "foo",
                "bar",
            ),
            # Expect request values to be used
            (
                "foo",
                "bar",
            ),
        ),
    ],
    ids=[
        "No user conversation, no request values",
        "No user conversation, request values provided",
        "User conversation exists, no request values",
        "Request matches user conversation",
    ],
)
def test_evaluate_model_hints(
    user_conversation,
    request_values,
    expected_values,
) -> None:
    """Test evaluate_model_hints function with various scenarios."""
    # Unpack fixtures
    request_provider, request_model = request_values
    expected_provider, expected_model = expected_values

    query_request = QueryRequest(
        query="What is love?",
        provider=request_provider,
        model=request_model,
    )  # pylint: disable=missing-kwoa

    model_id, provider_id = evaluate_model_hints(user_conversation, query_request)

    assert provider_id == expected_provider
    assert model_id == expected_model


@pytest.mark.asyncio
async def test_query_endpoint_rejects_model_provider_override_without_permission(
    mocker, dummy_request
) -> None:
    """Assert 403 and message when request includes model/provider without MODEL_OVERRIDE."""
    # Patch endpoint configuration (no need to set customization)
    cfg = AppConfig()
    cfg.init_from_dict(
        {
            "name": "test",
            "service": {
                "host": "localhost",
                "port": 8080,
                "auth_enabled": False,
                "workers": 1,
                "color_log": True,
                "access_log": True,
            },
            "llama_stack": {
                "api_key": "test-key",
                "url": "http://test.com:1234",
                "use_as_library_client": False,
            },
            "user_data_collection": {"transcripts_enabled": False},
            "mcp_servers": [],
        }
    )
    mocker.patch("app.endpoints.query.configuration", cfg)

    # Patch authorization to exclude MODEL_OVERRIDE from authorized actions
    access_resolver = mocker.Mock()
    access_resolver.check_access.return_value = True
    access_resolver.get_actions.return_value = set(Action) - {Action.MODEL_OVERRIDE}
    mocker.patch(
        "authorization.middleware.get_authorization_resolvers",
        return_value=(NoopRolesResolver(), access_resolver),
    )

    # Build a request that tries to override model/provider
    query_request = QueryRequest(query="What?", model="m", provider="p")

    with pytest.raises(HTTPException) as exc_info:
        await query_endpoint_handler(
            request=dummy_request, query_request=query_request, auth=MOCK_AUTH
        )

    expected_msg = (
        "This instance does not permit overriding model/provider in the query request "
        "(missing permission: MODEL_OVERRIDE). Please remove the model and provider "
        "fields from your request."
    )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail["response"] == expected_msg


@pytest.mark.asyncio
async def test_get_topic_summary_successful_response(mocker) -> None:
    """Test get_topic_summary with successful response from agent."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message.content = "This is a topic summary about OpenStack"

    # Mock the get_temp_agent function
    mock_get_temp_agent = mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the interleaved_content_as_str function
    mocker.patch(
        "app.endpoints.query.interleaved_content_as_str",
        return_value="This is a topic summary about OpenStack",
    )

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="You are a topic summarizer",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is OpenStack?", client=mock_client, model_id="test_model"
    )

    # Assertions
    assert result == "This is a topic summary about OpenStack"

    # Verify get_temp_agent was called with correct parameters
    mock_get_temp_agent.assert_called_once_with(
        mock_client, "test_model", "You are a topic summarizer"
    )

    # Verify create_turn was called with correct parameters
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(role="user", content="What is OpenStack?")],
        session_id="session_123",
        stream=False,
        toolgroups=None,
    )


@pytest.mark.asyncio
async def test_get_topic_summary_empty_response(mocker) -> None:
    """Test get_topic_summary with empty response from agent."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message = None

    # Mock the get_temp_agent function
    mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="You are a topic summarizer",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is OpenStack?", client=mock_client, model_id="test_model"
    )

    # Assertions
    assert result == ""


@pytest.mark.asyncio
async def test_get_topic_summary_none_content(mocker) -> None:
    """Test get_topic_summary with None content in response."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message.content = None

    # Mock the get_temp_agent function
    mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="You are a topic summarizer",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is OpenStack?", client=mock_client, model_id="test_model"
    )

    # Assertions
    assert result == ""


@pytest.mark.asyncio
async def test_get_topic_summary_with_interleaved_content(mocker) -> None:
    """Test get_topic_summary with interleaved content response."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_content = [TextContentItem(text="Topic summary", type="text")]
    mock_response.output_message.content = mock_content

    # Mock the get_temp_agent function
    mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the interleaved_content_as_str function
    mock_interleaved_content_as_str = mocker.patch(
        "app.endpoints.query.interleaved_content_as_str", return_value="Topic summary"
    )

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="You are a topic summarizer",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is OpenStack?", client=mock_client, model_id="test_model"
    )

    # Assertions
    assert result == "Topic summary"

    # Verify interleaved_content_as_str was called with the content
    mock_interleaved_content_as_str.assert_called_once_with(mock_content)


@pytest.mark.asyncio
async def test_get_topic_summary_system_prompt_retrieval(mocker) -> None:
    """Test that get_topic_summary properly retrieves and uses the system prompt."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message.content = "Topic summary"

    # Mock the get_temp_agent function
    mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the interleaved_content_as_str function
    mocker.patch(
        "app.endpoints.query.interleaved_content_as_str", return_value="Topic summary"
    )

    # Mock the get_topic_summary_system_prompt function
    mock_get_topic_summary_system_prompt = mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="Custom topic summarizer prompt",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is OpenStack?", client=mock_client, model_id="test_model"
    )

    # Assertions
    assert result == "Topic summary"

    # Verify get_topic_summary_system_prompt was called with configuration
    mock_get_topic_summary_system_prompt.assert_called_once_with(mock_config)


@pytest.mark.asyncio
async def test_query_endpoint_handler_conversation_not_found(
    mocker, dummy_request
) -> None:
    """Test that a 404 is raised for a non-existant conversation_id."""
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    mocker.patch(
        "app.endpoints.query.validate_conversation_ownership", return_value=None
    )

    query_request = QueryRequest(
        query="What is OpenStack?",
        conversation_id="00000000-0000-0000-0000-000000000001",
    )

    with pytest.raises(HTTPException) as exc_info:
        await query_endpoint_handler(
            request=dummy_request, query_request=query_request, auth=MOCK_AUTH
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Conversation not found" in exc_info.value.detail["response"]


@pytest.mark.asyncio
async def test_get_topic_summary_agent_creation_parameters(mocker) -> None:
    """Test that get_topic_summary creates agent with correct parameters."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message.content = "Topic summary"

    # Mock the get_temp_agent function
    mock_get_temp_agent = mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "session_123", "conversation_456"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the interleaved_content_as_str function
    mocker.patch(
        "app.endpoints.query.interleaved_content_as_str", return_value="Topic summary"
    )

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="Custom system prompt",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="Test question?", client=mock_client, model_id="custom_model"
    )

    # Assertions
    assert result == "Topic summary"

    # Verify get_temp_agent was called with correct parameters
    mock_get_temp_agent.assert_called_once_with(
        mock_client, "custom_model", "Custom system prompt"
    )


@pytest.mark.asyncio
async def test_get_topic_summary_create_turn_parameters(mocker) -> None:
    """Test that get_topic_summary calls create_turn with correct parameters."""
    # Mock the dependencies
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.output_message.content = "Topic summary"

    # Mock the get_temp_agent function
    mocker.patch(
        "app.endpoints.query.get_temp_agent",
        return_value=(mock_agent, "test_session", "test_conversation"),
    )

    # Mock the agent's create_turn method
    mock_agent.create_turn.return_value = mock_response

    # Mock the interleaved_content_as_str function
    mocker.patch(
        "app.endpoints.query.interleaved_content_as_str", return_value="Topic summary"
    )

    # Mock the get_topic_summary_system_prompt function
    mocker.patch(
        "app.endpoints.query.get_topic_summary_system_prompt",
        return_value="Custom system prompt",
    )

    # Mock the configuration
    mock_config = mocker.Mock()
    mocker.patch("app.endpoints.query.configuration", mock_config)

    # Call the function
    result = await get_topic_summary(
        question="What is the meaning of life?",
        client=mock_client,
        model_id="test_model",
    )

    # Assertions
    assert result == "Topic summary"

    # Verify create_turn was called with correct parameters
    mock_agent.create_turn.assert_called_once_with(
        messages=[UserMessage(role="user", content="What is the meaning of life?")],
        session_id="test_session",
        stream=False,
        toolgroups=None,
    )
