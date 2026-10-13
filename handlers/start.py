# Start and Profile Handlers with Modern Single-Screen Interactive Dashboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import html
from database.db import db
from keyboards.user_kb import (
    get_main_reply_kb,
    get_pending_deposit_kb,
    get_language_kb,
    get_main_dashboard_inline_kb,
    get_user_profile_kb,
    make_custom_button
)
from config import ADMIN_USERNAME, OFFICIAL_CHANNEL, ADMIN_IDS
from utils.i18n import t, LANGUAGES
from utils.emojis import em_tag
from utils.ui_nav import render_screen

router = Router()

def escape_md(text: str) -> str:
    """Escapes Telegram Markdown special characters from user inputs."""
    if not text:
        return ""
    for ch in ["\\", "_", "*", "`", "[", "]"]:
        text = text.replace(ch, f"\\{ch}")
    return text

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS or ADMIN_IDS == [0] or user_id in ADMIN_IDS:
        return True
    return db.is_sub_admin(user_id)

def format_main_dashboard_text(user_id: int, user_obj=None, lang: str = "bn", bonus_html: str = "", course_invite_html: str = "") -> str:
    """Creates a high-end, compact master dashboard screen matching the agent_47vip store aesthetics."""
    db_user = db.get_user(user_id)
    if not db_user and user_obj:
        db_user = db.register_or_update_user(user_id, getattr(user_obj, "username", None), getattr(user_obj, "first_name", None))
    elif not db_user:
        db_user = {"balance_bdt": 0.0, "balance_usd": 0.0, "is_reseller": 0, "referral_points": 0}
        
    first_name = user_obj.first_name if user_obj else db_user.get("first_name", "Customer")
    safe_name = html.escape(first_name or "Customer")
    
    em_dia = em_tag("diamond", "💎")
    em_wal = em_tag("wallet", "💰")
    em_usr = em_tag("profile", "👤")
    em_shd = em_tag("verify", "🛡️")
    em_crs = em_tag("courses", "🎓")
    em_dgt = em_tag("digital", "⚡")
    em_gft = em_tag("free_claim", "🎁")
    em_res = em_tag("reseller", "🤝")
    is_res = db_user.get("is_reseller", 0) >= 1
    points = db_user.get("referral_points", 0) or 0
    box_border = "━━━━━━━━━━━━━━━━━━━━"
    
    announcement = db.get_setting("welcome_announcement", "").strip()
    ann_html = f"📢 <b>বিশেষ নোটিশ:</b>\n<i>{html.escape(announcement)}</i>\n\n" if announcement else ""
    
    if lang == "en":
        tier_label = "👑 VIP Reseller" if is_res else "⭐ Verified User"
        text = (
            f"{ann_html}"
            f"{box_border}\n"
            f"💎 <b>ALL IN ONE VIP STORE</b> 💎\n"
            f"{box_border}\n"
            f"{em_usr} <b>Customer ID:</b> <code>#{user_id}</code>\n"
            f"{em_shd} <b>Account Tier:</b> <code>{tier_label}</code>\n"
            f"{em_wal} <b>Wallet Balance:</b> <b>৳{db_user['balance_bdt']:.2f}</b> | <b>${db_user['balance_usd']:.2f}</b>\n"
            f"💎 <b>Reward Points:</b> <b>{points} Pts</b>\n"
            f"🟢 <b>Status:</b> <code>24/7 Instant Auto-Delivery</code>\n"
            f"{box_border}{bonus_html}{course_invite_html}\n\n"
            f"👉 <i>Tap any button below to browse or manage:</i>"
        )
    elif lang == "hi":
        tier_label = "👑 वीआईपी रीसेलर" if is_res else "⭐ वेरीफाइड यूजर"
        text = (
            f"{ann_html}"
            f"{box_border}\n"
            f"💎 <b>ALL IN ONE VIP STORE</b> 💎\n"
            f"{box_border}\n"
            f"{em_usr} <b>कस्टमर आईडी:</b> <code>#{user_id}</code>\n"
            f"{em_shd} <b>मेंबरशिप:</b> <code>{tier_label}</code>\n"
            f"{em_wal} <b>वॉलेट बैलेंस:</b> <b>৳{db_user['balance_bdt']:.2f}</b> | <b>${db_user['balance_usd']:.2f}</b>\n"
            f"💎 <b>रिवॉर्ड पॉइंट्स:</b> <b>{points} Pts</b>\n"
            f"🟢 <b>सर्विस स्टेटस:</b> <code>24/7 इंस्टेंट ऑटो-डिलीवरी</code>\n"
            f"{box_border}{bonus_html}{course_invite_html}\n\n"
            f"👉 <i>ब्राउज करने के लिए नीचे दिए गए बटन पर टैप करें:</i>"
        )
    else: # Bengali (default)
        tier_label = "👑 ভিআইপি রিসেলার" if is_res else "⭐ ভেরিফাইড ইউজার"
        text = (
            f"{ann_html}"
            f"{box_border}\n"
            f"💎 <b>ALL IN ONE VIP STORE</b> 💎\n"
            f"{box_border}\n"
            f"{em_usr} <b>কাস্টমার আইডি:</b> <code>#{user_id}</code>\n"
            f"{em_shd} <b>মেম্বারশিপ:</b> <code>{tier_label}</code>\n"
            f"{em_wal} <b>ওয়ালেট ব্যালেন্স:</b> <b>৳{db_user['balance_bdt']:.2f}</b> | <b>${db_user['balance_usd']:.2f}</b>\n"
            f"💎 <b>রেফারেল পয়েন্ট:</b> <b>{points} Pts</b>\n"
            f"🟢 <b>সার্ভিস স্ট্যাটাস:</b> <code>ইনস্ট্যান্ট ডেলিভারি ২৪/৭</code>\n"
            f"{box_border}{bonus_html}{course_invite_html}\n\n"
            f"👉 <i>নিচের মেনু থেকে আপনার অপশন বেছে নিন:</i>"
        )
    return text

