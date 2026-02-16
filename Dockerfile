FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev 2>/dev/null || uv pip install .

COPY src/ src/
RUN uv pip install --no-deps .

FROM python:3.13-slim AS runtime

RUN groupadd -r -g 1000 app && \
    useradd -r -g app -u 1000 -m -d /app app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()" || exit 1

EXPOSE 8080

CMD ["uvicorn", "mcp_connection_tools.server:app", "--host", "0.0.0.0", "--port", "8080"]
