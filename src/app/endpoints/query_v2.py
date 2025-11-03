"""Handler for REST API call to provide answer to query using Response API."""

import logging
from typing import Annotated, Any, cast

from llama_stack_client import AsyncLlamaStackClient  # type: ignore
from llama_stack.apis.agents.openai_responses import (
    OpenAIResponseObject,
)

from fastapi import APIRouter, Request, Depends

from app.endpoints.query import (
    query_endpoint_handler_base,
    validate_attachments_metadata,
)
from authentication import get_auth_dependency
from authentication.interface import AuthTuple
from authorization.middleware import authorize
from configuration import configuration
import metrics
from models.config import Action
from models.requests import QueryRequest
from models.responses import (
    ForbiddenResponse,
    QueryResponse,
    ReferencedDocument,
    UnauthorizedResponse,
)
from utils.endpoints import (
    get_system_prompt,
    get_topic_summary_system_prompt,
)
from utils.mcp_headers import mcp_headers_dependency
from utils.token_counter import TokenCounter
from utils.types import TurnSummary, ToolCallSummary

logger = logging.getLogger("app.endpoints.handlers")
router = APIRouter(tags=["query_v2"])

query_v2_response: dict[int | str, dict[str, Any]] = {
    200: {
        "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
        "response": "LLM answer",
        "referenced_documents": [
            {
                "doc_url": "https://docs.openshift.com/"
                "container-platform/4.15/operators/olm/index.html",
                "doc_title": "Operator Lifecycle Manager (OLM)",
            }
        ],
    },
    400: {
        "description": "Missing or invalid credentials provided by client",
        "model": UnauthorizedResponse,
    },
    403: {
        "description": "User is not authorized",
        "model": ForbiddenResponse,
    },
    500: {
        "detail": {
            "response": "Unable to connect to Llama Stack",
            "cause": "Connection error.",
        }
    },
}


async def get_topic_summary(
    question: str, client: AsyncLlamaStackClient, model_id: str
) -> str:
    """
    Get a topic summary for a question using Responses API.

    This is the Responses API version of get_topic_summary, which uses
    client.responses.create() instead of the Agent API.

    Args:
        question: The question to generate a topic summary for
        client: The AsyncLlamaStackClient to use for the request
        model_id: The llama stack model ID (full format: provider/model)

    Returns:
        str: The topic summary for the question
    """
    topic_summary_system_prompt = get_topic_summary_system_prompt(configuration)

    try:
        # Use Responses API to generate topic summary
        response = await client.responses.create(
            input=question,
            model=model_id,
            instructions=topic_summary_system_prompt,
            stream=False,
            store=False,  # Don't store topic summary requests
        )
        response = cast(OpenAIResponseObject, response)

        # Extract text from response output
        summary_text = ""
        for output_item in response.output:
            if hasattr(output_item, "content"):
                if isinstance(output_item.content, str):
                    summary_text += output_item.content
                elif isinstance(output_item.content, list):
                    for content_item in output_item.content:
                        if hasattr(content_item, "text"):
                            summary_text += content_item.text

        return summary_text.strip() if summary_text else ""
    except Exception as e:
        logger.warning("Failed to generate topic summary: %s", e)
        return ""  # Return empty string on failure


@router.post("/query", responses=query_v2_response)
@authorize(Action.QUERY)
async def query_endpoint_handler_v2(
    request: Request,
    query_request: QueryRequest,
    auth: Annotated[AuthTuple, Depends(get_auth_dependency())],
    mcp_headers: dict[str, dict[str, str]] = Depends(mcp_headers_dependency),
) -> QueryResponse:
    """
    Handle request to the /query endpoint using Responses API.

    This is a wrapper around query_endpoint_handler_base that provides
    the Responses API specific retrieve_response and get_topic_summary functions.

    Returns:
        QueryResponse: Contains the conversation ID and the LLM-generated response.
    """
    return await query_endpoint_handler_base(
        request=request,
        query_request=query_request,
        auth=auth,
        mcp_headers=mcp_headers,
        retrieve_response_func=retrieve_response,
        get_topic_summary_func=get_topic_summary,
    )