def format_user_orders_data(user_id: int, lang: str = "bn"):
    """Renders user past orders with one-click back navigation."""
    orders = db.get_user_orders(user_id)
    em_box = em_tag("box", "📦")
    em_wal = em_tag("wallet", "💰")
    
    if not orders:
        text = t("orders_vault_empty", lang)
    else:
        text = t("orders_vault_header", lang)
        paid_label = t("orders_paid_label", lang)
        date_label = t("orders_date_label", lang)
        access_label = t("orders_access_label", lang)
        for idx, order in enumerate(orders[:10], start=1):
            clean_title = html.escape(str(order.get("product_title", "Product")))
            clean_delivery = html.escape(str(order.get("delivery_content", "Delivered")))
            text += (
                f"<b>#{idx} | {clean_title}</b>\n"
                f"{em_wal} {paid_label}: <code>৳{order['amount_paid']} {order['currency']}</code>\n"
                f"📅 {date_label}: <code>{order['created_at'][:16]}</code>\n"
                f"🔑 <b>{access_label}:</b>\n"
                f"<pre>{clean_delivery}</pre>\n"
                f"────────────────────\n"
            )
        if len(orders) > 10:
            more_txt = f"\n<i>({len(orders)-10} more past orders archived in database)</i>\n" if lang == "en" else f"\n<i>(ডাটাবেজে আরও {len(orders)-10} টি অতীত অর্ডার সংরক্ষিত রয়েছে)</i>\n"
            text += more_txt

    kb_buttons = [
        [
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=kb_buttons)

@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    user = message.from_user
    db_user = db.register_or_update_user(user.id, user.username, user.first_name)
    lang = db.get_user_language(user.id)
    admin_flag = is_admin(user.id)
    
    args = message.text.split(maxsplit=1) if message.text else []
    deep_param = args[1].strip() if len(args) > 1 else None

    # Handle deep-link reseller verification (e.g., ?start=verify_RS-1002)
    if deep_param and (deep_param.startswith("verify_") or deep_param.startswith("v_")):
        from handlers.verify import generate_verification_certificate
        from keyboards.user_kb import get_reseller_verification_kb
        query = deep_param.replace("verify_", "").replace("v_", "")
        target = db.verify_reseller(query)
        cert = generate_verification_certificate(target, query, lang=lang)
        uname = target.get("username") if target else None

        safe_fname = html.escape(user.first_name or "Partner")
        header_text = (
            f"👋 <b>Welcome, {safe_fname}!</b>\n\n🛡️ <b>Reseller verification result below:</b>"
        ) if lang == "en" else (
            f"👋 <b>স্বাগতম, {safe_fname}!</b>\n\n🛡️ <b>রিসেলার সততা যাচাইকরণ রেজাল্ট নিচে দেওয়া হলো:</b>"
        )
        await message.answer(
            header_text,
            reply_markup=get_main_dashboard_inline_kb(lang, is_admin=admin_flag),
            parse_mode="HTML"
        )
        try:
            await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang), parse_mode="HTML")
        except Exception:
            await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang))
        return

    # Handle deep-link referral (e.g., ?start=ref_12345, ?start=ref_12345_c12, or ?start=12345)
    welcome_bonus_text = ""
    target_course_info = None
    if deep_param:
        target_ref_id = None
        target_course_id = None
        cleaned = deep_param.replace("ref_", "")
        if "_c" in cleaned:
            parts = cleaned.split("_c")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                target_ref_id = int(parts[0])
                target_course_id = int(parts[1])
        elif cleaned.isdigit():
            target_ref_id = int(cleaned)

        if target_ref_id and target_ref_id != user.id:
            reward_res = db.process_referral_join(user.id, target_ref_id, course_id=target_course_id)
            if reward_res:
                from utils.notifier import notify_referral_rewards
                user_info = {
                    "id": user.id,
                    "first_name": user.first_name,
                    "username": user.username
                }
                await notify_referral_rewards(message.bot, user_info, reward_res)
                if reward_res.get("welcome_bonus", 0) > 0:
                    welcome_bonus_text = f"\n🎁 <b>রেফারেল স্পেশাল গিফট:</b> আপনার ওয়ালেটে <code>+৳{reward_res['welcome_bonus']:.2f} BDT</code> ফ্রি স্টার্টার ব্যালেন্স যুক্ত হয়েছে!\n"
                db_user = db.get_user(user.id)
            if target_course_id:
                target_course_info = db.get_product(target_course_id)

    course_invite_html = ""
    if target_course_info:
        course_invite_html = (
            f"\n🎯 <b>বিশেষ আমন্ত্রণ:</b> আপনার বন্ধু আপনাকে <b>{html.escape(target_course_info['title'])}</b> "
            f"কোর্সটি দেখার জন্য ইনভাইট করেছেন!\n"
        )


    welcome_text = format_main_dashboard_text(
        user_id=user.id,
        user_obj=user,
        lang=lang,
        bonus_html=welcome_bonus_text,
        course_invite_html=course_invite_html
    )
    kb = get_main_dashboard_inline_kb(lang, is_admin=admin_flag)
    try:
        await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await message.answer(welcome_text, reply_markup=kb)


