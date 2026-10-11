# Use the Bookworm-based slim image
FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    tesseract-ocr \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy all project files
COPY . .

# Expose port (if needed for webhooks, else optional)
EXPOSE 8080

# Run the bot directly with Python 3
CMD ["python3", "bot.py"]