async def retrieve_response(  # pylint: disable=too-many-locals,too-many-branches
    client: AsyncLlamaStackClient,
    model_id: str,
    query_request: QueryRequest,
    token: str,
    mcp_headers: dict[str, dict[str, str]] | None = None,
    *,
    provider_id: str = "",
) -> tuple[TurnSummary, str, list[ReferencedDocument], TokenCounter]:
    """
    Retrieve response from LLMs and agents.

    Retrieves a response from the Llama Stack LLM or agent for a
    given query, handling shield configuration, tool usage, and
    attachment validation.

    This function configures system prompts and toolgroups
    (including RAG and MCP integration) as needed based on
    the query request and system configuration. It
    validates attachments, manages conversation and session
    context, and processes MCP headers for multi-component
    processing. Corresponding metrics are updated.

    Parameters:
        model_id (str): The identifier of the LLM model to use.
        provider_id (str): The identifier of the LLM provider to use.
        query_request (QueryRequest): The user's query and associated metadata.
        token (str): The authentication token for authorization.
        mcp_headers (dict[str, dict[str, str]], optional): Headers for multi-component processing.

    Returns:
        tuple[TurnSummary, str]: A tuple containing a summary of the LLM or agent's response content
        and the conversation ID, the list of parsed referenced documents,
        and token usage information.
    """
    # TODO(ltomasbo): implement shields support once available in Responses API
    logger.info("Shields are not yet supported in Responses API. Disabling safety")

    # use system prompt from request or default one
    system_prompt = get_system_prompt(query_request, configuration)
    logger.debug("Using system prompt: %s", system_prompt)

    # TODO(lucasagomes): redact attachments content before sending to LLM
    # if attachments are provided, validate them
    if query_request.attachments:
        validate_attachments_metadata(query_request.attachments)

    # Prepare tools for responses API
    toolgroups: list[dict[str, Any]] | None = None
    if not query_request.no_tools:
        toolgroups = []
        # Get vector stores for RAG tools
        vector_store_ids = [
            vector_store.id for vector_store in (await client.vector_stores.list()).data
        ]

        # Add RAG tools if vector stores are available
        rag_tools = get_rag_tools(vector_store_ids)
        if rag_tools:
            toolgroups.extend(rag_tools)

        # Add MCP server tools
        mcp_tools = get_mcp_tools(configuration.mcp_servers, token)
        if mcp_tools:
            toolgroups.extend(mcp_tools)
            logger.debug(
                "Configured %d MCP tools: %s",
                len(mcp_tools),
                [tool.get("server_label", "unknown") for tool in mcp_tools],
            )
        # Convert empty list to None for consistency with existing behavior
        if not toolgroups:
            toolgroups = None

    # Prepare input for Responses API
    # Convert attachments to text and concatenate with query
    input_text = query_request.query
    if query_request.attachments:
        for attachment in query_request.attachments:
            # Append attachment content with type label
            input_text += (
                f"\n\n[Attachment: {attachment.attachment_type}]\n{attachment.content}"
            )

    # Create OpenAI response using responses API
    response = await client.responses.create(
        input=input_text,
        model=model_id,
        instructions=system_prompt,
        previous_response_id=query_request.conversation_id,
        tools=cast(Any, toolgroups),
        stream=False,
        store=True,
    )
    response = cast(OpenAIResponseObject, response)

    logger.debug(
        "Received response with ID: %s, output items: %d",
        response.id,
        len(response.output),
    )

    # Return the response ID - client can use it for chaining if desired
    conversation_id = response.id

    # Process OpenAI response format
    llm_response = ""
    tool_calls: list[ToolCallSummary] = []

    for output_item in response.output:
        if hasattr(output_item, "content") and output_item.content:
            # Extract text content from message output
            if isinstance(output_item.content, list):
                for content_item in output_item.content:
                    if hasattr(content_item, "text"):
                        llm_response += content_item.text
            elif hasattr(output_item.content, "text"):
                llm_response += output_item.content.text
            elif isinstance(output_item.content, str):
                llm_response += output_item.content

        # Process tool calls if present
        if hasattr(output_item, "tool_calls") and output_item.tool_calls:
            for tool_call in output_item.tool_calls:
                tool_name = (
                    tool_call.function.name
                    if hasattr(tool_call, "function")
                    else "unknown"
                )
                tool_args = (
                    tool_call.function.arguments
                    if hasattr(tool_call, "function")
                    else {}
                )
                tool_calls.append(
                    ToolCallSummary(
                        id=(
                            tool_call.id
                            if hasattr(tool_call, "id")
                            else str(len(tool_calls))
                        ),
                        name=tool_name,
                        args=tool_args,
                        response=None,  # Tool responses would be in subsequent output items
                    )
                )

    logger.info(
        "Response processing complete - Tool calls: %d, Response length: %d chars",
        len(tool_calls),
        len(llm_response),
    )

    summary = TurnSummary(
        llm_response=llm_response,
        tool_calls=tool_calls,
    )

    # Extract referenced documents and token usage from Responses API response
    referenced_documents = parse_referenced_documents_from_responses_api(response)
    model_label = model_id.split("/", 1)[1] if "/" in model_id else model_id
    token_usage = extract_token_usage_from_responses_api(
        response, model_label, provider_id, system_prompt
    )

    if not summary.llm_response:
        logger.warning(
            "Response lacks content (conversation_id=%s)",
            conversation_id,
        )
    return (summary, conversation_id, referenced_documents, token_usage)


