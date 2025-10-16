FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements_gdrive.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements_gdrive.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run batch processing by default
CMD ["python", "run_gdrive.py", "batch"]
