# Integration Layer

This folder wraps external providers behind backend-owned clients.

## Files

- `composio_client.py` - low-level Composio HTTP client for connection links, connected accounts, tool execution, and disconnect.
- `gmail.py` - Gmail read fallback/status helper used by the Gmail summary tool.

## Runtime Flow

```text
Integration API / Tool
-> integration_service
-> ComposioClient
-> Composio connected account / provider tool
-> normalized result
-> tool output
```

AgentHub stores connection metadata in `integration_connections`. Provider tokens are handled by Composio and must not be exposed to the frontend.
