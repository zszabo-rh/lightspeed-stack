"""Implementation of common test steps."""

from behave import given, then  # pyright: ignore[reportAttributeAccessIssue]
from behave.runner import Context


@then("The body of the response has proper username")
def check_body_username(context: Context) -> None:
    """Check that the username is correct in response."""
    # TODO: add step implementation
    assert context is not None


@given("I remove the auth header")
def remove_auth_header(context: Context) -> None:
    """Remove the auth header."""
    # TODO: add step implementation
    assert context is not None


@given("I modify the auth header so that the user is it authorized")
def modify_auth_header(context: Context) -> None:
    """Modify the auth header making the user unauthorized."""
    # TODO: add step implementation
    assert context is not None
