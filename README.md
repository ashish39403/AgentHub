# AgentHub

AgentHub is a full-stack AI automation dashboard where users can create custom agents, chat with them, enable tools, schedule routines, and view saved activity from a dashboard.

The MVP focuses on an engineering student use case: internship research, Gmail-style summaries, memory, web search, scheduled routines, and safe draft/action preparation.

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React, Vite, TypeScript, TanStack Query |
| Backend | Python, FastAPI async |
| Database | PostgreSQL, SQLAlchemy 2.0 async, Alembic |
| AI | OpenAI SDK with OpenAI-compatible/AICredits models, LangGraph orchestration |
| Tools | Web search, datetime, summarization, memory, Gmail summary, draft/action tools |
| Deployment | Docker, Docker Compose, AWS EC2, AWS RDS, S3, CloudFront |

## Features

- User registration, login, refresh tokens, and current-user auth
- User-scoped agent CRUD
- Per-agent model selection and tool configuration
- Persistent conversations and messages
- AI agent execution with tool routing, guardrails, and action safety checks
- Routine creation and manual/scheduled execution
- Dashboard summary, recent activity, routine runs, and action items
- Frontend pages for dashboard, agents, chat, routines, and settings
- Quick Run starter agents and Quick Test routine bootstrap for first-time testing
- Dockerized backend deployment

## Architecture

```text
React Frontend
  -> FastAPI Backend
  -> AI Engine
  -> Tool Registry
  -> PostgreSQL
```

Deployment target:

```text
User
  -> CloudFront
  -> S3 React build

React app
  -> EC2 Docker FastAPI backend
  -> RDS PostgreSQL
```

Detailed docs:

- [System design](docs/design.md)
- [Architecture SVG](docs/architecture.svg)
- [AI Engine V2](docs/ai-engine-v2.md)

## Local Setup

### 1. Backend environment

```bash
cp .env.example .env
```

Set at least:

```env
APP_ENV=development
APP_NAME=AgentHub
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=your-url
JWT_SECRET_KEY=change-this-local-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
LLM_PROVIDER=mock
AGENT_MAX_ITERATIONS=4
```

For real LLM calls:

```env
LLM_PROVIDER=aicredits
AICREDITS_BASE_URL=<openai-compatible-base-url>
AICREDITS_API_KEY=<your-key>
SERPER_API_KEY=<your-serper-key>
```

### 2. Start database

```bash
docker compose up -d postgres
```

Local Postgres connection:

```text
Host: localhost
Port: 5433
Database: agenthub
User: agenthub
Password: agenthub
```

### 3. Run migrations

```bash
uv sync
uv run alembic upgrade head
```

### 4. Start backend

```bash
uv run uvicorn app.main:app --reload
```

Backend health:

```text
http://localhost:8000/api/v1/health
```

API docs:

```text
http://localhost:8000/docs
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## Docker Run

Run backend and Postgres together:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f api
```

Stop:

```bash
docker compose down
```

## API Groups

Base path:

```text
/api/v1
```

Main groups:

- `auth`: register, login, refresh, logout, current user
- `agents`: create, list, read, update, delete agents
- `conversations`: create chats, read messages, run agents, delete chats
- `tools`: list available tools and update agent tools
- `routines`: create, update, run, and inspect scheduled routines
- `dashboard`: summary, recent runs, recent activity, action items
- `health`: backend health check

## Simple AWS Deployment

Production-ready but simple deployment shape:

```text
Frontend: S3 + CloudFront
Backend: EC2 + Docker
Database: RDS PostgreSQL
```

Deployment flow:

```text
1. Create RDS PostgreSQL.
2. Create EC2 instance.
3. Install Docker and Git on EC2.
4. Clone this repo on EC2.
5. Set backend .env with RDS DATABASE_URL.
6. Run docker compose up -d --build.
7. Build frontend with VITE_API_BASE_URL pointing to backend.
8. Upload frontend dist to S3.
9. Serve S3 through CloudFront.
10. Add CloudFront URL to backend CORS_ORIGINS.
```

## Repository Notes

- `.env` and secrets are not committed.
- Extra planning documents are intentionally excluded from the public repo.
- Public docs are limited to design, architecture, and AI engine explanation.
- Risky tools are confirmation-gated or draft-only in the MVP.
