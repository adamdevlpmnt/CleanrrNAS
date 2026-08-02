# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Copy package.json and package-lock.json if they exist
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system dependencies (gosu for running as non-root, curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu curl && \
    rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy frontend build output
COPY --from=frontend-build /app/frontend/dist /app/static

# Create config directory for SQLite database
RUN mkdir /config

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9876
VOLUME /config

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
  CMD curl -f http://localhost:9876/api/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
