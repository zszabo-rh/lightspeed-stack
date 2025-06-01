"""Unit tests for runners."""

from unittest.mock import patch


from runners.uvicorn import start_uvicorn


def test_start_uvicorn() -> None:
    """Test the function to start Uvicorn server."""
    # don't start real Uvicorn server
    with patch("uvicorn.run") as mocked_run:
        start_uvicorn()
        mocked_run.assert_called_once_with(
            "app.main:app",
            host="localhost",
            port=8080,
            workers=1,
            log_level=20,
            use_colors=True,
            access_log=True,
        )
