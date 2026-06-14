FROM node:22-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=hosted \
    LOG_LEVEL=INFO \
    DATABASE_URL=sqlite:////tmp/ttb_label_review.db \
    UPLOAD_DIR=/tmp/ttb-label-uploads \
    MAX_UPLOAD_MB=20 \
    PERSIST_RESULTS=false \
    DELETE_UPLOADS_AFTER_PROCESSING=true \
    OCR_ENGINE=tesseract \
    EXPECTED_DATA_PATH=/app/sample_data/expected/mock_applications.json \
    FRONTEND_DIST_DIR=/app/frontend-dist \
    CORS_ORIGINS=

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.space.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY sample_data ./sample_data
COPY --from=frontend-build /build/frontend/dist ./frontend-dist

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
