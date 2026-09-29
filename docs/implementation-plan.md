# AgentHub End-to-End Implementation Plan

## Purpose

This file is the build roadmap for AgentHub. It converts the PRD, spec, and design into a practical implementation sequence so the backend can be built cleanly, tested step by step, and connected later to an external frontend.

The MVP is focused on an engineering student who wants personal AI agents for:

- daily internship research
- Gmail summaries and important email ranking
- scheduled agent routines
- saved results and logs for a dashboard

The frontend is out of scope for this repository. This backend should expose clean APIs that any frontend can consume.

## Build Principles

1. Build one milestone at a time.
2. Keep every feature small, testable, and explainable.
3. Add tests with each feature.
4. Keep secrets only in `.env`.
5. Update `.env.example` whenever a new environment variable is added.
6. Ask before adding new packages.
7. Keep all user data scoped by `user_id`.
8. Log routine runs and tool actions.
9. Gate dangerous actions such as sending, deleting, or applying.
10. Prefer clear backend architecture over shortcuts.

## Final Backend Scope

The backend should support:

- user registration and login
- JWT access and refresh tokens
- user-scoped agent CRUD
- conversations and messages
- custom agent loop with tool calling
- internship research agent behavior
- Gmail summary agent behavior
- scheduled routines
- routine run logs
- tool action logs
- dashboard-ready APIs
- Docker-based local setup
- tests and API documentation

## Recommended Folder Structure

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── agents.py
│   │       ├── conversations.py
│   │       ├── routines.py
│   │       └── dashboard.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── agent.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── routine.py
│   │   ├── routine_run.py
│   │   └── tool_action_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── agent.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── routine.py
│   │   ├── routine_run.py
│   │   └── dashboard.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── agents.py
│   │   ├── conversations.py
│   │   ├── routines.py
│   │   └── routine_runs.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── agent_service.py
│   │   ├── conversation_service.py
│   │   ├── routine_service.py
│   │   └── dashboard_service.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── loop.py
│   │   ├── prompts.py
│   │   ├── types.py
│   │   └── llm_client.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── internship_research.py
│   │   ├── gmail_summary.py
│   │   ├── datetime_tool.py
│   │   └── draft_message.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── composio_client.py
│   │   ├── gmail.py
│   │   └── search.py
│   └── scheduler/
│       ├── __init__.py
│       ├── scheduler.py
│       └── jobs.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_agents.py
│   ├── test_agent_loop.py
│   └── test_routines.py
├── alembic/
├── docs/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Milestone 0: Planning Docs

Status: done after these files exist:

- `PRD.md`
- `AGENTS.md`
- `docs/spec.md`
- `docs/design.md`
- `docs/implementation-plan.md`

Done means:

- MVP scope is clear.
- Non-goals are clear.
- Safety rules are written.
- Backend/frontend boundary is clear.

## Milestone 1: Backend Foundation

Goal: create a clean FastAPI backend skeleton.

Build:

- `pyproject.toml`
- FastAPI app in `app/main.py`
- API v1 router
- settings in `app/core/config.py`
- standard error response helper
- `/api/v1/health`
- pytest setup
- `.env.example`

Tests:

- health endpoint returns success
- app starts with test settings

Done means:

- backend runs locally
- tests pass
- project structure is ready for real features

## Milestone 2: Database Foundation

Goal: connect async PostgreSQL with migrations.

Build:

- SQLAlchemy async engine/session
- declarative base
- Alembic setup
- initial models:
  - users
  - agents
  - conversations
  - messages
  - routines
  - routine_runs
  - tool_action_logs
- first migration
- Docker Compose with PostgreSQL

Tests:

- test database session works
- migrations can run
- model creation works in test DB

Done means:

- local Postgres works through Docker
- database schema can be recreated from migrations

## Milestone 3: Auth

Goal: secure all user-owned APIs.

Build:

- password hashing with `pwdlib`
- user registration
- login
- access token creation
- refresh token creation
- current user dependency
- `/api/v1/auth/me`
- consistent auth errors

Tests:

- register user
- duplicate email rejected
- login succeeds with correct password
- login fails with wrong password
- protected route requires token

Done means:

- user identity works end to end
- future resources can be scoped safely

## Milestone 4: Agent CRUD

Goal: users can create and manage agents.

Build:

- agent model/repository/service
- create agent
- list current user's agents
- get one agent
- update agent
- delete agent
- ownership checks

Tests:

- create agent
- list only own agents
- cannot read another user's agent
- update/delete only own agent

Done means:

- the future frontend can manage user agents safely

## Milestone 5: Conversations And Messages

Goal: store chat history for each agent.

Build:

- create conversation for an agent
- list conversations for an agent
- get conversation detail
- save user messages
- save assistant messages
- save tool messages

Tests:

- create conversation
- add messages
- history is ordered
- ownership checks work

Done means:

- agents have persistent memory through saved conversation history

## Milestone 6: Core Agent Loop

Goal: implement the custom tool-calling agent loop.

Build:

- LLM client wrapper
- agent loop input/output types
- tool registry
- max iteration limit
- tool call execution
- final response saving
- safe error handling

Initial internal tools:

- date/time tool
- internship research mock/tool
- draft message tool
- save report tool

Tests:

- loop returns final answer without tools
- loop executes a tool call
- loop stops at max iterations
- tool errors are handled safely

Done means:

- the backend has a real explainable agent loop
- no heavy agent framework is required

## Milestone 7: Internship Research MVP

Goal: make the first product-specific agent useful.

