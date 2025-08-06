"""Shared pytest fixtures for unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture(name="prepare_agent_mocks", scope="function")
def prepare_agent_mocks_fixture(mocker):
    """Prepare for mock for the LLM agent.

    Provides common mocks for AsyncLlamaStackClient and AsyncAgent
    with proper agent_id setup to avoid initialization errors.

    Returns:
        tuple: (mock_client, mock_agent)
    """
    mock_client = mocker.AsyncMock()
    mock_agent = mocker.AsyncMock()

    # Set up agent_id property to avoid "Agent ID not initialized" error
    mock_agent._agent_id = "test_agent_id"  # pylint: disable=protected-access
    mock_agent.agent_id = "test_agent_id"

    # Set up create_turn mock structure for query endpoints that need it
    mock_agent.create_turn.return_value.steps = []

    yield mock_client, mock_agent
