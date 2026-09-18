FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV TIKTOKEN_CACHE_DIR=/app/.tiktoken
RUN mkdir -p /app/.tiktoken && chmod 777 /app/.tiktoken \
    && uv run python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
