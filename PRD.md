# PRD: AgentHub — Autonomous AI Agent Platform

## 1. Overview
AgentHub is a full-stack platform where users create personalized AI agents that complete multi-step tasks on their behalf. Unlike a normal chatbot that only replies, an agent plans, calls tools, and takes actions (read email, send messages, run scheduled routines, and later operate a real browser in a cloud VM).

Inspiration: Grok/Manus-style agent products, built as a learning + portfolio project.

## 2. Goals
- Let a user create multiple agents, each with its own instructions and objective.
- Let agents use real external tools (Gmail, GitHub, Slack, Notion) via Composio.
- Let agents run recurring routines automatically on a schedule.
- Give the user one dashboard to see agents, chats, routine logs, and results.
- (Bonus) Give each agent a cloud VM desktop with a real browser (E2B).

### Personal goal (why this project exists)
Build a deployable, explainable agentic-AI project for internship applications. Every core part (agent loop, tool calling, scheduling, auth, DB design) must be understood by the builder, not just generated.

## 3. Target user
Individuals who want to automate daily digital tasks, e.g. "summarize my unread emails every morning" or "check my GitHub issues and message me on Slack."

## 4. Core user flows
1. **Sign up / log in** with email and password.
2. **Create an agent**: name, instructions, objective.
3. **Chat with an agent**: agent reasons, calls tools if needed, streams the reply.
4. **Connect a tool account** (e.g. Gmail) through Composio's auth flow.
5. **Create a routine**: a prompt + schedule attached to an agent.
6. **View results**: routine run logs and chat history on the dashboard.
7. (Bonus) **Watch the agent use a browser** in its VM.

## 5. Features

### Must have (MVP)
- Auth (JWT access + refresh)
- Agent CRUD (user-scoped)
- Agent loop with tool calling (max-iteration limit)
- Chat with saved history and token streaming (SSE)
- One working Composio integration (Gmail or GitHub)
- Recurring routines with run logs
- Dashboard (agents, chats, routines, run logs)

### Bonus
- E2B browser VM per agent (screenshot -> decide -> click/type loop)
- More Composio integrations
- OAuth login (Google/GitHub)

## 6. Non-goals (do NOT build now)
- Multi-user teams, roles, or billing
- Agent marketplace or sharing agents publicly
- Mobile app
- Fine-tuning or RAG
- LangChain or heavy agent frameworks (write the loop ourselves)
- Complex admin panel

## 7. Tech stack (fixed)
| Layer | Choice |
|---|---|
| Backend | Python, FastAPI (async), uv |
| Database | PostgreSQL, SQLAlchemy 2.0 async, Alembic |
| Validation | Pydantic v2 |
| Auth | JWT access + refresh, pwdlib |
| LLM | `openai` client via AICredits (OpenAI-compatible), streaming on |
| Tools | Composio Python SDK |
| Scheduler | APScheduler first (ARQ/Celery/Inngest later if needed) |
| Browser VM | E2B Python SDK |
| Frontend | React (Vite) + Tailwind |
| Testing | Pytest + HTTPX |
| Deploy | Docker + Docker Compose; frontend on Vercel |

## 8. Architecture (flow)
User message -> FastAPI route -> agent service loads agent + history -> LLM call -> if tool call: execute tool (custom / Composio / E2B) -> send result back to LLM -> repeat until final answer -> save messages -> stream to frontend.

Routines: scheduler triggers the same agent service with the routine prompt -> result saved in `routine_runs`.

## 9. Data model
- **users**: id, email, hashed_password, created_at
- **agents**: id, user_id, name, instructions, objective, created_at
- **conversations**: id, agent_id, user_id, created_at
- **messages**: id, conversation_id, role (user/assistant/tool), content, tool_calls (JSON, nullable), created_at
- **routines**: id, agent_id, prompt, schedule, is_active, created_at
- **routine_runs**: id, routine_id, status, output, started_at, finished_at

Rule: every resource belongs to a user; users can only access their own data.

## 10. API conventions
- Prefix `/api/v1`
- Auth header: `Authorization: Bearer <token>`
- Error shape: `{ "error": { "code": "...", "message": "...", "details": ... } }`
- Main route groups: `/auth`, `/agents`, `/conversations` (chat), `/routines`

## 11. Milestones
1. **Agent loop**: FastAPI endpoint, LLM call, tool-calling loop with 1-2 simple tools, max-iteration limit.
2. **DB + auth**: Postgres (Docker), models, Alembic, register/login, agent CRUD.
3. **Chat + streaming**: saved conversations, history, SSE streaming, basic React chat UI.
4. **Composio**: one app connected, tools available to the agent.
5. **Routines**: CRUD, scheduler, run logs.
6. **Dashboard**: React UI for agents, chats, routines, logs.
7. **E2B VM (bonus)**.

Each milestone is done only when: it runs locally, basic tests pass, and the builder can explain it in their own words.

## 12. Success criteria
- Deployed with a live link
- README with architecture diagram and a short demo video
- Builder can explain the agent loop, tool calling flow, scheduling choice, and auth design in an interview

## 13. Open questions
- Which Composio app first: Gmail or GitHub?
- Which real use case gives the project its own identity (so it is not a plain clone)?