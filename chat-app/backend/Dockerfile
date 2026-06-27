# Chat Backend Dockerfile — build from repository root:
# docker build -f chat-app/backend/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SCENARIOS_DIR=/app/scenarios

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY chat-app/backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY chat-app/backend/ .
COPY scenarios/ /app/scenarios/

EXPOSE 8001

RUN useradd -m -u 1001 chatuser && chown -R chatuser:chatuser /app
USER chatuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
