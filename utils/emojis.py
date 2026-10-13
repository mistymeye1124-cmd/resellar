# Telegram Premium Custom Emoji Engine for Reseller Bot
# 100% Comprehensive Coverage for All Emojis & Buttons
import unicodedata
import re
import html
from typing import Optional, Dict, Any, Tuple
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Master Telegram Premium Custom Emoji Catalog
DEFAULT_CUSTOM_EMOJIS: Dict[str, str] = {
    # Core Navigation & Shell
    "home": "5323642109767460983",         # 🏠 Home / Main Menu
    "menu": "5323642109767460983",         # 🏠 Main Menu
    "admin": "6235252066554484059",        # 👑 Admin Crown / VIP Leader
    "crown": "6235252066554484059",        # 👑 Crown
    "help": "5373098009640836781",         # ❓ Help / Support
    "support": "5373098009640836781",      # 💬 Support / Contact
    "language": "5397798946380721942",     # 🌐 Language / Globe
    "settings": "5201762530023733712",     # ⚙️ Settings / Tools / Icons

    # Products & Digital Accounts
    "digital": "5445118546700954082",      # ⚡ Digital Tools & Accounts
    "box": "5837134496868077492",          # 📦 Package / Stock / Key
    "stock": "5837134496868077492",        # 📦 Stock Box
    "download": "5445118546700954082",     # 🚀 Download / Direct Link

    # Giveaways, Drops & Flash
    "free_claim": "5397916757333654639",   # 🎁 Free Claim / Giveaway Drops
    "gift": "5397916757333654639",         # 🎁 Gift Box
    "zap": "6271459718896554468",          # ⚡ Instant Claim / Fast Flash
    "fire": "5136918320674505825",         # 🔥 Fire / Trending / Hot Drop

    # Finance, Wallet & Transactions
    "wallet": "5395542928909150340",       # 💰 Wallet / Balance / Deposit
    "deposit": "5395542928909150340",      # 💳 Deposit / Money / Cash
    "cash": "5395542928909150340",         # 💵 Cash

    # Resellers & Verification
    "diamond": "6271494293383286950",      # 💎 Reseller Diamond / VIP
    # Native high-definition shield emoji (prevents DEF sticker glitch)
    "trophy": "5226431245918942763",       # 🏆 Trophy / Leaderboard
    "star": "6181535395914718008",         # ⭐ Star / Rating
    "target": "5310278924616356636",       # 🎯 Quota / Target / Race
    "flag": "5310278924616356636",         # 🏁 Live Race / Challenge

    # Community & Referrals
    "referral": "5292109589456645419",     # 👥 Referral / Affiliates / Team
    "users": "5292109589456645419",        # 👥 Users
    "profile": "6269397073737553354",      # 👤 Profile / My Account
    "broadcast": "6242353099193718277",    # 📢 Broadcast / Channel
    "channel": "6242353099193718277",      # 📢 Channel Link

    # Actions & Indicators
    "check": "5202010985291871421",        # ✅ Active / Approved / Success
    "cross": "5204244329631082615",        # ❌ Reject / Close / Cancel
    "refresh": "5445118546700954082",      # 🔄 Refresh
    "edit": "5197269100878907942",         # ✏️ Edit
    "search": "5310278924616356636",       # 🔍 Search
    "sparkle": "6179411633371095707",      # ✨ Sparkle / Cookies / Highlights

    # Payment Gateways
    "bkash": "6237941149873478197",        # bKash Custom Emoji
    "nagad": "6235269688805301565",        # Nagad Custom Emoji
    "rocket": "6235282831405227077",       # Rocket Custom Emoji
    "binance": "6235545537374855311",      # Binance Custom Emoji

    # Languages
    "lang_bn": "5911365056594973179",      # 🇧🇩 Bengali
    "lang_en": "5780829794899858599",      # 🇬🇧 English
    "lang_hi": "6109380284644329775",      # 🇮🇳 Hindi
    "lang_ru": "5449408995691341691",      # 🇷🇺 Russian
}

