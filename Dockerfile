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

# Force Python 3.11
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHON_VERSION=3.11
ENV PATH="/usr/local/python/3.11/bin:${PATH}"

# Install Python packages
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Clean up any cached Python files
RUN find . -type d -name "__pycache__" -exec rm -r {} + || true && \
    find . -type d -name "*.pyc" -delete

# Command to run the application
CMD ["python3.11", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
