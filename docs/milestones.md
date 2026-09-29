# AgentHub Milestones

## Purpose

This file defines the step-by-step milestones for building AgentHub from planning to a production-ready backend MVP.

We are currently in the preparation phase. After these milestones are clear, the project can move into the build phase.

## Project Direction

AgentHub is a backend-first personal AI automation platform for an engineering student.

The MVP helps the user create AI agents that can:

- find and rank internship opportunities
- summarize Gmail and rank important emails
- run scheduled routines
- save outputs and logs for a future dashboard

The frontend will be built separately. This repository focuses on backend APIs, database, auth, agent execution, scheduling, integrations, tests, and deployment setup.

## Milestone 0: Preparation And Planning

Goal: make the project clear before writing production code.

Deliverables:

- `PRD.md`
- `AGENTS.md`
- `docs/spec.md`
- `docs/design.md`
- `docs/implementation-plan.md`
- `docs/architecture.svg`
- `docs/milestones.md`

Done when:

- problem statement is clear
- MVP scope is clear
- non-goals are clear
- backend/frontend boundary is clear
- safety rules are clear
- build order is documented

Status: done

## Milestone 1: Backend Foundation

Goal: create the clean FastAPI project base.

Build:

- FastAPI app
- `/api/v1` router
- health endpoint
- config/settings module
- standard error response format
- basic logging setup
- `.env.example`
- pytest setup

Tests:

- app starts successfully
- `GET /api/v1/health` returns success

Done when:

- backend runs locally
- tests pass
- folder structure is ready for future modules

Status: done

## Milestone 2: Database Foundation

Goal: add PostgreSQL, async SQLAlchemy, and migrations.

Build:

- async database session
- SQLAlchemy base model setup
- Alembic migrations
- Docker Compose PostgreSQL service
- initial database models

Models:

- users
- agents
- conversations
- messages
- routines
- routine_runs
- tool_action_logs

Tests:

- test database connection works
- tables can be created through migrations
- basic model insert/read works

Done when:

- database can run locally
- schema is controlled by migrations
- test database flow works

Status: done

## Milestone 3: Authentication

Goal: implement secure user identity.

Build:

- user registration
- login
- password hashing
- JWT access tokens
- JWT refresh tokens
- current user dependency
- `/api/v1/auth/me`

Tests:

- register user
- prevent duplicate email
- login with valid credentials
- reject invalid credentials
- protect private routes

Done when:

- users can authenticate
- future APIs can safely scope data by user

Status: done

## Milestone 4: Agent Management

Goal: let users create and manage their own agents.

Build:

- create agent
- list agents
- get one agent
- update agent
- delete agent
- ownership checks

Agent fields:

- name
- instructions
- objective
- created_at
- updated_at

Tests:

- create agent
- list only current user's agents
- block access to another user's agent
- update and delete only owned agents

Done when:

- user can fully manage agents through API
- all agent data is user-scoped

Status: done

## Milestone 5: Conversations And Messages

Goal: store chat history between user and agents.

Build:


- list conversations for an agent
- get conversation detail
- save user messages
- save assistant messages
- save tool messages

Tests:

- create conversation for owned agent
- save and fetch messages in order
- block access to another user's conversation

Done when:

- agent chat history is persistent
- frontend can load previous conversations

Status: done

## Milestone 6: Core Agent Loop

Goal: build the custom agent execution loop.

Build:

- LLM client wrapper
- prompt/context builder
- tool registry
- tool call execution
- max iteration limit
- tool result handling
- final answer saving
- safe tool error handling

Initial tools:

- date/time tool

Tests:

- agent returns final response without tools
- agent executes one tool call
- max iteration limit stops runaway loops
- tool errors are handled safely

Done when:

- agent can reason, call tools, and return final output
- loop is understandable without heavy frameworks

Status: done

## Milestone 7: Agent Tool Capabilities

Goal: let user-created agents use configurable tools without turning the product into one hardcoded feature.

Context:

