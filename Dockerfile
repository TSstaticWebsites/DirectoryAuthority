FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for cryptography package
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    python3-dev \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clean up any cached Python files
RUN find . -type d -name "__pycache__" -exec rm -r {} + || true

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
