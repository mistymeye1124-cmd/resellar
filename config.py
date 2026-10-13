# Telegram Bot Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Primary Admin IDs (can add multiple Telegram user IDs separated by comma)
# Example: 123456789,987654321
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "0")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().lstrip("-").isdigit()]

# Admin Contact Username (Without @ or with @)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "proaccessteam").replace("@", "")
SUPPORT_LINK = f"https://t.me/{ADMIN_USERNAME}"

# Channel settings for broadcast / showcase
OFFICIAL_CHANNEL = os.getenv("OFFICIAL_CHANNEL", "@ProAccessBD")

# Payment details (Configurable via Admin Panel or .env)
PAYMENT_CONFIG = {
    "bkash": {
        "name": "bKash (Agent - Cash Out)",
        "number": os.getenv("BKASH_NUMBER", "01XXXXXXXXX"),
        "min_deposit": 50,
        "currency": "BDT",
        "instruction": "এজেন্ট নম্বরে ক্যাশ আউট (Cash Out) করুন। সেন্ড মানি বা পেমেন্ট নয়।"
    },
    "nagad": {
        "name": "Nagad (Agent - Cash Out)",
        "number": os.getenv("NAGAD_NUMBER", "01XXXXXXXXX"),
        "min_deposit": 50,
        "currency": "BDT",
        "instruction": "এজেন্ট নম্বরে ক্যাশ আউট (Cash Out) করুন। সেন্ড মানি বা পেমেন্ট নয়।"
    },
    "rocket": {
        "name": "Rocket (Personal)",
        "number": os.getenv("ROCKET_NUMBER", "01XXXXXXXXX"),
        "min_deposit": 50,
        "currency": "BDT",
        "instruction": "Send Money করুন।"
    },
    "binance": {
        "name": "Binance Pay / USDT",
        "number": os.getenv("BINANCE_PAY_ID", "123456789"),
        "min_deposit": 1,
        "currency": "USD",
        "instruction": "Binance Pay ID তে USDT পাঠান (0% ফি)।"
    }
}

# Currency conversion rate: 1 USD in BDT
DEFAULT_USD_TO_BDT_RATE = float(os.getenv("USD_TO_BDT_RATE", "127.0"))
USD_TO_BDT_RATE = DEFAULT_USD_TO_BDT_RATE

def get_live_usd_rate() -> float:
    """Returns dynamic USD to BDT rate from database settings, falling back to config default."""
    try:
        from database.db import db
        val = db.get_setting("usd_to_bdt_rate") or db.get_setting("usd_rate")
        if val:
            return float(val)
    except Exception:
        pass
    return DEFAULT_USD_TO_BDT_RATE
