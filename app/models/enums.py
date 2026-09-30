from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class RoutineRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ToolActionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IntegrationProvider(StrEnum):
    GMAIL = "gmail"
    NOTION = "notion"
    GITHUB = "github"


class IntegrationConnectionStatus(StrEnum):
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
