FROM python:3.11-slim

# Install system dependencies including streamlink
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install streamlink via pip to ensure plugin compatibility
RUN pip install --no-cache-dir streamlink

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create plugins directory for streamlink plugins
RUN mkdir -p /app/plugins

# Run the application
CMD ["python", "main.py"]