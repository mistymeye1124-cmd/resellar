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
from keyboards.user_kb import (
    get_product_detail_kb,
    get_course_search_results_kb,
    get_course_not_found_kb,
    get_casual_guide_kb,
    get_course_request_prompt_kb
)
from utils.ui_nav import render_screen, render_safe_html_text

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
    
    prompt_text = (
        "🎯 <b>প্রিমিয়াম কোর্স ও সফটওয়্যার রিকোয়েস্ট হাব</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "আপনার পছন্দের যে কোর্স, টুল বা প্রিমিয়াম অ্যাকাউন্টটি আমাদের ক্যাটালগে নেই, "
        "তার <b>নাম</b> অথবা <b>অফিশিয়াল ওয়েবসাইট লিংক</b> লিখে পাঠান:\n\n"
        "<i>(উদাহরণস্বরূপ: 10 Minute School Web Dev, অথবা Bohubrihi Python, অথবা https://udemy.com/...)</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 আমাদের অ্যাডমিন টিম রিকোয়েস্ট পাওয়ার সাথে সাথেই তা ব্যবস্থা করার উদ্যোগ নেবে!"
    )
    kb = get_course_request_prompt_kb()
    if isinstance(event, CallbackQuery):
        await event.answer()
        await render_screen(event, prompt_text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(prompt_text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "cancel_course_req")
async def handle_cancel_course_req(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("❌ রিকোয়েস্ট বাতিল করা হয়েছে।")
    from handlers.start import format_main_dashboard_text, is_admin
    from keyboards.user_kb import get_main_dashboard_inline_kb
    lang = db.get_user_language(call.from_user.id)
    text = format_main_dashboard_text(call.from_user.id, call.from_user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(call.from_user.id))
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.message(CourseRequestState.waiting_for_details)
async def handle_course_request_received(message: Message, state: FSMContext, bot: Bot):
    if not message.text or not message.text.strip():
        await message.answer("❌ অনুগ্রহ করে কোর্স বা সফটওয়্যারের নাম বা লিংক টেক্সট আকারে লিখে পাঠান:")
        return

    req_query = message.text.strip()
    user = message.from_user
    full_name = html.escape(user.full_name or "Customer")
    uname = f"@{user.username}" if user.username else "N/A"

    # Save to database
    req_id = db.record_course_request(user.id, user.full_name or "Customer", req_query)
    await state.clear()

    # User confirmation
    confirm_text = (
        "✅ <b>আপনার কোর্স রিকোয়েস্ট সফলভাবে জমা হয়েছে!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>রিকোয়েস্টকৃত আইটেম:</b>\n<code>{html.escape(req_query)}</code>\n\n"
        f"🆔 <b>রিকোয়েস্ট ট্র্যাকিং আইডি:</b> <code>#REQ-{req_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 আমাদের অ্যাডমিন টিম এটি পর্যালোচনা করে দ্রুত ক্যাটালগে যুক্ত করবে অথবা আপনার সাথে ইনবক্সে যোগাযোগ করবে। ধন্যবাদ!"
    )
    buttons = [
        [
            make_custom_button(text="🎓 ক্যাটালগ ব্রাউজ করুন", callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text="💬 সরাসরি অ্যাডমিন", url=f"https://t.me/{ADMIN_USERNAME}", emoji_key="support")
        ],
        [
            make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")
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
    query = last_search_query.get(user_id)
    if not query:
        await call.answer()
        from aiogram.fsm.context import FSMContext
        await call.message.answer("✏️ অনুগ্রহ করে যে কোর্সটি চান তার নাম বা লিংক লিখে পাঠান:")
        return

    user = call.from_user
    full_name = html.escape(user.full_name or "Customer")
    uname = f"@{user.username}" if user.username else "N/A"

    req_id = db.record_course_request(user_id, user.full_name or "Customer", query)
    await call.answer("✅ আপনার রিকোয়েস্ট সফলভাবে জমা হয়েছে!", show_alert=True)

    text = (
        "✅ <b>আপনার রিকোয়েস্ট সফলভাবে জমা হয়েছে!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>রিকোয়েস্টকৃত আইটেম:</b>\n<code>{html.escape(query)}</code>\n\n"
        f"🆔 <b>রিকোয়েস্ট আইডি:</b> <code>#REQ-{req_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 আমাদের টিম দ্রুত এটি ক্যাটালগে যুক্ত করবে অথবা আপনার সাথে যোগাযোগ করবে।"
    )
    buttons = [
        [
            make_custom_button(text="🎓 ক্যাটালগ ব্রাউজ করুন", callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text="🏠 মূল মেনু", callback_data="main_menu", emoji_key="home")
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


# --- 2. SMART SEARCH & INTENT RECOGNITION LISTENER ---

@router.message(F.text)
async def handle_smart_course_search(message: Message, bot: Bot, state: FSMContext):
    # 0. Never intercept if user is in any active input flow (deposit, verify, request, admin, etc.)
    current_state = await state.get_state()
    if current_state is not None:
        return

    text = message.text.strip()
    if not text or text.startswith("/"):
        return

    # Skip if text belongs to recognized reply buttons (handled elsewhere)
    t_lower = text.lower()
    for known in [
        "browse courses", "কোর্স সমূহ", "digital accounts", "ডিজিটাল শপ",
        "free drops", "ফ্রি গিভঅ্যাওয়ে", "refer & earn", "ফ্রি কোর্স",
        "add balance", "ডিপোজিট", "reseller hub", "রিসেলার প্যানেল",
        "my profile", "প্রোফাইল", "my purchases", "অর্ডার", "verify reseller",
        "সততা যাচাই", "support & help", "হেল্প", "language", "admin panel"
    ]:
        if known in t_lower:
            return

    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

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
        cnt = casual_tracker.get(user_id, 0) + 1
        casual_tracker[user_id] = cnt
        if cnt == 1:
            # First greeting: stay silent / no spam
            return
        else:
            # Consecutive greeting (2nd message): send friendly guidance card
            casual_tracker[user_id] = 0
            guide_text = (
                "👋 <b>আসসালামু আলাইকুম ভাই!</b>\n\n"
                "আপনার কি কোনো নির্দিষ্ট কোর্স, সফটওয়্যার বা প্রিমিয়াম অ্যাকাউন্ট লাগবে?\n\n"
                "• বট ব্যবহার করতে নিচের কিবোর্ড বাটনগুলো ব্যবহার করুন\n"
                "• অথবা আপনার যে কোর্স বা সফটওয়্যারটি প্রয়োজন তার <b>নাম বা ওয়েবসাইট লিংক</b> সরাসরি এখানে লিখে পাঠিয়ে দিন!"
            )
            await message.answer(guide_text, reply_markup=get_casual_guide_kb(lang), parse_mode="HTML")
            return

    # CHECK 2: Short Meaningless Junk / Typo (Intent C)
    if len(text) < 2 or t_lower in JUNK_WORDS:
        return

    # CHECK 3: Check URL, Keywords or Course Name (Intent A)
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
        
        reg_bdt = int(prod["price_bdt"])
        reg_usd = prod["price_usd"]
        
        em_dia = em_tag("diamond", "💎")
        em_crs = em_tag("courses", "🎓")
        em_box = em_tag("box", "📦")
        
        detail_text = (
            f"🎯 <b>আপনার কাঙ্ক্ষিত কোর্সটি খুঁজে পাওয়া গেছে!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{em_crs} <b>{html.escape(prod['title'])}</b>\n\n"
            f"📝 <b>বিবরণ:</b>\n{render_safe_html_text(prod.get('description', '')[:300])}...\n\n"
            f"💰 <b>মূল্য:</b> <b>৳{reg_bdt} BDT</b> অথবা <b>${reg_usd} USD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👉 <i>ইনস্ট্যান্ট এক্সেস নিতে বা রেফারেল দিয়ে ফ্রি পেতে নিচের বাটনে চাপুন:</i>"
        )
        if prod.get("photo_file_id"):
            try:
                await message.answer_photo(
                    photo=prod["photo_file_id"],
                    caption=detail_text,
                    reply_markup=get_product_detail_kb(prod, in_stock, lang),
                    parse_mode="HTML"
                )
                return
            except Exception:
                pass

        await message.answer(detail_text, reply_markup=get_product_detail_kb(prod, in_stock, lang), parse_mode="HTML")
        return

    # 2. Multiple matches found -> Deliver interactive selection list!
    elif len(matches) > 1:
        list_text = (
            f"🔍 <b>সার্চ রেজাল্ট: {len(matches)} টি কোর্স পাওয়া গেছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"আপনি যা খুঁজছেন: <code>{html.escape(text)}</code>\n\n"
            "👇 যে কোর্সটির বিবরণ ও মূল্য দেখতে চান নিচের অপশন থেকে বেছে নিন:"
        )
        await message.answer(list_text, reply_markup=get_course_search_results_kb(matches, text, lang), parse_mode="HTML")
        return

    # 3. No match found -> Deliver professional Course Request lead capture!
    else:
        # If it was a URL, or contained search keywords, or was an explicit search phrase
        if is_url or has_keyword or len(text.split()) >= 2 or len(text) >= 4:
            not_found_text = (
                "🔍 <b>সার্চ রেজাল্ট: ক্যাটালগে পাওয়া যায়নি</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"আপনি যা খুঁজছেন:\n<code>{html.escape(text)}</code>\n\n"
                "⚠️ দুঃখিত, এই কোর্সটি বা লিংকটি বর্তমানে আমাদের ক্যাটালগে সরাসরি নেই।\n\n"
                "💡 <b>তবে কোনো চিন্তা নেই!</b> আমাদের কাছে আনলিমিটেড প্রিমিয়াম রিসোর্স ও প্রোভাইডার এক্সেস রয়েছে। "
                "আপনি চাইলে এখনই এটি রিকোয়েস্ট করতে পারেন—আমাদের অ্যাডমিন টিম দ্রুত আপনার জন্য এটি ম্যানেজ করে দেবে!"
            )
            await message.answer(not_found_text, reply_markup=get_course_not_found_kb(text, lang), parse_mode="HTML")
            return
