# Free Claim & Multi-Category Giveaway Hub Handler - Ultra Clean HTML Formatting
import logging
import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db import db
from keyboards.user_kb import (
    get_free_claim_categories_kb,
    get_free_claim_hub_kb,
    get_claim_action_kb
)
from utils.invite_helper import generate_single_use_invite_link
from utils.i18n import t
from utils.ui_nav import render_screen

logger = logging.getLogger(__name__)
router = Router()

CATEGORY_META = {
    "accounts": {
        "name_bn": "প্রিমিয়াম অ্যাকাউন্টস",
        "name_en": "Premium Accounts",
        "icon": "🔐",
        "desc_bn": "Netflix, Canva, Prime, VPN ইত্যাদির প্রিমিয়াম আইডি ও পাসওয়ার্ড গিভঅ্যাওয়ে।",
        "default_guide": (
            "1️⃣ অফিসিয়াল ওয়েবসাইট বা মোবাইল অ্যাপে প্রবেশ করুন।\n"
            "2️⃣ প্রাপ্ত ইমেইল এবং পাসওয়ার্ড দিয়ে লগইন সম্পন্ন করুন।\n"
            "3️⃣ আপনার প্রোফাইল সিলেক্ট করে ব্যবহার শুরু করুন।\n"
            "⚠️ পাসওয়ার্ড, ইমেইল বা প্রোফাইল নেম পরিবর্তনের চেষ্টা করবেন না।"
        )
    },
    "cookies": {
        "name_bn": "ব্রাউজার কুকিজ",
        "name_en": "Browser Cookies",
        "icon": "🍪",
        "desc_bn": "OTT এবং AI টুলস এর ব্রাউজার সেশন কুকিজ (Cookie-Editor এক্সটেনশন দিয়ে ব্যবহারের জন্য)।",
        "default_guide": (
            "1️⃣ পিসিতে Chrome বা Brave ব্রাউজারে 'Cookie-Editor' এক্সটেনশন ইনস্টল করুন।\n"
            "2️⃣ সংশ্লিষ্ট সাইটের হোমপেজে যান (যেমন: netflix.com বা chatgpt.com)।\n"
            "3️⃣ Cookie-Editor এক্সটেনশনে ক্লিক করে 'Import' বাটনে চাপ দিন।\n"
            "4️⃣ প্রাপ্ত কুকিজ কোড পেস্ট করে 'Import' করুন এবং পেজটি একবার Reload দিন!\n"
            "⚠️ ব্যবহারের পর কখনই 'Log Out' বাটনে চাপ দেবেন না, সরাসরি ব্রাউজার ট্যাব কেটে দেবেন।"
        )
    },
    "subscription": {
        "name_bn": "সাবস্ক্রিপশন ও গিফট কি",
        "name_en": "Subscriptions & Keys",
        "icon": "👑",
        "desc_bn": "সফটওয়্যার লাইসেন্স কি, রিডিম কোড, ডিসকর্ড নাইট্রো এবং এক্সক্লুসিভ ভাউচার কোড।",
        "default_guide": (
            "1️⃣ সংশ্লিষ্ট সার্ভিস বা সফটওয়্যারের অফিসিয়াল Redeem / Promo কোড পেজে যান।\n"
            "2️⃣ আপনার প্রাপ্ত ভাউচার বা লাইসেন্স কি-টি কপি করে পেস্ট করুন।\n"
            "3️⃣ 'Activate' বা 'Apply' এ ক্লিক করলেই আপনার সাবস্ক্রিপশন চালু হয়ে যাবে।"
        )
    },
    "channel": {
        "name_bn": "ভিআইপি চ্যানেল অ্যাক্সেস",
        "name_en": "VIP Channel Access",
        "icon": "📢",
        "desc_bn": "আমাদের এক্সক্লুসিভ প্রাইভেট ও ভিআইপি চ্যানেলে ফ্রি প্রবেশের ওয়ান-টাইম ইনভাইট লিংক।",
        "default_guide": (
            "1️⃣ নিচের ক্লেইম বাটনে চাপ দিলে আপনার জন্য ১-বার ব্যবহারযোগ্য লিংক তৈরি হবে।\n"
            "2️⃣ 'জয়েন করুন' বাটনে ক্লিক করে সরাসরি চ্যানেলে প্রবেশ করুন।\n"
            "⚠️ এই লিংক শুধুমাত্র আপনার জন্য ১-বার ভ্যালিড। অন্য কাউকে দিলে আপনি আর ঢুকতে পারবেন না।"
        )
    },
    "tools_drive": {
        "name_bn": "টুলস ও ক্লাউড ড্রাইভ ভল্ট",
        "name_en": "Tools & Cloud Drive",
        "icon": "💾",
        "desc_bn": "প্রিমিয়াম কোর্স, মেগা ক্লাউড ফোল্ডার, ডিজিটাল অ্যাসেট ও প্রয়োজনীয় টুলস।",
        "default_guide": (
            "1️⃣ নিচের দেওয়া ড্রাইভ বা ক্লাউড লিংকে ক্লিক করুন।\n"
            "2️⃣ ফাইলগুলো আপনার নিজস্ব ড্রাইভে 'Make a copy' করুন অথবা সরাসরি ডাউনলোড করে নিন।"
        )
    }
}

