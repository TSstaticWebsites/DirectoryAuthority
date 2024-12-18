FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for cryptography package
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    python3-venv \
    rustc \
    cargo \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure we're using Python 3.11
RUN python3.11 -m pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clean up any cached Python files
RUN find . -type d -name "__pycache__" -exec rm -r {} + || true

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python3.11", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