@router.message(Command("menu"))
@router.message(F.text.in_([
    "Menu", "মেনু", "Main Menu", "মূল মেনু", "হোম", "Home",
    "🏠 মূল মেনু", "🏠 Main Menu", "🏠 मुख्य मेनू",
    "🏠 মূল মেনু (Start / Menu)", "🏠 Main Menu (Start)", "🏠 मुख्य मेनू (Start)",
    "মূল মেনু (Start / Menu)", "Main Menu (Start)", "Start", "স্টার্ট", "🏠 Start"
]))
async def handle_menu_cmd(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    user = message.from_user
    lang = db.get_user_language(user.id)
    text = format_main_dashboard_text(user.id, user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(user.id))
    try:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=kb)

@router.message(Command("language"))
@router.message(F.text.in_([
    "Language / ভাষা / भाषा", "🌐 Language / ভাষা / भाषा", "Language", "ভাষা", "भाषा"
]))
async def handle_language_cmd(message: Message):
    lang = db.get_user_language(message.from_user.id)
    prompt = t("lang_select_prompt", lang)
    await message.answer(prompt, reply_markup=get_language_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "nav_lang")
async def handle_language_nav(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    prompt = t("lang_select_prompt", lang)
    await render_screen(call, prompt, reply_markup=get_language_kb(lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language_callback(call: CallbackQuery):
    new_lang = call.data.split(":")[1]
    user_id = call.from_user.id
    db.set_user_language(user_id, new_lang)
    lang_name = LANGUAGES.get(new_lang, 'English')
    await call.answer(f"🌐 Language updated to {lang_name}!", show_alert=False)
    
    # Seamlessly re-render the master dashboard in the new language in-place!
    text = format_main_dashboard_text(user_id, call.from_user, new_lang)
    kb = get_main_dashboard_inline_kb(new_lang, is_admin=is_admin(user_id))
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

    # Synchronize persistent bottom reply keyboard to match selected language immediately
    reply_kb = get_main_reply_kb(new_lang, is_admin=is_admin(user_id))
    confirm_msg = f"✅ Menu language updated to <b>{lang_name}</b>" if new_lang == "en" else f"✅ মেনু ভাষা পরিবর্তন করা হয়েছে: <b>{lang_name}</b>"
    try:
        await call.message.answer(confirm_msg, reply_markup=reply_kb, parse_mode="HTML")
    except Exception:
        pass

def format_user_profile_data(user_id: int, user_obj=None):
    db_user = db.get_user(user_id)
    if not db_user and user_obj:
        db_user = db.register_or_update_user(user_id, user_obj.username, user_obj.first_name)
    orders = db.get_user_orders(user_id)
    ref_summary = db.get_user_referral_summary(user_id)
    lang = db.get_user_language(user_id)
    
    is_reseller = db_user.get("is_reseller", 0) >= 1
    tier_label = "👑 VIP Reseller Partner" if is_reseller else "⭐ Verified Customer"
    
    first_name = user_obj.first_name if user_obj else db_user.get("first_name", "Customer")
    username = user_obj.username if user_obj else db_user.get("username")
    safe_name = html.escape(first_name or "Customer")
    uname = f"@{html.escape(username)}" if username else "N/A"

    em_dia = em_tag("diamond", "💎")
    em_wal = em_tag("wallet", "💰")
    em_usr = em_tag("profile", "👤")
    em_shd = em_tag("verify", "🛡️")
    em_ord = em_tag("orders", "📦")
    em_crs = em_tag("courses", "🎓")

    box_border = "━━━━━━━━━━━━━━━━━━━━"
    
    if lang == "en":
        tier_label = "👑 VIP Reseller" if is_reseller else "⭐ Verified User"
        profile_text = (
            f"{box_border}\n"
            f"👤 <b>VIP CUSTOMER PROFILE</b>\n"
            f"{box_border}\n"
            f"<i>Welcome {safe_name}! Account profile & vault:</i>\n\n"
            f"{em_usr} <b>Customer ID:</b> <code>#{user_id}</code>\n"
            f"{em_shd} <b>Membership Tier:</b> <code>{tier_label}</code>\n"
            f"🏷️ <b>Telegram User:</b> {uname}\n"
            f"{box_border}\n"
            f"{em_wal} <b>Wallet Balance:</b>\n"
            f"• <b>BDT:</b> <b>৳{db_user['balance_bdt']:.2f}</b>\n"
            f"• <b>USD:</b> <b>${db_user['balance_usd']:.2f}</b>\n\n"
            f"💎 <b>Referral Earnings & Points:</b>\n"
            f"• 🌟 Points: <b>{ref_summary['available_points']} Pts</b> <i>(~৳{ref_summary['bdt_value']:.0f})</i>\n"
            f"• 👥 Referrals: <b>{ref_summary['total_referrals']}</b> (T1: {ref_summary['t1_count']} | T2: {ref_summary['t2_count']})\n"
            f"• {em_crs} Course Referrals: <b>{ref_summary['course_referrals']}</b>\n"
            f"• 💱 Cash Converted: <b>৳{ref_summary['converted_bdt_total']:.2f}</b>\n\n"
            f"{em_ord} <b>Shopping History:</b>\n"
            f"• Spent: <b>৳{db_user['total_spent_bdt']:.2f}</b> (${db_user['total_spent_usd']:.2f})\n"
            f"• Orders: <b>{len(orders)} Orders</b>\n"
            f"{box_border}\n\n"
            f"💡 <i>Use buttons below to convert points or manage:</i>"
        )
    else:
        tier_label = "👑 ভিআইপি রিসেলার" if is_reseller else "⭐ ভেরিফাইড ইউজার"
        profile_text = (
            f"{box_border}\n"
            f"👤 <b>কাস্টমার প্রোফাইল ও ভল্ট</b>\n"
            f"{box_border}\n"
            f"<i>স্বাগতম {safe_name}! আপনার প্রোফাইল বিবরণ:</i>\n\n"
            f"{em_usr} <b>কাস্টমার আইডি:</b> <code>#{user_id}</code>\n"
            f"{em_shd} <b>মেম্বারশিপ টায়ার:</b> <code>{tier_label}</code>\n"
            f"🏷️ <b>টেলিগ্রাম ইউজার:</b> {uname}\n"
            f"{box_border}\n"
            f"{em_wal} <b>ওয়ালেট ব্যালেন্স:</b>\n"
            f"• <b>টাকা:</b> <b>৳{db_user['balance_bdt']:.2f}</b>\n"
            f"• <b>ডলার:</b> <b>${db_user['balance_usd']:.2f}</b>\n\n"
            f"💎 <b>রেফারেল আর্নিং ও পয়েন্ট ভল্ট:</b>\n"
            f"• 🌟 পয়েন্ট: <b>{ref_summary['available_points']} Pts</b> <i>(~৳{ref_summary['bdt_value']:.0f})</i>\n"
            f"• 👥 রেফারেল: <b>{ref_summary['total_referrals']} জন</b> (T1: {ref_summary['t1_count']} | T2: {ref_summary['t2_count']})\n"
            f"• {em_crs} কোর্স রেফারেল: <b>{ref_summary['course_referrals']} টি</b>\n"
            f"• 💱 ক্যাশ কনভার্ট: <b>৳{ref_summary['converted_bdt_total']:.2f}</b>\n\n"
            f"{em_ord} <b>শপিং হিস্ট্রি ও সামারি:</b>\n"
            f"• মোট কেনাকাটা: <b>৳{db_user['total_spent_bdt']:.2f}</b> (${db_user['total_spent_usd']:.2f})\n"
            f"• সম্পন্ন অর্ডার: <b>{len(orders)} টি</b>\n"
            f"{box_border}\n\n"
            f"💡 <i>পয়েন্ট রূপান্তর করতে বা সরাসরি কোর্স কিনতে নিচের বাটন চাপুন:</i>"
        )
    kb = get_user_profile_kb(
        user_id=user_id,
        available_points=ref_summary['available_points'],
        balance_bdt=db_user['balance_bdt'],
        lang=lang
    )
    return profile_text, kb

@router.message(F.text.in_([
    "My Profile (প্রোফাইল)", "👤 My Profile (প্রোফাইল)", "My Profile", "👤 My Profile", 
    "मेरी प्रोफाइल (Profile)", "👤 मेरी प्रोफाइल (Profile)", "Profile", "প্রোফাইল"
]))
async def handle_profile(message: Message):
    text, kb = format_user_profile_data(message.from_user.id, message.from_user)
    try:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=kb)

@router.callback_query(F.data.in_(["profile_refresh", "nav_profile"]))
async def handle_profile_refresh_callback(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    lang = db.get_user_language(call.from_user.id)
    alert_txt = "🔄 Profile data refreshed!" if lang == "en" else "🔄 প্রোফাইল ডাটা আপডেট করা হয়েছে!"
    await call.answer(alert_txt)
    text, kb = format_user_profile_data(call.from_user.id, call.from_user)
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.message(Command("orders"))
@router.message(F.text.in_([
    "My Purchases (অর্ডার)", "📦 My Purchases (অর্ডার)", "My Purchases", "📦 My Purchases",
    "मेरी खरीदारी (Orders)", "📦 मेरी खरीदारी (Orders)", "Orders", "অর্ডার"
]))
async def handle_my_purchases(message: Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    text, kb = format_user_orders_data(user_id, lang)
    try:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "nav_orders")
async def handle_orders_nav(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    text, kb = format_user_orders_data(user_id, lang)
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.message(F.text.in_([
    "Support & Help (হেল্প)", "💬 Support & Help (হেল্প)", "Support & Help", "💬 Support & Help",
    "সাপোর্ট এবং सहायता (Help)", "💬 সাপোর্ট এবং सहायता (Help)", "सपोर्ट और सहायता (Help)", "Support", "হেল্প"
]))
async def handle_support(message: Message):
    lang = db.get_user_language(message.from_user.id)
    em_sup = em_tag("support", "💬")
    em_adm = em_tag("admin", "👑")
    em_chn = em_tag("channel", "📢")
    
    support_text = t(
        "support_card_text",
        lang,
        em_sup=em_sup,
        em_adm=em_adm,
        em_chn=em_chn,
        admin=ADMIN_USERNAME,
        channel=OFFICIAL_CHANNEL
    )
    await message.answer(
        support_text,
        reply_markup=get_pending_deposit_kb(ADMIN_USERNAME, lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(call: CallbackQuery, state: FSMContext = None):
    """Central back button handler that returns user seamlessly in-place to the Master Dashboard."""
    if state:
        await state.clear()
    await call.answer()
    user = call.from_user
    lang = db.get_user_language(user.id)
    text = format_main_dashboard_text(user.id, user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(user.id))
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")
