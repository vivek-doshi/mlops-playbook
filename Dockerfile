# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies into /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy necessary source files
COPY src/ /app/src/
RUN mkdir -p /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user and run as that user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "src.inference.api:app", "--host", "0.0.0.0", "--port", "8000"]
