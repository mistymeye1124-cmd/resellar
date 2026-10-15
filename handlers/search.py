# Smart Course Search, Intent Recognition, Anti-Spam & Customer Course Request Handlers
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import html
import re
from typing import Dict, Any
from database.db import db
from config import ADMIN_USERNAME, ADMIN_IDS, get_live_usd_rate
from utils.emojis import make_custom_button, em_tag
from utils.i18n import t, localize_item_name
from keyboards.user_kb import (
    get_product_detail_kb,
    get_course_search_results_kb,
    get_course_not_found_kb,
    get_casual_guide_kb,
    get_course_request_prompt_kb
)
from utils.ui_nav import render_screen, render_safe_html_text, get_cached_bot_info

router = Router()

class CourseRequestState(StatesGroup):
    waiting_for_details = State()

# In-memory session trackers
casual_tracker: Dict[int, int] = {}
last_search_query: Dict[int, str] = {}

# Set of common reply keyboard buttons to avoid intercepting
KNOWN_MENU_TEXTS = {
    "courses", "digital", "free_claim", "referral", "deposit", "reseller",
    "profile", "orders", "verify", "support", "language", "admin"
}

GREETING_WORDS = {
    "hi", "hello", "hey", "hei", "vai", "bhai", "ভাই", "হাই", "হ্যালো",
    "kemon achen", "kemon asen", "ki khobor", "salam", "assalamu alaikum",
    "সালাম", "আসসালামু আলাইকুম", "hola", "yo", "bro", "vaiya", "vai kemon achen"
}

JUNK_WORDS = {
    "ok", "hmm", "hm", "accha", "acha", "hobe", "?", "??", "???", "....",
    "nice", "good", "thik ace", "ha", "na", "yes", "no"
}

INTENT_KEYWORDS = {
    "course", "কোর্স", "lagbe", "লাগবে", "chai", "চাই", "kinte", "কিনতে",
    "dam", "দাম", "price", "account", "অ্যাকাউন্ট", "tool", "drive", "ড্রাইভ",
    "subscription", "software", "ace", "ache", "kivabe", "need", "buy",
    "learn", "video", "tutorial", "link", "লিংক", "nibo", "নিব"
}

# --- 1. COURSE REQUEST PROMPT & WORKFLOW ---

