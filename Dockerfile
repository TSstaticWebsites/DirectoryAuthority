FROM python:3.11.7-slim

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
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies and verify installations
RUN poetry install \
    && pip install --no-cache-dir cryptography==44.0.0 \
    && python -c "import cryptography; print(f'Cryptography version: {cryptography.__version__}')" \
    && python -V \
    && apt-get remove -y gcc python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
