from models.responses import QueryResponse


class TestQueryResponse:
    """Test cases for the QueryResponse model."""

    def test_constructor(self) -> None:
        """Test the QueryResponse constructor."""
        qr = QueryResponse(
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
            response="LLM answer",
        )
        assert qr.conversation_id == "123e4567-e89b-12d3-a456-426614174000"
        assert qr.response == "LLM answer"

    def test_optional_conversation_id(self) -> None:
        """Test the QueryResponse with default conversation ID."""
        qr = QueryResponse(response="LLM answer")
        assert qr.conversation_id is None
        assert qr.response == "LLM answer"
