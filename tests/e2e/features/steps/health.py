"""Implementation of common test steps."""

from behave import given  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context


@given("The llama-stack connection is disrupted")
def llama_stack_connection_broken(context: Context) -> None:
    """Break llama_stack connection."""
    # TODO: add step implementation
    assert context is not None


@given("the service is stopped")
def stop_service(context: Context) -> None:
    """Stop service."""
    # TODO: add step implementation
    assert context is not None
