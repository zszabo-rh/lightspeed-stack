# Agent Context Preloading

## Overview

Agent Context Preloading is a feature that allows the assisted-chat agent to automatically gather context about the user's environment when a new conversation session is created. This eliminates the need for the agent to repeatedly call MCP tools during conversations and improves the user experience by reducing back-and-forth interactions.

## Use Cases

This feature addresses scenarios where the agent needs contextual knowledge to provide better responses:

1. **Domain-specific reference data**: Pre-load lists, catalogs, or configurations that the agent needs to reference
2. **User-specific context**: Load user's resources, preferences, or settings at the start of a conversation
3. **System state information**: Provide current system status or available options upfront

**Example for assisted-chat**: Pre-loading user clusters, available versions, and operator bundles allows the agent to answer questions like "create a cluster with the latest version" or "get ISO for my production cluster" without additional tool calls.

## How It Works

When context preloading is enabled:

1. **Session Creation**: When a new conversation session is created, configured MCP tools are automatically executed.
2. **Context Storage**: Results are formatted and stored as a hidden turn in the conversation history.
3. **Agent Access**: The agent has access to this context in all subsequent turns via the conversation history.
4. **No User Visibility**: The hidden context turn is automatically filtered out from user-facing API responses.
5. **One-Time Operation**: Context is loaded only once per session, minimizing token usage.

## Configuration

Add the following to your `lightspeed-stack.yaml`:

```yaml
# First, ensure you have MCP servers configured
mcp_servers:
  - name: mcp::assisted
    url: "http://assisted-service-mcp:8000/mcp"

# Then configure agent context preloading
agent_context_preloading:
  enabled: true  # Set to false to disable
  intro_message: "Here is contextual information for this session:"
  tools:
    # List of MCP tools to execute for context preloading
    # IMPORTANT: mcp_server must match the "name" field in your mcp_servers configuration
    - tool_name: "list_clusters"
      mcp_server: "mcp::assisted"  # Must match the MCP server name above
      label: "Your Clusters"  # Optional: custom display label
      empty_message: "You currently have no clusters."  # Optional: message when empty
    
    - tool_name: "list_versions"
      mcp_server: "mcp::assisted"
      label: "Available Versions"
      empty_message: "No versions available."
    
    - tool_name: "list_operator_bundles"
      mcp_server: "mcp::assisted"
      label: "Available Operator Bundles"
```

### Configuration Options

#### Top-Level Options

##### `enabled` (boolean, default: `false`)
Whether to enable context preloading. Set to `true` to activate the feature.

##### `intro_message` (string, default: `"Here is contextual information for this session:"`)
Introductory message that appears before the context data. Customize this to fit your domain/use case.

##### `tools` (array of objects)
List of MCP tools to execute when creating a new session.

#### Tool Configuration Options

Each tool in the `tools` array supports:

- **`tool_name`** (string, required): Name of the MCP tool to execute
- **`mcp_server`** (string, required): Name of the MCP server providing the tool. **Must match the `name` field in your `mcp_servers` configuration** (e.g., `mcp::assisted`, not just `assisted`)
- **`label`** (string, optional): Custom label to display instead of the tool name
- **`empty_message`** (string, optional): Message to display when the tool returns empty data (empty list, empty dict, null, etc.)

## Tool Result Format

Tool results are included as-is in the context message, with an optional label. The tool's output format is preserved exactly as returned by the MCP server.

**Example output**:
```
**Your Clusters**:
[{"id": "cluster-1", "name": "production", "status": "ready"}, {"id": "cluster-2", "name": "development", "status": "installing"}]
```

**For empty results** (when `empty_message` is configured):
```
**Your Clusters**: You currently have no clusters.
```

The agent is responsible for interpreting and presenting this data appropriately to the user.

## Performance Considerations

### Token Usage

- **Initial Turn**: Context data is loaded once and stored in the first turn
- **Subsequent Turns**: Context is included in the conversation history (minimal incremental cost)
- **No Per-Turn Overhead**: Unlike on-demand tool calling, there's no additional tool execution cost per turn

### Latency

- Context loading happens asynchronously during session creation
- Does not block the user's first message
- Failed tool executions are logged but don't prevent session creation

## Error Handling

The implementation includes robust error handling:

1. **Tool Execution Failures**: If a tool fails, execution continues with other tools
2. **Missing MCP Servers**: Validated at configuration time and runtime
3. **Invalid Tool Names**: Validated against available tools
4. **Network Issues**: Logged and gracefully handled without blocking session creation

## Implementation Details

### Hidden Turn Marker

Context preloading turns are marked with the prefix `CONTEXT_PRELOAD:` which allows them to be:
- Identified and filtered from user-facing responses
- Preserved in the conversation history for agent access
- Distinguished from regular conversation turns

### Response Filtering

The `simplify_session_data()` function in `conversations.py` automatically filters out context preloading turns when returning conversation history to users.

### MCP Headers

Authentication headers for MCP servers are automatically passed to context preloading tools, ensuring proper access control.

## Troubleshooting

### MCP server toolgroup not found

If you see errors like:
```
MCP server toolgroup 'assisted-service-mcp' not found. Available toolgroups: ['builtin::rag', 'mcp::assisted']
```

**Solution**: The `mcp_server` value in `agent_context_preloading.tools` must exactly match the `name` field in your `mcp_servers` configuration. In the example above, change:
```yaml
mcp_server: "assisted-service-mcp"  # Wrong
```
to:
```yaml
mcp_server: "mcp::assisted"  # Correct - matches the MCP server name
```

### Context not appearing in agent responses

1. Verify `enabled: true` in configuration
2. **Check that MCP server names match exactly** (see above)
3. Verify tool names are correct (case-sensitive)
4. Check logs for tool execution errors

### Tools failing to execute

1. Verify MCP server is registered and accessible
2. Check MCP authentication headers are properly configured
3. Review logs for specific error messages
4. Verify tools don't require parameters (currently unsupported)

### Conversation history showing context

If context turns are visible in the API:
1. Verify the turn starts with `CONTEXT_PRELOAD:` marker
2. Check `simplify_session_data()` filtering logic
3. Review conversation endpoint implementation

