"""Implementation of common test steps."""

from behave import then  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context


@then("The proper conversation is returned")
def check_returned_conversation(context: Context) -> None:
    """Check the conversation in response."""
    # TODO: add step implementation
    assert context.response is not None


@then("the deleted conversation is not found")
def check_deleted_conversation(context: Context) -> None:
    """Check whether the deleted conversation is gone."""
    # TODO: add step implementation
    assert context.response is not None
