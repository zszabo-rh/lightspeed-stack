"""Implementation of common test steps."""

from behave import then  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context


@then("The body of the response has proper name {service_name} and version {version}")
def check_name_version(context: Context, service_name: str, version: str) -> None:
    """Check proper service name and version number."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    assert response_json["name"] == service_name, f"name is {response_json["name"]}"
    assert (
        response_json["service_version"] == version
    ), f"version is {response_json["service_version"]}"


@then("The body of the response has llama-stack version {llama_version}")
def check_llama_version(context: Context, llama_version: str) -> None:
    """Check proper llama-stack version number."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    assert (
        response_json["llama_stack_version"] == llama_version
    ), f"llama-stack version is {response_json["llama_stack_version"]}"


@then("The body of the response has proper model structure")
def check_model_structure(context: Context) -> None:
    """Check that the first LLM model has the correct structure and required fields."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    assert "models" in response_json, "Response missing 'models' field"
    models = response_json["models"]
    assert len(models) > 0, "Response has empty list of models"

    # Find first LLM model (same logic as environment.py)
    llm_model = None
    for model in models:
        if model.get("api_model_type") == "llm":
            llm_model = model
            break

    assert llm_model is not None, "No LLM model found in response"

    # Get expected values from context
    expected_model = context.default_model
    expected_provider = context.default_provider

    # Validate structure and values
    assert llm_model["type"] == "model", "type should be 'model'"
    assert llm_model["api_model_type"] == "llm", "api_model_type should be 'llm'"
    assert llm_model["model_type"] == "llm", "model_type should be 'llm'"
    assert (
        llm_model["provider_id"] == expected_provider
    ), f"provider_id should be '{expected_provider}'"
    assert (
        llm_model["provider_resource_id"] == expected_model
    ), f"provider_resource_id should be '{expected_model}'"
    assert (
        llm_model["identifier"] == f"{expected_provider}/{expected_model}"
    ), f"identifier should be '{expected_provider}/{expected_model}'"