Build:

- internship research tool
- input fields such as role, skills, location, remote preference, and experience level
- ranking logic
- summarized output format
- saved report output

Suggested output structure:

```json
{
  "summary": "string",
  "top_opportunities": [
    {
      "title": "string",
      "company": "string",
      "location": "string",
      "reason": "string",
      "apply_url": "string",
      "priority": "high"
    }
  ],
  "action_items": ["string"]
}
```

Tests:

- research tool returns structured results
- ranking is deterministic for mock data
- agent can summarize tool results

Done means:

- demo can show a student getting ranked internship opportunities

## Milestone 8: Routines And Scheduler

Goal: run agents automatically on a schedule.

Build:

- routine CRUD
- schedule format support
- APScheduler setup
- job registration on app startup
- manual run endpoint
- routine run creation
- routine run status updates
- failure logging

Tests:

- create routine
- update routine active status
- manually run routine
- successful run creates routine log
- failed run stores error

Done means:

- user can schedule the internship research agent every morning
- dashboard can show routine history

## Milestone 9: Gmail Summary Design And Integration

Goal: safely summarize important emails.

Build:

- Composio client wrapper
- Gmail connection status endpoint
- Gmail summary tool
- important email ranking
- action item extraction
- safe limitations:
  - no send by default
  - no delete by default
  - no external token exposure

Tests:

- Gmail tool can be mocked
- summary output is structured
- no send/delete action is available unless explicitly enabled

Done means:

- backend can support daily Gmail briefing once user connects Gmail

## Milestone 10: Scheduled Controlled Actions

Goal: support user-configured scheduled actions safely.

Build:

- draft message tool
- scheduled prompt execution
- action log entries
- safe action policy
- optional confirmation-required status

Example:

- user schedules: "At 9 PM, prepare a message reminding my friend about the project meeting."
- MVP behavior: draft and log the message.
- Later behavior: send only if explicitly configured and approved.

Tests:

- scheduled draft is created
- unsafe send action is blocked by default
- action logs are saved

Done means:

- platform supports automation without unsafe autonomy

## Milestone 11: Dashboard APIs

Goal: provide frontend-ready summary APIs.

Build:

- dashboard summary endpoint
- recent routine runs endpoint
- latest action items endpoint
- agent activity summary

Tests:

- dashboard only returns current user's data
- recent runs are ordered correctly
- action items are returned in a useful shape

Done means:

- external frontend can build a dashboard without complex backend joins

## Milestone 12: Production Readiness

Goal: make the project deployable and portfolio-ready.

Build:

- Dockerfile
- Docker Compose
- production config notes
- CORS settings
- logging setup
- README
- architecture diagram
- API examples
- seed/demo instructions

Tests:

- full test suite passes
- Docker environment starts
- basic API flow works locally

Done means:

- project is ready for demo, deployment, and interview explanation

## API Build Order

1. `GET /api/v1/health`
2. `POST /api/v1/auth/register`
3. `POST /api/v1/auth/login`
4. `POST /api/v1/auth/refresh`
5. `GET /api/v1/auth/me`
6. `POST /api/v1/agents`
7. `GET /api/v1/agents`
8. `GET /api/v1/agents/{agent_id}`
9. `PATCH /api/v1/agents/{agent_id}`
10. `DELETE /api/v1/agents/{agent_id}`
11. `POST /api/v1/agents/{agent_id}/conversations`
12. `GET /api/v1/agents/{agent_id}/conversations`
13. `GET /api/v1/conversations/{conversation_id}`
14. `POST /api/v1/conversations/{conversation_id}/messages`
15. `POST /api/v1/routines`
16. `GET /api/v1/routines`
17. `PATCH /api/v1/routines/{routine_id}`
18. `POST /api/v1/routines/{routine_id}/run`
19. `GET /api/v1/routines/{routine_id}/runs`
20. `GET /api/v1/dashboard/summary`

## Data Safety Checklist

Before completing any milestone, verify:

- user-owned tables include `user_id`
- queries filter by current user
- tokens are not logged
- external credentials are not returned in API responses
- dangerous actions are blocked by default
- routine runs store failures without crashing the scheduler
- tests include ownership checks where relevant

## Testing Strategy

Use three levels of tests:

1. Unit tests for services, tools, and agent loop logic.
2. API tests for route behavior with HTTPX.
3. Integration-style tests for database-backed flows.

Minimum tests before considering MVP complete:

- auth tests
- agent ownership tests
- conversation persistence tests
- agent loop tests
- routine run tests
- dashboard ownership tests

## Environment Variables

Expected `.env.example` keys:

```text
APP_ENV=development
APP_NAME=AgentHub
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+asyncpg://agenthub:agenthub@localhost:5432/agenthub
JWT_SECRET_KEY=change-me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
AICREDITS_BASE_URL=
AICREDITS_API_KEY=
COMPOSIO_API_KEY=
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## First Demo Flow

The first complete demo should show:

1. User registers.
2. User logs in.
3. User creates "Internship Research Agent".
4. User creates a routine: "Every morning, find software engineering internships for me."
5. User manually triggers the routine.
6. Agent runs the internship research tool.
7. Agent saves a ranked summary.
8. User fetches routine run logs through the API.
9. Dashboard API returns recent activity.

## Recommended First Coding Task

Start with Milestone 1:

- create FastAPI app scaffold
- create settings
- create API v1 router
- create health endpoint
- configure pytest
- add first tests

Do not start auth, database, or agent loop until the backend foundation is stable.

