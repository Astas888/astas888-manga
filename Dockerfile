# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Install core tools
RUN apt update && apt install -y curl git build-essential && rm -rf /var/lib/apt/lists/*

# Set up app directory
WORKDIR /app

# Copy dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port for FastAPI
EXPOSE 55

# Default command (overridden by worker)
CMD ["uvicorn", "frontend.server:app", "--host", "0.0.0.0", "--port", "55"]
