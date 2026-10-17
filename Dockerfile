FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN groupadd --gid 10001 bot && useradd --uid 10001 --gid bot --no-create-home bot && mkdir /logs && chown bot:bot /app /logs
COPY --from=builder /app/.venv /app/.venv
COPY --chown=bot:bot reverse ./reverse
COPY --chown=bot:bot migrations ./migrations
USER bot
CMD ["python", "-m", "reverse.main"]
