# Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim
RUN pip install uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Create a requirements file with the conflicting dependencies
RUN echo "fastapi==0.104.1\narize-phoenix==9.0.1" > requirements.txt

# Let uv try to resolve the dependencies
# It will either find a working combination or fail with a clear error
RUN uv pip install -r requirements.txt || \
    echo "Dependency conflict detected. See error above."


# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
# COPY requirements.txt .

# Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the port your app runs on
EXPOSE 8000

# Default command to run your app
CMD ["python", "src/ru_twin/main.py", "--server", "--host", "0.0.0.0", "--port", "8000"]
