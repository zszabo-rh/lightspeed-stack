"""Unit tests for UnauthorizedResponse model."""

from models.responses import UnauthorizedResponse, DetailModel


class TestUnauthorizedResponse:
    """Test cases for the UnauthorizedResponse model."""

    def test_constructor_without_user_id(self) -> None:
        """Test UnauthorizedResponse when user_id is not provided."""
        ur = UnauthorizedResponse()
        assert isinstance(ur.detail, DetailModel)
        assert ur.detail.response == "Unauthorized"
        assert ur.detail.cause == "Missing or invalid credentials provided by client"

    def test_constructor_with_user_id(self) -> None:
        """Test UnauthorizedResponse when user_id is provided."""
        ur = UnauthorizedResponse(user_id="user_123")
        assert isinstance(ur.detail, DetailModel)
        assert ur.detail.response == "Unauthorized"
        assert ur.detail.cause == "User user_123 is unauthorized"
