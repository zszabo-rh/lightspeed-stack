"""Unit tests for UnauthorizedResponse model."""

import pytest

from pydantic import ValidationError

from models.responses import UnauthorizedResponse


class TestUnauthorizedResponse:
    """Test cases for the UnauthorizedResponse model."""

    def test_constructor(self) -> None:
        """Test the UnauthorizedResponse constructor."""
        ur = UnauthorizedResponse(
            detail="Missing or invalid credentials provided by client"
        )
        assert ur.detail == "Missing or invalid credentials provided by client"

    def test_constructor_fields_required(self) -> None:
        """Test the UnauthorizedResponse constructor."""
        with pytest.raises(ValidationError):
            _ = UnauthorizedResponse()  # pyright: ignore
