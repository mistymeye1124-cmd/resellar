# Course and Digital Product Catalog & Purchase Handler
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import html
from database.db import db
from keyboards.user_kb import (
    get_categories_kb,
    get_subcategories_kb,
    get_products_kb,
    get_product_detail_kb,
    get_buy_confirm_kb
)
from utils.invite_helper import generate_single_use_invite_link
from config import ADMIN_IDS, USD_TO_BDT_RATE, get_live_usd_rate
from utils.i18n import t
from utils.notifier import notify_admin_order
from utils.emojis import em_tag

router = Router()

from utils.ui_nav import render_screen, safe_switch_screen, render_safe_html_text

class BuyCouponState(StatesGroup):
    waiting_for_code = State()

@router.message(F.text.in_([
    "Browse Courses (কোর্স সমূহ)", "🎓 Browse Courses (কোর্স সমূহ)", "Browse Courses", "🎓 Browse Courses", "कोर्सेस देखें (Courses)", "🎓 कोर्सेस देखें (Courses)", "কোর্স সমূহ", "কোর্স"
]))
async def handle_browse_courses(message: Message):
    cats = db.get_categories_by_type("course")
    lang = db.get_user_language(message.from_user.id)
    em_crs = em_tag("courses", "🎓")
    text = (
        f"{em_crs} <b>প্রিমিয়াম কোর্স স্টোর — কারিকুলাম ও ক্যাটাগরি</b> {em_crs}\n\n"
        "আমাদের ডিজিটাল শপে সেরা ইন্সট্রাক্টরদের শীর্ষ কোর্সগুলো সাজানো আছে।\n"
        "👇 আপনার পছন্দের ক্যাটাগরি বেছে নিন:"
    )
    await message.answer(text, reply_markup=get_categories_kb(cats, "course", lang), parse_mode="HTML")

@router.message(F.text.in_([
    "Digital Tools & Accounts", "⚡ Digital Tools & Accounts", "ডিজিটাল টুলস (Tools & Accounts)", "⚡ ডিজিটাল টুলস (Tools & Accounts)", "ডিজিটাল টুल्स (Tools & Accounts)", "⚡ ডিজিটাল টুल्स (Tools & Accounts)", "डिजिटल टूल्स (Tools & Accounts)", "⚡ डिजिटल टूल्स (Tools & Accounts)"
]))
async def handle_browse_digital(message: Message):
    cats = db.get_categories_by_type("digital")
    lang = db.get_user_language(message.from_user.id)
    em_dgt = em_tag("digital", "⚡")
    text = (
        f"{em_dgt} <b>ডিজিটাল একাউন্টস ও এআই টুলস হাব</b> {em_dgt}\n\n"
        "ওটিটি প্ল্যাটফর্ম, ভিপিএন, এআই টুলস ও প্রিমিয়াম সফটওয়্যার লাইসেন্স।\n"
        "👇 আপনার প্রয়োজনীয় ক্যাটাগরি নির্বাচন করুন:"
    )
    await message.answer(text, reply_markup=get_categories_kb(cats, "digital", lang), parse_mode="HTML")