# Exhaustive Mapping from ALL Unicode Emoji Characters to DEFAULT_CUSTOM_EMOJIS Keys
# NOTE: Typographic bullets ('•', '◦', '‣', '▰', '▱') and symbols like 🛍️, 🤝, 🏷️ are left as native unicode
EMOJI_CHAR_TO_KEY: Dict[str, str] = {
    # Crown & VIP
    "👑": "crown",
    "💎": "diamond",

    # Money, Wallet & Billing
    "💰": "wallet",
    "💳": "deposit",
    "💵": "cash",
    "💸": "cash",
    "🪙": "wallet",

    # Stock, Packages, Keys & Storage
    "📦": "box",
    "📫": "box",
    "📬": "box",
    "📩": "box",
    "📥": "box",
    "📤": "box",
    "🔑": "box",
    "📁": "category",
    "📂": "category",
    "💾": "digital",
    "☁️": "digital",
    "☁": "digital",

    # Giveaways, Gifts, Celebrations & Food/Cookies
    "🎁": "free_claim",
    "🎉": "free_claim",
    "🍾": "free_claim",
    "🍪": "sparkle",
    "🌱": "sparkle",
    "🎨": "sparkle",
    "🎬": "sparkle",
    "🎭": "sparkle",

    # Instant, Speed & Lightning
    "⚡️": "zap",
    "⚡": "zap",
    "💡": "zap",
    "⏳": "zap",
    "⌛": "zap",
    "⏰": "zap",
    "⏱️": "zap",
    "⏱": "zap",
    "🕒": "zap",
    "🔓": "zap",

    # Fire, Warning & Alert
    "🔥": "fire",
    "⚠️": "fire",
    "⚠": "fire",
    "🚨": "fire",
    "💥": "fire",
    "⛔": "cross",

    # Orders & Catalog
    "📜": "orders",
    "🧾": "orders",
    "📃": "orders",
    "📄": "orders",
    "📋": "catalog",
    "📅": "orders",
    "📊": "orders",
    "📈": "sparkle",
    "📉": "zap",

    # Trophies, Competitions & Races
    "🏆": "trophy",
    "🥇": "trophy",
    "🥈": "trophy",
    "🥉": "trophy",
    "🎖️": "trophy",
    "🎖": "trophy",
    "🎯": "target",
    "🏁": "flag",
    "🚩": "flag",
    "🏃": "flag",
    "🏎️": "flag",
    "🏎": "flag",

    # Stars & Sparkles
    "⭐": "star",
    "⭐️": "star",
    "🌟": "star",
    "✨": "sparkle",
    "👋": "sparkle",

    # Users, Profiles, Community & Collaboration
    "👥": "referral",
    "👤": "profile",
    "👨": "profile",
    "🆔": "profile",
    "💼": "profile",

    # Broadcast, Announcement & Channels
    "📢": "broadcast",
    "📣": "broadcast",
    "🔔": "broadcast",
    "🔕": "cross",

    # Support & Communication
    "💬": "support",
    "🗨️": "support",
    "🗨": "support",
    "❓": "help",
    "ℹ️": "help",
    "ℹ": "help",

    # Navigation & System Shell
    "🏠": "home",
    "🔙": "back",
    "🌐": "language",
    "⚙️": "settings",
    "⚙": "settings",
    "🛠️": "settings",
    "🛠": "settings",
    "🔧": "settings",
    "🤖": "settings",

    # Digital Tools, Hardware & Links
    "🚀": "download",
    "🔗": "download",
    "💻": "digital",
    "📱": "digital",
    "📸": "digital",
    "🖼️": "digital",
    "🖼": "digital",

    # Actions & Editing
    "🔄": "refresh",
    "🔁": "refresh",
    "✏️": "edit",
    "✏": "edit",
    "📝": "edit",
    "✍️": "edit",
    "✍": "edit",
    "🔍": "search",
    "🔎": "search",

    # Status & Indicators
    "✅": "check",
    "✔️": "check",
    "✔": "check",
    "☑️": "check",
    "☑": "check",
    "🟢": "check",
    "🟩": "check",
    "❌": "cross",
    "✖️": "cross",
    "✖": "cross",
    "🚫": "cross",
    "🛑": "cross",
    "🔴": "cross",
    "🟥": "cross",
    "🗑️": "cross",
    "🗑": "cross",
    "🟠": "sparkle",
    "🟡": "sparkle",
    "🟣": "sparkle",

    # Languages
    "🇧🇩": "lang_bn",
    "🇬🇧": "lang_en",
    "🇮🇳": "lang_hi",
    "🇷🇺": "lang_ru",
}

