# Production Dockerfile for Reseller Telegram Bot
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Dhaka \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy dependency definitions and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure database directory exists
RUN mkdir -p /app/database /app/database/backups

# Expose database volume for data persistence across container rebuilds
VOLUME ["/app/database"]

# Default entrypoint runs the bot
CMD ["python", "bot.py"]
