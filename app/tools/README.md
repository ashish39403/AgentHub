# Tool Layer

This folder contains backend-owned tools that agents can use through the tool registry.

## Runtime Flow

```text
Agent run
-> ToolRegistry definitions
-> LLM/tool router chooses a tool
-> ToolRegistry.execute(...)
-> concrete tool handler
-> tool result saved as message + tool_action_log
-> LLM receives formatted tool output
-> final answer passes guardrails
```

## Files

- `registry.py` - central registry of tool names, schemas, handlers, and safety metadata.
- `context.py` - runtime context passed into tools, including database session, user id, and agent id.
- `search_tool.py` - web search tool using Serper first and optional Tavily fallback.
- `datetime_tool.py` - current datetime helper.
- `internal_tools.py` - internal safe tools such as text summarization and draft message creation.
- `memory_tools.py` - long-term agent memory save/read tools backed by the database.
- `gmail_tools.py` - Gmail summary/ranking tool; uses Composio when connected and safe fallback data otherwise.
- `integration_tools.py` - Composio-backed GitHub/Notion tools and safe Slack action preparation.
- `action_policy.py` - safety checks for actions that require confirmation.

## Safety

Read-only tools can run directly. External write/send/delete actions must be prepared or confirmation-gated. Tool calls are scoped by `user_id` and `agent_id` through `ToolContext`.
