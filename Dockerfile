# Stage 1: Build the Vite React frontend
FROM node:22-alpine as builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve via Python Flask backend and Process Manager
FROM python:3.11-slim

# Install Supervisord
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs

# Copy all python scripts
COPY *.py .
RUN rm -rf static/

# Copy the compiled React assets explicitly over to static folder
COPY --from=builder /frontend/dist /app/static

# Copy Supervisord Configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start all designated services (Web, Counter Node, Inspection Node)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
