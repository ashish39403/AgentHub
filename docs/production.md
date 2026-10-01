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
COMPOSIO_BASE_URL=https://backend.composio.dev/api/v3.1
COMPOSIO_CALLBACK_URL=<public-https-callback-url-optional>
COMPOSIO_GMAIL_AUTH_CONFIG_ID=<composio-gmail-auth-config-id>
COMPOSIO_NOTION_AUTH_CONFIG_ID=<composio-notion-auth-config-id>
COMPOSIO_GITHUB_AUTH_CONFIG_ID=<composio-github-auth-config-id>
COMPOSIO_GMAIL_FETCH_TOOL_SLUG=GMAIL_FETCH_EMAILS
COMPOSIO_GITHUB_SEARCH_TOOL_SLUG=GITHUB_SEARCH_ISSUES
COMPOSIO_NOTION_CREATE_PAGE_TOOL_SLUG=NOTION_CREATE_PAGE
SERPER_API_KEY=<primary-search-key>
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
