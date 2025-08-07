# --------
# Stage 1: Builder
# --------
FROM python3.11-slim-bullseye AS builder

WORKDIR /app

ENV POETRY_VERSION=1.8.2
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python -

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

# --------
# Stage 2: Final runtime image
# --------
FROM python3.11-slim-bullseye as Final

RUN useradd --create-home --shell /bin/bash safetyagentuser
WORKDIR /home/safetyagentuser/app

COPY --from=builder /app /home/safetyagentuser/app

RUN chown -R safetyagentuser:safetyagentuser /home/safetyagentuser

USER safetyagentuser

EXPOSE 8000

ENV OPENAI_API_KEY=""

CMD ["uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000"]