@router.callback_query(F.data == "back_cats")
async def handle_back_cats(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    cats = db.get_categories(parent_id=None)
    lang = db.get_user_language(call.from_user.id)
    em_crs = em_tag("courses", "🛍️")
    text = (
        f"{em_crs} <b>প্রিমিয়াম শপ — সকল ক্যাটাগরি ও প্ল্যাটফর্ম</b> {em_crs}\n\n"
        "আমাদের ডিজিটাল স্টোরে প্রিমিয়াম একাডেমি কোর্স, টুলস ও অ্যাকাউন্ট সাজানো আছে।\n"
        "👇 আপনার পছন্দের প্ল্যাটফর্ম বা ক্যাটাগরি বেছে নিন:"
    )
    await render_screen(call, text, reply_markup=get_categories_kb(cats, "all", lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat:"))
async def handle_category_select(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    cat = db.get_category(cat_id)
    if not cat:
        await call.answer("ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
        
    await call.answer()
    em_cat = em_tag("category", "📁")
    lang = db.get_user_language(call.from_user.id)
    
    # Check if this category has subcategories
    if db.has_subcategories(cat_id):
        subcats = db.get_subcategories(cat_id)
        text = (
            f"{em_cat} <b>{html.escape(cat['name'])}</b>\n\n"
            "📚 <b>বিষয়ভিত্তিক কোর্স ট্র্যাক ও সাব-ক্যাটাগরি:</b>\n"
            "👇 আপনি কোন বিষয়ের কোর্স খুঁজছেন নিচে বেছে নিন:"
        )
        await render_screen(call, text, reply_markup=get_subcategories_kb(subcats, cat_id, lang), parse_mode="HTML")
        return

    # Direct category products
    products = db.get_products_by_category(cat_id)
    if not products:
        text = (
            f"{em_cat} <b>{html.escape(cat['name'])}</b>\n\n"
            "⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো কোর্স/প্রোডাক্ট সক্রিয় নেই।\n"
            "খুব শীঘ্রই নতুন কোর্স ও স্টক যুক্ত করা হবে!"
        )
        from utils.emojis import make_custom_button
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [make_custom_button(text="🔙 ক্যাটাগরি (Back)", callback_data="back_cats", emoji_key="back")],
            [make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")]
        ])
        await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")
        return
        
    text = (
        f"{em_cat} <b>{html.escape(cat['name'])}</b>\n\n"
        f"📊 মোট উপলব্ধ প্রোডাক্ট: <b>{len(products)} টি</b>\n"
        "👇 বিস্তারিত দেখতে নিচের কোর্সে ক্লিক করুন:"
    )
    await render_screen(call, text, reply_markup=get_products_kb(products, cat_id, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("subcat:"))
async def handle_subcategory_select(call: CallbackQuery):
    subcat_id = int(call.data.split(":")[1])
    subcat = db.get_category(subcat_id)
    if not subcat:
        await call.answer("সাব-ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
        
    await call.answer()
    em_cat = em_tag("category", "📁")
    lang = db.get_user_language(call.from_user.id)
    parent_cat = db.get_category(subcat.get("parent_id")) if subcat.get("parent_id") else None
    parent_name = f"{parent_cat['name']} ❯ " if parent_cat else ""
    
    products = db.get_products_by_subcategory(subcat_id)
    from utils.emojis import make_custom_button
    if not products:
        text = (
            f"{em_cat} <b>{parent_name}{html.escape(subcat['name'])}</b>\n\n"
            "⚠️ এই সাব-ক্যাটাগরিতে বর্তমানে কোনো কোর্স সক্রিয় নেই।\n"
            "খুব শীঘ্রই নতুন কোর্স ও স্টক যুক্ত করা হবে!"
        )
        parent_id = subcat.get('parent_id')
        back_cb = f"cat:{parent_id}" if parent_id else "back_cats"
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [make_custom_button(text="🔙 সাব-ক্যাটাগরি (Back)", callback_data=back_cb, emoji_key="back")],
            [make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")]
        ])
        await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")
        return
        
    text = (
        f"{em_cat} <b>{parent_name}{html.escape(subcat['name'])}</b>\n\n"
        f"📊 মোট উপলব্ধ কোর্স: <b>{len(products)} টি</b>\n"
        "👇 বিস্তারিত দেখতে নিচের কোর্সে ক্লিক করুন:"
    )
    await render_screen(call, text, reply_markup=get_products_kb(products, category_id=subcat.get("parent_id", subcat_id), subcategory_id=subcat_id, parent_id=subcat.get("parent_id"), lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("prod:"))
async def handle_product_detail(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    await call.answer()
    
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    # Check Stock
    is_in_stock_flag = bool(prod.get("is_in_stock", 1) if prod.get("is_in_stock") is not None else 1)
    if not is_in_stock_flag:
        in_stock = False
        stock_str = "❌ <b>স্টক শেষ (Out of Stock)</b>"
    elif prod["product_type"] == "stock_account":
        stock_cnt = db.get_stock_count(prod_id)
        if stock_cnt > 0:
            in_stock = True
            stock_str = f"✅ <b>ইন-স্টক: {stock_cnt} টি অ্যাকাউন্ট / কি উপলব্ধ</b>"
        elif prod.get("drive_link") and ("http" in prod["drive_link"] or ":" in prod["drive_link"]):
            in_stock = True
            stock_str = "⚡ <b>ইনস্ট্যান্ট অটো-ডেলিভারি প্রস্তুত</b>"
        else:
            in_stock = False
            stock_str = "❌ <b>স্টক শেষ (Out of Stock)</b>"
    else:
        in_stock = True
        stock_str = "⚡ <b>ইনস্ট্যান্ট অটো-ডেলিভারি প্রস্তুত</b>"
        
    type_labels = {
        "channel_link": "🔒 Private VIP Telegram Channel (1-Time Single-Use Link)",
        "dual_access": "🔥 Dual Package (VIP Channel & Personal Account Access)",
        "stock_account": "🔑 Ready-Made Account / License Key (Instant Delivery)",
        "drive_link": "☁️ Google Drive / Mega Cloud Vault",
        "manual": "🛠️ Custom Setup / Activated on Your Mail"
    }

    reg_bdt = int(prod["price_bdt"])
    reg_usd = prod["price_usd"]
    res_bdt = int(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else int(reg_bdt * 0.70)
    res_usd = prod["reseller_price_usd"] if prod.get("reseller_price_usd") else round(reg_usd * 0.70, 2)
    charge_bdt = res_bdt if is_reseller else reg_bdt

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_bal_bdt = float(user.get("balance_bdt") or 0.0)
    bal_pct = min(100, int((user_bal_bdt / charge_bdt) * 100)) if charge_bdt > 0 else 100
    bars = int(bal_pct / 10)
    filled_bars = "▰" * bars
    empty_bars = "▱" * (10 - bars)
    prog_bar = f"{filled_bars}{empty_bars} {bal_pct}%"
    rem_bdt = max(0.0, charge_bdt - user_bal_bdt)
    rem_refs = max(1, int(rem_bdt / t1_bonus)) if t1_bonus > 0 else 1

    sales_info = ""
    if prod.get("sales_page_url"):
        sales_info = f"🌐 <b>কোর্স কারিকুলাম ও সেলস পেজ:</b>\n<code>{html.escape(prod['sales_page_url'])}</code>\n\n"

    has_dual = (float(prod.get("price_channel_bdt") or 0) > 0 and float(prod.get("price_account_bdt") or 0) > 0)
    if has_dual:
        live_rate = get_live_usd_rate()
        ch_b = float(prod["price_channel_bdt"])
        ch_u = float(prod.get("price_channel_usd") or round(ch_b / live_rate, 2))
        acc_b = float(prod["price_account_bdt"])
        acc_u = float(prod.get("price_account_usd") or round(acc_b / live_rate, 2))
        
        if is_reseller:
            r_ch_b = float(prod.get("reseller_price_channel_bdt") or round(ch_b * 0.70, 2))
            r_acc_b = float(prod.get("reseller_price_account_bdt") or round(acc_b * 0.70, 2))
            price_section = (
                f"💳 <b>প্যাকেজ অপশন ও স্পেশাল পাইকারি রেট:</b>\n"
                f"• 📢 <b>VIP Channel Access:</b> <b>৳{int(r_ch_b)} BDT</b> (${round(r_ch_b/live_rate, 2)}) <i>(খুচরা ৳{int(ch_b)})</i>\n"
                f"• 🔐 <b>Personal Account / Drive:</b> <b>৳{int(r_acc_b)} BDT</b> (${round(r_acc_b/live_rate, 2)}) <i>(খুচরা ৳{int(acc_b)})</i>\n\n"
                f"🎁 <b>রেফারেল দিয়ে ফ্রি নিন:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>"
            )
        else:
            price_section = (
                f"💳 <b>প্যাকেজ অপশন ও মূল্য তালিকা:</b>\n"
                f"• 📢 <b>VIP Channel Access:</b> <b>৳{int(ch_b)} BDT</b> (${ch_u} USD)\n"
                f"• 🔐 <b>Personal Account / Drive:</b> <b>৳{int(acc_b)} BDT</b> (${acc_u} USD)\n\n"
                f"🎁 <b>অথবা রেফারেল দিয়ে সম্পূর্ণ ফ্রি:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(বর্তমান ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>\n"
                f"🎯 <i>(আর মাত্র ৳{int(rem_bdt)} বা {rem_refs} টি রেফারেল করলেই ফ্রি আনলক!)</i>"
            )
        active_prod = prod
    elif is_reseller:
        price_section = (
            f"💎 <b>আপনার স্পেশাল পাইকারি রেট:</b> <b>৳{res_bdt} BDT</b> | <b>${res_usd} USD</b>\n"
            f"🏷️ <i>(সাধারণ খুচরা মূল্য: ৳{reg_bdt} — আপনি সেভ করছেন ৳{reg_bdt - res_bdt}!)</i>\n"
            f"🎁 <b>রেফারেল দিয়ে ফ্রি নিন:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
            f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>"
        )
        active_prod = dict(prod)
        active_prod["price_bdt"] = res_bdt
        active_prod["price_usd"] = res_usd
    else:
        price_section = (
            f"💰 <b>মূল্য:</b> <b>৳{reg_bdt} BDT</b> অথবা <b>${reg_usd} USD</b>\n"
            f"🎁 <b>অথবা রেফারেল দিয়ে সম্পূর্ণ ফ্রি:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
            f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(বর্তমান ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>\n"
            f"🎯 <i>(আর মাত্র ৳{int(rem_bdt)} বা {rem_refs} টি রেফারেল করলেই ফ্রি আনলক!)</i>"
        )
        active_prod = prod

    category_label = ""
    if prod.get("subcategory_id"):
        subcat = db.get_category(prod["subcategory_id"])
        parent = db.get_category(prod.get("category_id"))
        if subcat and parent:
            category_label = f"📁 <b>ক্যাটাগরি:</b> <code>{html.escape(parent['name'])} ❯ {html.escape(subcat['name'])}</code>\n"
        elif subcat:
            category_label = f"📁 <b>ক্যাটাগরি:</b> <code>{html.escape(subcat['name'])}</code>\n"
    elif prod.get("category_id"):
        cat = db.get_category(prod["category_id"])
        if cat:
            category_label = f"📁 <b>ক্যাটাগরি:</b> <code>{html.escape(cat['name'])}</code>\n"

    em_crs = em_tag("courses", "🎓")
    em_box = em_tag("box", "📦")
    detail_text = (
        f"{em_crs} <b>{html.escape(prod['title'])}</b> {em_crs}\n\n"
        f"📝 <b>কোর্স বিবরণ ও কারিকুলাম:</b>\n{render_safe_html_text(prod['description'])}\n\n"
        f"{sales_info}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{category_label}"
        f"{em_box} <b>অ্যাক্সেস টাইপ:</b> {type_labels.get(prod['product_type'], 'Digital')}\n"
        f"📊 <b>স্টক অবস্থা:</b> {stock_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{price_section}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👉 <i>ইনস্ট্যান্ট অ্যাক্সেস নিতে নিচের বাটনে ক্লিক করুন:</i>"
    )
    
    lang = db.get_user_language(user_id)
    photo_id = prod.get("photo_file_id")
    await safe_switch_screen(
        call,
        detail_text,
        reply_markup=get_product_detail_kb(active_prod, in_stock, lang),
        photo_url=photo_id,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("claim_ref:"))
async def handle_claim_ref(call: CallbackQuery, bot: Bot):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    reg_bdt = float(prod["price_bdt"])
    res_bdt = float(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else round(reg_bdt * 0.70, 2)
    charge_bdt = res_bdt if is_reseller else reg_bdt
    user_bal = float(user.get("balance_bdt") or 0.0)
    user_pts = user.get("referral_points", 0) or 0

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1

    # If user has enough referral points OR balance, offer instant unlock!
    if user_pts >= refs_needed or user_bal >= charge_bdt:
        from utils.emojis import make_custom_button
        pay_confirm_text = (
            f"🎉 <b>অভিনন্দন! আপনার অ্যাকাউন্টে পর্যাপ্ত রিসোর্স রয়েছে!</b>\n\n"
            f"📦 <b>কোর্স:</b> {html.escape(prod['title'])}\n"
            f"💰 <b>প্রয়োজনীয় মূল্য:</b> <code>৳{int(charge_bdt)} BDT</code> (বা <b>{refs_needed} Pts</b>)\n"
            f"💳 <b>আপনার BDT ব্যালেন্স:</b> <code>৳{user_bal:.2f} BDT</code>\n"
            f"💎 <b>আপনার রেফারেল পয়েন্ট:</b> <code>{user_pts} Pts</code>\n\n"
            f"👇 আপনি যেভাবে কোর্সটি পেতে চান নিচের বাটন চাপুন:"
        )
        buttons = []
        if user_pts >= refs_needed:
            buttons.append([
                make_custom_button(
                    text=f"🎁 Pay with Referrals ({refs_needed} Pts)",
                    callback_data=f"confirm_buy:{prod_id}:REF",
                    emoji_key="free_claim"
                )
            ])
        if user_bal >= charge_bdt:
            buttons.append([
                make_custom_button(
                    text=f"💰 Pay with Balance (৳{int(charge_bdt)})",
                    callback_data=f"confirm_buy:{prod_id}:BDT",
                    emoji_key="check"
                )
            ])
        buttons.append([
            make_custom_button(text="🔙 পূর্ববর্তী (Back)", callback_data=f"prod:{prod_id}", emoji_key="back"),
            make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")
        ])
        await render_screen(call, pay_confirm_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
        return

    # If user doesn't have enough balance or points, show the viral progress modal
    rem_bdt = max(0.0, charge_bdt - user_bal)
    rem_refs = max(0, refs_needed - user_pts)
    bal_pct = min(100, int((user_bal / charge_bdt) * 100)) if charge_bdt > 0 else 100
    bars = int(bal_pct / 10)
    filled_bars = "▰" * bars
    empty_bars = "▱" * (10 - bars)
    prog_bar = f"{filled_bars}{empty_bars} {bal_pct}%"

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "AllInOneProAccess_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}_c{prod_id}"

    t2_pct = float(db.get_setting("referral_t2_percent", "50.0"))
    welcome_bonus = float(db.get_setting("referral_welcome_bonus", "5.0"))
    gift_str = f"▫️ 🎉 নতুন ফ্রেন্ড জয়েন করলেই পাবে: **৳{welcome_bonus:.0f} BDT** ওয়েলকাম বোনাস\n" if welcome_bonus > 0 else ""

    progress_modal = (
        "🌟 **রেফারেল দিয়ে সম্পূর্ণ ফ্রিতে কোর্সটি আনলক করুন!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 **কোর্সের নাম:** {prod['title']}\n"
        f"💰 **কোর্সের সম্পূর্ণ মূল্য:** **৳{int(charge_bdt)} BDT** (বা **{refs_needed} Points**)\n"
        f"💳 **আপনার বর্তমান ওয়ালেট ব্যালেন্স:** **৳{user_bal:.2f} BDT**\n"
        f"💎 **আপনার বর্তমান রেফারেল পয়েন্ট:** **{user_pts} Pts** (প্রয়োজন: **{refs_needed} Pts**)\n\n"
        f"⚡ **আপনার আনলক প্রগ্রেস:** `{prog_bar}`\n"
        f"🎯 **টার্গেট:** আর মাত্র **{rem_refs} টি রেফারেল** হলেই কোর্সটি সম্পূর্ণ ফ্রি!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 **আপনার বিশেষ কোর্স রেফারেল লিংক (ট্যাপ করলেই কপি):**\n"
        f"`{ref_link}`\n\n"
        "💎 **রেফারেলের এক্সক্লুসিভ বেনিফিট:**\n"
        f"▫️ 👤 সরাসরি রেফারেল বোনাস: **+1 Point (+৳{t1_bonus:.0f} BDT)** ইনস্ট্যান্ট\n"
        f"▫️ 👥 টিম প্যাসিভ কমিশন: **+{t2_pct:.0f}%** লাইফটাইম হাফ কমিশন\n"
        f"{gift_str}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 **১-ট্যাপে লিংক কপি করতে বা সরাসরি শেয়ার করতে নিচের বাটন চাপুন:**"
    )
    from keyboards.user_kb import get_referral_progress_kb
    await render_screen(call, progress_modal, reply_markup=get_referral_progress_kb(prod_id, bot_username, user_id), parse_mode="Markdown")

@router.callback_query(F.data.startswith("gen_course_ref:"))
async def handle_gen_course_ref(call: CallbackQuery, bot: Bot):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    user_id = call.from_user.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "AllInOneProAccess_bot"
    course_link = f"https://t.me/{bot_username}?start=ref_{user_id}_c{prod_id}"
    lang = db.get_user_language(user_id)
    
    await call.answer()
    
    text = (
        "🔗 <b>এই কোর্সের স্পেশাল রেফারেল লিংক</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 <b>কোর্স:</b> {html.escape(prod['title'])}\n"
        f"🔗 <b>আপনার পার্সোনাল কোর্স লিংক:</b>\n"
        f"<code>{course_link}</code>\n"
        "<i>(ট্যাপ করলেই লিংক কপি হবে অথবা নিচের বাটনে চাপুন)</i>\n\n"
        "💡 <b>সুবিধাসমূহ:</b>\n"
        "• কোনো বন্ধু এই লিংকে ক্লিক করে বটে আসলে সে সরাসরি এই কোর্সের পেইজ দেখতে পাবে।\n"
        "• আপনার প্রোফাইলে ট্র্যাক থাকবে এই কোর্সের মাধ্যমে কতজন বন্ধু জয়েন করেছে।\n"
        "• বন্ধু জয়েন করলেই আপনার অ্যাকাউন্টে সরাসরি রেফারেল পয়েন্ট যুক্ত হবে!\n\n"
        "👇 ১-ট্যাপে লিংক কপি করতে বা সরাসরি শেয়ার করতে নিচের বাটন চাপুন:"
    )
    from keyboards.user_kb import get_course_ref_share_kb
    await render_screen(call, text, reply_markup=get_course_ref_share_kb(bot_username, user_id, prod, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("copy_course_ref:"))
async def handle_copy_course_ref(call: CallbackQuery, bot: Bot):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "AllInOneProAccess_bot"
    course_link = f"https://t.me/{bot_username}?start=ref_{call.from_user.id}_c{prod_id}"
    await call.answer(f"📋 রেফারেল লিংক:\n{course_link}", show_alert=True)

@router.callback_query(F.data.startswith("buy_tier_select:"))
async def handle_buy_tier_select(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer("⚠️ দুঃখিত, এই কোর্সটি বর্তমানে 'আউট অব স্টক' (Out of Stock)!", show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    is_reseller = user.get("is_reseller", 0) >= 1 if user else False
    lang = db.get_user_language(user_id)
    
    live_rate = get_live_usd_rate()
    ch_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
    ch_usd = float(prod.get("price_channel_usd") or round(ch_bdt / live_rate, 2))
    acc_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
    acc_usd = float(prod.get("price_account_usd") or round(acc_bdt / live_rate, 2))
    
    if is_reseller:
        ch_bdt = float(prod.get("reseller_price_channel_bdt") or round(ch_bdt * 0.70, 2))
        ch_usd = round(ch_bdt / live_rate, 2)
        acc_bdt = float(prod.get("reseller_price_account_bdt") or round(acc_bdt * 0.70, 2))
        acc_usd = round(acc_bdt / live_rate, 2)
        
    await call.answer()
    
    text = (
        f"🛒 <b>প্যাকেজ নির্বাচন করুন: {html.escape(prod['title'])}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "এই কোর্সের জন্য ২টি পৃথক অ্যাক্সেস প্যাকেজ উপলব্ধ রয়েছে:\n\n"
        f"1️⃣ 📢 <b>VIP Telegram Channel Access:</b>\n"
        "• প্রাইভেট ভিআইপি চ্যানেলে লাইফটাইম অ্যাক্সেস (1-Time Invite Link)\n"
        f"• মূল্য: <b>৳{int(ch_bdt)} BDT</b> (${ch_usd} USD)\n\n"
        f"2️⃣ 🔐 <b>Personal Account / Drive Access:</b>\n"
        "• পার্সোনাল লগইন অ্যাকাউন্ট বা ডিরেক্ট ড্রাইভ অ্যাক্সেস\n"
        f"• মূল্য: <b>৳{int(acc_bdt)} BDT</b> (${acc_usd} USD)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 আপনি কোন অ্যাক্সেসটি নিতে চান নিচের অপশন থেকে বেছে নিন:"
    )
    from keyboards.user_kb import get_access_tier_selection_kb
    await render_screen(call, text, reply_markup=get_access_tier_selection_kb(prod_id, ch_bdt, ch_usd, acc_bdt, acc_usd, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("buy_tier:"))
async def handle_buy_tier_chosen(call: CallbackQuery):
    parts = call.data.split(":")
    prod_id = int(parts[1])
    tier = parts[2] # 'channel' or 'account'
    
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer("⚠️ দুঃখিত, এই কোর্সটি বর্তমানে 'আউট অব স্টক' (Out of Stock)!", show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    lang = db.get_user_language(user_id)

    live_rate = get_live_usd_rate()
    if tier == "channel":
        tier_title = "📢 VIP Channel Access"
        reg_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_channel_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_channel_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)
    else:
        tier_title = "🔐 Personal Account Access"
        reg_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_account_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_account_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)

    charge_bdt = res_bdt if is_reseller else reg_bdt
    charge_usd = res_usd if is_reseller else reg_usd
    reseller_badge = "💎 <b>(রিসেলার পাইকারি ডিসকাউন্ট প্রযোজ্য)</b>" if is_reseller else ""

    vip_pass = db.get_active_reseller_vip_pass(user_id) if is_reseller else None
    if vip_pass:
        extra_bdt = float(vip_pass.get("discount_bdt", 0.0))
        charge_bdt = max(0, charge_bdt - int(extra_bdt))
        charge_usd = round(charge_bdt / live_rate, 2)
        reseller_badge = (
            f"💎 <b>(রিসেলার সাধারণ পাইকারি: ৳{int(res_bdt)})</b>\n"
            f"🏆 <b>[টপ-সেলার রিওয়ার্ড: -৳{int(extra_bdt)} অতিরিক্ত ছাড়!]</b>\n"
            f"⏳ অফার মেয়াদ বাকি: <code>{vip_pass['days_left']} দিন</code> (অর্ডার বাকি: <code>{vip_pass['remaining_uses']} টি</code>)"
        )

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_pts = user.get("referral_points", 0) or 0

    await call.answer()
    
    text = (
        f"🛒 <b>অর্ডার চেকআউট কনফার্মেশন</b>\n"
        f"<b>{html.escape(prod['title'])}</b>\n"
        f"🏷️ <b>নির্বাচিত প্যাকেজ:</b> {tier_title}\n"
        f"{reseller_badge}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 প্যাকেজ মূল্য: <b>৳{int(charge_bdt)} BDT</b> অথবা <b>${charge_usd} USD</b>\n\n"
        f"💳 <b>আপনার বর্তমান ওয়ালেট ব্যালেন্স:</b>\n"
        f"• BDT: <b>৳{user['balance_bdt']:.2f} BDT</b>\n"
        f"• USD: <b>${user['balance_usd']:.2f} USD</b>\n"
        f"• রেফারেল পয়েন্ট: <b>{user_pts} Pts</b> (প্রয়োজন: {refs_needed} Pts)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 আপনি কোন ব্যালেন্স বা পয়েন্ট দিয়ে পে করতে চান নির্বাচন করুন:"
    )
    await render_screen(call, text, reply_markup=get_buy_confirm_kb(prod_id, charge_bdt, charge_usd, tier=tier, has_coupon=False, refs_needed=refs_needed, user_pts=user_pts, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("buy:"))
async def handle_buy_prompt(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer("⚠️ দুঃখিত, এই কোর্সটি বর্তমানে 'আউট অব স্টক' (Out of Stock)!", show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    lang = db.get_user_language(user_id)

    reg_bdt = int(prod["price_bdt"])
    reg_usd = prod["price_usd"]
    res_bdt = int(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else int(reg_bdt * 0.70)
    res_usd = prod["reseller_price_usd"] if prod.get("reseller_price_usd") else round(reg_usd * 0.70, 2)

    charge_bdt = res_bdt if is_reseller else reg_bdt
    charge_usd = res_usd if is_reseller else reg_usd
    reseller_badge = "💎 <b>(রিসেলার ডিসকাউন্ট প্রযোজ্য)</b>" if is_reseller else ""

    # Check for active Reseller VIP Pass (Extra Top-Seller Reward Discount)
    vip_pass = db.get_active_reseller_vip_pass(user_id) if is_reseller else None
    if vip_pass:
        extra_bdt = float(vip_pass.get("discount_bdt", 0.0))
        charge_bdt = max(0, charge_bdt - int(extra_bdt))
        charge_usd = round(charge_bdt / get_live_usd_rate(), 2)
        reseller_badge = (
            f"💎 <b>(রিসেলার সাধারণ পাইকারি: ৳{res_bdt})</b>\n"
            f"🏆 <b>[টপ-সেলার রিওয়ার্ড: -৳{int(extra_bdt)} অতিরিক্ত ছাড়!]</b>\n"
            f"⏳ অফার মেয়াদ বাকি: <code>{vip_pass['days_left']} দিন</code> (অর্ডার বাকি: <code>{vip_pass['remaining_uses']} টি</code>)"
        )

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_pts = user.get("referral_points", 0) or 0

    await call.answer()
    
    text = (
        f"🛒 <b>অর্ডার চেকআউট কনফার্মেশন</b>\n"
        f"<b>{html.escape(prod['title'])}</b>\n"
        f"{reseller_badge}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 কোর্স মূল্য: <b>৳{charge_bdt} BDT</b> অথবা <b>${charge_usd} USD</b>\n\n"
        f"💳 <b>আপনার বর্তমান ওয়ালেট ব্যালেন্স:</b>\n"
        f"• BDT: <b>৳{user['balance_bdt']:.2f} BDT</b>\n"
        f"• USD: <b>${user['balance_usd']:.2f} USD</b>\n"
        f"• রেফারেল পয়েন্ট: <b>{user_pts} Pts</b> (প্রয়োজন: {refs_needed} Pts)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 আপনি কোন ব্যালেন্স বা পয়েন্ট দিয়ে পে করতে চান নির্বাচন করুন:"
    )
    await render_screen(call, text, reply_markup=get_buy_confirm_kb(prod_id, charge_bdt, charge_usd, has_coupon=False, refs_needed=refs_needed, user_pts=user_pts, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("apply_coupon:"))
async def handle_apply_coupon_start(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    prod_id = int(parts[1])
    tier = parts[2] if len(parts) > 2 else "default"
    await state.update_data(coupon_prod_id=prod_id, coupon_tier=tier)
    await state.set_state(BuyCouponState.waiting_for_code)
    await call.answer()
    
    cancel_cb = f"buy_tier:{prod_id}:{tier}" if tier != "default" else f"buy:{prod_id}"
    text = (
        "🎟️ **কুপন বা ভাউচার কোড ব্যবহার করুন**\n\n"
        "👉 আপনার কুপন কোডটি লিখে সেন্ড করুন:\n"
        "_(যেমন: VIP50 বা SPECIAL100)_"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 ব্যাকে যান (Back)", callback_data=cancel_cb),
            InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
        ]
    ])
    await render_screen(call, text, reply_markup=cancel_kb, parse_mode="Markdown")

@router.message(BuyCouponState.waiting_for_code)
async def handle_apply_coupon_code(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে কুপন কোডটি টেক্সট আকারে লিখে পাঠান:")
        return
    code = message.text.strip().upper()
    data = await state.get_data()
    prod_id = data.get("coupon_prod_id")
    tier = data.get("coupon_tier", "default")
    if not prod_id:
        await state.clear()
        await message.answer("⚠️ সেশন মেয়াদোত্তীর্ণ। আবার চেষ্টা করুন।")
        return
        
    cancel_cb = f"buy_tier:{prod_id}:{tier}" if tier != "default" else f"buy:{prod_id}"
    coupon = db.get_coupon(code)
    if not coupon:
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ ফিরে যান", callback_data=cancel_cb)]
        ])
        await message.answer("❌ **ভুল কুপন কোড অথবা মেয়াদ শেষ হয়ে গেছে!**\n\nসঠিক কোড দিন অথবা ফিরে যান:", reply_markup=cancel_kb, parse_mode="Markdown")
        return
        
    prod = db.get_product(prod_id)
    if not prod:
        await state.clear()
        return
        
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, message.from_user.username, message.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    
    if tier == "channel":
        reg_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
        res_bdt = float(prod.get("reseller_price_channel_bdt") or round(reg_bdt * 0.70, 2))
    elif tier == "account":
        reg_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
        res_bdt = float(prod.get("reseller_price_account_bdt") or round(reg_bdt * 0.70, 2))
    else:
        reg_bdt = float(prod["price_bdt"])
        res_bdt = float(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else round(reg_bdt * 0.70, 2)
        
    base_bdt = res_bdt if is_reseller else reg_bdt
    discount_bdt = float(coupon.get("discount_bdt", 0.0))
    final_bdt = max(0.0, base_bdt - discount_bdt)
    final_usd = round(final_bdt / get_live_usd_rate(), 2)
    
    await state.clear()
    
    tier_label = f" ({'📢 VIP Channel' if tier == 'channel' else '🔐 Account Access'})" if tier != 'default' else ""
    confirm_text = (
        f"🛒 **অর্ডার কনফার্মেশন: {prod['title']}{tier_label}**\n\n"
        f"🏷️ **প্রযোজ্য কুপন:** `{code}` (৳{int(discount_bdt)} BDT ছাড় ✅)\n"
        f"💰 **পরিশোধযোগ্য মূল্য:** `৳{int(final_bdt)} BDT` অথবা `${final_usd} USD`\n\n"
        f"💳 **আপনার বর্তমান ব্যালেন্স:**\n"
        f"• BDT: `৳{user['balance_bdt']:.2f}`\n"
        f"• USD: `${user['balance_usd']:.2f}`\n\n"
        "আপনি কোন ব্যালেন্স দিয়ে পে করতে চান নির্বাচন করুন:"
    )
    
    buttons = [
        [
            InlineKeyboardButton(text=f"✅ Pay ৳{int(final_bdt)} (BDT)", callback_data=f"confirm_buy:{prod_id}:BDT:{tier}:{code}"),
            InlineKeyboardButton(text=f"✅ Pay ${final_usd} (USD)", callback_data=f"confirm_buy:{prod_id}:USD:{tier}:{code}")
        ],
        [
            InlineKeyboardButton(text="💳 Add Balance", callback_data="add_balance_shortcut")
        ],
        [
            InlineKeyboardButton(text="🔙 Back", callback_data=cancel_cb),
            InlineKeyboardButton(text="🏠 Home", callback_data="main_menu")
        ]
    ]
    await message.answer(confirm_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("confirm_buy:"))
async def handle_confirm_buy(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    prod_id = int(parts[1])
    currency = parts[2] # 'BDT' or 'USD'
    tier = "default"
    coupon_code = None
    if len(parts) == 4:
        if parts[3] in ["channel", "account", "default"]:
            tier = parts[3]
        else:
            coupon_code = parts[3]
    elif len(parts) >= 5:
        tier = parts[3]
        coupon_code = parts[4]
    
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    # Price Calculation based on access tier
    live_rate = get_live_usd_rate()
    if tier == "channel":
        reg_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_channel_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_channel_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)
    elif tier == "account":
        reg_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_account_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_account_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)
    else:
        reg_bdt = float(prod["price_bdt"])
        reg_usd = float(prod["price_usd"])
        res_bdt = float(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else round(reg_bdt * 0.70, 2)
        res_usd = float(prod["reseller_price_usd"]) if prod.get("reseller_price_usd") else round(reg_usd * 0.70, 2)

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(reg_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_pts = user.get("referral_points", 0) or 0

    if currency == "REF":
        price = refs_needed
        savings = reg_bdt
    elif currency == "BDT":
        price = res_bdt if is_reseller else reg_bdt
        savings = (reg_bdt - res_bdt) if is_reseller else 0.0
    else:
        price = res_usd if is_reseller else reg_usd
        savings = (reg_usd - res_usd) if is_reseller else 0.0

    applied_vip_pass_id = None
    # Apply active Reseller VIP Pass (Top-Seller Reward) if active
    if is_reseller and not coupon_code and currency != "REF":
        vip_pass = db.get_active_reseller_vip_pass(user_id)
        if vip_pass:
            extra_disc_bdt = float(vip_pass.get("discount_bdt", 0.0))
            if currency == "BDT":
                price = max(0.0, price - extra_disc_bdt)
                savings += extra_disc_bdt
            else:
                extra_disc_usd = round(extra_disc_bdt / live_rate, 2)
                price = max(0.0, price - extra_disc_usd)
                savings += extra_disc_usd
            applied_vip_pass_id = vip_pass["id"]

    # Apply Coupon Discount if provided
    if coupon_code and currency != "REF":
        coupon = db.get_coupon(coupon_code)
        if coupon:
            disc_bdt = float(coupon.get("discount_bdt", 0.0))
            if currency == "BDT":
                price = max(0.0, price - disc_bdt)
                savings += disc_bdt
            else:
                disc_usd = round(disc_bdt / live_rate, 2)
                price = max(0.0, price - disc_usd)
                savings += disc_usd
            db.use_coupon(coupon_code)

    if prod.get("is_in_stock", 1) == 0:
        await call.answer("❌ এই আইটেমটি বর্তমানে স্টকে নেই!", show_alert=True)
        return

    # 1. Balance / Points Check
    if currency == "REF":
        if user_pts < price:
            await call.answer("❌ পর্যাপ্ত রেফারেল পয়েন্ট নেই!", show_alert=True)
            insufficient_text = (
                "❌ <b>আপনার অ্যাকাউন্টে পর্যাপ্ত রেফারেল পয়েন্ট নেই!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 প্রয়োজনীয় পয়েন্ট: <b>{price} Pts</b>\n"
                f"🌟 আপনার বর্তমান পয়েন্ট: <b>{user_pts} Pts</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚡ বন্ধুদের রেফার করে পয়েন্ট অর্জন করুন অথবা ওয়ালেটে টাকা ডিপোজিট করে কোর্স কিনুন।"
            )
            await render_screen(
                call,
                insufficient_text,
                reply_markup=get_buy_confirm_kb(prod_id, reg_bdt, round(reg_bdt / live_rate, 2), tier=tier, refs_needed=refs_needed, user_pts=user_pts),
                parse_mode="HTML"
            )
            return
    else:
        user_bal = user["balance_bdt"] if currency == "BDT" else user["balance_usd"]
        if user_bal < price:
            await call.answer("❌ পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)
            unit = "৳" if currency == "BDT" else "$"
            insufficient_text = (
                "❌ <b>আপনার ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 প্রয়োজনীয় ব্যালেন্স: <b>{unit}{price}</b>\n"
                f"💳 আপনার বর্তমান ব্যালেন্স: <b>{unit}{user_bal:.2f}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚡ অনুগ্রহ করে নিচের বাটন থেকে ওয়ালেটে ব্যালেন্স রিচার্জ (ডিপোজিট) করুন।"
            )
            await render_screen(
                call,
                insufficient_text,
                reply_markup=get_buy_confirm_kb(prod_id, price, round(price / live_rate, 2), tier=tier, refs_needed=refs_needed, user_pts=user_pts),
                parse_mode="HTML"
            )
            return
        
    # 2. Deduct Balance or Points
    if currency == "REF":
        deducted = db.deduct_referral_points(user_id, price)
        if not deducted:
            await call.answer("❌ পয়েন্ট কাটতে সমস্যা হয়েছে!", show_alert=True)
            return
    else:
        deducted = db.deduct_user_balance(user_id, price, currency)
        if not deducted:
            await call.answer("❌ ব্যালেন্স কাটতে সমস্যা হয়েছে!", show_alert=True)
            return

    # 3. Check Stock or Access Delivery according to Tier
    delivery_data = ""
    if tier == "channel" or (tier == "default" and prod["product_type"] == "channel_link"):
        channel_id = prod.get("channel_id") or ""
        if channel_id:
            delivery_data = await generate_single_use_invite_link(bot, channel_id, prod["title"])
        elif prod.get("drive_link"):
            delivery_data = prod["drive_link"]
        else:
            delivery_data = "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অর্ডারের ইনভাইট লিংক পাঠাবে।"
    elif tier == "account" or (tier == "default" and prod["product_type"] == "stock_account"):
        item = db.pop_stock_item(prod_id, user_id)
        if item:
            delivery_data = item
        elif prod.get("drive_link"):
            delivery_data = prod["drive_link"]
        else:
            delivery_data = "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অ্যাকাউন্টের অ্যাক্সেস তথ্য দ্রুত পাঠাবে।"
    elif prod["product_type"] == "drive_link":
        delivery_data = prod.get("drive_link") or "https://drive.google.com"
    else:
        delivery_data = "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অর্ডারের জন্য যোগাযোগ করবে।"
        
    # 4. Record Order
    order_id = db.record_order(
        user_id=user_id,
        product_id=prod_id,
        product_title=prod["title"],
        product_type=f"{prod['product_type']}:{tier}" if tier != "default" else prod["product_type"],
        amount_paid=price,
        currency=currency,
        delivery_content=delivery_data,
        is_reseller_order=1 if is_reseller else 0,
        savings_bdt=savings if currency in ["BDT", "REF"] else 0.0,
        savings_usd=savings if currency == "USD" else 0.0,
        access_tier=tier
    )
    
    if is_reseller:
        db.increment_reseller_sale(user_id)
        if applied_vip_pass_id:
            db.record_vip_pass_usage(applied_vip_pass_id)
            
        # Automatic Race Challenge Target Check!
        win = db.check_and_claim_challenge_reward(user_id)
        if win:
            try:
                win_text = (
                    "🎉🏆🍾 **বিজয়ীর মুকুট! আপনি সেলস চ্যালেঞ্জ জয় করেছেন!** 🍾🏆🎉\n\n"
                    f"অবিশ্বাস্য গতিতে আপনি সবার আগে এই মাসের **{win['target_sales']} টি সেলস** সম্পূর্ণ করে "
                    f"**#{win['rank']} নম্বর বিজয়ী স্লট** দখল করেছেন!\n\n"
                    "🎁 **আপনার এক্সক্লুসিভ রিওয়ার্ড পাস আনলক হয়েছে:**\n"
                    f"• 🎟️ কুপন কোড: `{win['coupon_code']}`\n"
                    f"• 💥 অতিরিক্ত ছাড়: `৳{win['discount_bdt']:.0f} BDT` (প্রতিটি কেনাকাটায় পাইকারি রেটের চেয়েও কমে!)\n"
                    f"• ⏳ মেয়াদ: `{win['days_valid']} দিন`\n"
                    f"• 📦 মোট ব্যবহার সীমা: `{win['max_uses']} টি অর্ডার`\n\n"
                    "⚡ এখন থেকে আপনার প্রতিটি অর্ডারে স্বয়ংক্রিয়ভাবে এই বিশেষ ছাড় বাদ যাবে! অভিনন্দন!"
                )
                await bot.send_message(chat_id=user_id, text=win_text, parse_mode="Markdown")
            except Exception:
                pass

            race_admin_alert = (
                "🔥 **চ্যালেঞ্জ বিজয়ী অ্যালার্ট! (Race Winner Alert)** 🏆\n\n"
                f"👤 রিসেলার: {win['first_name']} (@{win.get('username') or 'N/A'})\n"
                f"🆔 আইডি: `{user_id}` [{win['reseller_code']}]\n"
                f"🎯 সম্পন্ন সেলস: `{win['sales_at_win']} / {win['target_sales']} টি`\n"
                f"🎖️ দখলকৃত স্লট: **#{win['rank']} বিজয়ী**\n"
                f"⚡ অবশিষ্ট স্লট: `{win['remaining_slots']} / {win['max_slots']} টি`\n\n"
                f"রিসেলারের জন্য ৳{win['discount_bdt']:.0f} ছাড়ের ভিআইপি পাস আনলক হয়েছে!"
            )
            for admin_id in ADMIN_IDS:
                if admin_id > 0:
                    try:
                        await bot.send_message(chat_id=admin_id, text=race_admin_alert, parse_mode="Markdown")
                    except Exception:
                        pass
        
    await call.answer("🎉 অর্ডার সফল হয়েছে!", show_alert=True)
    
    lang = db.get_user_language(user_id)
    if currency == "REF":
        success_text = (
            "🎉 <b>রেফারেল পয়েন্ট দিয়ে অর্ডার সফল হয়েছে!</b>\n\n"
            f"📦 <b>কোর্স:</b> {html.escape(prod['title'])}\n"
            f"💎 <b>পরিশোধিত পয়েন্ট:</b> <code>{price} Pts</code> (মূল্য: ৳{int(reg_bdt)} BDT)\n"
            f"🆔 <b>অর্ডার আইডি:</b> <code>#{order_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>আপনার ডেলিভারি তথ্য / এক্সেস ডাটা:</b>\n"
            f"<pre>{html.escape(delivery_data)}</pre>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <i>আপনার অর্ডারটি প্রোফাইলের 'My Purchases' এ স্থায়ীভাবে সংরক্ষিত থাকবে।</i>"
        )
    else:
        success_text = t(
            "order_success",
            lang,
            order_id=order_id,
            title=html.escape(prod['title']),
            amount=price,
            currency=currency,
            delivery_data=html.escape(delivery_data)
        )
    if tier == "channel":
        success_text += "\n🏷️ <b>অ্যাক্সেস প্যাকেজ:</b> 📢 VIP Channel Access"
    elif tier == "account":
        success_text += "\n🏷️ <b>অ্যাক্সেস প্যাকেজ:</b> 🔐 Personal Account Access"
        
    from keyboards.user_kb import make_custom_button
    order_done_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text="📜 My Orders (অর্ডার সমূহ)", callback_data="nav_orders", emoji_key="orders"),
            make_custom_button(text="🛍️ More Courses (আরও কোর্স)", callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")
        ]
    ])
    await render_screen(call, success_text, reply_markup=order_done_kb, parse_mode="HTML")
    
    # 5. Referral Commission Credit
    if currency == "BDT" and price > 0:
        ref_reward = db.credit_referral_reward(user_id, price)
        if ref_reward:
            try:
                ref_msg = (
                    "🎁 **রেফারেল বোনাস অর্জিত হয়েছে!**\n\n"
                    f"আপনার রেফারেল লিংকের মাধ্যমে {ref_reward['buyer_name']} একটি সফল অর্ডার সম্পন্ন করেছেন।\n"
                    f"💰 অর্জিত কমিশন: `+৳{ref_reward['bonus_amount']:.2f} BDT` আপনার ওয়ালেটে যুক্ত করা হয়েছে!"
                )
                await bot.send_message(chat_id=ref_reward["referrer_id"], text=ref_msg, parse_mode="Markdown")
            except Exception:
                pass

    # 6. Notify Admin Instantly with interactive action buttons
    buyer = db.get_user(user_id) or {}
    order_payload = {
        "id": order_id,
        "product_title": prod['title'],
        "product_type": prod['product_type'],
        "amount_paid": price,
        "currency": currency,
        "is_reseller_order": bool(is_reseller),
        "remaining_balance": buyer.get("balance_bdt", 0.0)
    }
    user_payload = {
        "id": user_id,
        "full_name": call.from_user.full_name,
        "username": call.from_user.username
    }
    await notify_admin_order(bot, order_payload, user_payload)

@router.callback_query(F.data == "out_of_stock")
async def handle_out_of_stock(call: CallbackQuery):
    await call.answer("❌ এই আইটেমটি বর্তমানে স্টকে নেই। শীঘ্রই রিস্টক করা হবে!", show_alert=True)
