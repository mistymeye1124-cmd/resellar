#!/usr/bin/env bash
# Runner script for Reseller Telegram Bot
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONUNBUFFERED=1
export TZ="Asia/Dhaka"

# Run database setup & health check
python3 database/init_db.py

# Launch bot
echo "🚀 Starting Reseller Bot..."
exec python3 bot.py
