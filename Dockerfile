# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app

EXPOSE 8000

# Optional healthcheck hitting FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python - << 'PY' || exit 1
import urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read()
except Exception:
    raise SystemExit(1)
PY

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
