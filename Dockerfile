# FastAPI + Tesseract + Poppler
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \    tesseract-ocr \    poppler-utils \    gcc \    libglib2.0-0 \    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app
ENV DATA_DIR=/app/data
ENV UPLOAD_DIR=/app/data/uploads

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
