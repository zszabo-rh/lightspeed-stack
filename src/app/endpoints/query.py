"""Handler for REST API call to provide answer to query."""

import logging
from typing import Any

from llama_stack_client.lib.agents.agent import Agent  # type: ignore
from llama_stack_client import LlamaStackClient  # type: ignore
from llama_stack_client.types import UserMessage  # type: ignore
from llama_stack_client.types.model_list_response import ModelListResponse

from fastapi import APIRouter, Request, HTTPException, status

from client import get_llama_stack_client
from configuration import configuration
from models.responses import QueryResponse
from models.requests import QueryRequest, Attachment
import constants

logger = logging.getLogger("app.endpoints.handlers")
router = APIRouter(tags=["query"])


query_response: dict[int | str, dict[str, Any]] = {
    200: {
        "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
        "response": "LLM ansert",
    },
}


@router.post("/query", responses=query_response)
def query_endpoint_handler(
    request: Request, query_request: QueryRequest
) -> QueryResponse:
    """Handle request to the /query endpoint."""
    llama_stack_config = configuration.llama_stack_configuration
    logger.info("LLama stack config: %s", llama_stack_config)
    client = get_llama_stack_client(llama_stack_config)
    model_id = select_model_id(client, query_request)
    response = retrieve_response(client, model_id, query_request)
    return QueryResponse(
        conversation_id=query_request.conversation_id, response=response
    )


def select_model_id(client: LlamaStackClient, query_request: QueryRequest) -> str:
    """Select the model ID based on the request or available models."""
    models: ModelListResponse = client.models.list()
    model_id = query_request.model
    provider_id = query_request.provider

    # TODO(lucasagomes): support default model selection via configuration
    if not model_id:
        logger.info("No model specified in request, using the first available LLM")
        try:
            model = next(
                m
                for m in models
                if m.model_type == "llm"  # pyright: ignore[reportAttributeAccessIssue]
            ).identifier
            logger.info(f"Selected model: {model}")
            return model
        except (StopIteration, AttributeError):
            message = "No LLM model found in available models"
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "response": constants.UNABLE_TO_PROCESS_RESPONSE,
                    "cause": message,
                },
            )

    logger.info(f"Searching for model: {model_id}, provider: {provider_id}")
    if not any(
        m.identifier == model_id and m.provider_id == provider_id for m in models
    ):
        message = f"Model {model_id} from provider {provider_id} not found in available models"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "response": constants.UNABLE_TO_PROCESS_RESPONSE,
                "cause": message,
            },
        )

    return model_id


def retrieve_response(
    client: LlamaStackClient, model_id: str, query_request: QueryRequest
) -> str:
    """Retrieve response from LLMs and agents."""
    available_shields = [shield.identifier for shield in client.shields.list()]
    if not available_shields:
        logger.info("No available shields. Disabling safety")
    else:
        logger.info(f"Available shields found: {available_shields}")

    # use system prompt from request or default one
    system_prompt = (
        query_request.system_prompt
        if query_request.system_prompt
        else constants.DEFAULT_SYSTEM_PROMPT
    )
    logger.debug(f"Using system prompt: {system_prompt}")

    # TODO(lucasagomes): redact attachments content before sending to LLM
    # if attachments are provided, validate them
    if query_request.attachments:
        validate_attachments_metadata(query_request.attachments)

    agent = Agent(
        client,
        model=model_id,
        instructions=system_prompt,
        input_shields=available_shields if available_shields else [],
        tools=[],
    )
    session_id = agent.create_session("chat_session")
    logger.debug(f"Session ID: {session_id}")
    response = agent.create_turn(
        messages=[UserMessage(role="user", content=query_request.query)],
        session_id=session_id,
        documents=query_request.get_documents(),
        stream=False,
    )

    return str(
        response.output_message.content  # pyright: ignore[reportAttributeAccessIssue]
    )


def validate_attachments_metadata(attachments: list[Attachment]) -> None:
    """Validate the attachments metadata provided in the request.

    Raises HTTPException if any attachment has an improper type or content type.
    """
    for attachment in attachments:
        if attachment.attachment_type not in constants.ATTACHMENT_TYPES:
            message = (
                f"Attachment with improper type {attachment.attachment_type} detected"
            )
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "response": constants.UNABLE_TO_PROCESS_RESPONSE,
                    "cause": message,
                },
            )
        if attachment.content_type not in constants.ATTACHMENT_CONTENT_TYPES:
            message = f"Attachment with improper content type {attachment.content_type} detected"
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "response": constants.UNABLE_TO_PROCESS_RESPONSE,
                    "cause": message,
                },
            )
