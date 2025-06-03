"""Model for service requests."""

from typing import Optional, Self

from pydantic import BaseModel, model_validator

from llama_stack_client.types.agents.turn_create_params import Document


class Attachment(BaseModel):
    """Model representing an attachment that can be send from UI as part of query.

    List of attachments can be optional part of 'query' request.

    Attributes:
        attachment_type: The attachment type, like "log", "configuration" etc.
        content_type: The content type as defined in MIME standard
        content: The actual attachment content

    YAML attachments with **kind** and **metadata/name** attributes will
    be handled as resources with specified name:
    ```
    kind: Pod
    metadata:
        name: private-reg
    ```
    """

    attachment_type: str
    content_type: str
    content: str

    # provides examples for /docs endpoint
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "attachment_type": "log",
                    "content_type": "text/plain",
                    "content": "this is attachment",
                },
                {
                    "attachment_type": "configuration",
                    "content_type": "application/yaml",
                    "content": "kind: Pod\n metadata:\n name:    private-reg",
                },
                {
                    "attachment_type": "configuration",
                    "content_type": "application/yaml",
                    "content": "foo: bar",
                },
            ]
        }
    }


# TODO(lucasagomes): add media_type when needed, current implementation
# does not support streaming response, so this is not used
class QueryRequest(BaseModel):
    """Model representing a request for the LLM (Language Model).

    Attributes:
        query: The query string.
        conversation_id: The optional conversation ID (UUID).
        provider: The optional provider.
        model: The optional model.
        system_prompt: The optional system prompt.
        attachments: The optional attachments.

    Example:
        ```python
        query_request = QueryRequest(query="Tell me about Kubernetes")
        ```
    """

    query: str
    conversation_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    attachments: Optional[list[Attachment]] = None

    # provides examples for /docs endpoint
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "query": "write a deployment yaml for the mongodb image",
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "provider": "openai",
                    "model": "model-name",
                    "system_prompt": "You are a helpful assistant",
                    "attachments": [
                        {
                            "attachment_type": "log",
                            "content_type": "text/plain",
                            "content": "this is attachment",
                        },
                        {
                            "attachment_type": "configuration",
                            "content_type": "application/yaml",
                            "content": "kind: Pod\n metadata:\n    name: private-reg",
                        },
                        {
                            "attachment_type": "configuration",
                            "content_type": "application/yaml",
                            "content": "foo: bar",
                        },
                    ],
                }
            ]
        },
    }

    def get_documents(self) -> list[Document]:
        """Return the list of documents from the attachments."""
        if not self.attachments:
            return []
        return [
            Document(content=att.content, mime_type=att.content_type)
            for att in self.attachments  # pylint: disable=not-an-iterable
        ]

    @model_validator(mode="after")
    def validate_provider_and_model(self) -> Self:
        """Perform validation on the provider and model."""
        if self.model and not self.provider:
            raise ValueError("Provider must be specified if model is specified")
        if self.provider and not self.model:
            raise ValueError("Model must be specified if provider is specified")
        return self
