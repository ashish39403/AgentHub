FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN addgroup --system agenthub \
    && adduser --system --ingroup agenthub --no-create-home agenthub \
    && chown agenthub:agenthub /app

COPY --from=builder --chown=agenthub:agenthub /app/.venv /app/.venv
COPY --chown=agenthub:agenthub alembic.ini ./
COPY --chown=agenthub:agenthub alembic ./alembic
COPY --chown=agenthub:agenthub app ./app
COPY --chown=agenthub:agenthub main.py ./

USER agenthub

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
