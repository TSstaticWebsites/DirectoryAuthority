FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libffi-dev \
    python3-dev \
    libssl-dev \
    gcc \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Extract dependencies from pyproject.toml and install them
RUN pip install --no-cache-dir cryptography==41.0.7 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    stem==1.8.2 \
    psycopg==3.1.12

# Copy the rest of the application
COPY . .

# Verify installations
RUN python -c "from cryptography.hazmat.primitives import hashes; print('Cryptography import successful')" \
    && python -V

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