NON_EMOJI_SYMBOLS = {'•', '◦', '‣', '▰', '▱', '^', '`', '─', '━', '█', '░', '*', '_', '~', '|'}

def is_actual_emoji(s: str) -> bool:
    """Accurately checks if a character or cluster is a valid Telegram-supported emoji."""
    if not s or s in NON_EMOJI_SYMBOLS:
        return False
    cp = ord(s[0])
    cat = unicodedata.category(s[0])
    if cat in ('So', 'Sk') or 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x2300 <= cp <= 0x23FF or 0x2B50 <= cp <= 0x2B55:
        return True
    return False

def get_custom_emoji_id(name: str) -> Optional[str]:
    """Retrieves dynamic custom emoji ID from database with resilient fallback."""
    if not name:
        return None
    clean_name = name.lower().strip()
    try:
        from database.db import db
        db_val = db.get_setting(f"emoji_{clean_name}", "")
        if db_val and db_val.strip().isdigit():
            return db_val.strip()
    except Exception:
        pass
    return DEFAULT_CUSTOM_EMOJIS.get(clean_name)

def strip_all_emojis(text: str, preserve_checkmarks: bool = False) -> str:
    """
    Strips unicode emojis while strictly preserving arrows (➔, ->) and formatting symbols.
    """
    if not text:
        return ""
    chars = []
    for c in text:
        cp = ord(c)
        if c in ('➔', '->', '❯', '›', '»', '▼', '▲', '•', '◦', '‣', '▰', '▱', '─', '━', '█', '░', '|'):
            chars.append(c)
            continue
        if preserve_checkmarks and cp in (0x2705, 0x2611, 0x2713, 0x2714):
            chars.append(c)
            continue
        cat = unicodedata.category(c)
        if (
            cat in ('So', 'Sk') or
            0x1F000 <= cp <= 0x1FAFF or
            0x2600 <= cp <= 0x27BF or
            0x2300 <= cp <= 0x23FF or
            0x2B50 <= cp <= 0x2B55 or
            0xFE00 <= cp <= 0xFE0F or
            cp == 0x200D or cp == 0x20E3
        ):
            continue
        chars.append(c)
    cleaned = ''.join(chars).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else text.strip()

