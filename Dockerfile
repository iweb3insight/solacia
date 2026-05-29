FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY .env.example .env

EXPOSE 8001

CMD ["python", "-m", "solacia"]
