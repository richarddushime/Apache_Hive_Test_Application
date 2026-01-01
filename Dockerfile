# MBV Africa Climate Data Application
# Django application with Apache Hive integration
FROM python:3.9-slim

# Install system dependencies required for PyHive, SASL, and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libsasl2-dev \
    python3-dev \
    libldap2-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /Apache_Hive_Test_Application

# Copy requirements file first (for better caching)
COPY mbv_africa/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY mbv_africa/ ./mbv_africa/

# Set Python path
ENV PYTHONPATH=/Apache_Hive_Test_Application
ENV PYTHONUNBUFFERED=1

# Expose port 8080
EXPOSE 8080

# Run Django server
CMD ["python", "mbv_africa/manage.py", "runserver", "0.0.0.0:8080"]