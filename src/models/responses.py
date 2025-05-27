from pydantic import BaseModel
from typing import Any, Optional


class ModelsResponse(BaseModel):
    """Model representing a response to models request."""

    models: list[dict[str, Any]]


# TODO(lucasagomes): a lot of fields to add to QueryResponse. For now
# we are keeping it simple. The missing fields are:
# - referenced_documents: The optional URLs and titles for the documents used
#   to generate the response.
# - truncated: Set to True if conversation history was truncated to be within context window.
# - input_tokens: Number of tokens sent to LLM
# - output_tokens: Number of tokens received from LLM
# - available_quotas: Quota available as measured by all configured quota limiters
# - tool_calls: List of tool requests.
# - tool_results: List of tool results.
# See LLMResponse in ols-service for more details.
class QueryResponse(BaseModel):
    """Model representing LLM response to a query.

    Attributes:
        conversation_id: The optional conversation ID (UUID).
        response: The response.
    """

    conversation_id: Optional[str] = None
    response: str

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "response": "Operator Lifecycle Manager (OLM) helps users install...",
                }
            ]
        }
    }


class InfoResponse(BaseModel):
    """Model representing a response to a info request.

    Attributes:
        name: Service name.
        version: Service version.

    Example:
        ```python
        info_response = InfoResponse(
            name="Lightspeed Stack",
            version="1.0.0",
        )
        ```
    """

    name: str
    version: str

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Lightspeed Stack",
                    "version": "1.0.0",
                }
            ]
        }
    }


class ReadinessResponse(BaseModel):
    """Model representing a response to a readiness request.

    Attributes:
        ready: The readiness of the service.
        reason: The reason for the readiness.

    Example:
        ```python
        readiness_response = ReadinessResponse(ready=True, reason="service is ready")
        ```
    """

    ready: bool
    reason: str

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ready": True,
                    "reason": "service is ready",
                }
            ]
        }
    }


class LivenessResponse(BaseModel):
    """Model representing a response to a liveness request.

    Attributes:
        alive: If app is alive.

    Example:
        ```python
        liveness_response = LivenessResponse(alive=True)
        ```
    """

    alive: bool

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "alive": True,
                }
            ]
        }
    }


class NotAvailableResponse(BaseModel):
    """Model representing error response for readiness endpoint."""

    detail: dict[str, str]

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": {
                        "response": "Service is not ready",
                        "cause": "Index is not ready",
                    }
                },
                {
                    "detail": {
                        "response": "Service is not ready",
                        "cause": "LLM is not ready",
                    },
                },
            ]
        }
    }
