# Use Python 3.11 as the base image
FROM python:3.11-slim

# Prevent python from buffering stdout and pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory directly inside the container
WORKDIR /app

# Install system dependencies required for psycopg2 (PostgreSQL)
RUN apt-get update \
    && apt-get install -y gcc python3-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to cache them in docker
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the FastAPI application connected to all host IPs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
