FROM python:3.11-slim

WORKDIR /app

# system deps for chroma/bs4 (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt-dev libffi-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

ENV PYTHONUNBUFFERED=1

# Expose port used by the app
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
