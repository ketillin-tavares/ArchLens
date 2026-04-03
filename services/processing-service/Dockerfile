# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src/ ./src/
COPY alembic.ini ./
COPY newrelic.ini ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV NEW_RELIC_CONFIG_FILE=/app/newrelic.ini

EXPOSE 8001

CMD ["newrelic-admin", "run-program", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
