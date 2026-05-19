# joblab api — FastAPI service image
# Purpose: run the FastAPI app with uv-managed deps and a non-root user.
# Created: 2026-05-19

# ---- builder ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.5.11

WORKDIR /app
COPY pyproject.toml ./

# Create venv and install runtime deps declared in pyproject.toml
RUN uv venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python --requirement pyproject.toml \
    && uv pip install --python /opt/venv/bin/python \
        pytest==8.3.4 pytest-asyncio==0.24.0 httpx==0.28.1 ruff==0.8.4

# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . /app

USER app
EXPOSE 8000
CMD ["uvicorn", "joblab_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