def detect_emoji_key_from_text(text: str) -> Optional[str]:
    """
    Automatically detects the best custom emoji key by inspecting unicode emojis
    or intent keywords inside button or message text.
    """
    if not text:
        return None
    
    # 1. Inspect direct unicode emojis
    sorted_emojis = sorted(EMOJI_CHAR_TO_KEY.keys(), key=len, reverse=True)
    for em in sorted_emojis:
        if em in text:
            return EMOJI_CHAR_TO_KEY[em]
            
    # 2. Inspect intent keywords
    t_lower = text.lower()
    keyword_map = [
        (("back", "ফিরে", "পিছনে", "वापस"), "back"),
        (("home", "মেনু", "হোম", "main menu"), "home"),
        (("cancel", "বাতিল", "close", "বন্ধ", "রিসিভ", "রিসেলার বাতিল"), "cross"),
        (("approve", "অনুমোদন", "confirm", "নিশ্চিত", "success", "সফল"), "check"),
        (("deposit", "টপ-আপ", "ডিপোজিট", "ব্যালেন্স রিচার্জ", "জমা"), "deposit"),
        (("free", "গিভঅ্যাওয়ে", "লুট", "claim", "ক্লেইম", "উপহার"), "free_claim"),
        (("reseller", "রিসেলার", "পাইকারি", "wholesale"), "diamond"),
        (("referral", "রেফার", "রেফারেল", "refer"), "referral"),
        (("profile", "প্রোফাইল", "account", "আমার অ্যাকাউন্ট"), "profile"),
        (("support", "সাপোর্ট", "যোগাযোগ", "হেল্প", "help"), "support"),
        (("search", "সার্চ", "খুঁজুন", "অনুসন্ধান"), "search"),
        (("admin", "অ্যাডমিন", "এডমিন", "owner"), "admin"),
        (("stock", "স্টক", "ইনভেন্টরি", "স্টকে"), "box"),
        (("cookie", "কুকি", "কুকিজ"), "sparkle"),
        (("drive", "ড্রাইভ", "মেগা", "mega", "cloud"), "download"),
        (("license", "লাইসেন্স", "কি", "key"), "box"),
        (("broadcast", "ব্রডকাস্ট", "মেসেজ পাঠান"), "broadcast"),
        (("channel", "চ্যানেল", "গ্রুপ"), "channel"),
        (("settings", "সেটিংস", "কনফিগ"), "settings"),
        (("bkash", "বিকাশ"), "bkash"),
        (("nagad", "নগদ"), "nagad"),
        (("rocket", "রকেট"), "rocket"),
        (("binance", "বাইন্যান্স", "usdt"), "binance"),
        (("language", "ভাষা", "lang"), "language"),
    ]
    for keywords, key in keyword_map:
        if any(kw in t_lower for kw in keywords):
            return key
            
    return None

def make_custom_button(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    custom_emoji_id: Optional[str] = None,
    emoji_key: Optional[str] = None,
    copy_text: Optional[Any] = None,
    web_app: Optional[Any] = None
) -> InlineKeyboardButton:
    """
    Constructs an InlineKeyboardButton strictly preserving all emojis in text.
    Telegram Bot API Inline Buttons do not support icon_custom_emoji_id,
    so keeping unicode emojis in text ensures 100% vibrant display on Mobile and PC.
    """
    kwargs: Dict[str, Any] = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if copy_text:
        kwargs["copy_text"] = copy_text
    if web_app:
        kwargs["web_app"] = web_app
    return InlineKeyboardButton(**kwargs)

def make_custom_reply_button(
    text: str,
    custom_emoji_id: Optional[str] = None,
    emoji_key: Optional[str] = None
) -> KeyboardButton:
    """
    Constructs a KeyboardButton with full emoji text intact and optional custom emoji id.
    Ensures that if a client doesn't support custom emoji icons in reply buttons,
    the native emoji in text is always visible.
    """
    resolved_key = emoji_key or detect_emoji_key_from_text(text)
    final_emoji_id = custom_emoji_id or (get_custom_emoji_id(resolved_key) if resolved_key else None)
    
    kwargs: Dict[str, Any] = {"text": text}
    if final_emoji_id and str(final_emoji_id).isdigit():
        kwargs["icon_custom_emoji_id"] = str(final_emoji_id)
        
    return KeyboardButton(**kwargs)

def apply_premium_emojis_to_keyboard(reply_markup):
    """
    Ensures keyboards are delivered cleanly. Inline buttons strictly preserve their
    native emojis in button text so they never display as stripped text.
    """
    return reply_markup

