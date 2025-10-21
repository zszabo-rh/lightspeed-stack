"""Unit tests for context preloader utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.config import AgentContextPreloading, ContextPreloadingTool
from utils.context_preloader import (
    CONTEXT_PRELOAD_MARKER,
    execute_preloading_tools,
    execute_single_tool,
    format_tool_result,
    is_context_preloading_turn,
)


class TestIsContextPreloadingTurn:
    """Tests for is_context_preloading_turn function."""

    def test_identifies_context_preloading_turn(self):
        """Test that context preloading turns are correctly identified."""
        content = f"{CONTEXT_PRELOAD_MARKER}Some context data"
        assert is_context_preloading_turn(content) is True

    def test_rejects_non_preloading_turn(self):
        """Test that regular turns are not identified as preloading."""
        content = "Regular user message"
        assert is_context_preloading_turn(content) is False

    def test_handles_non_string_content(self):
        """Test that non-string content is handled safely."""
        assert is_context_preloading_turn(None) is False
        assert is_context_preloading_turn([]) is False
        assert is_context_preloading_turn({"key": "value"}) is False


class TestFormatToolResult:
    """Tests for format_tool_result function."""

    def test_formats_result_with_tool_name(self):
        """Test formatting tool result with default tool name."""
        tool_config = ContextPreloadingTool(
            tool_name="test_tool", mcp_server="test_server"
        )
        result = MagicMock()
        result.content = [MagicMock(text='{"key": "value"}')]

        formatted = format_tool_result(tool_config, result)

        assert "test_tool" in formatted
        assert "key" in formatted
        assert "value" in formatted

    def test_uses_custom_label(self):
        """Test that custom label is used instead of tool name."""
        tool_config = ContextPreloadingTool(
            tool_name="test_tool", 
            mcp_server="test_server", 
            label="Custom Label"
        )
        result = MagicMock()
        result.content = [MagicMock(text='{"key": "value"}')]

        formatted = format_tool_result(tool_config, result)

        assert "Custom Label" in formatted
        assert "test_tool" not in formatted

    def test_uses_empty_message(self):
        """Test that empty message is used for empty results."""
        tool_config = ContextPreloadingTool(
            tool_name="test_tool",
            mcp_server="test_server",
            label="Test Data",
            empty_message="No data available."
        )
        result = MagicMock()
        result.content = [MagicMock(text='[]')]

        formatted = format_tool_result(tool_config, result)

        assert "Test Data" in formatted
        assert "No data available" in formatted

    def test_returns_raw_result(self):
        """Test that raw result is returned as-is."""
        tool_config = ContextPreloadingTool(
            tool_name="test_tool",
            mcp_server="test_server"
        )
        result = MagicMock()
        result.content = [MagicMock(text='Some raw text result')]

        formatted = format_tool_result(tool_config, result)

        assert "test_tool" in formatted
        assert "Some raw text result" in formatted


@pytest.mark.asyncio
class TestExecuteSingleTool:
    """Tests for execute_single_tool function."""

    async def test_executes_tool_successfully(self):
        """Test successful tool execution."""
        # Setup mocks
        client = AsyncMock()
        toolgroup = MagicMock()
        toolgroup.provider_resource_id = "test-mcp-server"
        toolgroup.identifier = "test-toolgroup-id"
        client.toolgroups.list.return_value = [toolgroup]

        tool = MagicMock()
        tool.identifier = "test_tool"
        client.tools.list.return_value = [tool]

        result = MagicMock()
        result.content = [MagicMock(text='{"result": "success"}')]
        client.tool_runtime.invoke_tool.return_value = result

        tool_config = ContextPreloadingTool(
            tool_name="test_tool", mcp_server="test-mcp-server"
        )

        # Execute
        result = await execute_single_tool(client, tool_config, {})

        # Verify
        assert result.content[0].text == '{"result": "success"}'
        client.tool_runtime.invoke_tool.assert_called_once()

    async def test_raises_error_for_missing_toolgroup(self):
        """Test error handling for missing toolgroup."""
        client = AsyncMock()
        client.toolgroups.list.return_value = []

        tool_config = ContextPreloadingTool(
            tool_name="test_tool", mcp_server="missing-server"
        )

        with pytest.raises(ValueError, match="MCP server toolgroup.*not found"):
            await execute_single_tool(client, tool_config, {})

    async def test_raises_error_for_missing_tool(self):
        """Test error handling for missing tool."""
        client = AsyncMock()
        toolgroup = MagicMock()
        toolgroup.provider_resource_id = "test-mcp-server"
        toolgroup.identifier = "test-toolgroup-id"
        client.toolgroups.list.return_value = [toolgroup]

        client.tools.list.return_value = []

        tool_config = ContextPreloadingTool(
            tool_name="missing_tool", mcp_server="test-mcp-server"
        )

        with pytest.raises(ValueError, match="Tool.*not found"):
            await execute_single_tool(client, tool_config, {})


@pytest.mark.asyncio
class TestExecutePreloadingTools:
    """Tests for execute_preloading_tools function."""

    async def test_skips_when_disabled(self):
        """Test that preloading is skipped when disabled."""
        config = AgentContextPreloading(enabled=False, tools=[])
        result = await execute_preloading_tools(AsyncMock(), config, {})
        assert result == ""

    async def test_skips_when_no_tools(self):
        """Test that preloading is skipped when no tools configured."""
        config = AgentContextPreloading(enabled=True, tools=[])
        result = await execute_preloading_tools(AsyncMock(), config, {})
        assert result == ""

    @patch("utils.context_preloader.execute_single_tool")
    async def test_executes_configured_tools(self, mock_execute):
        """Test that all configured tools are executed."""
        # Setup
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"data": "test"}')]
        mock_execute.return_value = mock_result

        tool1 = ContextPreloadingTool(
            tool_name="tool1", mcp_server="server1"
        )
        tool2 = ContextPreloadingTool(
            tool_name="tool2", mcp_server="server1"
        )
        config = AgentContextPreloading(enabled=True, tools=[tool1, tool2])

        # Execute
        result = await execute_preloading_tools(AsyncMock(), config, {})

        # Verify
        assert CONTEXT_PRELOAD_MARKER in result
        assert mock_execute.call_count == 2

    @patch("utils.context_preloader.execute_single_tool")
    async def test_continues_on_tool_failure(self, mock_execute):
        """Test that execution continues when a tool fails."""
        # Setup - first tool fails, second succeeds
        mock_execute.side_effect = [
            Exception("Tool failed"),
            MagicMock(content=[MagicMock(text='{"data": "success"}')]),
        ]

        tool1 = ContextPreloadingTool(
            tool_name="tool1", mcp_server="server1"
        )
        tool2 = ContextPreloadingTool(
            tool_name="tool2", mcp_server="server1"
        )
        config = AgentContextPreloading(enabled=True, tools=[tool1, tool2])

        # Execute
        result = await execute_preloading_tools(AsyncMock(), config, {})

        # Verify - should still return result from successful tool
        assert result != ""
        assert mock_execute.call_count == 2

