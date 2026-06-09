FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
