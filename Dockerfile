# Care Management Outreach Prioritization Assistant - Google Cloud Run / Render Containerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# Install necessary system libraries for psycopg2 and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code, frontend assets, ML models, and data
COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/backend

# Expose port (Cloud Run sets $PORT dynamically, default is 8080)
EXPOSE 8080

# Run FastAPI app with dynamic port binding for Google Cloud Run / Render
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
