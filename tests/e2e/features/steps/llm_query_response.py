"""LLM query and response steps."""

import requests
from behave import then, step  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context

DEFAULT_LLM_TIMEOUT = 60


@step('I change the system prompt to "{system_prompt}"')
def change_system_prompt(context: Context, system_prompt: str) -> None:
    """Change the system prompt."""
    context.system_prompt = system_prompt
    # TODO: add step implementation
    assert context is not None


@step('I modify the request body by removing the "{field}"')
def remove_field_prompt(context: Context, field: str) -> None:
    """Remove the field from the prompt."""
    context.field = field
    # TODO: add step implementation
    assert context is not None


@step("I wait for the response to be completed")
def wait_for_complete_response(context: Context) -> None:
    """Wait for the response to be complete."""
    assert context is not None


@step('I use "{endpoint}" to ask question "{question}"')
def ask_question(context: Context, endpoint: str, question: str) -> None:
    """Call the service REST API endpoint with question."""
    base = f"http://{context.hostname}:{context.port}"
    path = f"{context.api_prefix}/{endpoint}".replace("//", "/")
    url = base + path
    data = {"query": question}
    context.response = requests.post(url, json=data, timeout=DEFAULT_LLM_TIMEOUT)


@then("The response should have proper LLM response format")
def check_llm_response_format(context: Context) -> None:
    """Check the format of response from the service with LLM-generated answer."""
    assert context.response is not None
    response_json = context.response.json()
    assert "conversation_id" in response_json
    assert "response" in response_json


@then("The response should not be truncated")
def check_llm_response_not_truncated(context: Context) -> None:
    """Check that the response from LLM is not truncated."""
    assert context.response is not None
    response_json = context.response.json()
    assert response_json["truncated"] is False


@then("The response should contain following fragments")
def check_fragments_in_response(context: Context) -> None:
    """Check that all specified fragments are present in the LLM response.

    First checks that the HTTP response exists and contains a
    "response" field. For each fragment listed in the scenario's
    table under "Fragments in LLM response", asserts that it
    appears as a substring in the LLM's response. Raises an
    assertion error if any fragment is missing or if the fragments
    table is not provided.
    """
    assert context.response is not None
    response_json = context.response.json()
    response = response_json["response"]

    assert context.table is not None, "Fragments are not specified in table"

    for fragment in context.table:
        expected = fragment["Fragments in LLM response"]
        assert (
            expected in response
        ), f"Fragment '{expected}' not found in LLM response: '{response}'"
