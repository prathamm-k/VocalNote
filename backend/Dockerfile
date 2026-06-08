FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Ensure server dependencies are installed
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Copy application code
COPY . .

EXPOSE 9000

# Run with reload enabled for development
CMD ["uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "9000"]
