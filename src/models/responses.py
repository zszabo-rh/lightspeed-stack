from pydantic import BaseModel
from typing import Any


class ModelsResponse(BaseModel):
    """Model representing a response to models request."""

    models: list[dict[str, Any]]


class QueryResponse(BaseModel):
    """Model representing LLM response to a query."""

    query: str
    response: str


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
