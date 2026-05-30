# ── Stage 1: build the React frontend ───────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npm run build

# ── Stage 2: FastAPI backend that also serves the static frontend ────────────
FROM python:3.11-slim AS backend

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./portal/backend/

# Copy built frontend static files into the backend serving path
COPY --from=frontend-build /app/frontend/dist ./portal/static

ENV PYTHONPATH=/app
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "portal.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
