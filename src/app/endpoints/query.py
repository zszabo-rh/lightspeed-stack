"""Handler for REST API call to provide answer to query."""

import logging
from typing import Any

from llama_stack_client.lib.agents.agent import Agent  # type: ignore
from llama_stack_client import LlamaStackClient  # type: ignore
from llama_stack_client.types import UserMessage  # type: ignore

from fastapi import APIRouter, Request

from client import get_llama_stack_client
from configuration import configuration
from models.responses import QueryResponse

logger = logging.getLogger("app.endpoints.handlers")
router = APIRouter(tags=["models"])


query_response: dict[int | str, dict[str, Any]] = {
    200: {
        "query": "User query",
        "answer": "LLM ansert",
    },
}


@router.post("/query", responses=query_response)
def query_endpoint_handler(request: Request, query: str) -> QueryResponse:
    llama_stack_config = configuration.llama_stack_configuration
    logger.info("LLama stack config: %s", llama_stack_config)

    client = get_llama_stack_client(llama_stack_config)

    # retrieve list of available models
    models = client.models.list()

    # select the first LLM
    llm = next(m for m in models if m.model_type == "llm")
    model_id = llm.identifier

    logger.info("Model: %s", model_id)

    response = retrieve_response(client, model_id, query)

    return QueryResponse(query=query, response=response)


def retrieve_response(client: LlamaStackClient, model_id: str, prompt: str) -> str:

    available_shields = [shield.identifier for shield in client.shields.list()]
    if not available_shields:
        logger.info("No available shields. Disabling safety")
    else:
        logger.info(f"Available shields found: {available_shields}")

    agent = Agent(
        client,
        model=model_id,
        instructions="You are a helpful assistant",
        input_shields=available_shields if available_shields else [],
        tools=[],
    )
    session_id = agent.create_session("chat_session")
    response = agent.create_turn(
        messages=[UserMessage(role="user", content=prompt)],
        session_id=session_id,
        stream=False,
    )

    return str(response.output_message.content)
