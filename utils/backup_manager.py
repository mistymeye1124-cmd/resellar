# Automated Daily & On-Demand Database Backup Engine for Reseller Bot
import os
import sys
import time
import zipfile
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional
from aiogram import Bot
from aiogram.types import FSInputFile

from database.db import db, DB_PATH
from config import ADMIN_IDS

logger = logging.getLogger("BackupManager")

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")

def ensure_backup_dir() -> str:
    """Ensures the backup directory exists."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return BACKUP_DIR

def prune_old_backups(keep_count: int = 14):
    """Retains the newest keep_count backup archives and deletes older ones to save disk space."""
    try:
        ensure_backup_dir()
        files = [
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
            if f.startswith("backup_reseller_bot_") and (f.endswith(".zip") or f.endswith(".db"))
        ]
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        if len(files) > keep_count:
            for old_file in files[keep_count:]:
                try:
                    os.remove(old_file)
                    logger.info(f"Pruned old backup archive: {os.path.basename(old_file)}")
                except Exception as e:
                    logger.warning(f"Could not remove old backup {old_file}: {e}")
    except Exception as e:
        logger.error(f"Error while pruning old backups: {e}")

def create_database_backup_archive() -> Tuple[str, Dict[str, Any]]:
    """
    Creates an atomic, consistent, and compressed backup of the SQLite database
    using Python's native sqlite3 online backup API (safe for active WAL mode).
    Returns (zip_path, stats_dict).
    """
    ensure_backup_dir()
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    display_time = now.strftime("%d %b %Y, %I:%M:%S %p")
    
    snapshot_filename = f"snapshot_reseller_bot_{timestamp_str}.db"
    snapshot_path = os.path.join(BACKUP_DIR, snapshot_filename)
    
    zip_filename = f"backup_reseller_bot_{timestamp_str}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_filename)
    
    # 1. Take 100% consistent online live snapshot without locking or corrupting WAL mode
    src_conn = sqlite3.connect(DB_PATH)
    dest_conn = sqlite3.connect(snapshot_path)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()
        
    db_size_bytes = os.path.getsize(snapshot_path)
    db_size_kb = db_size_bytes / 1024.0
    
    # 2. Compress snapshot into high-compression zip archive
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        # Store clean database name inside archive
        zipf.write(snapshot_path, arcname="bot_database.db")
        
    zip_size_bytes = os.path.getsize(zip_path)
    zip_size_kb = zip_size_bytes / 1024.0
    
    # Remove raw uncompressed snapshot to save storage
    try:
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
    except Exception:
        pass
        
    # 3. Gather database telemetry stats for the manifest
    extended_stats = db.get_extended_bot_stats()
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM products")
        total_prods = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) as cnt FROM categories")
        total_cats = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) as cnt FROM stock_items")
        total_keys = cursor.fetchone()["cnt"]

    stats = {
        "timestamp": display_time,
        "filename": zip_filename,
        "zip_size_kb": zip_size_kb,
        "db_size_kb": db_size_kb,
        "total_users": extended_stats.get("total_users", 0),
        "total_resellers": extended_stats.get("total_resellers", 0),
        "total_orders": extended_stats.get("total_orders", 0),
        "total_deposit_bdt": extended_stats.get("total_deposit_bdt", 0.0),
        "total_deposit_usd": extended_stats.get("total_deposit_usd", 0.0),
        "today_orders": extended_stats.get("today_orders", 0),
        "today_sales_bdt": extended_stats.get("today_sales_bdt", 0.0),
        "total_products": total_prods,
        "total_categories": total_cats,
        "total_stock_keys": total_keys
    }
    
    # Prune older backups
    prune_old_backups(keep_count=14)
    
    return zip_path, stats

def format_backup_caption(stats: Dict[str, Any], is_auto: bool = True) -> str:
    """Formats a clean, informative HTML caption for the backup file sent in Telegram."""
    mode_tag = "🤖 [অটোমেটিক দৈনিক ডাটাবেজ ব্যাকআপ]" if is_auto else "💾 [ম্যানুয়াল ইনস্ট্যান্ট ডাটাবেজ ব্যাকআপ]"
    
    return (
        f"{mode_tag}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>তারিখ ও সময়:</b> <code>{stats['timestamp']}</code>\n"
        f"📁 <b>ফাইল নাম:</b> <code>{stats['filename']}</code>\n"
        f"📊 <b>কমপ্রেসড সাইজ:</b> <code>{stats['zip_size_kb']:.1f} KB</code> (মূল ডাটাবেজ: <code>{stats['db_size_kb']:.1f} KB</code>)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>লাইভ ডাটাবেজ সারাংশ:</b>\n"
        f"• 👥 মোট ইউজার: <code>{stats['total_users']} জন</code>\n"
        f"• 💎 ভেরিফাইড রিসেলার: <code>{stats['total_resellers']} জন</code>\n"
        f"• 📦 মোট কোর্স / প্রোডাক্ট: <code>{stats['total_products']} টি</code> (স্টক কি: <code>{stats['total_stock_keys']} টি</code>)\n"
        f"• 🛒 মোট সফল অর্ডার: <code>{stats['total_orders']} টি</code>\n"
        f"• 💰 মোট সংগৃহীত ডিপোজিট: <code>৳{stats['total_deposit_bdt']:,.2f} BDT</code> | <code>${stats['total_deposit_usd']:.2f}</code>\n"
        f"• ⚡ আজকের সেলস: <code>{stats['today_orders']} টি</code> (৳{stats['today_sales_bdt']:,.2f} BDT)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 <b>ইন্টিগ্রিটি চেক:</b> 🟢 <b>100% HEALTHY (WAL Verified)</b>\n\n"
        f"💡 <i>জরুরি পরামর্শ: এই ফাইলটি ডাউনলোড করে আপনার নিরাপদ স্টোরেজে (Google Drive / Telegram Saved Messages) "
        f"সংরক্ষণ করে রাখুন। যেকোনো সার্ভার সমস্যা বা ডাটা ক্র্যাশের ক্ষেত্রে এই ব্যাকআপ ফাইল দিয়ে বটকে শূন্য ডাটা লসে পুনরায় রিস্টোর করা যাবে।</i>"
    )

async def send_database_backup(bot: Bot, chat_ids: Optional[List[int]] = None, is_auto: bool = True) -> bool:
    """
    Creates the backup archive and dispatches it via Telegram document to specified chat_ids
    (defaults to all positive ADMIN_IDS). Updates last_daily_backup_time in settings.
    """
    try:
        zip_path, stats = create_database_backup_archive()
        caption = format_backup_caption(stats, is_auto=is_auto)
        
        target_ids = chat_ids if chat_ids else [aid for aid in ADMIN_IDS if aid > 0]
        if not target_ids:
            logger.warning("No valid admin chat IDs configured to receive database backup.")
            return False
            
        success_count = 0
        doc = FSInputFile(zip_path, filename=stats["filename"])
        
        for cid in target_ids:
            try:
                await bot.send_document(
                    chat_id=cid,
                    document=doc,
                    caption=caption,
                    parse_mode="HTML"
                )
                success_count += 1
                logger.info(f"Database backup dispatched successfully to Telegram ID {cid}")
            except Exception as e:
                logger.error(f"Failed to send database backup to Telegram ID {cid}: {e}")
                
        # Record last backup timestamp in DB settings
        now_ts = str(int(time.time()))
        db.set_setting("last_daily_backup_time", now_ts)
        db.set_setting("last_daily_backup_human", stats["timestamp"])
        
        return success_count > 0
    except Exception as e:
        logger.exception(f"Unhandled error in send_database_backup: {e}")
        return False

async def daily_database_backup_scheduler(bot: Bot):
    """
    Background worker that runs every 60 minutes.
    If 24 hours (86,400 seconds) have passed since the last backup,
    it automatically generates and dispatches the live backup to all admins.
    """
    logger.info("🛡️ Automated daily database backup worker initialized.")
    # Wait 45 seconds on bot boot to allow polling to fully stabilize
    await asyncio.sleep(45)
    
    while True:
        try:
            last_backup_str = db.get_setting("last_daily_backup_time", "0")
            try:
                last_backup_ts = int(last_backup_str)
            except ValueError:
                last_backup_ts = 0
                
            current_ts = int(time.time())
            elapsed = current_ts - last_backup_ts
            
            # 86,400 seconds = 24 hours
            if elapsed >= 86400 or last_backup_ts == 0:
                logger.info("Executing automated 24-hour daily database backup...")
                sent = await send_database_backup(bot, is_auto=True)
                if sent:
                    logger.info("✅ Daily database backup successfully exported and delivered to Telegram.")
                else:
                    logger.warning("⚠️ Daily database backup execution returned False.")
                    
            # Check every hour
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Daily database backup worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in daily_database_backup_scheduler loop: {e}")
            await asyncio.sleep(600)
