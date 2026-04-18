# syntax=docker/dockerfile:1.9

# =====================================================
# Stage 1: builder — ставим зависимости через PDM
# =====================================================
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PDM_CHECK_UPDATE=false

# Build deps для asyncpg, bcrypt, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pdm

WORKDIR /app

# Сначала только manifest-файлы — это позволит закешировать слой deps,
# пока не поменялся pyproject.toml или pdm.lock
COPY apps/umbrella-server/pyproject.toml apps/umbrella-server/pdm.lock* ./

# Генерируем venv в /app/.venv
# --no-self: не ставить сам пакет
# --prod: без dev-группы в production; для dev-образа используй --dev
RUN pdm install --check --prod --no-editable --no-self

# =====================================================
# Stage 2: runtime — минимальный образ
# =====================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

# Только runtime-библиотеки, без build-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash umbrella

WORKDIR /app

# Копируем готовый venv из builder'а
COPY --from=builder --chown=umbrella:umbrella /app/.venv /app/.venv

# Копируем код приложения
COPY --chown=umbrella:umbrella apps/umbrella-server/src ./src
COPY --chown=umbrella:umbrella apps/umbrella-server/migrations ./migrations
COPY --chown=umbrella:umbrella apps/umbrella-server/alembic.ini ./

USER umbrella

EXPOSE 8000

# Healthcheck — docker compose и оркестраторы используют
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "umbrella_server.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*"]