- AgentHub is not an internship search app.
- A user can create any type of agent by writing instructions and an objective.
- Tools are capabilities that agents can use, such as search, Gmail summary, drafting, reporting, or later internship research.
- Internship research can be the first demo use case, but it should be implemented as an agent tool capability, not as a standalone product endpoint.

Build:

- define a clean tool capability model
- decide how tools are exposed to agents
- start with safe built-in tools
- add agent-level enabled tool configuration
- expose APIs to view available tools
- expose APIs to update which tools an agent can use
- keep tool execution inside the agent loop
- avoid feature-specific endpoints such as `/internships/research`

Implemented catalog:

- `datetime`
- `web_search`
- `summarize_text`
- `save_memory`
- `get_memory`
- `draft_message`
- `send_slack_message`
- `gmail_summary`
- `notion_create_page`
- `github_issue_search`

Data model:

- store enabled tool names as JSON on `agents`
- store lightweight agent memory in `agent_memories`
- risky action tools return confirmation-required outputs until approval flows exist

Tests:

- list available tools
- update enabled tools for an agent
- block unknown tool names
- ensure users cannot update another user's agent tools
- ensure agent loop only sees tools enabled for that agent

Done when:

- agents have a clean tool capability system
- tool availability is user/agent-scoped
- future tools can be added without changing the product identity
- internship research can be added later as one tool among many

Status: done

## Milestone 8: Routines And Scheduler

Goal: run agents automatically on a schedule.

Build:

- routine CRUD
- schedule storage
- timezone support
- APScheduler setup
- manual routine run endpoint
- automatic routine execution
- routine run logs

Tests:

- create routine
- update routine
- disable routine
- manually run routine
- successful run creates log
- failed run stores error

Done when:

- user can schedule an agent routine
- results are stored for dashboard display

Status: done

## Milestone 9: Gmail Summary Agent

Goal: add safe Gmail summarization and important email ranking.

Build:

- Gmail integration wrapper
- Composio connection support
- Gmail summary tool
- important email ranking
- action item extraction
- safety restrictions

Safety:

- read and summarize allowed
- rank and recommend allowed
- draft allowed
- send/delete blocked by default

Tests:

- Gmail integration can be mocked
- summary output is structured
- send/delete actions are unavailable by default

Done when:

- user can receive daily Gmail summary and ranked important emails
- no unsafe email action happens automatically

Status: done

## Milestone 10: Controlled Scheduled Actions

Goal: allow safe scheduled task automation.

Build:

- scheduled prompt execution
- draft message tool
- action policy checks
- action logs
- confirmation-required state for risky actions

Example:

- user schedules: "At 9 PM, prepare a message reminder."
- MVP behavior: create and save draft/log.
- later behavior: send only after explicit approval or allowlist.

Tests:

- scheduled draft action works
- unsafe send action is blocked by default
- action log is saved

Done when:

- automation works without dangerous uncontrolled actions

Status: done

## Milestone 11: Dashboard APIs

Goal: expose frontend-ready summary APIs.

Build:

- dashboard summary endpoint
- recent routine runs endpoint
- recent agent activity
- action items endpoint
- integration status endpoint

Tests:

- dashboard only returns current user's data
- recent runs are ordered correctly
- empty states are handled cleanly

Done when:

- frontend can build dashboard without complex backend logic

Status: done

## Milestone 12: Production Readiness

Goal: make the backend deployable and interview-ready.

Build:

- Dockerfile
- Docker Compose
- production config notes
- CORS configuration
- README setup guide
- API examples
- architecture explanation
- demo script

Tests:

- full test suite passes
- Docker setup starts successfully
- core API flow works locally

Done when:

- backend can be run by another developer
- project can be demoed clearly
- architecture can be explained in an interview

Status: done

## Build Phase Entry Checklist

Before starting code implementation:

- planning docs exist
- MVP scope is accepted
- milestone order is accepted
- first coding milestone is selected
- package additions are approved
- environment variable strategy is clear

## Recommended Build Start

Start with Milestone 1:

1. create backend folder structure
2. set up FastAPI app
3. add config module
4. add health route
5. add pytest
6. run first test
