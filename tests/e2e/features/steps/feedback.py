"""Implementation of common test steps."""

from behave import given, when  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context
import requests

# default timeout for HTTP operations
DEFAULT_TIMEOUT = 10


@when(
    "I access endpoint {endpoint:w} using HTTP POST with conversation ID {conversationID:w}"
)
def access_rest_api_endpoint_post(
    context: Context, endpoint: str, conversation_id: str
) -> None:
    """Send POST HTTP request with JSON payload to tested service.

    The JSON payload is retrieved from `context.text` attribute,
    which must not be None. The response is stored in
    `context.response` attribute.
    """
    base = f"http://{context.hostname}:{context.port}"
    path = f"{context.api_prefix}/{endpoint}".replace("//", "/")
    url = base + path

    assert conversation_id is not None, "Payload needs to be specified"
    # TODO: finish the conversation ID handling

    # perform REST API call
    context.response = requests.post(url, timeout=DEFAULT_TIMEOUT)


@given("I disable the feedback")
def disable_feedback(context: Context) -> None:
    """Disable feedback."""
    # TODO: add step implementation
    assert context is not None
