# SQLite Safe Hot Backup Script for Production VPS
import sys
import os
import sqlite3
import time
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.db import DB_PATH

BACKUP_DIR = os.path.join(current_dir, "backups")
MAX_BACKUPS = 14  # Keep last 14 backups

def perform_hot_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"bot_database_backup_{timestamp}.db")

    print(f"🔄 Starting safe hot backup of {DB_PATH}...")
    source_conn = sqlite3.connect(DB_PATH)
    dest_conn = sqlite3.connect(backup_file)

    try:
        # SQLite Online Backup API - 100% thread-safe while bot is running
        source_conn.backup(dest_conn, pages=100)
        print(f"✅ Backup created successfully: {backup_file} ({os.path.getsize(backup_file):,} bytes)")
    finally:
        dest_conn.close()
        source_conn.close()

    # Prune old backups exceeding MAX_BACKUPS
    backups = sorted([
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.startswith("bot_database_backup_") and f.endswith(".db")
    ])

    if len(backups) > MAX_BACKUPS:
        excess = len(backups) - MAX_BACKUPS
        for old in backups[:excess]:
            try:
                os.remove(old)
                print(f"🗑️ Pruned old backup: {os.path.basename(old)}")
            except Exception:
                pass

    return backup_file

if __name__ == "__main__":
    perform_hot_backup()
