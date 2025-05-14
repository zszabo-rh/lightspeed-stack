"""Handler for REST API call to provide answer to query."""

import logging
from typing import Any

from llama_stack.distribution.library_client import LlamaStackAsLibraryClient
from llama_stack_client import LlamaStackClient

from fastapi import APIRouter, Request

from configuration import configuration
from models.config import LLamaStackConfiguration
from models.responses import QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["models"])


query_response: dict[int | str, dict[str, Any]] = {
    200: {
        "query": "User query",
        "answer": "LLM ansert",
    },
}


@router.post("/query", responses=query_response)
def info_endpoint_handler(request: Request, query: str) -> QueryResponse:
    llama_stack_config = configuration.llama_stack_configuration
    logger.info("LLama stack config: %s", llama_stack_config)
    client = getLLamaStackClient(llama_stack_config)
    client = LlamaStackClient(
        base_url=llama_stack_config.url, api_key=llama_stack_config.api_key
    )

    # retrieve list of available models
    models = client.models.list()

    # select the first LLM
    llm = next(m for m in models if m.model_type == "llm")
    model_id = llm.identifier

    logger.info("Model: %s", model_id)

    response = client.inference.chat_completion(
        model_id=model_id,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query},
        ],
    )
    return QueryResponse(query=query, response=str(response.completion_message.content))


def getLLamaStackClient(
    llama_stack_config: LLamaStackConfiguration,
) -> LlamaStackClient:
    if llama_stack_config.use_as_library_client is True:
        client = LlamaStackAsLibraryClient("ollama")
        client.initialize()
        return client
    else:
        return LlamaStackClient(
            base_url=llama_stack_config.url, api_key=llama_stack_config.api_key
        )
