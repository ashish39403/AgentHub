# AgentHub Project Guide

## Project

AgentHub is a backend-first personal AI automation platform. The MVP focuses on an engineering student who creates AI agents for recurring tasks such as internship research, Gmail summaries, email ranking, and scheduled task automation.

The frontend will be built separately. This repository should provide production-ready backend APIs, database models, agent execution logic, integrations, scheduled routines, logs, tests, and deployment setup.

## MVP Direction

We are not building a complete general-purpose agent platform in one pass. We are building a focused MVP around a clear internship problem:

- An engineering student needs to find relevant internships daily.
- The student also wants daily Gmail summaries and ranked important emails.
- The student can create agents, attach schedules, and view saved outputs through a future dashboard.

## Tech Stack

- Backend: Python, FastAPI async
- Package/runtime: uv
- Database: PostgreSQL
- ORM: SQLAlchemy 2.0 async
- Migrations: Alembic
- Validation: Pydantic v2
- Auth: JWT access and refresh tokens, pwdlib
- LLM: OpenAI SDK with AICredits/OpenAI-compatible base URLs
- Tools: internal tools first, Composio later
- Scheduler: APScheduler for MVP
- Browser VM: E2B later, not MVP
- Testing: Pytest and HTTPX
- Deployment: Docker and Docker Compose

## Engineering Rules

1. Show a short plan before implementing any feature.
2. Keep changes scoped to the current milestone.
3. Add or update tests with every feature.
4. Never commit secrets, API keys, tokens, or credentials.
5. Secrets must live only in `.env` or environment variables.
6. Keep `.env.example` updated when adding new required settings.
7. Ask before adding a new package or framework.
8. Use the official OpenAI Python SDK for OpenAI-compatible LLM calls instead of custom raw HTTP clients.
9. Prefer simple explicit code over heavy abstractions.
10. Do not use LangChain or heavy agent frameworks for the MVP agent loop.
11. Every user-owned resource must be scoped by `user_id`.
12. Sensitive actions such as sending messages, sending emails, deleting emails, or applying to internships must require explicit user configuration or confirmation.
13. Routine runs and tool actions must be logged.
14. APIs should be frontend-ready, stable, and documented.

## Safety Rules

- Read, summarize, rank, draft, and recommend actions are allowed in the MVP.
- Sending, deleting, applying, or messaging automatically must be gated by explicit user approval or a dedicated safe configuration.
- Agents must have a max-iteration limit.
- Tool errors should be captured and returned in a safe, user-readable form.
- Agent runs should never expose another user's data.

## Development Style

- Use clean architecture boundaries:
  - API routes handle HTTP concerns.
  - Services handle business logic.
  - Repositories handle database access.
  - Agent modules handle LLM/tool execution.
  - Integrations wrap external APIs.
- Keep functions small and testable.
- Use typed request/response schemas.
- Prefer dependency injection for database sessions, auth, and services.
- Keep logs useful but never log secrets.
