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
from utils.i18n import t, localize_item_name
from utils.notifier import notify_admin_order
from utils.emojis import em_tag

router = Router()

from utils.ui_nav import render_screen, safe_switch_screen, render_safe_html_text, get_cached_bot_info

class BuyCouponState(StatesGroup):
    waiting_for_code = State()

@router.message(F.text.in_([
    "Browse Courses (কোর্স সমূহ)", "🎓 Browse Courses (কোর্স সমূহ)", "Browse Courses", "🎓 Browse Courses", 
    "🎓 কোর্স ভল্ট (Courses)", "কোর্স ভল্ট (Courses)", "🎓 কোর্স ভল্ট", "কোর্স ভল্ট",
    "कोर्सेस देखें (Courses)", "🎓 कोर्सेस देखें (Courses)", "কোর্স সমূহ", "কোর্স", "Courses"
]))
async def handle_browse_courses(message: Message):
    cats = db.get_categories_by_type("course")
    lang = db.get_user_language(message.from_user.id)
    text = t("shop_courses_text", lang)
    await message.answer(text, reply_markup=get_categories_kb(cats, "course", lang), parse_mode="HTML")

@router.message(F.text.in_([
    "Digital Tools & Accounts", "⚡ Digital Tools & Accounts", "ডিজিটাল টুলস (Tools & Accounts)", "⚡ ডিজিটাল টুলস (Tools & Accounts)", "ডিজিটাল টুल्स (Tools & Accounts)", "⚡ ডিজিটাল টুल्स (Tools & Accounts)", "डिजिटल टूल्स (Tools & Accounts)", "⚡ डिजिटल टूल्स (Tools & Accounts)"
]))
async def handle_browse_digital(message: Message):
    cats = db.get_categories_by_type("digital")
    lang = db.get_user_language(message.from_user.id)
    text = t("shop_digital_text", lang)
    await message.answer(text, reply_markup=get_categories_kb(cats, "digital", lang), parse_mode="HTML")

