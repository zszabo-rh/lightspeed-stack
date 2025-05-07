from pydantic import BaseModel


class ModelsResponse(BaseModel):
    """Model representing a response to models request."""

    models: list[dict] 


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
