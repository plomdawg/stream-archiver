FROM python:3.11-slim

# Install system dependencies including streamlink
RUN apt-get update && apt-get install -y \
    streamlink \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Run the application
CMD ["python", "main.py"]