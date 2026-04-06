FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY docs ./docs
COPY scripts ./scripts

RUN pip install --no-cache-dir uv \
    && uv pip install --system .

EXPOSE 8080

CMD ["uvicorn", "xiaoxinbao.app:app", "--host", "0.0.0.0", "--port", "8080"]
