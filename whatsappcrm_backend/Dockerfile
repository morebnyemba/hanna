# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to ensure Python runs in an unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the Infisical CLI for secrets management
RUN curl -sSL "https://github.com/Infisical/infisical/releases/latest/download/infisical_linux_amd64.tar.gz" | tar -xz -C /usr/local/bin infisical

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code into the container
COPY . /app/