"""Implementation of common test steps."""

import json
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


@then("The body of the response has proper shield structure")
def check_shield_structure(context: Context) -> None:
    """Check that the first shield has the correct structure and required fields."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    assert "shields" in response_json, "Response missing 'shields' field"
    shields = response_json["shields"]
    assert len(shields) > 0, "Response has empty list of shields"

    # Find first shield
    found_shield = None
    for shield in shields:
        if shield.get("type") == "shield":
            found_shield = shield
            break

    assert found_shield is not None, "No shield found in response"

    expected_model = context.default_model

    # Validate structure and values
    assert found_shield["type"] == "shield", "type should be 'shield'"
    assert (
        found_shield["provider_id"] == "llama-guard"
    ), "provider_id should be 'llama-guard'"
    assert (
        found_shield["provider_resource_id"] == expected_model
    ), f"provider_resource_id should be '{expected_model}'"
    assert (
        found_shield["identifier"] == "llama-guard-shield"
    ), "identifier should be 'llama-guard-shield'"


@then("The response contains {count:d} tools listed for provider {provider_name}")
def check_tool_count(context: Context, count: int, provider_name: str) -> None:
    """Check that the number of tools for defined provider is correct."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    assert "tools" in response_json, "Response missing 'tools' field"
    tools = response_json["tools"]
    assert len(tools) > 0, "Response has empty list of tools"

    provider_tools = []

    for tool in tools:
        if tool["provider_id"] == provider_name:
            provider_tools.append(tool)

    assert len(provider_tools) == count


@then("The body of the response has proper structure for provider {provider_name}")
def check_tool_structure(context: Context, provider_name: str) -> None:
    """Check that the first listed tool for defined provider has the correct structure."""
    response_json = context.response.json()
    assert response_json is not None, "Response is not valid JSON"

    expected_json = json.loads(context.text)

    assert "tools" in response_json, "Response missing 'tools' field"
    tools = response_json["tools"]
    assert len(tools) > 0, "Response has empty list of tools"

    provider_tool = None

    for tool in tools:
        if tool["provider_id"] == provider_name:
            provider_tool = tool
            break

    assert provider_tool is not None, "No tool found in response"

    # Validate structure and values
    assert (
        provider_tool["identifier"] == expected_json["identifier"]
    ), f"identifier should be {expected_json["identifier"]}, but was {provider_tool["identifier"]}"
    assert (
        provider_tool["description"] == expected_json["description"]
    ), f"description should be {expected_json["description"]}"
    assert (
        provider_tool["provider_id"] == expected_json["provider_id"]
    ), f"provider_id should be {expected_json["provider_id"]}"
    assert (
        provider_tool["toolgroup_id"] == expected_json["toolgroup_id"]
    ), f"toolgroup_id should be {expected_json["toolgroup_id"]}"
    assert (
        provider_tool["server_source"] == expected_json["server_source"]
    ), f"server_source should be {expected_json["server_source"]}"
    assert (
        provider_tool["type"] == expected_json["type"]
    ), f"type should be {expected_json["type"]}"
