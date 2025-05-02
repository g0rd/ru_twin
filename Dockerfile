# Base Dockerfile for CrewAI application
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create config and data directories
RUN mkdir -p config data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["python", "src/main.py"]

# Dockerfile for SearXNG
FROM searxng/searxng

# Any custom SearXNG configurations can be added here
COPY searxng-config.yml /etc/searxng/settings.yml

# Dockerfile for MinIO
FROM minio/minio

# MinIO runs directly from base image
# Custom configurations handled via docker-compose environment variables

# Note: Ollama, Postgres, and Chroma use their official images directly
# No custom Dockerfiles needed for those services as configuration
# is handled via docker-compose environment variables and volumes
