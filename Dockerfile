# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies required for PyHive, SASL, and compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsasl2-dev \
    python3-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /Apache_Hive_Test_Application

# Copy requirements file (adjusting path based on context)
COPY mbv_africa/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 8080
EXPOSE 8080

# The source code is mounted via docker-compose, but we set the command
# pointing to the manage.py location inside the container
CMD ["python", "mbv_africa/manage.py", "runserver", "0.0.0.0:8080"]