@router.callback_query(F.data == "back_cats")
async def handle_back_cats(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    cats = db.get_categories(parent_id=None)
    lang = db.get_user_language(call.from_user.id)
    text = t("shop_all_cats_text", lang)
    await render_screen(call, text, reply_markup=get_categories_kb(cats, "all", lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat:"))
async def handle_category_select(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    cat = db.get_category(cat_id)
    lang = db.get_user_language(call.from_user.id)
    if not cat:
        err_msg = "Category not found!" if lang in ["en", "hi", "ur"] else "ক্যাটাগরি পাওয়া যায়নি!"
        await call.answer(err_msg, show_alert=True)
        return
        
    await call.answer()
    em_cat = "📁"
    clean_cat_name = localize_item_name(cat['name'], lang)
    has_lead_emoji = any(ord(c) > 10000 for c in clean_cat_name[:3]) if clean_cat_name else False
    cat_header = clean_cat_name if has_lead_emoji else f"{em_cat} {clean_cat_name}"
    
    box_border = "━━━━━━━━━━━━━━━━━━━━"
    # Check if this category has subcategories
    if db.has_subcategories(cat_id):
        subcats = db.get_subcategories(cat_id)
        sub_prompt = t("subcat_selector_prompt", lang)
        text = (
            f"{box_border}\n"
            f"<b>{html.escape(cat_header)}</b>\n"
            f"{box_border}\n\n"
            f"{sub_prompt}\n"
            f"{box_border}"
        )
        await render_screen(call, text, reply_markup=get_subcategories_kb(subcats, cat_id, lang), parse_mode="HTML")
        return

    # Direct category products
    products = db.get_products_by_category(cat_id)
    if not products:
        no_prod_text = t("cat_no_products", lang)
        text = (
            f"{box_border}\n"
            f"<b>{html.escape(cat_header)}</b>\n"
            f"{box_border}\n\n"
            f"{no_prod_text}\n"
            f"{box_border}"
        )
        from utils.emojis import make_custom_button
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                make_custom_button(text=t("btn_back_cats", lang), callback_data="back_cats", emoji_key="back"),
                make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
            ]
        ])
        await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")
        return
        
    count_prompt = t("cat_products_count_prompt", lang, count=len(products))
    text = (
        f"{box_border}\n"
        f"<b>{html.escape(cat_header)}</b>\n"
        f"{box_border}\n\n"
        f"{count_prompt}\n"
        f"{box_border}"
    )
    await render_screen(call, text, reply_markup=get_products_kb(products, cat_id, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("subcat:"))
async def handle_subcategory_select(call: CallbackQuery):
    subcat_id = int(call.data.split(":")[1])
    subcat = db.get_category(subcat_id)
    if not subcat:
        lang = db.get_user_language(call.from_user.id)
        await call.answer(t("catalog_subcat_not_found_alert", lang), show_alert=True)
        return
        
    await call.answer()
    em_cat = em_tag("category", "📁")
    lang = db.get_user_language(call.from_user.id)
    parent_cat = db.get_category(subcat.get("parent_id")) if subcat.get("parent_id") else None
    parent_clean = localize_item_name(parent_cat['name'], lang) if parent_cat else ""
    parent_name = f"{parent_clean} ❯ " if parent_clean else ""
    subcat_clean = localize_item_name(subcat['name'], lang)
    
    products = db.get_products_by_subcategory(subcat_id)
    from utils.emojis import make_custom_button
    box_border = "━━━━━━━━━━━━━━━━━━━━"
    if not products:
        empty_text = t("subcat_empty_notice", lang)
        text = (
            f"{box_border}\n"
            f"<b>{parent_name}{html.escape(subcat_clean)}</b>\n"
            f"{box_border}\n\n"
            f"{empty_text}\n"
            f"{box_border}"
        )
        parent_id = subcat.get('parent_id')
        back_cb = f"cat:{parent_id}" if parent_id else "back_cats"
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                make_custom_button(text=t("btn_back_subcats", lang), callback_data=back_cb, emoji_key="back"),
                make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
            ]
        ])
        await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")
        return
        
    count_prompt = t("cat_products_count_prompt", lang, count=len(products))
    text = (
        f"{box_border}\n"
        f"<b>{parent_name}{html.escape(subcat_clean)}</b>\n"
        f"{box_border}\n\n"
        f"{count_prompt}\n"
        f"{box_border}"
    )
    await render_screen(call, text, reply_markup=get_products_kb(products, category_id=subcat.get("parent_id", subcat_id), subcategory_id=subcat_id, parent_id=subcat.get("parent_id"), lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("prod:"))
async def handle_product_detail(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    if not prod:
        err_msg = "Product not found!" if lang in ["en", "hi", "ur"] else "প্রোডাক্ট পাওয়া যায়নি!"
        await call.answer(err_msg, show_alert=True)
        return
        
    await call.answer()
    
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    # Check Stock
    is_in_stock_flag = bool(prod.get("is_in_stock", 1) if prod.get("is_in_stock") is not None else 1)
    if not is_in_stock_flag:
        in_stock = False
        stock_str = t("product_stock_out", lang)
    elif prod["product_type"] == "stock_account":
        stock_cnt = db.get_stock_count(prod_id)
        if stock_cnt > 0:
            in_stock = True
            stock_str = t("product_stock_in", lang, count=stock_cnt)
        elif prod.get("drive_link") and ("http" in prod["drive_link"] or ":" in prod["drive_link"]):
            in_stock = True
            stock_str = t("product_stock_instant", lang)
        else:
            in_stock = False
            stock_str = t("product_stock_out", lang)
    else:
        in_stock = True
        stock_str = t("product_stock_instant", lang)
        
    if lang in ["en", "hi", "ur"]:
        type_labels = {
            "channel_link": "🔒 Private VIP Telegram Channel (1-Time Invite Link)",
            "dual_access": "🔥 Dual Package (VIP Channel & Personal Account Access)",
            "stock_account": "🔑 Ready-Made Account / License Key (Instant Delivery)",
            "drive_link": "☁️ Google Drive / Cloud Vault",
            "manual": "🛠️ Custom Setup / Activated on Your Mail"
        }
        sales_title = "Course Curriculum & Sales Page:"
        cat_title = "Category:"
        access_title = "Access Type:"
        stock_title = "Stock Status:"
        cta_text = "👉 <i>Click any button below for instant delivery:</i>"
    else:
        type_labels = {
            "channel_link": "🔒 প্রাইভেট ভিআইপি টেলিগ্রাম চ্যানেল (1-টাইম ইনভাইট লিংক)",
            "dual_access": "🔥 ডুয়েল প্যাকেজ (ভিআইপি চ্যানেল ও পার্সোনাল অ্যাকাউন্ট অ্যাক্সেস)",
            "stock_account": "🔑 রেডিমেড অ্যাকাউন্ট / লাইসেন্স কি (ইনস্ট্যান্ট ডেলিভারি)",
            "drive_link": "☁️ গুগল ড্রাইভ / ক্লাউড ভল্ট",
            "manual": "🛠️ কাস্টম সেটআপ / আপনার মেইলে অ্যাক্টিভেশন"
        }
        sales_title = "কোর্স কারিকুলাম ও সেলস পেজ:"
        cat_title = "ক্যাটাগরি:"
        access_title = "অ্যাক্সেস টাইপ:"
        stock_title = "স্টক অবস্থা:"
        cta_text = "👉 <i>ইনস্ট্যান্ট অ্যাক্সেস নিতে নিচের বাটনে ক্লিক করুন:</i>"

    ch_p = float(prod.get("price_channel_bdt") or 0)
    acc_p = float(prod.get("price_account_bdt") or 0)
    main_p = float(prod["price_bdt"] or 0)
    eff_p = ch_p if ch_p > 0 else (acc_p if acc_p > 0 else main_p)

    reg_bdt = int(eff_p)
    reg_usd = prod["price_usd"] or round(reg_bdt / get_live_usd_rate(), 2)
    res_bdt = int(prod["reseller_price_bdt"]) if (prod.get("reseller_price_bdt") and float(prod["reseller_price_bdt"]) > 0) else int(reg_bdt * 0.70)
    res_usd = prod["reseller_price_usd"] if (prod.get("reseller_price_usd") and float(prod["reseller_price_usd"]) > 0) else round(reg_usd * 0.70, 2)
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
        sales_info = f"🌐 <b>{sales_title}</b>\n<code>{html.escape(prod['sales_page_url'])}</code>\n\n"

    has_dual = (ch_p > 0 and acc_p > 0)
    live_rate = get_live_usd_rate()
    if has_dual:
        ch_b = ch_p
        ch_u = float(prod.get("price_channel_usd") or round(ch_b / live_rate, 2))
        acc_b = acc_p
        acc_u = float(prod.get("price_account_usd") or round(acc_b / live_rate, 2))
        
        if lang in ["en", "hi", "ur"]:
            if is_reseller:
                r_ch_b = float(prod.get("reseller_price_channel_bdt") or round(ch_b * 0.70, 2))
                r_acc_b = float(prod.get("reseller_price_account_bdt") or round(acc_b * 0.70, 2))
                price_section = (
                    f"💳 <b>Package Options & Wholesale Rates:</b>\n"
                    f"• 📢 <b>VIP Channel:</b> <b>৳{int(r_ch_b)} BDT</b> (${round(r_ch_b/live_rate, 2)} USD) <i>(Retail: ৳{int(ch_b)})</i>\n"
                    f"• 🔐 <b>Personal Account:</b> <b>৳{int(r_acc_b)} BDT</b> (${round(r_acc_b/live_rate, 2)} USD) <i>(Retail: ৳{int(acc_b)})</i>\n\n"
                    f"🎁 <b>Unlock Free with Referrals:</b> <code>{refs_needed} referrals</code>\n"
                    f"📊 <b>Your Balance Progress:</b> <code>{prog_bar}</code> <i>(Balance: ৳{user_bal_bdt:.0f} / ${user_bal_bdt/live_rate:.2f})</i>"
                )
            else:
                price_section = (
                    f"💳 <b>Access Packages & Price List:</b>\n"
                    f"• 📢 <b>VIP Channel:</b> <b>৳{int(ch_b)} BDT</b> (${ch_u} USD)\n"
                    f"• 🔐 <b>Personal Account:</b> <b>৳{int(acc_b)} BDT</b> (${acc_u} USD)\n\n"
                    f"🎁 <b>Unlock Free with Referrals:</b> <code>{refs_needed} referrals</code>\n"
                    f"📊 <b>Your Balance Progress:</b> <code>{prog_bar}</code> <i>(Balance: ৳{user_bal_bdt:.0f} / ${user_bal_bdt/live_rate:.2f})</i>"
                )
        else:
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
    elif ch_p > 0 and acc_p <= 0:
        ch_b = ch_p
        ch_u = float(prod.get("price_channel_usd") or round(ch_b / live_rate, 2))
        r_ch_b = float(prod.get("reseller_price_channel_bdt") or round(ch_b * 0.70, 2))
        charge_bdt = r_ch_b if is_reseller else ch_b
        refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
        rem_bdt = max(0.0, charge_bdt - user_bal_bdt)
        rem_refs = max(1, int(rem_bdt / t1_bonus)) if t1_bonus > 0 else 1
        
        if is_reseller:
            price_section = (
                f"💳 <b>প্যাকেজ অপশন (ভিআইপি চ্যানেল অ্যাক্সেস):</b>\n"
                f"• 📢 <b>VIP Channel Access:</b> <b>৳{int(r_ch_b)} BDT</b> (${round(r_ch_b/live_rate, 2)}) <i>(খুচরা ৳{int(ch_b)})</i>\n\n"
                f"🎁 <b>রেফারেল দিয়ে ফ্রি নিন:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>"
            )
        else:
            price_section = (
                f"💳 <b>প্যাকেজ অপশন (ভিআইপি চ্যানেল অ্যাক্সেস):</b>\n"
                f"• 📢 <b>VIP Channel Access:</b> <b>৳{int(ch_b)} BDT</b> (${ch_u} USD)\n\n"
                f"🎁 <b>অথবা রেফারেল দিয়ে সম্পূর্ণ ফ্রি:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(বর্তমান ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>\n"
                f"🎯 <i>(আর মাত্র ৳{int(rem_bdt)} বা {rem_refs} টি রেফারেল করলেই ফ্রি আনলক!)</i>"
            )
        active_prod = dict(prod)
        active_prod["price_bdt"] = ch_b
        active_prod["price_usd"] = ch_u
    elif acc_p > 0 and ch_p <= 0:
        acc_b = acc_p
        acc_u = float(prod.get("price_account_usd") or round(acc_b / live_rate, 2))
        r_acc_b = float(prod.get("reseller_price_account_bdt") or round(acc_b * 0.70, 2))
        charge_bdt = r_acc_b if is_reseller else acc_b
        refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
        rem_bdt = max(0.0, charge_bdt - user_bal_bdt)
        rem_refs = max(1, int(rem_bdt / t1_bonus)) if t1_bonus > 0 else 1

        if is_reseller:
            price_section = (
                f"💳 <b>প্যাকেজ অপশন (পার্সোনাল একাউন্ট / ড্রাইভ):</b>\n"
                f"• 🔐 <b>Personal Account / Drive:</b> <b>৳{int(r_acc_b)} BDT</b> (${round(r_acc_b/live_rate, 2)}) <i>(খুচরা ৳{int(acc_b)})</i>\n\n"
                f"🎁 <b>রেফারেল দিয়ে ফ্রি নিন:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>"
            )
        else:
            price_section = (
                f"💳 <b>প্যাকেজ অপশন (পার্সোনাল একাউন্ট / ড্রাইভ):</b>\n"
                f"• 🔐 <b>Personal Account / Drive:</b> <b>৳{int(acc_b)} BDT</b> (${acc_u} USD)\n\n"
                f"🎁 <b>অথবা রেফারেল দিয়ে সম্পূর্ণ ফ্রি:</b> মাত্র <code>{refs_needed} টি</code> রেফারেল!\n"
                f"📊 <b>আপনার ব্যালেন্স প্রগ্রেস:</b> <code>{prog_bar}</code> <i>(বর্তমান ব্যালেন্স: ৳{user_bal_bdt:.0f})</i>\n"
                f"🎯 <i>(আর মাত্র ৳{int(rem_bdt)} বা {rem_refs} টি রেফারেল করলেই ফ্রি আনলক!)</i>"
            )
        active_prod = dict(prod)
        active_prod["price_bdt"] = acc_b
        active_prod["price_usd"] = acc_u
    elif is_reseller:
        if lang in ["en", "hi", "ur"]:
            price_section = (
                f"💎 <b>Wholesale Reseller Rate:</b> <b>৳{res_bdt} BDT</b> | <b>${res_usd} USD</b>\n"
                f"🏷️ <i>(Retail: ৳{reg_bdt} — You save ৳{reg_bdt - res_bdt}!)</i>\n"
                f"🎁 <b>Unlock Free with Referrals:</b> <code>{refs_needed} referrals</code>\n"
                f"📊 <b>Balance Progress:</b> <code>{prog_bar}</code> <i>(Balance: ৳{user_bal_bdt:.0f} / ${user_bal_bdt/live_rate:.2f})</i>"
            )
        else:
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
        if lang in ["en", "hi", "ur"]:
            price_section = (
                f"💰 <b>Price:</b> <b>৳{reg_bdt} BDT</b> or <b>${reg_usd} USD</b>\n"
                f"🎁 <b>Or Unlock Free with Referrals:</b> <code>{refs_needed} referrals</code>\n"
                f"📊 <b>Balance Progress:</b> <code>{prog_bar}</code> <i>(Balance: ৳{user_bal_bdt:.0f} / ${user_bal_bdt/live_rate:.2f})</i>"
            )
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
            p_name = localize_item_name(parent['name'], lang)
            sc_name = localize_item_name(subcat['name'], lang)
            category_label = f"📁 <b>{cat_title}</b> <code>{html.escape(p_name)} ❯ {html.escape(sc_name)}</code>\n"
        elif subcat:
            sc_name = localize_item_name(subcat['name'], lang)
            category_label = f"📁 <b>{cat_title}</b> <code>{html.escape(sc_name)}</code>\n"
    elif prod.get("category_id"):
        cat = db.get_category(prod["category_id"])
        if cat:
            c_name = localize_item_name(cat['name'], lang)
            category_label = f"📁 <b>{cat_title}</b> <code>{html.escape(c_name)}</code>\n"

    em_crs = em_tag("courses", "🎓")
    em_box = em_tag("box", "📦")
    clean_title = localize_item_name(prod['title'], lang)
    detail_text = (
        f"{em_crs} <b>{html.escape(clean_title)}</b> {em_crs}\n\n"
        f"📝 <b>{sales_title if not prod.get('sales_page_url') else 'Curriculum & Overview:'}</b>\n{render_safe_html_text(prod['description'])}\n\n"
        f"{sales_info}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{category_label}"
        f"{em_box} <b>{access_title}</b> {type_labels.get(prod['product_type'], 'Digital')}\n"
        f"📊 <b>{stock_title}</b> {stock_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{price_section}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{cta_text}"
    )
    
    photo_id = prod.get("photo_file_id")
    await safe_switch_screen(
        call,
        detail_text,
        reply_markup=get_product_detail_kb(active_prod, in_stock, lang, user_id=user_id),
        photo_url=photo_id,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("locked_account_tier:"))
async def handle_locked_account_tier(call: CallbackQuery):
    lang = db.get_user_language(call.from_user.id)
    alert_text = (
        "🔒 Account Access is Restricted!\n\n"
        "This option is reserved exclusively for Elite VIP Resellers.\n\n"
        "👉 You can purchase the VIP Channel Access, or contact Admin to upgrade your tier."
        if lang in ["en", "hi", "ur"] else
        "🔒 অ্যাকাউন্ট অ্যাক্সেস সংরক্ষিত!\n\n"
        "এই অপশনটি শুধুমাত্র ভেরিফাইড Elite VIP রিসেলার পার্টনারদের জন্য।\n\n"
        "👉 আপনি ভিআইপি চ্যানেল অ্যাক্সেস নিতে পারেন, অথবা এলিট টায়ারে আপগ্রেডের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।"
    )
    await call.answer(alert_text, show_alert=True)

@router.callback_query(F.data.startswith("locked_channel_tier:"))
async def handle_locked_channel_tier(call: CallbackQuery):
    lang = db.get_user_language(call.from_user.id)
    alert_text = (
        "🔒 Channel Access is currently disabled for your account."
        if lang in ["en", "hi", "ur"] else
        "🔒 আপনার অ্যাকাউন্টে চ্যানেল অ্যাক্সেস সাময়িকভাবে বন্ধ রয়েছে।"
    )
    await call.answer(alert_text, show_alert=True)

@router.callback_query(F.data.startswith("claim_ref:"))
async def handle_claim_ref(call: CallbackQuery, bot: Bot):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        lang = db.get_user_language(call.from_user.id)
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    lang = db.get_user_language(user_id)
    clean_title = localize_item_name(prod['title'], lang)

    ch_p = float(prod.get("price_channel_bdt") or 0)
    acc_p = float(prod.get("price_account_bdt") or 0)
    eff_bdt = ch_p if (ch_p > 0 and acc_p <= 0) else (acc_p if (acc_p > 0 and ch_p <= 0) else float(prod.get("price_bdt") or 0))
    if eff_bdt <= 0 and (ch_p > 0 or acc_p > 0):
        eff_bdt = ch_p if ch_p > 0 else acc_p
    reg_bdt = eff_bdt
    res_bdt = float(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else round(reg_bdt * 0.70, 2)
    charge_bdt = res_bdt if is_reseller else reg_bdt
    user_bal = float(user.get("balance_bdt") or 0.0)
    user_pts = user.get("referral_points", 0) or 0

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1

    # If user has enough referral points OR balance, offer instant unlock!
    if user_pts >= refs_needed or user_bal >= charge_bdt:
        from utils.emojis import make_custom_button
        if lang in ["en", "hi", "ur"]:
            pay_confirm_text = (
                f"🎉 <b>Congratulations! You have sufficient resources!</b>\n\n"
                f"📦 <b>Course:</b> {html.escape(clean_title)}\n"
                f"💰 <b>Required:</b> <code>৳{int(charge_bdt)} BDT</code> (or <b>{refs_needed} Pts</b>)\n"
                f"💳 <b>Your BDT Balance:</b> <code>৳{user_bal:.2f} BDT</code>\n"
                f"💎 <b>Your Referral Points:</b> <code>{user_pts} Pts</code>\n\n"
                f"👇 Choose how you want to unlock this item:"
            )
        else:
            pay_confirm_text = (
                f"🎉 <b>অভিনন্দন! আপনার অ্যাকাউন্টে পর্যাপ্ত রিসোর্স রয়েছে!</b>\n\n"
                f"📦 <b>কোর্স:</b> {html.escape(clean_title)}\n"
                f"💰 <b>প্রয়োজনীয় মূল্য:</b> <code>৳{int(charge_bdt)} BDT</code> (বা <b>{refs_needed} Pts</b>)\n"
                f"💳 <b>আপনার BDT ব্যালেন্স:</b> <code>৳{user_bal:.2f} BDT</code>\n"
                f"💎 <b>আপনার রেফারেল পয়েন্ট:</b> <code>{user_pts} Pts</code>\n\n"
                f"👇 আপনি যেভাবে কোর্সটি পেতে চান নিচের বাটন চাপুন:"
            )
        buttons = []
        if user_pts >= refs_needed:
            btn_txt = f"🎁 Pay with Referrals ({refs_needed} Pts)" if lang in ["en", "hi", "ur"] else f"🎁 রেফারেল পয়েন্ট দিয়ে নিন ({refs_needed} Pts)"
            buttons.append([
                make_custom_button(
                    text=btn_txt,
                    callback_data=f"confirm_buy:{prod_id}:REF",
                    emoji_key="free_claim"
                )
            ])
        if user_bal >= charge_bdt:
            bal_txt = f"💰 Pay with Balance (৳{int(charge_bdt)})" if lang in ["en", "hi", "ur"] else f"💰 ওয়ালেট দিয়ে নিন (৳{int(charge_bdt)})"
            buttons.append([
                make_custom_button(
                    text=bal_txt,
                    callback_data=f"confirm_buy:{prod_id}:BDT",
                    emoji_key="check"
                )
            ])
        buttons.append([
            make_custom_button(text=t("btn_back", lang), callback_data=f"prod:{prod_id}", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
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

    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}_c{prod_id}"

    t2_pct = float(db.get_setting("referral_t2_percent", "50.0"))
    welcome_bonus = float(db.get_setting("referral_welcome_bonus", "5.0"))
    if lang in ["en", "hi", "ur"]:
        gift_str = f"▫️ 🎉 New friends join & receive: **৳{welcome_bonus:.0f} BDT** welcome bonus\n" if welcome_bonus > 0 else ""
        progress_modal = (
            "🌟 **Unlock this Course Completely FREE with Referrals!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 **Course:** {clean_title}\n"
            f"💰 **Regular Price:** **৳{int(charge_bdt)} BDT** (or **{refs_needed} Points**)\n"
            f"💳 **Wallet Balance:** **৳{user_bal:.2f} BDT**\n"
            f"💎 **Referral Points:** **{user_pts} Pts** (Needed: **{refs_needed} Pts**)\n\n"
            f"⚡ **Unlock Progress:** `{prog_bar}`\n"
            f"🎯 **Target:** Only **{rem_refs} more referrals** to unlock for free!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 **Your Unique Course Invite Link (Tap to copy):**\n"
            f"`{ref_link}`\n\n"
            "💎 **Exclusive Referral Benefits:**\n"
            f"▫️ 👤 Direct Referral Bonus: **+1 Point (+৳{t1_bonus:.0f} BDT)** instant\n"
            f"▫️ 👥 Passive Team Commission: **+{t2_pct:.0f}%** lifetime\n"
            f"{gift_str}"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 **Tap below to copy or share directly:**"
        )
    else:
        gift_str = f"▫️ 🎉 নতুন ফ্রেন্ড জয়েন করলেই পাবে: **৳{welcome_bonus:.0f} BDT** ওয়েলকাম বোনাস\n" if welcome_bonus > 0 else ""
        progress_modal = (
            "🌟 **রেফারেল দিয়ে সম্পূর্ণ ফ্রিতে কোর্সটি আনলক করুন!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 **কোর্সের নাম:** {clean_title}\n"
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
    await render_screen(call, progress_modal, reply_markup=get_referral_progress_kb(prod_id, bot_username, user_id, lang=lang), parse_mode="Markdown")

@router.callback_query(F.data.startswith("gen_course_ref:"))
async def handle_gen_course_ref(call: CallbackQuery, bot: Bot):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        lang = db.get_user_language(call.from_user.id)
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    course_link = f"https://t.me/{bot_username}?start=ref_{user_id}_c{prod_id}"
    lang = db.get_user_language(user_id)
    clean_title = localize_item_name(prod['title'], lang)
    
    await call.answer()
    
    if lang in ["en", "hi", "ur"]:
        text = (
            "🔗 <b>Special Referral Link for this Course</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 <b>Course:</b> {html.escape(clean_title)}\n"
            f"🔗 <b>Your Personal Course Link:</b>\n"
            f"<code>{course_link}</code>\n"
            "<i>(Tap to copy link or use button below)</i>\n\n"
            "💡 <b>Benefits:</b>\n"
            "• Friends clicking this link land directly on this course page.\n"
            "• Track how many friends joined through this course.\n"
            "• Earn reward points credited immediately when friends join!\n\n"
            "👇 Tap below to copy or share directly:"
        )
    else:
        text = (
            "🔗 <b>এই কোর্সের স্পেশাল রেফারেল লিংক</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎓 <b>কোর্স:</b> {html.escape(clean_title)}\n"
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
    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    course_link = f"https://t.me/{bot_username}?start=ref_{call.from_user.id}_c{prod_id}"
    lang = db.get_user_language(call.from_user.id)
    alert_txt = f"📋 Referral Link:\n{course_link}" if lang in ["en", "hi", "ur"] else f"📋 রেফারেল লিংক:\n{course_link}"
    await call.answer(alert_txt, show_alert=True)

@router.callback_query(F.data.startswith("buy_tier_select:"))
async def handle_buy_tier_select(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    lang = db.get_user_language(call.from_user.id)
    if not prod:
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer(t("out_of_stock_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    is_reseller = user.get("is_reseller", 0) >= 1 if user else False
    lang = db.get_user_language(user_id)
    clean_title = localize_item_name(prod['title'], lang)
    
    live_rate = get_live_usd_rate()
    ch_raw = float(prod.get("price_channel_bdt") or 0)
    acc_raw = float(prod.get("price_account_bdt") or 0)

    # If only one tier is active (> 0), bypass dual selection directly to single checkout
    if ch_raw > 0 and acc_raw <= 0:
        call.data = f"buy_tier:{prod_id}:channel"
        await handle_buy_tier_chosen(call)
        return
    elif acc_raw > 0 and ch_raw <= 0:
        call.data = f"buy_tier:{prod_id}:account"
        await handle_buy_tier_chosen(call)
        return

    ch_bdt = ch_raw if ch_raw > 0 else float(prod.get("price_bdt") or 0)
    ch_usd = float(prod.get("price_channel_usd") or round(ch_bdt / live_rate, 2))
    acc_bdt = acc_raw if acc_raw > 0 else float(prod.get("price_bdt") or 0)
    acc_usd = float(prod.get("price_account_usd") or round(acc_bdt / live_rate, 2))
    
    if is_reseller:
        ch_bdt = float(prod.get("reseller_price_channel_bdt") or round(ch_bdt * 0.70, 2))
        ch_usd = round(ch_bdt / live_rate, 2)
        acc_bdt = float(prod.get("reseller_price_account_bdt") or round(acc_bdt * 0.70, 2))
        acc_usd = round(acc_bdt / live_rate, 2)
        
    await call.answer()
    
    text = t(
        "checkout_tier_intro",
        lang,
        title=html.escape(clean_title),
        ch_bdt=int(ch_bdt),
        ch_usd=ch_usd,
        acc_bdt=int(acc_bdt),
        acc_usd=acc_usd
    )
    from keyboards.user_kb import get_access_tier_selection_kb
    await render_screen(call, text, reply_markup=get_access_tier_selection_kb(prod_id, ch_bdt, ch_usd, acc_bdt, acc_usd, lang=lang, user_id=user_id), parse_mode="HTML")

@router.callback_query(F.data.startswith("buy_tier:"))
async def handle_buy_tier_chosen(call: CallbackQuery):
    parts = call.data.split(":")
    prod_id = int(parts[1])
    tier = parts[2] # 'channel' or 'account'
    
    prod = db.get_product(prod_id)
    lang = db.get_user_language(call.from_user.id)
    if not prod:
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer(t("out_of_stock_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    # Security Guard: Reseller Sell Permissions check
    if is_reseller:
        perms = db.get_user_permissions(user_id)
        if tier == "account" and not perms["can_sell_account"]:
            alert_text = (
                "🔒 Account Access is Restricted!\n\n"
                "This option is reserved exclusively for Elite VIP Resellers.\n\n"
                "👉 You can purchase VIP Channel Access, or contact Admin to upgrade."
                if lang in ["en", "hi", "ur"] else
                "🔒 অ্যাকাউন্ট অ্যাক্সেস সংরক্ষিত!\n\n"
                "এই অপশনটি শুধুমাত্র ভেরিফাইড Elite VIP রিসেলার পার্টনারদের জন্য।\n\n"
                "👉 আপনি ভিআইপি চ্যানেল অ্যাক্সেস নিতে পারেন, অথবা এলিট টায়ারে আপগ্রেডের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।"
            )
            await call.answer(alert_text, show_alert=True)
            return
        if tier == "channel" and not perms["can_sell_channel"]:
            alert_text = (
                "🔒 Channel Access is currently disabled for your account."
                if lang in ["en", "hi", "ur"] else
                "🔒 আপনার অ্যাকাউন্টে চ্যানেল অ্যাক্সেস সাময়িকভাবে বন্ধ রয়েছে।"
            )
            await call.answer(alert_text, show_alert=True)
            return

    lang = db.get_user_language(user_id)
    clean_title = localize_item_name(prod['title'], lang)

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
    
    if is_reseller:
        reseller_badge = "💎 <b>(Wholesale Reseller Discount Applied)</b>" if lang in ["en", "hi", "ur"] else "💎 <b>(রিসেলার পাইকারি ডিসকাউন্ট প্রযোজ্য)</b>"
    else:
        reseller_badge = ""

    vip_pass = db.get_active_reseller_vip_pass(user_id) if is_reseller else None
    if vip_pass:
        extra_bdt = float(vip_pass.get("discount_bdt", 0.0))
        charge_bdt = max(0, charge_bdt - int(extra_bdt))
        charge_usd = round(charge_bdt / live_rate, 2)
        if lang in ["en", "hi", "ur"]:
            reseller_badge = (
                f"💎 <b>(Regular Wholesale: ৳{int(res_bdt)})</b>\n"
                f"🏆 <b>[Top-Seller VIP Pass: -৳{int(extra_bdt)} Extra Off!]</b>\n"
                f"⏳ Valid for: <code>{vip_pass['days_left']} days</code> (Orders left: <code>{vip_pass['remaining_uses']}</code>)"
            )
        else:
            reseller_badge = (
                f"💎 <b>(রিসেলার সাধারণ পাইকারি: ৳{int(res_bdt)})</b>\n"
                f"🏆 <b>[টপ-সেলার রিওয়ার্ড: -৳{int(extra_bdt)} অতিরিক্ত ছাড়!]</b>\n"
                f"⏳ অফার মেয়াদ বাকি: <code>{vip_pass['days_left']} দিন</code> (অর্ডার বাকি: <code>{vip_pass['remaining_uses']} টি</code>)"
            )

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_pts = user.get("referral_points", 0) or 0

    await call.answer()
    
    tier_label = f"🏷️ <b>Selected Package:</b> {tier_title}\n" if lang in ["en", "hi", "ur"] else f"🏷️ <b>নির্বাচিত প্যাকেজ:</b> {tier_title}\n"
    text = t(
        "checkout_confirm_card",
        lang,
        title=html.escape(clean_title),
        tier_badge=tier_label,
        reseller_badge=reseller_badge,
        charge_bdt=int(charge_bdt),
        charge_usd=charge_usd,
        bal_bdt=user['balance_bdt'],
        bal_usd=user['balance_usd'],
        user_pts=user_pts,
        refs_needed=refs_needed
    )
    await render_screen(call, text, reply_markup=get_buy_confirm_kb(prod_id, charge_bdt, charge_usd, tier=tier, has_coupon=False, refs_needed=refs_needed, user_pts=user_pts, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("buy:"))
async def handle_buy_prompt(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    lang = db.get_user_language(call.from_user.id)
    if not prod:
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
    if prod.get("is_in_stock") is not None and prod.get("is_in_stock") == 0:
        await call.answer(t("out_of_stock_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    clean_title = localize_item_name(prod['title'], lang)
    ch_p = float(prod.get("price_channel_bdt") or 0)
    acc_p = float(prod.get("price_account_bdt") or 0)
    eff_p = ch_p if ch_p > 0 else (acc_p if acc_p > 0 else float(prod["price_bdt"] or 0))

    reg_bdt = int(eff_p)
    reg_usd = prod["price_usd"] or round(reg_bdt / get_live_usd_rate(), 2)
    res_bdt = int(prod["reseller_price_bdt"]) if (prod.get("reseller_price_bdt") and float(prod["reseller_price_bdt"]) > 0) else int(reg_bdt * 0.70)
    res_usd = prod["reseller_price_usd"] if (prod.get("reseller_price_usd") and float(prod["reseller_price_usd"]) > 0) else round(reg_usd * 0.70, 2)

    charge_bdt = res_bdt if is_reseller else reg_bdt
    charge_usd = res_usd if is_reseller else reg_usd
    
    if is_reseller:
        reseller_badge = "💎 <b>(Wholesale Reseller Discount Applied)</b>" if lang in ["en", "hi", "ur"] else "💎 <b>(রিসেলার ডিসকাউন্ট প্রযোজ্য)</b>"
    else:
        reseller_badge = ""

    # Check for active Reseller VIP Pass (Extra Top-Seller Reward Discount)
    vip_pass = db.get_active_reseller_vip_pass(user_id) if is_reseller else None
    if vip_pass:
        extra_bdt = float(vip_pass.get("discount_bdt", 0.0))
        charge_bdt = max(0, charge_bdt - int(extra_bdt))
        charge_usd = round(charge_bdt / get_live_usd_rate(), 2)
        if lang in ["en", "hi", "ur"]:
            reseller_badge = (
                f"💎 <b>(Regular Wholesale: ৳{res_bdt})</b>\n"
                f"🏆 <b>[Top-Seller VIP Pass: -৳{int(extra_bdt)} Extra Off!]</b>\n"
                f"⏳ Valid for: <code>{vip_pass['days_left']} days</code> (Orders left: <code>{vip_pass['remaining_uses']}</code>)"
            )
        else:
            reseller_badge = (
                f"💎 <b>(রিসেলার সাধারণ পাইকারি: ৳{res_bdt})</b>\n"
                f"🏆 <b>[টপ-সেলার রিওয়ার্ড: -৳{int(extra_bdt)} অতিরিক্ত ছাড়!]</b>\n"
                f"⏳ অফার মেয়াদ বাকি: <code>{vip_pass['days_left']} দিন</code> (অর্ডার বাকি: <code>{vip_pass['remaining_uses']} টি</code>)"
            )

    t1_bonus = float(db.get_setting("referral_t1_bonus", "10.0"))
    refs_needed = max(1, int(charge_bdt / t1_bonus)) if t1_bonus > 0 else 1
    user_pts = user.get("referral_points", 0) or 0

    await call.answer()
    
    text = t(
        "checkout_confirm_card",
        lang,
        title=html.escape(clean_title),
        tier_badge="",
        reseller_badge=reseller_badge,
        charge_bdt=charge_bdt,
        charge_usd=charge_usd,
        bal_bdt=user['balance_bdt'],
        bal_usd=user['balance_usd'],
        user_pts=user_pts,
        refs_needed=refs_needed
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
    
    lang = db.get_user_language(call.from_user.id)
    cancel_cb = f"buy_tier:{prod_id}:{tier}" if tier != "default" else f"buy:{prod_id}"
    text = t("coupon_start_prompt", lang)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data=cancel_cb),
            InlineKeyboardButton(text=t("btn_home", lang), callback_data="main_menu")
        ]
    ])
    await render_screen(call, text, reply_markup=cancel_kb, parse_mode="Markdown")

@router.message(BuyCouponState.waiting_for_code)
async def handle_apply_coupon_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    if not message.text:
        err_msg = "❌ Please send the coupon code as text:" if lang in ["en", "hi", "ur"] else "❌ অনুগ্রহ করে কুপন কোডটি টেক্সট আকারে লিখে পাঠান:"
        await message.answer(err_msg)
        return
        
    code = message.text.strip().upper()
    data = await state.get_data()
    prod_id = data.get("coupon_prod_id")
    tier = data.get("coupon_tier", "default")
    if not prod_id:
        await state.clear()
        expired_msg = "⚠️ Session expired. Please try again." if lang in ["en", "hi", "ur"] else "⚠️ সেশন মেয়াদোত্তীর্ণ। আবার চেষ্টা করুন।"
        await message.answer(expired_msg)
        return
        
    cancel_cb = f"buy_tier:{prod_id}:{tier}" if tier != "default" else f"buy:{prod_id}"
    coupon = db.get_coupon(code)
    if not coupon:
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data=cancel_cb)]
        ])
        await message.answer(t("coupon_invalid_alert", lang), reply_markup=cancel_kb, parse_mode="Markdown")
        return
        
    prod = db.get_product(prod_id)
    if not prod:
        await state.clear()
        return
        
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, message.from_user.username, message.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1
    clean_title = localize_item_name(prod['title'], lang)
    
    ch_p = float(prod.get("price_channel_bdt") or 0)
    acc_p = float(prod.get("price_account_bdt") or 0)
    if tier == "channel" or (tier == "default" and ch_p > 0 and acc_p <= 0):
        reg_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
        res_bdt = float(prod.get("reseller_price_channel_bdt") or round(reg_bdt * 0.70, 2))
    elif tier == "account" or (tier == "default" and acc_p > 0 and ch_p <= 0):
        reg_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
        res_bdt = float(prod.get("reseller_price_account_bdt") or round(reg_bdt * 0.70, 2))
    else:
        eff_p = ch_p if ch_p > 0 else (acc_p if acc_p > 0 else float(prod.get("price_bdt") or 0))
        reg_bdt = eff_p
        res_bdt = float(prod["reseller_price_bdt"]) if prod.get("reseller_price_bdt") else round(reg_bdt * 0.70, 2)
        
    base_bdt = res_bdt if is_reseller else reg_bdt
    discount_bdt = float(coupon.get("discount_bdt", 0.0))
    final_bdt = max(0.0, base_bdt - discount_bdt)
    final_usd = round(final_bdt / get_live_usd_rate(), 2)
    
    await state.clear()
    
    tier_label = f" ({'📢 VIP Channel' if tier == 'channel' else '🔐 Account Access'})" if tier != 'default' else ""
    confirm_text = t(
        "coupon_applied_card",
        lang,
        title=clean_title,
        tier_label=tier_label,
        code=code,
        discount_bdt=int(discount_bdt),
        final_bdt=int(final_bdt),
        final_usd=final_usd,
        bal_bdt=user['balance_bdt'],
        bal_usd=user['balance_usd']
    )
    
    buttons = [
        [
            InlineKeyboardButton(text=f"✅ Pay ৳{int(final_bdt)} (BDT)", callback_data=f"confirm_buy:{prod_id}:BDT:{tier}:{code}"),
            InlineKeyboardButton(text=f"✅ Pay ${final_usd} (USD)", callback_data=f"confirm_buy:{prod_id}:USD:{tier}:{code}")
        ],
        [
            InlineKeyboardButton(text=t("btn_add_balance", lang), callback_data="add_balance_shortcut")
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data=cancel_cb),
            InlineKeyboardButton(text=t("btn_home", lang), callback_data="main_menu")
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
    
    lang = db.get_user_language(call.from_user.id)
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer(t("catalog_prod_not_found_alert", lang), show_alert=True)
        return
        
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    is_reseller = user.get("is_reseller", 0) >= 1

    ch_p = float(prod.get("price_channel_bdt") or 0)
    acc_p = float(prod.get("price_account_bdt") or 0)
    is_channel_action = (tier == "channel" or (tier == "default" and (prod.get("product_type") == "channel_link" or (ch_p > 0 and acc_p <= 0))))
    is_account_action = (tier == "account" or (tier == "default" and (prod.get("product_type") in ["stock_account", "drive_link"] or (acc_p > 0 and ch_p <= 0))))

    # Security Guard: Reseller Sell Permissions check before deducting any money or points
    if is_reseller:
        perms = db.get_user_permissions(user_id)
        if is_account_action and not perms["can_sell_account"]:
            alert_msg = (
                "🔒 Account Access is Restricted!\nThis option is reserved for Elite VIP Resellers."
                if lang in ["en", "hi", "ur"] else
                "🔒 অ্যাকাউন্ট অ্যাক্সেস সংরক্ষিত!\nএই অপশনটি শুধুমাত্র ভেরিফাইড Elite VIP রিসেলারদের জন্য।"
            )
            await call.answer(alert_msg, show_alert=True)
            return
        if is_channel_action and not perms["can_sell_channel"]:
            alert_msg = (
                "🔒 Channel Access is currently disabled for your account."
                if lang in ["en", "hi", "ur"] else
                "🔒 আপনার অ্যাকাউন্টে চ্যানেল অ্যাক্সেস সাময়িকভাবে বন্ধ রয়েছে।"
            )
            await call.answer(alert_msg, show_alert=True)
            return

    # Price Calculation based on access tier
    live_rate = get_live_usd_rate()
    if tier == "channel" or (tier == "default" and ch_p > 0 and acc_p <= 0):
        reg_bdt = float(prod.get("price_channel_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_channel_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_channel_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)
    elif tier == "account" or (tier == "default" and acc_p > 0 and ch_p <= 0):
        reg_bdt = float(prod.get("price_account_bdt") or prod["price_bdt"])
        reg_usd = float(prod.get("price_account_usd") or round(reg_bdt / live_rate, 2))
        res_bdt = float(prod.get("reseller_price_account_bdt") or round(reg_bdt * 0.70, 2))
        res_usd = round(res_bdt / live_rate, 2)
    else:
        eff_p = ch_p if ch_p > 0 else (acc_p if acc_p > 0 else float(prod.get("price_bdt") or 0))
        reg_bdt = eff_p
        reg_usd = float(prod.get("price_usd") or 0)
        if reg_usd <= 0:
            reg_usd = round(reg_bdt / live_rate, 2)
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

    lang = db.get_user_language(user_id)
    clean_title = localize_item_name(prod['title'], lang)

    if prod.get("is_in_stock", 1) == 0:
        await call.answer(t("out_of_stock_alert", lang), show_alert=True)
        return

    # 1. Balance / Points Check
    if currency == "REF":
        if user_pts < price:
            alert_msg = "❌ Insufficient points!" if lang in ["en", "hi", "ur"] else "❌ পর্যাপ্ত রেফারেল পয়েন্ট নেই!"
            await call.answer(alert_msg, show_alert=True)
            insufficient_text = t("insufficient_points", lang, price=price, user_pts=user_pts)
            await render_screen(
                call,
                insufficient_text,
                reply_markup=get_buy_confirm_kb(prod_id, reg_bdt, round(reg_bdt / live_rate, 2), tier=tier, refs_needed=refs_needed, user_pts=user_pts, lang=lang),
                parse_mode="HTML"
            )
            return
    else:
        user_bal = user["balance_bdt"] if currency == "BDT" else user["balance_usd"]
        if user_bal < price:
            alert_msg = "❌ Insufficient balance!" if lang in ["en", "hi", "ur"] else "❌ পর্যাপ্ত ব্যালেন্স নেই!"
            await call.answer(alert_msg, show_alert=True)
            unit = "৳" if currency == "BDT" else "$"
            insufficient_text = t("insufficient_balance", lang, unit=unit, price=price, user_bal=user_bal)
            await render_screen(
                call,
                insufficient_text,
                reply_markup=get_buy_confirm_kb(prod_id, price, round(price / live_rate, 2), tier=tier, refs_needed=refs_needed, user_pts=user_pts, lang=lang),
                parse_mode="HTML"
            )
            return
        
    # 2. Deduct Balance or Points
    if currency == "REF":
        deducted = db.deduct_referral_points(user_id, price)
        if not deducted:
            err_msg = "❌ Failed to deduct points!" if lang in ["en", "hi", "ur"] else "❌ পয়েন্ট কাটতে সমস্যা হয়েছে!"
            await call.answer(err_msg, show_alert=True)
            return
    else:
        deducted = db.deduct_user_balance(user_id, price, currency)
        if not deducted:
            err_msg = "❌ Failed to deduct balance!" if lang in ["en", "hi", "ur"] else "❌ ব্যালেন্স কাটতে সমস্যা হয়েছে!"
            await call.answer(err_msg, show_alert=True)
            return

    # 3. Check Stock or Access Delivery according to Tier
    delivery_data = ""
    is_manual_delivery = False
    manual_delivery_reason = ""
    if is_channel_action:
        channel_id = prod.get("channel_id") or ""
        if channel_id:
            delivery_data = await generate_single_use_invite_link(bot, channel_id, prod["title"])
            if not delivery_data:
                is_manual_delivery = True
                manual_delivery_reason = "চ্যানেলে বটের অ্যাডমিন ইনভাইট পারমিশন নেই বা চ্যানেল আইডি সঠিক নয়"
                delivery_data = "Manual Processing: Admin will send your invite link shortly." if lang in ["en", "hi", "ur"] else "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অর্ডারের ইনভাইট লিংক পাঠাবে।"
        elif prod.get("drive_link"):
            delivery_data = prod["drive_link"]
        else:
            is_manual_delivery = True
            manual_delivery_reason = "কোর্সে কোনো চ্যানেল বা ড্রাইভ লিংক যুক্ত নেই"
            delivery_data = "Manual Processing: Admin will send your invite link shortly." if lang in ["en", "hi", "ur"] else "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অর্ডারের ইনভাইট লিংক পাঠাবে।"
    elif is_account_action:
        item = db.pop_stock_item(prod_id, user_id)
        if item:
            delivery_data = item
        elif prod.get("drive_link"):
            delivery_data = prod["drive_link"]
        else:
            is_manual_delivery = True
            manual_delivery_reason = "স্টকে কোনো অ্যাকাউন্ট/কি অবশিষ্ট নেই"
            delivery_data = "Manual Processing: Admin will send your account credentials shortly." if lang in ["en", "hi", "ur"] else "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অ্যাকাউন্টের অ্যাক্সেস তথ্য দ্রুত পাঠাবে।"
    elif prod["product_type"] == "drive_link":
        delivery_data = prod.get("drive_link") or "https://drive.google.com"
    else:
        delivery_data = "Manual Processing: Admin will contact you regarding your order." if lang in ["en", "hi", "ur"] else "ম্যানুয়াল প্রসেসিং: অ্যাডমিন আপনার অর্ডারের জন্য যোগাযোগ করবে।"
        
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
        
    success_alert = "🎉 Order completed successfully!" if lang in ["en", "hi", "ur"] else "🎉 অর্ডার সফল হয়েছে!"
    await call.answer(success_alert, show_alert=True)
    
    if currency == "REF":
        if lang in ["en", "hi", "ur"]:
            success_text = (
                "🎉 <b>Order Completed with Referral Points!</b>\n\n"
                f"📦 <b>Course:</b> {html.escape(clean_title)}\n"
                f"💎 <b>Points Paid:</b> <code>{price} Pts</code> (Value: ৳{int(reg_bdt)} BDT)\n"
                f"🆔 <b>Order ID:</b> <code>#{order_id}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔑 <b>Your Delivery Credentials / Access Data:</b>\n"
                f"<pre>{html.escape(delivery_data)}</pre>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>Your order is permanently stored under 'My Purchases'.</i>"
            )
        else:
            success_text = (
                "🎉 <b>রেফারেল পয়েন্ট দিয়ে অর্ডার সফল হয়েছে!</b>\n\n"
                f"📦 <b>কোর্স:</b> {html.escape(clean_title)}\n"
                f"💎 <b>পরিশোধিত পয়েন্ট:</b> <code>{price} Pts</code> (মূল্য: ৳{int(reg_bdt)} BDT)\n"
                f"🆔 <b>অর্ডার আইডি:</b> <code>#{order_id}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔑 <b>আপনার ডেলিভারি তথ্য / অ্যাক্সেস ডাটা:</b>\n"
                f"<pre>{html.escape(delivery_data)}</pre>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>আপনার অর্ডারটি প্রোফাইলের 'My Purchases' এ স্থায়ীভাবে সংরক্ষিত থাকবে।</i>"
            )
    else:
        success_text = t(
            "order_success",
            lang,
            order_id=order_id,
            title=html.escape(clean_title),
            amount=price,
            currency=currency,
            delivery_data=html.escape(delivery_data)
        )
    if tier == "channel":
        pkg_label = "📢 VIP Channel Access"
        success_text += f"\n🏷️ <b>Access Package:</b> {pkg_label}" if lang in ["en", "hi", "ur"] else f"\n🏷️ <b>অ্যাক্সেস প্যাকেজ:</b> {pkg_label}"
    elif tier == "account":
        pkg_label = "🔐 Personal Account Access"
        success_text += f"\n🏷️ <b>Access Package:</b> {pkg_label}" if lang in ["en", "hi", "ur"] else f"\n🏷️ <b>অ্যাক্সেস প্যাকেজ:</b> {pkg_label}"
        
    from keyboards.user_kb import make_custom_button
    order_done_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text=t("btn_orders", lang), callback_data="nav_orders", emoji_key="orders"),
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
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
        "remaining_balance": buyer.get("balance_bdt", 0.0),
        "manual_delivery": is_manual_delivery,
        "manual_reason": manual_delivery_reason,
        "access_tier": tier
    }
    user_payload = {
        "id": user_id,
        "full_name": call.from_user.full_name,
        "username": call.from_user.username
    }
    await notify_admin_order(bot, order_payload, user_payload)

@router.callback_query(F.data == "out_of_stock")
async def handle_out_of_stock(call: CallbackQuery):
    lang = db.get_user_language(call.from_user.id)
    await call.answer(t("out_of_stock_alert", lang), show_alert=True)
