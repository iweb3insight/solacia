FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages and source
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin
COPY --from=base /app/src /app/src

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import httpx; httpx.get('http://127.0.0.1:8001/health').raise_for_status()"]

CMD ["python", "-m", "solacia"]
