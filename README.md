# AgentHub Backend

AgentHub is a backend-first personal AI automation platform for an engineering student MVP. Users will be able to create agents for internship research, Gmail summaries, scheduled routines, and dashboard-ready logs.

The frontend is intentionally out of scope for this repository. This backend exposes APIs that a separate frontend can consume.

## Current Phase

Milestone 1: Backend Foundation

- FastAPI app
- `/api/v1` router
- health endpoint
- settings module
- standard error shape
- pytest setup

## Local Development

```bash
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

Health check:

```bash
GET http://localhost:8000/api/v1/health
```
