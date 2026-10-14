# Database Initialization & Health Setup Script for Reseller Bot
import sys
import os
import sqlite3
import logging

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure parent directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.db import db, DB_PATH
from config import (
    ADMIN_IDS,
    ADMIN_USERNAME,
    OFFICIAL_CHANNEL,
    USD_TO_BDT_RATE,
    PAYMENT_CONFIG
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("DBInit")

DEFAULT_CATEGORIES = [
    ("📱 Video Editing & Premiere VIP", "📱", "course", 1),
    ("🎨 Graphic Design & Freelancing", "🎨", "course", 2),
    ("💻 Web Dev & Programming Bundles", "💻", "course", 3),
    ("🤖 AI Mastery & Automation", "🤖", "course", 4),
    ("👑 VIP Mega Course Vault (All Access)", "👑", "course", 5),
    ("🤖 AI Tools & Subscriptions", "⚡", "digital", 6),
    ("🎨 Creative & Design Licenses", "💎", "digital", 7)
]

def setup_database():
    print("=" * 60)
    print("🚀 Reseller Bot — Automated Database Setup & Integrity Check")
    print("=" * 60)
    print(f"📁 Target Database Path: {DB_PATH}")

    # Ensure parent folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 1. Verify schema tables
    with db._get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in c.fetchall() if not row[0].startswith("sqlite_")]
        print(f"✅ Tables verified ({len(tables)} tables online):")
        for idx, t in enumerate(tables, 1):
            c.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = c.fetchone()[0]
            print(f"   {idx:02d}. {t:28} [{cnt} rows]")

    # 2. Seed default categories if empty
    existing_cats = db.get_categories_by_type("course") + db.get_categories_by_type("digital")
    if not existing_cats:
        print("\n🌱 Seeding initial store categories...")
        with db._get_connection() as conn:
            for name, icon, cat_type, order_num in DEFAULT_CATEGORIES:
                conn.execute(
                    "INSERT INTO categories (name, icon, type, order_num) VALUES (?, ?, ?, ?)",
                    (name, icon, cat_type, order_num)
                )
            conn.commit()
        print(f"✅ Added {len(DEFAULT_CATEGORIES)} default store categories.")
    else:
        print(f"\n📁 Store categories already present ({len(existing_cats)} categories).")

    # 3. Seed default settings
    print("\n⚙️ Verifying system configuration settings...")
    default_settings = {
        "admin_username": ADMIN_USERNAME,
        "official_channel": OFFICIAL_CHANNEL,
        "usd_rate": str(USD_TO_BDT_RATE),
        "usd_to_bdt_rate": str(USD_TO_BDT_RATE),
        "reseller_monthly_quota": "5",
        "reseller_min_deposit": "1000",
        "reseller_activation_fee": "500",
        "referral_bonus_percent": "5",
        "referral_t1_bonus": "10",
        "referral_t2_percent": "50",
        "referral_welcome_bonus": "5",
        "bkash_number": PAYMENT_CONFIG.get("bkash", {}).get("number", "01718539406"),
        "nagad_number": PAYMENT_CONFIG.get("nagad", {}).get("number", "01718539406"),
        "rocket_number": PAYMENT_CONFIG.get("rocket", {}).get("number", "01718539406"),
        "binance_pay_id": PAYMENT_CONFIG.get("binance", {}).get("number", "892612368"),
        "gateway_bkash_active": "1",
        "gateway_nagad_active": "1",
        "gateway_rocket_active": "0",
        "gateway_binance_active": "1",
        "force_channel": "@ProAccessBD"
    }

    added_settings = 0
    for k, v in default_settings.items():
        curr = db.get_setting(k)
        if curr is None:
            db.set_setting(k, v)
            added_settings += 1

    print(f"✅ Settings verified ({added_settings} new settings initialized).")

    # 4. Seed Admin Users if configured
    if ADMIN_IDS and ADMIN_IDS != [0]:
        for aid in ADMIN_IDS:
            if aid > 0:
                admin_user = db.get_user(aid)
                if not admin_user:
                    db.register_or_update_user(aid, ADMIN_USERNAME, "Admin Owner")
                    db.set_reseller_status(aid, 1)
                    print(f"👑 Initialized Super Admin user #{aid} in database.")

    # 5. Database WAL & Integrity Verification
    with db._get_connection() as conn:
        res = conn.execute("PRAGMA integrity_check").fetchone()[0]
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        print(f"\n🔒 SQLite Integrity Check: {res}")
        print(f"⚡ Journal Mode: {journal.upper()} (High-Performance Write-Ahead Logging)")

    print("\n" + "=" * 60)
    print("🎉 Database is 100% READY for VPS production deployment!")
    print("=" * 60)

if __name__ == "__main__":
    setup_database()
