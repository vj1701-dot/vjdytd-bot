FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /downloads /downloads/temp /logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
