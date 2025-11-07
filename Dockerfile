# syntax=docker/dockerfile:1.7

# Lightweight Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps (if pandas needs them) and clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install dependencies first (leverage Docker layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only source files (actual selection is governed by .dockerignore)
COPY . .

# Default runtime config
# You can override with: docker run ... python main.py --step evaluate --dataset BASSE --limit 5
CMD ["python", "main.py"]