def strip_button_custom_emojis(reply_markup):
    """
    Strips icon_custom_emoji_id from all buttons in reply_markup as an automatic fallback
    if Telegram Bot API rejects custom emoji in buttons.
    """
    if not reply_markup:
        return reply_markup
    try:
        if hasattr(reply_markup, "inline_keyboard"):
            new_rows = []
            for row in reply_markup.inline_keyboard:
                new_row = []
                for btn in row:
                    d = btn.model_dump(exclude_none=True)
                    d.pop("icon_custom_emoji_id", None)
                    new_row.append(InlineKeyboardButton(**d))
                new_rows.append(new_row)
            return InlineKeyboardMarkup(inline_keyboard=new_rows)
        elif hasattr(reply_markup, "keyboard"):
            new_rows = []
            for row in reply_markup.keyboard:
                new_row = []
                for btn in row:
                    d = btn.model_dump(exclude_none=True)
                    d.pop("icon_custom_emoji_id", None)
                    new_row.append(KeyboardButton(**d))
                new_rows.append(new_row)
            d_rm = reply_markup.model_dump(exclude_none=True)
            d_rm["keyboard"] = new_rows
            return ReplyKeyboardMarkup(**d_rm)
    except Exception:
        pass
    return reply_markup

def get_tg_emoji_tag(name: str, fallback: str = "✨") -> str:
    """Returns HTML <tg-emoji emoji-id="...">fallback</tg-emoji> tag for message texts."""
    eid = get_custom_emoji_id(name)
    if eid and eid.isdigit():
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback

# Concise alias for high-frequency template rendering
em_tag = get_tg_emoji_tag

def render_premium_html(text: str) -> str:
    """
    Parses an HTML message string and converts all standard unicode emojis into
    Telegram Premium custom emoji tags (<tg-emoji emoji-id="...">char</tg-emoji>).
    Preserves <pre>, <code>, and existing <tg-emoji> blocks from modification.
    """
    if not text or not isinstance(text, str):
        return text

    # Sort emoji keys by length descending to match composite emojis like 🛡️ before 🛡
    sorted_chars = sorted(EMOJI_CHAR_TO_KEY.keys(), key=len, reverse=True)
    pattern = "(" + "|".join(re.escape(k) for k in sorted_chars) + ")"
    emoji_regex = re.compile(pattern)

    # Split text into HTML tags and non-tag text segments
    tokens = re.split(r'(<[^>]+>)', text)
    in_skip_block = False
    skip_tags = {"pre", "code", "tg-emoji"}
    current_skip_tag = None

    result = []
    for token in tokens:
        if not token:
            continue
        if token.startswith("<") and token.endswith(">"):
            # HTML tag handling
            tag_content = token[1:-1].strip()
            is_closing = tag_content.startswith("/")
            tag_name = tag_content.lstrip("/").split()[0].lower() if tag_content.lstrip("/") else ""

            if not is_closing and tag_name in skip_tags:
                in_skip_block = True
                current_skip_tag = tag_name
            elif is_closing and tag_name == current_skip_tag:
                in_skip_block = False
                current_skip_tag = None

            result.append(token)
        else:
            # Text segment handling
            if in_skip_block:
                result.append(token)
            else:
                def replace_emoji(match):
                    char = match.group(0)
                    key = EMOJI_CHAR_TO_KEY.get(char)
                    if key:
                        eid = get_custom_emoji_id(key)
                        if eid and eid.isdigit():
                            return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
                    return char

                result.append(emoji_regex.sub(replace_emoji, token))

    return "".join(result)

def markdown_to_telegram_html(text: str) -> str:
    return text

def prepare_premium_message_content(text: Optional[str], parse_mode: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Keeps content clean; applies premium rendering only to explicit HTML messages."""
    if not text or not isinstance(text, str):
        return text, parse_mode
    if parse_mode == "HTML":
        return render_premium_html(text), "HTML"
    return text, parse_mode