@router.message(F.text.in_([
    "Request Course (রিকোয়েস্ট)", "🎯 Request Course (রিকোয়েস্ট)", "Request Course",
    "🎯 Request Course", "কোর্স রিকোয়েস্ট", "রিকোয়েস্ট", "কোর্স রিকোয়েস্ট",
    "Request a Course", "কোর্স রিকোয়েস্ট করুন"
]))
@router.callback_query(F.data == "req_course_start")
async def handle_request_course_start(event: Message | CallbackQuery, state: FSMContext):
    await state.set_state(CourseRequestState.waiting_for_details)
    user_id = event.from_user.id
    lang = db.get_user_language(user_id)
    
    prompt_text = t("course_req_prompt_text", lang)
    kb = get_course_request_prompt_kb(lang)
    if isinstance(event, CallbackQuery):
        await event.answer()
        await render_screen(event, prompt_text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(prompt_text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "cancel_course_req")
async def handle_cancel_course_req(call: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = db.get_user_language(call.from_user.id)
    await call.answer(t("course_req_cancelled_alert", lang))
    from handlers.start import format_main_dashboard_text, is_admin
    from keyboards.user_kb import get_main_dashboard_inline_kb
    text = format_main_dashboard_text(call.from_user.id, call.from_user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(call.from_user.id))
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.message(CourseRequestState.waiting_for_details)
async def handle_course_request_received(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    if not message.text or not message.text.strip():
        err_msg = "❌ Please send the course name or website URL in text:" if lang in ["en", "hi", "ur"] else "❌ অনুগ্রহ করে কোর্স বা সফটওয়্যারের নাম বা লিংক টেক্সট আকারে লিখে পাঠান:"
        await message.answer(err_msg)
        return

    req_query = message.text.strip()
    user = message.from_user
    full_name = html.escape(user.full_name or "Customer")
    uname = f"@{user.username}" if user.username else "N/A"

    # Save to database
    req_id = db.record_course_request(user.id, user.full_name or "Customer", req_query)
    await state.clear()

    # User confirmation
    confirm_text = t("course_req_user_confirm", lang, item=html.escape(req_query), req_id=req_id)
    btn_browse = "🎓 Browse Catalog" if lang in ["en", "hi", "ur"] else "🎓 ক্যাটালগ ব্রাউজ করুন"
    btn_admin = "💬 Live Admin" if lang in ["en", "hi", "ur"] else "💬 সরাসরি অ্যাডমিন"
    buttons = [
        [
            make_custom_button(text=btn_browse, callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=btn_admin, url=f"https://t.me/{ADMIN_USERNAME}", emoji_key="support")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await message.answer(confirm_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

    # Admin Alert
    admin_alert = (
        "🔔 <b>নতুন কাস্টমার কোর্স রিকোয়েস্ট! (Course Request)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>কাস্টমার:</b> {full_name} ({uname})\n"
        f"🆔 <b>ইউজার আইডি:</b> <code>#{user.id}</code>\n"
        f"🏷️ <b>রিকোয়েস্ট আইডি:</b> <code>#REQ-{req_id}</code>\n\n"
        f"📦 <b>চাওয়া আইটেম / লিংক:</b>\n<code>{html.escape(req_query)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    admin_buttons = []
    if user.username:
        admin_buttons.append([
            InlineKeyboardButton(text=f"💬 চ্যাট করুন @{user.username}", url=f"https://t.me/{user.username}")
        ])
    admin_kb = InlineKeyboardMarkup(inline_keyboard=admin_buttons) if admin_buttons else None

    for admin_id in ADMIN_IDS:
        if admin_id > 0:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_alert, reply_markup=admin_kb, parse_mode="HTML")
            except Exception:
                pass

@router.callback_query(F.data == "quick_req_submit")
async def handle_quick_req_submit(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    query = last_search_query.get(user_id)
    if not query:
        await call.answer()
        err_prompt = "✏️ Please type the name or link of the course you want:" if lang in ["en", "hi", "ur"] else "✏️ অনুগ্রহ করে যে কোর্সটি চান তার নাম বা লিংক লিখে পাঠান:"
        await call.message.answer(err_prompt)
        return

    user = call.from_user
    full_name = html.escape(user.full_name or "Customer")
    uname = f"@{user.username}" if user.username else "N/A"

    req_id = db.record_course_request(user_id, user.full_name or "Customer", query)
    submit_alert = "✅ Your request has been submitted!" if lang in ["en", "hi", "ur"] else "✅ আপনার রিকোয়েস্ট সফলভাবে জমা হয়েছে!"
    await call.answer(submit_alert, show_alert=True)

    text = t("course_req_user_confirm", lang, item=html.escape(query), req_id=req_id)
    btn_browse = "🎓 Browse Catalog" if lang in ["en", "hi", "ur"] else "🎓 ক্যাটালগ ব্রাউজ করুন"
    buttons = [
        [
            make_custom_button(text=btn_browse, callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

    admin_alert = (
        "🔔 <b>নতুন ১-ট্যাপ কোর্স রিকোয়েস্ট! (1-Tap Request)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>কাস্টমার:</b> {full_name} ({uname})\n"
        f"🆔 <b>ইউজার আইডি:</b> <code>#{user_id}</code>\n"
        f"🏷️ <b>রিকোয়েস্ট আইডি:</b> <code>#REQ-{req_id}</code>\n\n"
        f"📦 <b>চাওয়া আইটেম / লিংক:</b>\n<code>{html.escape(query)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    admin_buttons = []
    if user.username:
        admin_buttons.append([
            InlineKeyboardButton(text=f"💬 চ্যাট করুন @{user.username}", url=f"https://t.me/{user.username}")
        ])
    admin_kb = InlineKeyboardMarkup(inline_keyboard=admin_buttons) if admin_buttons else None
    for admin_id in ADMIN_IDS:
        if admin_id > 0:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_alert, reply_markup=admin_kb, parse_mode="HTML")
            except Exception:
                pass


def detect_group_lang(text: str, user_tg_lang: str | None = None, db_user_lang: str | None = None) -> str:
    """Intelligently detects language for group chat context."""
    if re.search(r'[\u0600-\u06FF]', text):
        return "ur"
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    if db_user_lang and db_user_lang in ["ur", "hi", "en"]:
        return db_user_lang
    if user_tg_lang:
        code = user_tg_lang.lower()
        if code.startswith(("ur", "ar")):
            return "ur"
        if code.startswith("hi"):
            return "hi"
        if code.startswith("bn"):
            return "bn"
        if code.startswith("en"):
            return "en"
    if db_user_lang == "bn" and not text.isascii():
        return "bn"
    return "en"


def get_group_product_kb(product: Dict[str, Any], bot_username: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Delivers clean, safe action buttons for group chat (redirects purchase/access to private bot DM)."""
    buttons = []
    btn_buy_text = {
        "ur": "🛒 بوٹ میں حاصل کریں / تفصیلات",
        "hi": "🛒 बॉट में खरीदें / विवरण",
        "en": "🛒 Buy / View in Bot DM",
        "bn": "🛒 বট ইনবক্সে কিনুন / বিস্তারিত"
    }.get(lang, "🛒 Buy / View in Bot DM")

    buttons.append([
        InlineKeyboardButton(
            text=btn_buy_text,
            url=f"https://t.me/{bot_username}?start=c_{product['id']}"
        )
    ])

    sales_url = product.get("sales_page_url")
    if sales_url:
        btn_sales_text = {
            "ur": "🌐 کورس ویب سائٹ / تفصیلات",
            "hi": "🌐 कोर्स वेबसाइट / प्रीव्यू",
            "en": "🌐 Course Page / Preview",
            "bn": "🌐 কোর্স ওয়েবসাইট / প্রিভিউ"
        }.get(lang, "🌐 Course Page / Preview")
        buttons.append([
            InlineKeyboardButton(text=btn_sales_text, url=sales_url)
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- 2. SMART SEARCH & INTENT RECOGNITION LISTENER ---

@router.message(F.text)
async def handle_smart_course_search(message: Message, bot: Bot, state: FSMContext):
    # 0. Never intercept if user is in any active input flow (deposit, verify, request, admin, etc.)
    current_state = await state.get_state()
    if current_state is not None:
        return

    text = message.text.strip()
    if not text:
        return

    is_group = (message.chat.type in ["group", "supergroup"])

    # If in private chat, ignore slash commands here (handled by registered Command filters)
    if not is_group and text.startswith("/"):
        return

    t_lower = text.lower()

    # Skip if text belongs to recognized reply buttons (handled elsewhere)
    for known in [
        "main menu", "মূল মেনু", "menu", "মেনু", "হোম", "home",
        "browse courses", "কোর্স সমূহ", "digital accounts", "ডিজিটাল শপ",
        "free drops", "ফ্রি গিভঅ্যাওয়ে", "refer & earn", "ফ্রি কোর্স",
        "add balance", "ডিপোজিট", "reseller hub", "রিসেলার প্যানেল", "রিসেলার হাব", "reseller",
        "my profile", "প্রোফাইল", "my purchases", "অর্ডার", "verify reseller",
        "সততা যাচাই", "support & help", "হেল্প", "language", "admin panel"
    ]:
        if known in t_lower:
            return

    user_id = message.from_user.id

    # CHECK 1: Casual Greetings & Chat (Intent B - Anti-Spam)
    is_greeting = False
    if t_lower in GREETING_WORDS:
        is_greeting = True
    else:
        # Check if message starts with greeting without any product keyword
        words = t_lower.split()
        if len(words) <= 3 and any(w in GREETING_WORDS for w in words):
            if not any(k in t_lower for k in INTENT_KEYWORDS) and not ("." in t_lower and "/" in t_lower):
                is_greeting = True

    if is_greeting:
        # In groups/supergroups, stay 100% silent on greetings
        if is_group:
            return
        cnt = casual_tracker.get(user_id, 0) + 1
        casual_tracker[user_id] = cnt
        if cnt == 1:
            # First greeting in DM: stay silent
            return
        else:
            # Consecutive greeting in DM: send friendly guidance card
            casual_tracker[user_id] = 0
            lang = db.get_user_language(user_id)
            guide_text = t("search_casual_guide_text", lang)
            await message.answer(guide_text, reply_markup=get_casual_guide_kb(lang), parse_mode="HTML")
            return

    # CHECK 2: Short Meaningless Junk / Typo (Intent C)
    if len(text) < 2 or t_lower in JUNK_WORDS:
        return

    # =========================================================================
    # PATH A: GROUP & SUPERGROUP (VIP Group Anti-Spam & Dedicated Search)
    # =========================================================================
    if is_group:
        bot_info = await get_cached_bot_info(bot)
        bot_username = (bot_info.username or "").lower() if bot_info else ""

        is_reply_to_bot = bool(
            message.reply_to_message and
            message.reply_to_message.from_user and
            message.reply_to_message.from_user.id == bot.id
        )
        is_tagged = bool(bot_username and f"@{bot_username}" in t_lower) or is_reply_to_bot
        is_slash_search = t_lower.startswith(("/search", "/find", "/course"))
        is_explicit = is_tagged or is_slash_search

        # Clean query
        clean_query = text
        if bot_username and f"@{bot_username}" in t_lower:
            clean_query = re.sub(rf"@{re.escape(bot_username)}", "", clean_query, flags=re.IGNORECASE)
        if is_slash_search:
            clean_query = re.sub(r"^/(search|find|course)\s*", "", clean_query, flags=re.IGNORECASE)
        clean_query = clean_query.strip()

        # If user explicitly called bot without query
        if not clean_query or len(clean_query) < 2:
            if is_explicit:
                glang = detect_group_lang(text, message.from_user.language_code, db.get_user_language(user_id))
                prompt_msg = {
                    "ur": f"👋 جی! کورس یا ٹول تلاش کرنے کے لیے نام لکھیں۔ مثلاً:\n<code>@{bot_username} Python</code> یا <code>/search Python</code>",
                    "hi": f"👋 नमस्ते! कोई भी कोर्स या टूल खोजने के लिए नाम लिखें। जैसे:\n<code>@{bot_username} Python</code> या <code>/search Python</code>",
                    "en": f"👋 Hi! Type a course or tool name to search. Example:\n<code>@{bot_username} Python</code> or <code>/search Python</code>",
                    "bn": f"👋 আসসালামু আলাইকুম! কোনো কোর্স বা টুল খুঁজতে নাম লিখে পাঠান। যেমন:\n<code>@{bot_username} Python</code> বা <code>/search Python</code>"
                }.get(glang, f"👋 Hi! Type a course name to search. Example: <code>@{bot_username} Python</code>")
                await message.reply(prompt_msg, parse_mode="HTML")
            return

        # Check conversational guard:
        # If not explicit and not a URL: ignore long sentences (> 4 words) that are normal conversation between members
        words = clean_query.split()
        is_url = ("http://" in clean_query or "https://" in clean_query or "www." in clean_query or ('.' in clean_query and ' ' not in clean_query and '/' in clean_query))
        if not is_explicit and not is_url:
            if len(words) > 4 and not any(clean_query.lower().startswith(k) for k in ["course", "কোর্স", "kurs", "tutorial", "account", "tool"]):
                return

        # Execute DB search
        matches = db.search_courses(clean_query, limit=5)
        glang = detect_group_lang(clean_query, message.from_user.language_code, db.get_user_language(user_id))

        if not matches:
            # NO MATCH IN DB:
            # If not explicitly calling the bot, STAY 100% SILENT! (Group chat remains peaceful)
            if not is_explicit:
                return

            # Explicitly called: send compact 2-line polite DM redirect
            not_found_msg = {
                "ur": f"🔍 <b>'{html.escape(clean_query)}'</b> فوری کیٹلاگ میں نہیں ملا۔\nاس کورس کی درخواست کے لیے نیچے دیے گئے بٹن پر کلک کریں:",
                "hi": f"🔍 <b>'{html.escape(clean_query)}'</b> अभी कैटलॉग में नहीं मिला।\nइस कोर्स का अनुरोध करने के लिए नीचे दिए गए बटन पर टैप करें:",
                "en": f"🔍 <b>'{html.escape(clean_query)}'</b> was not found in the instant catalog.\nTap below to request this course directly in bot DM:",
                "bn": f"🔍 <b>'{html.escape(clean_query)}'</b> ইনস্ট্যান্ট ক্যাটালগে পাওয়া যায়নি।\nকোর্সটির রিকোয়েস্ট পাঠাতে নিচের বাটনে ট্যাপ করুন:"
            }.get(glang, f"🔍 <b>'{html.escape(clean_query)}'</b> is not in catalog. Tap below to request:")

            req_btn_text = {
                "ur": "📩 بوٹ میں کورس کی درخواست کریں",
                "hi": "📩 बॉट में कोर्स रिक्वेस्ट भेजें",
                "en": "📩 Request Course in Bot DM",
                "bn": "📩 বট ইনবক্সে রিকোয়েস্ট পাঠান"
            }.get(glang, "📩 Request Course in Bot DM")

            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=req_btn_text,
                    url=f"https://t.me/{bot_username}?start=req_course"
                )
            ]])
            await message.reply(not_found_msg, reply_markup=kb, parse_mode="HTML")
            return

        # MATCHES FOUND IN DB:
        if len(matches) == 1:
            prod = matches[0]
            ch_p = float(prod.get("price_channel_bdt") or 0)
            acc_p = float(prod.get("price_account_bdt") or 0)
            eff_bdt = ch_p if (ch_p > 0 and acc_p <= 0) else (acc_p if (acc_p > 0 and ch_p <= 0) else float(prod.get("price_bdt") or 0))
            if eff_bdt <= 0 and (ch_p > 0 or acc_p > 0):
                eff_bdt = ch_p if ch_p > 0 else acc_p
            reg_bdt = int(eff_bdt)
            reg_usd = prod["price_usd"] if float(prod.get("price_usd") or 0) > 0 else round(eff_bdt / get_live_usd_rate(), 2)
            em_crs = em_tag("courses", "🎓")
            c_title = localize_item_name(prod['title'], glang)
            detail_text = t(
                "search_found_single_text",
                glang,
                em_crs=em_crs,
                title=html.escape(c_title),
                desc=render_safe_html_text(prod.get('description', '')[:300]),
                bdt=reg_bdt,
                usd=reg_usd
            )
            g_kb = get_group_product_kb(prod, bot_username, glang)
            if prod.get("photo_file_id"):
                try:
                    await message.reply_photo(
                        photo=prod["photo_file_id"],
                        caption=detail_text,
                        reply_markup=g_kb,
                        parse_mode="HTML"
                    )
                    return
                except Exception:
                    pass
            await message.reply(detail_text, reply_markup=g_kb, parse_mode="HTML")
            return

        else:
            # Multiple matches found in group
            header = {
                "ur": f"🔍 <b>'{html.escape(clean_query)}'</b> کے لیے {len(matches)} کورسز ملے:",
                "hi": f"🔍 <b>'{html.escape(clean_query)}'</b> کے لیے {len(matches)} कोर्स मिले:",
                "en": f"🔍 Found {len(matches)} courses matching <b>'{html.escape(clean_query)}'</b>:",
                "bn": f"🔍 <b>'{html.escape(clean_query)}'</b> এর জন্য {len(matches)}টি কোর্স পাওয়া গেছে:"
            }.get(glang, f"🔍 Found {len(matches)} matching courses:")

            buttons = []
            for m in matches:
                m_title = localize_item_name(m['title'], glang)
                m_ch = float(m.get("price_channel_bdt") or 0)
                m_acc = float(m.get("price_account_bdt") or 0)
                m_eff = m_ch if (m_ch > 0 and m_acc <= 0) else (m_acc if (m_acc > 0 and m_ch <= 0) else float(m.get("price_bdt") or 0))
                if m_eff <= 0 and (m_ch > 0 or m_acc > 0):
                    m_eff = m_ch if m_ch > 0 else m_acc
                bdt = int(m_eff)
                btn_lbl = f"📦 {m_title[:32]} (৳{bdt})"
                buttons.append([
                    InlineKeyboardButton(
                        text=btn_lbl,
                        url=f"https://t.me/{bot_username}?start=c_{m['id']}"
                    )
                ])
            await message.reply(header, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
            return

    # =========================================================================
    # PATH B: PRIVATE DM (100% UNTOUCHED ORIGINAL SEARCH & LEAD CAPTURE)
    # =========================================================================
    lang = db.get_user_language(user_id)
    is_url = ("http://" in text or "https://" in text or "www." in text or ('.' in text and ' ' not in text and '/' in text))
    has_keyword = any(k in t_lower for k in INTENT_KEYWORDS)

    # Save to last search query
    last_search_query[user_id] = text
    casual_tracker[user_id] = 0

    # Execute smart DB search
    matches = db.search_courses(text, limit=6)

    # 1. Single match found -> Deliver direct product showcase card!
    if len(matches) == 1:
        prod = matches[0]
        in_stock = (prod.get("is_in_stock", 1) == 1)
        
        ch_p = float(prod.get("price_channel_bdt") or 0)
        acc_p = float(prod.get("price_account_bdt") or 0)
        eff_bdt = ch_p if (ch_p > 0 and acc_p <= 0) else (acc_p if (acc_p > 0 and ch_p <= 0) else float(prod.get("price_bdt") or 0))
        if eff_bdt <= 0 and (ch_p > 0 or acc_p > 0):
            eff_bdt = ch_p if ch_p > 0 else acc_p
        reg_bdt = int(eff_bdt)
        reg_usd = prod["price_usd"] if float(prod.get("price_usd") or 0) > 0 else round(eff_bdt / get_live_usd_rate(), 2)
        
        em_dia = em_tag("diamond", "💎")
        em_crs = em_tag("courses", "🎓")
        em_box = em_tag("box", "📦")
        
        c_title = localize_item_name(prod['title'], lang)
        detail_text = t(
            "search_found_single_text",
            lang,
            em_crs=em_crs,
            title=html.escape(c_title),
            desc=render_safe_html_text(prod.get('description', '')[:300]),
            bdt=reg_bdt,
            usd=reg_usd
        )
        if prod.get("photo_file_id"):
            try:
                await message.answer_photo(
                    photo=prod["photo_file_id"],
                    caption=detail_text,
                    reply_markup=get_product_detail_kb(prod, in_stock, lang, user_id=message.from_user.id),
                    parse_mode="HTML"
                )
                return
            except Exception:
                pass

        await message.answer(detail_text, reply_markup=get_product_detail_kb(prod, in_stock, lang, user_id=message.from_user.id), parse_mode="HTML")
        return

    # 2. Multiple matches found -> Deliver interactive selection list!
    elif len(matches) > 1:
        list_text = t(
            "search_found_multiple_text",
            lang,
            count=len(matches),
            query=html.escape(text)
        )
        await message.answer(list_text, reply_markup=get_course_search_results_kb(matches, text, lang), parse_mode="HTML")
        return

    # 3. No match found -> Deliver professional Course Request lead capture!
    else:
        # If it was a URL, or contained search keywords, or was an explicit search phrase
        if is_url or has_keyword or len(text.split()) >= 2 or len(text) >= 4:
            not_found_text = t(
                "search_not_found_text",
                lang,
                query=html.escape(text)
            )
            await message.answer(not_found_text, reply_markup=get_course_not_found_kb(text, lang), parse_mode="HTML")
            return