def parse_referenced_documents_from_responses_api(
    response: OpenAIResponseObject,
) -> list[ReferencedDocument]:
    """
    Parse referenced documents from OpenAI Responses API response.

    Args:
        response: The OpenAI Response API response object

    Returns:
        list[ReferencedDocument]: List of referenced documents with doc_url and doc_title
    """
    # TODO(ltomasbo): need to parse source documents from Responses API response.
    # The Responses API has a different structure than Agent API for referenced documents.
    # Need to extract from:
    # - OpenAIResponseOutputMessageFileSearchToolCall.results
    # - OpenAIResponseAnnotationCitation in message content
    # - OpenAIResponseAnnotationFileCitation in message content
    return []


def extract_token_usage_from_responses_api(
    response: OpenAIResponseObject, model: str, provider: str, system_prompt: str = ""
) -> TokenCounter:
    """
    Extract token usage from OpenAI Responses API response and update metrics.

    This function extracts token usage information from the Responses API response
    object and updates Prometheus metrics. If usage information is not available,
    it returns zero values without estimation.

    Note: When llama stack internally uses chat_completions, the usage field may be
    empty or a dict. This is expected and will be populated in future llama stack versions.

    Args:
        response: The OpenAI Response API response object
        model: The model identifier for metrics labeling
        provider: The provider identifier for metrics labeling
        system_prompt: The system prompt used (unused, kept for compatibility)

    Returns:
        TokenCounter: Token usage information with input_tokens and output_tokens
    """
    token_counter = TokenCounter()
    token_counter.llm_calls = 1

    # Extract usage from the response if available
    if response.usage:
        try:
            # Handle both dict and object cases due to llama_stack inconsistency:
            # - When llama_stack converts to chat_completions internally, usage is a dict
            # - When using proper Responses API, usage should be an object
            # TODO: Remove dict handling once llama_stack standardizes on object type
            if isinstance(response.usage, dict):
                input_tokens = response.usage.get("input_tokens", 0)
                output_tokens = response.usage.get("output_tokens", 0)
            else:
                # Object with attributes (expected final behavior)
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
            # Only set if we got valid values
            if input_tokens or output_tokens:
                token_counter.input_tokens = input_tokens or 0
                token_counter.output_tokens = output_tokens or 0

                logger.debug(
                    "Extracted token usage from Responses API: input=%d, output=%d",
                    token_counter.input_tokens,
                    token_counter.output_tokens,
                )

                # Update Prometheus metrics only when we have actual usage data
                try:
                    metrics.llm_token_sent_total.labels(provider, model).inc(
                        token_counter.input_tokens
                    )
                    metrics.llm_token_received_total.labels(provider, model).inc(
                        token_counter.output_tokens
                    )
                except (AttributeError, TypeError, ValueError) as e:
                    logger.warning("Failed to update token metrics: %s", e)
                _increment_llm_call_metric(provider, model)
            else:
                logger.debug(
                    "Usage object exists but tokens are 0 or None, treating as no usage info"
                )
                # Still increment the call counter
                _increment_llm_call_metric(provider, model)
        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(
                "Failed to extract token usage from response.usage: %s. Usage value: %s",
                e,
                response.usage,
            )
            # Still increment the call counter
            _increment_llm_call_metric(provider, model)
    else:
        # No usage information available - this is expected when llama stack
        # internally converts to chat_completions
        logger.debug(
            "No usage information in Responses API response, token counts will be 0"
        )
        # token_counter already initialized with 0 values
        # Still increment the call counter
        _increment_llm_call_metric(provider, model)

    return token_counter


def _increment_llm_call_metric(provider: str, model: str) -> None:
    """Helper to safely increment LLM call metric."""
    try:
        metrics.llm_calls_total.labels(provider, model).inc()
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning("Failed to update LLM call metric: %s", e)


def get_rag_tools(vector_store_ids: list[str]) -> list[dict[str, Any]] | None:
    """
    Convert vector store IDs to tools format for Responses API.

    Args:
        vector_store_ids: List of vector store identifiers

    Returns:
        list[dict[str, Any]] | None: List containing file_search tool configuration,
        or None if no vector stores provided
    """
    if not vector_store_ids:
        return None

    return [
        {
            "type": "file_search",
            "vector_store_ids": vector_store_ids,
            "max_num_results": 10,
        }
    ]


def get_mcp_tools(mcp_servers: list, token: str | None = None) -> list[dict[str, Any]]:
    """
    Convert MCP servers to tools format for Responses API.

    Args:
        mcp_servers: List of MCP server configurations
        token: Optional authentication token for MCP server authorization

    Returns:
        list[dict[str, Any]]: List of MCP tool definitions with server details and optional auth headers
    """
    tools = []
    for mcp_server in mcp_servers:
        tool_def = {
            "type": "mcp",
            "server_label": mcp_server.name,
            "server_url": mcp_server.url,
            "require_approval": "never",
        }

        # Add authentication if token provided (Response API format)
        if token:
            tool_def["headers"] = {"Authorization": f"Bearer {token}"}

        tools.append(tool_def)
    return tools
