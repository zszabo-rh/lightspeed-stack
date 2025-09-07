"""Unit tests for StatusResponse model."""

from models.responses import StatusResponse


class TestStatusResponse:
    """Test cases for the StatusResponse model."""

    def test_constructor_feedback_enabled(self) -> None:
        """Test the StatusResponse constructor."""
        sr = StatusResponse(functionality="feedback", status={"enabled": True})
        assert sr.functionality == "feedback"
        assert sr.status == {"enabled": True}

    def test_constructor_feedback_disabled(self) -> None:
        """Test the StatusResponse constructor."""
        sr = StatusResponse(functionality="feedback", status={"enabled": False})
        assert sr.functionality == "feedback"
        assert sr.status == {"enabled": False}
