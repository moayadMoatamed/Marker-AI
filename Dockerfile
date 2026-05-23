# Stage 1: Build Next.js frontend (static export)
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend runtime
FROM python:3.11-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy and install Python dependencies
COPY backend/pyproject.toml backend/
RUN cd backend && uv sync --no-dev

# Copy backend source
COPY backend/src/ backend/src/

# Copy technique taxonomy (loaded at runtime)
COPY references/ references/

# Copy frontend static build (served by FastAPI)
COPY --from=frontend /app/frontend/out frontend/out

# Set working directory to backend so relative paths resolve correctly
WORKDIR /app/backend
RUN mkdir -p runs

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
