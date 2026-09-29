# AgentHub Backend

AgentHub is a backend-first personal AI automation platform for an engineering student MVP. Users will be able to create agents for internship research, Gmail summaries, scheduled routines, and dashboard-ready logs.

The frontend is intentionally out of scope for this repository. This backend exposes APIs that a separate frontend can consume.

## Current Phase

Milestones 1-12 are implemented:

- FastAPI app
- `/api/v1` router
- health endpoint
- settings module
- standard error shape
- pytest setup
- PostgreSQL with Docker Compose
- SQLAlchemy async models
- Alembic migrations
- secure auth with register, login, refresh, logout, and current user
- user-scoped agent CRUD
- user-scoped conversations and message history
- custom agent loop with deterministic local LLM wrapper and tool calling
- agent-specific tool capabilities with a 10-tool catalog
- routines with manual execution and run logs
- safe Gmail summary tool and controlled scheduled actions
- dashboard summary, recent runs, recent activity, and action item APIs
- OpenAI SDK based LLM client for AICredits/OpenAI-compatible providers
- Dockerfile and Docker Compose setup
- production notes and demo script

## Local Development

```bash
uv sync
copy .env.example .env
uv run pytest
uv run uvicorn app.main:app --reload
```

Health check:

```bash
GET http://localhost:8000/api/v1/health
```

Auth endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Agent endpoints:

```text
POST   /api/v1/agents
GET    /api/v1/agents
GET    /api/v1/agents/{agent_id}
PATCH  /api/v1/agents/{agent_id}
DELETE /api/v1/agents/{agent_id}
```

Conversation endpoints:

```text
POST /api/v1/agents/{agent_id}/conversations
GET  /api/v1/agents/{agent_id}/conversations
GET  /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/messages
POST /api/v1/conversations/{conversation_id}/runs
```

Tool endpoints:

```text
GET /api/v1/tools
GET /api/v1/agents/{agent_id}/tools
PUT /api/v1/agents/{agent_id}/tools
```

Routine endpoints:

```text
POST   /api/v1/routines
GET    /api/v1/routines
GET    /api/v1/routines/{routine_id}
PATCH  /api/v1/routines/{routine_id}
DELETE /api/v1/routines/{routine_id}
POST   /api/v1/routines/{routine_id}/run
GET    /api/v1/routines/{routine_id}/runs
```

Integration endpoints:

```text
GET /api/v1/integrations/gmail/status
```

Dashboard endpoints:

```text
GET /api/v1/dashboard/summary
GET /api/v1/dashboard/recent-runs
GET /api/v1/dashboard/recent-activity
GET /api/v1/dashboard/action-items
```

## Database

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Local connection:

```text
Host: 127.0.0.1
Port: 5433
Database: agenthub
Username: agenthub
Password: agenthub
```

Run migrations after migration files are created:

```bash
uv run alembic upgrade head
```

## Docker

Run the API and PostgreSQL together:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000/api/v1/health
```

## LLM Provider

Local development defaults to the deterministic mock LLM:

```text
LLM_PROVIDER=mock
```

For real model calls through AICredits or another OpenAI-compatible provider:

```text
LLM_PROVIDER=aicredits
AICREDITS_BASE_URL=<provider-base-url>
AICREDITS_API_KEY=<secret>
```

Configured model roles live in `.env`:

```text
LLM_MODEL_DEFAULT
LLM_MODEL_FAST
LLM_MODEL_SMART
LLM_MODEL_REASONING
LLM_MODEL_CHEAP
LLM_MODEL_EXPERIMENTAL
```

## Docs

- Production notes: `docs/production.md`
- Demo script: `docs/demo-script.md`
- Milestone plan: `docs/milestones.md`
- Architecture diagram: `docs/architecture.svg`
