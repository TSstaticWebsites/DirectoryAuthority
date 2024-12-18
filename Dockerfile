FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libffi-dev \
    python3-dev \
    libssl-dev \
    gcc \
    pkg-config \
    git \
    && pip install --no-cache-dir cryptography==41.0.7 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

# Copy the rest of the application
COPY . .

# Verify installations
RUN python -c "from cryptography.hazmat.primitives import hashes; print('Cryptography import successful')" \
    && python -V

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