@router.message(Command("free"))
@router.message(Command("claim"))
@router.message(Command("free_claim"))
@router.message(F.text.in_([
    "Free Claim (গিভঅ্যাওয়ে)",
    "🎁 Free Claim (গিভঅ্যাওয়ে)",
    "Free Claim (Giveaways)",
    "🎁 Free Claim (Giveaways)",
    "ফ্রি ক্লেইম (Giveaway)",
    "🎁 ফ্রি ক্লেইম (Giveaway)",
    "Free Claim",
    "🎁 Free Claim",
    "গিভঅ্যাওয়ে",
    "🎁 গিভঅ্যাওয়ে",
    "/free",
    "/claim"
]))
async def handle_free_claim_text_cmd(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    lang = user.get("language", "bn") if user else "bn"
    
    counts = db.get_active_drop_counts_by_category()
    
    text = (
        "🎁 <b>ফ্রি ক্লেইম ও গিভঅ্যাওয়ে হাব (Free Claim Hub)</b> 🎁\n\n"
        "এখানে অ্যাডমিন ও সাপোর্ট টিম নিয়মিত বিভিন্ন প্রিমিয়াম সার্ভিস সম্পূর্ণ ফ্রিতে গিভঅ্যাওয়ে দিয়ে থাকে!\n"
        "⚡ নীতি: <b>'যে আগে ক্লেইম করবে সে আগে পাবে' (First-Come, First-Served)</b>\n\n"
        "📂 <b>চলমান ক্যাটাগরি সমূহ:</b>\n"
        "• 🔐 <b>প্রিমিয়াম একাউন্টস:</b> Netflix, Canva, Prime Video সরাসরি আইডি-পাসওয়ার্ড।\n"
        "• 🍪 <b>ব্রাউজার কুকিজ:</b> ওটিটি ও এআই প্ল্যাটফর্মের ইনস্ট্যান্ট লগইন কুকিজ।\n"
        "• 👑 <b>সাবস্ক্রিপশন ও কি:</b> বিভিন্ন অ্যাপ ও সফটওয়্যারের লাইসেন্স বা রিডিম কোড।\n"
        "• 📢 <b>ভিআইপি চ্যানেল:</b> অটো ১-জন ব্যবহারযোগ্য প্রাইভেট চ্যানেল ইনভাইট লিংক।\n"
        "• 💾 <b>টুলস ও ড্রাইভ ভল্ট:</b> প্রিমিয়াম মেগা ও ক্লাউড ড্রাইভ রিসোর্স লিংক।\n\n"
        f"🔥 <b>বর্তমানে সক্রিয় ড্রপ:</b> <code>{counts.get('total', 0)} টি</code>\n\n"
        "👇 আপনি কোন ক্যাটাগরির গিভঅ্যাওয়ে ক্লেইম করতে চান নিচে সিলেক্ট করুন:"
    ) if lang == "bn" else (
        "🎁 <b>Free Claim & Giveaway Hub</b> 🎁\n\n"
        "Claim free premium accounts, browser cookies, licenses, and VIP access!\n"
        "⚡ Rules: <b>First-come, first-served!</b> Limited slots available.\n\n"
        f"🔥 <b>Total Active Drops:</b> <code>{counts.get('total', 0)}</code>\n\n"
        "👇 Choose your desired giveaway category below:"
    )
    
    await message.answer(text, reply_markup=get_free_claim_categories_kb(counts, lang=lang), parse_mode="HTML")

handle_free_claim_cmd = handle_free_claim_text_cmd

@router.callback_query(F.data == "nav_free_claim")
async def handle_free_claim_nav(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    user_id = call.from_user.id
    user = db.get_user(user_id)
    lang = user.get("language", "bn") if user else "bn"
    
    counts = db.get_active_drop_counts_by_category()
    
    text = (
        "🎁 <b>ফ্রি ক্লেইম ও গিভঅ্যাওয়ে হাব (Free Claim Hub)</b> 🎁\n\n"
        "এখানে অ্যাডমিন ও সাপোর্ট টিম নিয়মিত বিভিন্ন প্রিমিয়াম সার্ভিস সম্পূর্ণ ফ্রিতে গিভঅ্যাওয়ে দিয়ে থাকে!\n"
        "⚡ নীতি: <b>'যে আগে ক্লেইম করবে সে আগে পাবে' (First-Come, First-Served)</b>\n\n"
        "📂 <b>চলমান ক্যাটাগরি সমূহ:</b>\n"
        "• 🔐 <b>প্রিমিয়াম একাউন্টস:</b> Netflix, Canva, Prime Video সরাসরি আইডি-পাসওয়ার্ড।\n"
        "• 🍪 <b>ব্রাউজার কুকিজ:</b> ওটিটি ও এআই প্ল্যাটফর্মের ইনস্ট্যান্ট লগইন কুকিজ।\n"
        "• 👑 <b>সাবস্ক্রিপশন ও কি:</b> বিভিন্ন অ্যাপ ও সফটওয়্যারের লাইসেন্স বা রিডিম কোড।\n"
        "• 📢 <b>ভিআইপি চ্যানেল:</b> অটো ১-জন ব্যবহারযোগ্য প্রাইভেট চ্যানেল ইনভাইট লিংক।\n"
        "• 💾 <b>টুলস ও ড্রাইভ ভল্ট:</b> প্রিমিয়াম মেগা ও ক্লাউড ড্রাইভ রিসোর্স লিংক।\n\n"
        f"🔥 <b>বর্তমানে সক্রিয় ড্রপ:</b> <code>{counts.get('total', 0)} টি</code>\n\n"
        "👇 আপনি কোন ক্যাটাগরির গিভঅ্যাওয়ে ক্লেইম করতে চান নিচে সিলেক্ট করুন:"
    ) if lang == "bn" else (
        "🎁 <b>Free Claim & Giveaway Hub</b> 🎁\n\n"
        "Claim free premium accounts, browser cookies, licenses, and VIP access!\n"
        "⚡ Rules: <b>First-come, first-served!</b> Limited slots available.\n\n"
        f"🔥 <b>Total Active Drops:</b> <code>{counts.get('total', 0)}</code>\n\n"
        "👇 Choose your desired giveaway category below:"
    )
    
    await render_screen(call, text, reply_markup=get_free_claim_categories_kb(counts, lang=lang), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("claim_cat:"))
async def handle_claim_category_view(call: CallbackQuery):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    lang = user.get("language", "bn") if user else "bn"
    
    category = call.data.split(":")[1]
    cat_filter = None if category == "all" else category
    drops = db.get_active_free_drops(category=cat_filter)
    
    meta = CATEGORY_META.get(category, {
        "name_bn": "সকল সক্রিয় গিভঅ্যাওয়ে",
        "name_en": "All Active Giveaways",
        "icon": "🔥",
        "desc_bn": "চলমান সকল ক্যাটাগরির গিভঅ্যাওয়ে তালিকা।"
    })
    
    cat_name = meta["name_bn"] if lang == "bn" else meta["name_en"]
    cat_icon = meta["icon"]
    
    if not drops:
        text = (
            f"{cat_icon} <b>{cat_name} সেকশন</b> {cat_icon}\n\n"
            f"ℹ️ {html.escape(meta.get('desc_bn', ''))}\n\n"
            "⚠️ <b>বর্তমানে এই ক্যাটাগরিতে কোনো সক্রিয় ড্রপ নেই!</b>\n"
            "অ্যাডমিন ও টিম মেম্বাররা যে কোনো সময় হঠাৎ এই সেকশনে নতুন গিভঅ্যাওয়ে ছাড়বে। চোখ রাখুন!\n\n"
            "⚡ নতুন ড্রপ আসার সাথে সাথে সবার আগে ক্লেইম করতে প্রস্তুত থাকুন।"
        ) if lang == "bn" else (
            f"{cat_icon} <b>{cat_name}</b> {cat_icon}\n\n"
            "⚠️ No active giveaways in this category right now.\n"
            "Our admin team drops new items frequently. Stay tuned!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 রিফ্রেশ (Refresh)", callback_data=f"claim_cat:{category}")],
            [
                InlineKeyboardButton(text="🔙 ক্যাটাগরি (Back)", callback_data="nav_free_claim"),
                InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
            ]
        ])
        await render_screen(call, text, reply_markup=kb, parse_mode="HTML")
        await call.answer()
        return

    text = (
        f"{cat_icon} <b>{cat_name} — সক্রিয় ড্রপ তালিকা</b> {cat_icon}\n\n"
        f"ℹ️ {html.escape(meta.get('desc_bn', ''))}\n"
        f"⚡ মোট সক্রিয় ড্রপ: <code>{len(drops)} টি</code>\n\n"
        "👇 যে ড্রপটি ক্লেইম করতে চান সেটির ওপর চাপ দিন:"
    ) if lang == "bn" else (
        f"{cat_icon} <b>{cat_name} — Active Drops</b> {cat_icon}\n\n"
        f"⚡ Active giveaways: <code>{len(drops)}</code>\n"
        "👇 Select a drop below to view details and claim:"
    )
    
    await render_screen(call, text, reply_markup=get_free_claim_hub_kb(drops, category=category, lang=lang), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("view_free_drop:"))
