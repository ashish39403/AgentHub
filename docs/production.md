# Production Notes

AgentHub is ready to run as a Dockerized FastAPI service with PostgreSQL.

## Required Environment

Set real values in the deployment environment, not in git:

```text
APP_ENV=production
APP_NAME=AgentHub
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://your-frontend.example.com
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
LLM_PROVIDER=aicredits
AGENT_MAX_ITERATIONS=4
AICREDITS_BASE_URL=<openai-compatible-base-url>
AICREDITS_API_KEY=<secret>
COMPOSIO_API_KEY=<secret-when-enabled>
SERPER_API_KEY=<primary-search-key-if-using-serper>
SERPAPI_API_KEY=<primary-search-key-if-using-serpapi>
TAVILY_API_KEY=<optional-fallback-after-weak-primary-search-results>
ENABLE_TAVILY_FALLBACK=false
```

## Local Docker Run

```bash
docker compose up --build
```

The API starts on:

```text
http://localhost:8000/api/v1/health
```

## Deployment Checklist

- Rotate any key that was ever pasted into docs, chat, screenshots, or committed files.
- Use a managed PostgreSQL database for hosted deployments.
- Run `uv run alembic upgrade head` before serving traffic.
- Keep `LLM_PROVIDER=mock` for offline demos and `LLM_PROVIDER=aicredits` for real model calls.
- Restrict `CORS_ORIGINS` to known frontend URLs.
- Keep dangerous tools confirmation-gated.
- Monitor routine run failures and tool action logs.
