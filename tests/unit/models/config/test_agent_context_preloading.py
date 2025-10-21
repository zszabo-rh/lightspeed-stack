"""Unit tests for agent context preloading configuration."""

import pytest
from pydantic import ValidationError

from models.config import AgentContextPreloading, ContextPreloadingTool


class TestContextPreloadingTool:
    """Tests for ContextPreloadingTool configuration model."""

    def test_creates_with_required_fields(self):
        """Test creating ContextPreloadingTool with required fields."""
        tool = ContextPreloadingTool(tool_name="test_tool", mcp_server="test_server")
        assert tool.tool_name == "test_tool"
        assert tool.mcp_server == "test_server"

    def test_creates_with_all_fields(self):
        """Test creating ContextPreloadingTool with all fields."""
        tool = ContextPreloadingTool(
            tool_name="test_tool", 
            mcp_server="test_server", 
            label="Custom Label",
            empty_message="No data"
        )
        assert tool.tool_name == "test_tool"
        assert tool.mcp_server == "test_server"
        assert tool.label == "Custom Label"
        assert tool.empty_message == "No data"

    def test_rejects_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError):
            ContextPreloadingTool(mcp_server="test_server")

        with pytest.raises(ValidationError):
            ContextPreloadingTool(tool_name="test_tool")


class TestAgentContextPreloading:
    """Tests for AgentContextPreloading configuration model."""

    def test_creates_with_defaults(self):
        """Test creating AgentContextPreloading with default values."""
        config = AgentContextPreloading()
        assert config.enabled is False
        assert config.intro_message == "Here is contextual information for this session:"
        assert config.tools == []

    def test_creates_with_enabled_true(self):
        """Test creating AgentContextPreloading with enabled=True."""
        config = AgentContextPreloading(enabled=True)
        assert config.enabled is True
        assert config.tools == []

    def test_creates_with_tools(self):
        """Test creating AgentContextPreloading with tools."""
        tool1 = ContextPreloadingTool(tool_name="tool1", mcp_server="server1")
        tool2 = ContextPreloadingTool(
            tool_name="tool2", mcp_server="server2", label="Custom Tool"
        )
        config = AgentContextPreloading(enabled=True, tools=[tool1, tool2])
        
        assert config.enabled is True
        assert len(config.tools) == 2
        assert config.tools[0].tool_name == "tool1"
        assert config.tools[1].tool_name == "tool2"
        assert config.tools[1].label == "Custom Tool"

    def test_serializes_to_dict(self):
        """Test serialization to dictionary."""
        tool = ContextPreloadingTool(tool_name="test_tool", mcp_server="test_server")
        config = AgentContextPreloading(enabled=True, tools=[tool])

        config_dict = config.model_dump()

        assert config_dict["enabled"] is True
        assert len(config_dict["tools"]) == 1
        assert config_dict["tools"][0]["tool_name"] == "test_tool"
        assert config_dict["tools"][0]["mcp_server"] == "test_server"
        assert config_dict["tools"][0]["label"] is None
        assert config_dict["tools"][0]["empty_message"] is None

    def test_parses_from_dict(self):
        """Test parsing from dictionary."""
        data = {
            "enabled": True,
            "tools": [
                {
                    "tool_name": "list_clusters",
                    "mcp_server": "assisted-service-mcp",
                    "label": "Your Clusters",
                }
            ],
        }
        
        config = AgentContextPreloading(**data)
        
        assert config.enabled is True
        assert len(config.tools) == 1
        assert config.tools[0].tool_name == "list_clusters"
        assert config.tools[0].label == "Your Clusters"

    def test_rejects_extra_fields(self):
        """Test that extra fields are rejected (extra='forbid')."""
        with pytest.raises(ValidationError):
            AgentContextPreloading(enabled=True, invalid_field="value")

    def test_empty_tools_list_allowed(self):
        """Test that empty tools list is allowed."""
        config = AgentContextPreloading(enabled=True, tools=[])
        assert config.enabled is True
        assert config.tools == []

    def test_custom_intro_message(self):
        """Test that custom intro message can be set."""
        custom_msg = "Custom introduction message"
        config = AgentContextPreloading(enabled=True, intro_message=custom_msg)
        assert config.intro_message == custom_msg