async def handle_view_free_drop(call: CallbackQuery):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    lang = user.get("language", "bn") if user else "bn"
    
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    
    if not drop:
        await call.answer("ড্রপ খুঁজে পাওয়া যায়নি!", show_alert=True)
        return

    cat_key = drop.get("giveaway_category", "accounts")
    meta = CATEGORY_META.get(cat_key, CATEGORY_META["accounts"])
    
    claim = db.get_user_drop_claim(drop_id, user_id)
    already_claimed = claim is not None
    remaining = max(0, drop["max_claims"] - drop["claimed_count"])
    
    status_icon = "🟢 ওপেন" if drop["is_active"] and remaining > 0 else "🔴 শেষ"
    
    type_names = {
        "channel_link": "🔒 Private Channel (1-Time Single-Use Link)",
        "bulk_combo": "📦 Account Combo / Access Key",
        "direct_link": "🔗 Direct Cloud Link"
    }
    drop_type_display = type_names.get(drop["drop_type"], drop["drop_type"])
    
    # Guide preparation
    guide_text = drop.get("instructions")
    if not guide_text or not guide_text.strip():
        guide_text = meta.get("default_guide", "ক্লেইম করার পর নির্দেশনা অনুযায়ী ব্যবহার করুন।")
    guide_esc = html.escape(guide_text)
    
    # Target Website / Portal Link
    site_link = (drop.get("site_link") or "").strip()
    if site_link and not site_link.startswith("http"):
        site_link = "https://" + site_link

    title_esc = html.escape(drop["title"])
    
    text = (
        f"{meta['icon']} <b>{title_esc}</b>\n\n"
        f"📂 <b>ক্যাটাগরি:</b> <code>{meta['name_bn']}</code>\n"
        f"🏷️ <b>ডেলিভারি ধরন:</b> <code>{drop_type_display}</code>\n"
        f"⚡ <b>স্ট্যাটাস:</b> {status_icon}\n"
        f"👥 <b>মোট কোটা:</b> <code>{drop['max_claims']} জন</code>\n"
        f"🔥 <b>অবশিষ্ট স্লট:</b> <code>{remaining} জন</code>\n\n"
    )
    
    if site_link:
        text += f"🌐 <b>অফিসিয়াল ওয়েবসাইট:</b> <a href=\"{site_link}\">{html.escape(site_link)}</a>\n\n"

    if drop.get("description"):
        text += f"📝 <b>বিবরণ ও শর্তাবলী:</b>\n{html.escape(drop['description'])}\n\n"
        
    text += f"📖 <b>কিভাবে ব্যবহার করবেন (How to Use):</b>\n{guide_esc}\n\n"
    
    req_refs = drop.get("required_referrals", 0)
    ref_stats = db.get_referral_stats(user_id)
    user_refs = ref_stats.get("t1_count", 0)
    
    is_locked = False
    ref_link = ""
    if req_refs > 0 and not already_claimed and remaining > 0 and drop["is_active"]:
        if user_refs < req_refs:
            is_locked = True
            bot_info = await call.bot.get_me()
            bot_uname = bot_info.username or "AllInOneProAccess_bot"
            ref_link = f"https://t.me/{bot_uname}?start=ref_{user_id}"

    if already_claimed:
        content_esc = html.escape(claim['delivery_content'])
        text += (
            "━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>আপনি ইতিমধ্যে এই ড্রপটি ক্লেইম করেছেন!</b>\n"
            "📦 <b>আপনার সংগৃহীত আইটেম/লগইন:</b>\n"
            f"<pre>{content_esc}</pre>\n"
            "<i>(আপনার ব্যক্তিগত কপি উপরে সংরক্ষিত আছে। কোডটিতে ট্যাপ করলেই কপি হয়ে যাবে)</i>"
        )
    elif remaining <= 0 or not drop["is_active"]:
        text += "❌ <b>দুঃখিত! এই ড্রপটির সকল স্লট ইতিমধ্যে শেষ হয়ে গেছে।</b>"
    elif is_locked:
        needed_refs = max(0, req_refs - user_refs)
        text += (
            "━━━━━━━━━━━━━━━━━━━\n"
            "🔒 <b>এই গিভঅ্যাওয়েটি আনলক করতে রেফারেল প্রয়োজন!</b> 🔒\n\n"
            f"🎁 এই আইটেমটি ক্লেইম করতে আপনার রেফারেল লিংক দিয়ে ন্যূনতম <b>{req_refs} জন</b> বন্ধুকে বটে জয়েন করাতে হবে।\n\n"
            f"📊 <b>আপনার রেফারেল অগ্রগতি:</b> <code>{user_refs} / {req_refs} জন</code> সম্পন্ন (বাকি আর <b>{needed_refs} জন</b>)\n\n"
            "💡 নিচের <b>'📲 বন্ধুদের সাথে শেয়ার করুন'</b> বাটনে চাপ দিয়ে বন্ধুদের ইনভাইট করুন। "
            "বন্ধুরা বটে স্টার্ট করলেই আপনার ক্লেইম বাটনটি সাথে সাথে আনলক হয়ে যাবে!"
        )
    else:
        unlock_notice = ""
        if req_refs > 0:
            unlock_notice = (
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 <b>অভিনন্দন! আপনার রেফারেল টাস্ক সম্পন্ন হয়েছে ({user_refs}/{req_refs} জন)!</b>\n"
                "🔓 <b>গিভঅ্যাওয়েটি আপনার জন্য আনলক হয়েছে!</b>\n\n"
            )
        text += f"{unlock_notice}🏃‍♂️ নিচের বাটনে চাপ দিয়ে দ্রুত আপনার ফ্রি স্লটটি ক্লেইম করে নিন!"

    kb = get_claim_action_kb(
        drop_id,
        already_claimed=already_claimed,
        remaining=remaining,
        category=cat_key,
        site_link=site_link,
        lang=lang,
        is_locked=is_locked,
        ref_link=ref_link,
        drop_title=drop["title"]
    )
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("execute_free_claim:"))
async def handle_execute_free_claim(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    
    if not drop:
        await call.answer("ড্রপ খুঁজে পাওয়া যায়নি!", show_alert=True)
        return
        
    if not drop["is_active"]:
        await call.answer("এই গিভঅ্যাওয়েটি শেষ হয়ে গেছে!", show_alert=True)
        return

    # Check if user already claimed
    existing_claim = db.get_user_drop_claim(drop_id, user_id)
    if existing_claim:
        await call.answer("আপনি ইতিমধ্যে এটি ক্লেইম করেছেন!", show_alert=True)
        return

    # Check remaining slots
    remaining = max(0, drop["max_claims"] - drop["claimed_count"])
    if remaining <= 0:
        await call.answer("দুঃখিত! সব স্লট ইতিমধ্যে শেষ হয়ে গেছে।", show_alert=True)
        return

    # Referral Gate Validation
    req_refs = drop.get("required_referrals", 0)
    if req_refs > 0:
        ref_stats = db.get_referral_stats(user_id)
        user_refs = ref_stats.get("t1_count", 0)
        if user_refs < req_refs:
            needed = req_refs - user_refs
            await call.answer(
                f"🔒 এই ড্রপটি লক করা! ক্লেইম করতে আপনার এখনো {needed} টি রেফারেল বাকি আছে। বন্ধুদের শেয়ার করে আনলক করুন!",
                show_alert=True
            )
            return

    cat_key = drop.get("giveaway_category", "accounts")
    meta = CATEGORY_META.get(cat_key, CATEGORY_META["accounts"])
    guide_text = drop.get("instructions")
    if not guide_text or not guide_text.strip():
        guide_text = meta.get("default_guide", "নির্দেশনা অনুযায়ী ব্যবহার করুন।")
    guide_esc = html.escape(guide_text)

    site_link = (drop.get("site_link") or "").strip()
    if site_link and not site_link.startswith("http"):
        site_link = "https://" + site_link

    title_esc = html.escape(drop["title"])
    drop_type = drop["drop_type"]
    
    if drop_type == "channel_link":
        channel_target = drop["channel_id"]
        if not channel_target:
            await call.answer("চ্যানেল লিংক কনফিগারেশন মিসিং!", show_alert=True)
            return
            
        await call.answer("আপনার জন্য সিঙ্গেল-ইউজ লিংক তৈরি হচ্ছে...", show_alert=False)
        invite_link = await generate_single_use_invite_link(bot, channel_target, drop["title"])
        
        res = db.claim_free_drop_item(drop_id, user_id, delivery_content=invite_link)
        if not res["success"]:
            await call.answer(f"❌ {res.get('message', 'ক্লেইম ব্যর্থ হয়েছে!')}", show_alert=True)
            return
            
        site_line = f"🌐 <b>অফিসিয়াল সাইট:</b> <a href=\"{site_link}\">{html.escape(site_link)}</a>\n\n" if site_link else ""
        
        success_msg = (
            "🎉 <b>অভিনন্দন! আপনার ফ্রি ভিআইপি চ্যানেল এক্সেস রেডি!</b> 🎉\n\n"
            f"📌 <b>ড্রপ:</b> <b>{title_esc}</b>\n"
            f"📂 <b>ক্যাটাগরি:</b> {meta['icon']} {meta['name_bn']}\n\n"
            f"{site_line}"
            f"🔗 <b>আপনার ব্যক্তিগত ১-বার ব্যবহারযোগ্য লিংক:</b>\n"
            f"<pre>{html.escape(invite_link)}</pre>\n\n"
            "📖 <b>ব্যবহারের নিয়ম:</b>\n"
            f"{guide_esc}\n\n"
            "⚠️ <b>জরুরী সতর্কতা:</b> এই লিংকটি শুধুমাত্র আপনার জন্য ১-বার প্রবেশযোগ্য (Member Limit = 1)। "
            "অন্য কাউকে দিলে আপনি নিজে আর ঢুকতে পারবেন না!"
        )
        
        kb_buttons = [
            [InlineKeyboardButton(text="🚀 জয়েন করুন (Join Channel)", url=invite_link)]
        ]
        if site_link:
            kb_buttons.append([InlineKeyboardButton(text="🌐 ওয়েবসাইট ভিজিট করুন", url=site_link)])
        kb_buttons.append([
            InlineKeyboardButton(text="🔙 ড্রপ তালিকা (Back)", callback_data=f"claim_cat:{cat_key}"),
            InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await render_screen(call, success_msg, reply_markup=kb, parse_mode="HTML")

    elif drop_type == "bulk_combo":
        res = db.claim_free_drop_item(drop_id, user_id)
        if not res["success"]:
            await call.answer(res.get("message", "ক্লেইম ব্যর্থ হয়েছে!"), show_alert=True)
            return
            
        combo_content = res["content"]
        
        category_title_map = {
            "cookies": "আপনার ফ্রি ব্রাউজার কুকিজ (JSON Code):",
            "subscription": "আপনার লাইসেন্স কি / ভাউচার কোড:",
            "accounts": "আপনার প্রিমিয়াম একাউন্ট ক্রেডেনশিয়াল:"
        }
        item_label = category_title_map.get(cat_key, "আপনার সংগৃহীত ড্রপ আইটেম:")
        
        site_line = f"🌐 <b>অফিসিয়াল সাইট:</b> <a href=\"{site_link}\">{html.escape(site_link)}</a>\n\n" if site_link else ""
        
        success_msg = (
            "🎉 <b>অভিনন্দন! আপনার ফ্রি গিভঅ্যাওয়ে ড্রপ ক্লেইম সম্পন্ন হয়েছে!</b> 🎉\n\n"
            f"📌 <b>ড্রপ:</b> <b>{title_esc}</b>\n"
            f"📂 <b>ক্যাটাগরি:</b> {meta['icon']} {meta['name_bn']}\n\n"
            f"{site_line}"
            f"📦 <b>{item_label}</b>\n"
            f"<pre>{html.escape(combo_content)}</pre>\n\n"
            "📖 <b>কিভাবে ব্যবহার করবেন (How to Use Guide):</b>\n"
            f"{guide_esc}\n\n"
            "💡 <i>বক্সে ট্যাপ করলেই কোড সরাসরি কপি হয়ে যাবে। কোনো সমস্যা হলে সাপোর্টে যোগাযোগ করুন।</i>"
        )
        
        kb_buttons = []
        if site_link:
            kb_buttons.append([InlineKeyboardButton(text="🌐 ওয়েবসাইটে প্রবেশ করুন (Open Site)", url=site_link)])
        kb_buttons.append([
            InlineKeyboardButton(text="🔙 ড্রপ তালিকা (Back)", callback_data=f"claim_cat:{cat_key}"),
            InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await render_screen(call, success_msg, reply_markup=kb, parse_mode="HTML")

    else: # direct_link
        link = drop["direct_link"] or "https://t.me"
        res = db.claim_free_drop_item(drop_id, user_id, delivery_content=link)
        if not res["success"]:
            await call.answer(res.get("message", "ক্লেইম ব্যর্থ হয়েছে!"), show_alert=True)
            return
            
        site_line = f"🌐 <b>অফিসিয়াল সাইট:</b> <a href=\"{site_link}\">{html.escape(site_link)}</a>\n\n" if site_link else ""
        
        success_msg = (
            "🎉 <b>অভিনন্দন! আপনার ফ্রি ড্রপ লিংক আনলক হয়েছে!</b> 🎉\n\n"
            f"📌 <b>ড্রপ:</b> <b>{title_esc}</b>\n"
            f"📂 <b>ক্যাটাগরি:</b> {meta['icon']} {meta['name_bn']}\n\n"
            f"{site_line}"
            f"🔗 <b>সিক্রেট অ্যাক্সেস লিংক:</b>\n"
            f"<pre>{html.escape(link)}</pre>\n\n"
            "📖 <b>ব্যবহারের নির্দেশিকা:</b>\n"
            f"{guide_esc}\n\n"
            "💡 <i>লিংকটি সংরক্ষণ করে রাখুন।</i>"
        )
        
        kb_buttons = [
            [InlineKeyboardButton(text="🔗 ওপেন লিংক (Open Link)", url=link if link.startswith("http") else "https://t.me")]
        ]
        if site_link:
            kb_buttons.append([InlineKeyboardButton(text="🌐 অফিসিয়াল ওয়েবসাইট", url=site_link)])
        kb_buttons.append([
            InlineKeyboardButton(text="🔙 ড্রপ তালিকা (Back)", callback_data=f"claim_cat:{cat_key}"),
            InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await render_screen(call, success_msg, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.in_(["noop_claimed", "noop_full"]))
async def handle_noop_drop_clicks(call: CallbackQuery):
    if call.data == "noop_claimed":
        await call.answer("আপনি ইতিমধ্যে এই ড্রপটি সফলভাবে ক্লেইম করেছেন! ড্রপের বিস্তারিততে আপনার কপি সেভ আছে।", show_alert=True)
    else:
        await call.answer("দুঃখিত, এই ড্রপটির সকল ফ্রি স্লট ইতিমধ্যে শেষ হয়ে গেছে!", show_alert=True)
