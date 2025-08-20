"""Implementation of common test steps."""

from behave import then  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context


@then(
    "The body of the response has proper name {system_prompt:w} and version {version:w}"
)
def check_name_version(context: Context, system_prompt: str, version: str) -> None:
    """Check proper name and version number."""
    context.system_prompt = system_prompt
    context.version = version
    # TODO: add step implementation
    assert context is not None


@then("The body of the response has proper metrics")
def check_metrics(context: Context) -> None:
    """Check proper metrics."""
    # TODO: add step implementation
    assert context is not None
