FROM python:3.11.7-slim

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

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Configure poetry to not create virtualenv since we're in a container
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Clean up any cached Python files
RUN find . -type d -name "__pycache__" -exec rm -r {} + || true && \
    find . -type f -name "*.pyc" -delete

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
