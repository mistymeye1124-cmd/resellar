# Dedicated Router for Groq AI Course Ingestion & Multi-Key Management
# 100% In-Place Seamless Screen Switching (Zero Chat Clutter)
import html
import logging
import re
from typing import Dict, Any, Optional
import aiohttp

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMIN_IDS, get_live_usd_rate
from database.db import db
from utils.groq_service import groq_pool, scrape_course_page, generate_course_with_groq
from keyboards.admin_kb import (
    get_groq_preview_kb, get_groq_keys_menu_kb, get_groq_key_delete_kb,
    get_admin_main_kb
)
from utils.ui_nav import safe_switch_screen, render_safe_html_text

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS or ADMIN_IDS == [0] or user_id in ADMIN_IDS:
        return True
    return db.is_sub_admin(user_id)


# --- FSM STATES ---
class GroqAutoCourseState(StatesGroup):
    waiting_for_url = State()
    review_and_shortcuts = State()
    editing_ch_price = State()
    editing_acc_price = State()
    editing_channel_target = State()
    editing_account_data = State()
    editing_title = State()
    editing_desc = State()
    selecting_category = State()
    adding_new_category = State()
    adding_new_subcategory = State()

class GroqKeysState(StatesGroup):
    waiting_for_new_key = State()


def get_cancel_to_preview_kb() -> InlineKeyboardMarkup:
    """Button to return to preview card in-place."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 প্রিভিউতে ফিরে যান (Cancel)", callback_data="groq_back_to_preview")]
    ])

def get_cancel_to_keys_kb() -> InlineKeyboardMarkup:
    """Button to return to Groq key manager in-place."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 কী-ম্যানেজারে ফিরে যান", callback_data="admin_groq_keys_menu")]
    ])


# =====================================================================
# 1. GROQ MULTI-KEY MANAGEMENT (100% IN-PLACE SWITCHING)
# =====================================================================

@router.callback_query(F.data == "admin_groq_keys_menu")
async def handle_groq_keys_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("অননুমোদিত অ্যাক্সেস!", show_alert=True)
        return
    await state.clear()
    await call.answer()

    keys = groq_pool.get_all_keys()
    total_keys = len(keys)
    active_key = groq_pool.get_active_key()
    active_masked = f"...{active_key[-6:]}" if active_key and len(active_key) > 6 else (active_key or "কোনো কী নেই")

    key_list_str = ""
    if keys:
        for idx, k in enumerate(keys, start=1):
            masked = f"`...{k[-6:]}`" if len(k) > 6 else f"`{k}`"
            is_cur = " 🟢 <i>(সক্রিয়)</i>" if k == active_key else ""
            key_list_str += f"• কী #{idx}: {masked}{is_cur}\n"
    else:
        key_list_str = "⚠️ <i>বর্তমানে কোনো Groq API কী যুক্ত নেই! ডিফল্টভাবে ওয়েব স্ক্র্যাপিং মেটাডাটা দিয়ে কাজ চলবে।</i>\n"

    text = (
        "🤖 <b>Groq AI মাল্টি-কী (Multi-Key) ইঞ্জিন হাব</b> ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>মোট যুক্ত কী:</b> <code>{total_keys} টি</code>\n"
        f"🟢 <b>বর্তমান সক্রিয় কী:</b> <code>{active_masked}</code>\n\n"
        "🔑 <b>যুক্ত কীগুলোর তালিকা:</b>\n"
        f"{key_list_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>অটো-ফেইলওভার আর্কিটেকচার:</b>\n"
        "• একাধিক Groq কী যুক্ত রাখতে পারবেন।\n"
        "• কোনো একটি কী-এর কোটা বা রেট-লিমিট (429) শেষ হলে বট <b>স্বয়ংক্রিয়ভাবে পরবর্তী কী-তে সুইচ করবে</b>।\n"
        "• ফলে কখনোই বট বা কোর্স জেনারেশন অফ হবে না!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 কী যোগ বা টেস্ট করতে নিচের বাটনে চাপ দিন:"
    )

    await safe_switch_screen(call, text, reply_markup=get_groq_keys_menu_kb(keys))


@router.callback_query(F.data == "groq_key_add")
async def handle_groq_key_add_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(GroqKeysState.waiting_for_new_key)
    await state.update_data(menu_msg_id=call.message.message_id, chat_id=call.message.chat.id)

    text = (
        "➕ <b>নতুন Groq API Key যুক্ত করুন:</b>\n\n"
        "👉 আপনার Groq কনসোল (console.groq.com) থেকে কপি করা <code>gsk_...</code> কী-টি এখানে সেন্ড করুন:\n"
        "<i>(একাধিক কী একসাথে যোগ করতে চাইলে কমা (,) দিয়ে আলাদা করে সেন্ড করতে পারেন)</i>"
    )
    await safe_switch_screen(call, text, reply_markup=get_cancel_to_keys_kb())


@router.message(GroqKeysState.waiting_for_new_key)
async def handle_groq_key_save(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    menu_msg_id = data.get("menu_msg_id")
    chat_id = data.get("chat_id", message.chat.id)

    # Clean user typed message to prevent chat clutter
    try:
        await message.delete()
    except Exception:
        pass

    raw_text = (message.text or "").strip()
    if not raw_text:
        return

    added_count = 0
    for chunk in re.split(r"[,\n]+", raw_text):
        chunk = chunk.strip()
        if chunk and (chunk.startswith("gsk_") or len(chunk) > 20):
            if groq_pool.add_key_to_db(chunk):
                added_count += 1

    await state.clear()
    keys = groq_pool.get_all_keys()
    total_keys = len(keys)
    active_key = groq_pool.get_active_key()
    active_masked = f"...{active_key[-6:]}" if active_key and len(active_key) > 6 else (active_key or "কোনো কী নেই")

    key_list_str = ""
    for idx, k in enumerate(keys, start=1):
        masked = f"`...{k[-6:]}`" if len(k) > 6 else f"`{k}`"
        is_cur = " 🟢 <i>(সক্রিয়)</i>" if k == active_key else ""
        key_list_str += f"• কী #{idx}: {masked}{is_cur}\n"

    status_badge = f"🎉 <b>সফল! {added_count} টি নতুন Groq API কী সক্রিয় পুলে যুক্ত হয়েছে!</b>\n\n" if added_count > 0 else "⚠️ <b>কী আগেই পুলে বিদ্যমান আছে!</b>\n\n"

    text = (
        f"{status_badge}"
        "🤖 <b>Groq AI মাল্টি-কী ইঞ্জিন হাব</b> ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>মোট যুক্ত কী:</b> <code>{total_keys} টি</code>\n"
        f"🟢 <b>বর্তমান সক্রিয় কী:</b> <code>{active_masked}</code>\n\n"
        "🔑 <b>যুক্ত কীগুলোর তালিকা:</b>\n"
        f"{key_list_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 কী পরিচালনা করতে নিচের বাটনে চাপ দিন:"
    )

    if menu_msg_id:
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=menu_msg_id, text=text, reply_markup=get_groq_keys_menu_kb(keys), parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=get_groq_keys_menu_kb(keys), parse_mode="HTML")


@router.callback_query(F.data == "groq_key_delete_menu")
async def handle_groq_key_del_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    keys = groq_pool.get_all_keys()
    if not keys:
        await call.answer("মুছে ফেলার মতো কোনো কী নেই!", show_alert=True)
        return
    text = "🗑️ <b>কোন Groq API Key মুছে ফেলতে চান নির্বাচন করুন:</b>"
    await safe_switch_screen(call, text, reply_markup=get_groq_key_delete_kb(keys))


@router.callback_query(F.data.startswith("groq_key_del_idx:"))
async def handle_groq_key_delete_exec(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    idx = int(call.data.split(":")[1])
    keys = groq_pool.get_all_keys()
    if 0 <= idx < len(keys):
        target_k = keys[idx]
        groq_pool.remove_key_from_db(target_k)
        await call.answer("কী সফলভাবে মুছে ফেলা হয়েছে!", show_alert=False)
    else:
        await call.answer("কী পাওয়া যায়নি!", show_alert=True)

    await handle_groq_keys_menu(call, None)


@router.callback_query(F.data == "groq_keys_reset_pool")
async def handle_groq_keys_reset(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    groq_pool._failed_keys.clear()
    await call.answer("✅ সমস্ত কী-এর ফেইলওভার কাউন্টার রিসেট হয়েছে!", show_alert=True)
    await handle_groq_keys_menu(call, None)


@router.callback_query(F.data == "groq_keys_test")
async def handle_groq_keys_test(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    keys = groq_pool.get_all_keys()
    if not keys:
        await call.answer("টেস্ট করার মতো কোনো কী নেই!", show_alert=True)
        return

    await call.answer()
    testing_text = "⚡ <b>Groq ক্লাউড সার্ভারে সমস্ত কী টেস্ট করা হচ্ছে...</b>\n<i>অনুগ্রহ করে ২-৩ সেকেন্ড অপেক্ষা করুন।</i>"
    await safe_switch_screen(call, testing_text, reply_markup=None)

    results = []
    import time
    for idx, k in enumerate(keys, start=1):
        masked = f"...{k[-6:]}" if len(k) > 6 else k
        t0 = time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                tested_ok = False
                headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
                for test_m in ["qwen/qwen3.8-27b", "llama-3.1-8b-instant", "llama3-8b-8192", "openai/gpt-oss-120b"]:
                    payload = {
                        "model": test_m,
                        "messages": [{"role": "user", "content": "Ping"}],
                        "max_tokens": 5
                    }
                    async with session.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers) as resp:
                        elapsed = int((time.time() - t0) * 1000)
                        if resp.status == 200:
                            results.append(f"• <b>কী #{idx} ({masked}):</b> ✅ সচল ({test_m.split('/')[-1]}, {elapsed}ms)")
                            tested_ok = True
                            break
                        elif resp.status == 429:
                            results.append(f"• <b>কী #{idx} ({masked}):</b> ⚠️ রেট-লিমিট শেষ (HTTP 429)")
                            tested_ok = True
                            break
                        elif resp.status == 404:
                            continue
                        elif resp.status in (401, 403):
                            results.append(f"• <b>কী #{idx} ({masked}):</b> ❌ ভুল বা অকার্যকর কী (HTTP {resp.status})")
                            tested_ok = True
                            break
                if not tested_ok:
                    results.append(f"• <b>কী #{idx} ({masked}):</b> ❌ মডেল রেসপন্স করছে না")
        except Exception as e:
            results.append(f"• <b>কী #{idx} ({masked}):</b> ❌ টাইমআউট / কানেকশন এরর")

    res_text = (
        "📊 <b>Groq API কী টেস্টের ফলাফল:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(results) + "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>সক্রিয় কীগুলো দিয়ে অটো-কোর্স ক্রিয়েটর ফুল স্পিডে কাজ করবে।</i>"
    )
    await safe_switch_screen(call, res_text, reply_markup=get_groq_keys_menu_kb(keys))


# =====================================================================
# 2. GROQ AI AUTO ADD COURSE (100% IN-PLACE PREVIEW CARD SWITCHING)
# =====================================================================

@router.callback_query(F.data == "admin_groq_auto_add")
async def handle_start_groq_auto_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("অননুমোদিত অ্যাক্সেস!", show_alert=True)
        return
    await state.clear()
    await call.answer()
    await state.set_state(GroqAutoCourseState.waiting_for_url)
    await state.update_data(prompt_msg_id=call.message.message_id, chat_id=call.message.chat.id)

    text = (
        "🤖 <b>Groq AI সুপার-স্পিড অটো কোর্স ক্রিয়েটর</b> ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 <b>কোর্সের সেলস পেইজ বা ওয়েবসাইট লিংক দিন:</b>\n\n"
        "📌 <i>যেকোনো প্ল্যাটফর্মের কোর্সের লিংক পেস্ট করুন:</i>\n"
        "• 10 Minute School\n"
        "• Bohubrihi\n"
        "• Ostad\n"
        "• Interactive Cares / Shikho / Udemy ইত্যাদি\n\n"
        "⚡ <b>বট স্বয়ংক্রিয়ভাবে কী করবে:</b>\n"
        "১. আসল রিয়েল কোর্স টাইটেল এক্সট্র্যাক্ট করবে।\n"
        "২. আসল ব্যানার ফটো কালেক্ট করবে।\n"
        "৩. আকর্ষণীয় ও কনভার্টিন বাংলা ডেসক্রিপশন ডিজাইন করবে।\n"
        "৪. চ্যানেল ও অ্যাকাউন্ট ২টা অপশন সাজিয়ে প্রিভিউ কার্ড রেডি করবে!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>এখন লিংকটি চ্যাটে সেন্ড করুন:</b>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 বাতিল / ড্যাশবোর্ড", callback_data="admin_main_dashboard")]
    ])
    await safe_switch_screen(call, text, reply_markup=cancel_kb)


@router.message(GroqAutoCourseState.waiting_for_url)
async def handle_groq_course_url(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    chat_id = data.get("chat_id", message.chat.id)

    # Clean user URL message so chat is not cluttered
    try:
        await message.delete()
    except Exception:
        pass

    raw_url = (message.text or "").strip()
    if not (raw_url.startswith("http://") or raw_url.startswith("https://")):
        if prompt_msg_id:
            try:
                err_text = "❌ <b>সঠিক ওয়েবসাইট লিংক দিন (http:// বা https:// সহ):</b>\n\n👇 আবার লিংকটি সেন্ড করুন:"
                cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 বাতিল", callback_data="admin_main_dashboard")]])
                await bot.edit_message_text(chat_id=chat_id, message_id=prompt_msg_id, text=err_text, reply_markup=cancel_kb, parse_mode="HTML")
            except Exception:
                pass
        return

    # Update prompt message to processing
    if prompt_msg_id:
        try:
            wait_text = (
                "⏳ <b>Groq AI কোর্সটি দ্রুত অ্যানালাইজ ও ডিজাইন করছে...</b>\n"
                "<i>(ওয়েবসাইট স্ক্র্যাপ ও আকর্ষণীয় কপিরাইটিং তৈরি হচ্ছে, দয়া করে ১-২ সেকেন্ড অপেক্ষা করুন ⚡)</i>"
            )
            await bot.edit_message_text(chat_id=chat_id, message_id=prompt_msg_id, text=wait_text, parse_mode="HTML")
        except Exception:
            pass

    # 1. Scrape Course sales page
    scraped = await scrape_course_page(raw_url)

    # 2. Call Groq AI with multi-key pool failover
    ai_result = await generate_course_with_groq(scraped, raw_url)

    # Default Category (first course category)
    cats = db.get_categories_by_type("course")
    def_cat_id = cats[0]["id"] if cats else 1
    def_cat_name = cats[0]["name"] if cats else "কোর্স (Courses)"

    # Store in FSM state
    course_data = {
        "title": ai_result["title"],
        "description": ai_result["description"],
        "sales_page_url": raw_url,
        "photo_file_id": ai_result.get("photo_file_id"),
        "price_channel_bdt": ai_result.get("price_channel_bdt", 150),
        "price_account_bdt": ai_result.get("price_account_bdt", 350),
        "channel_target": None,
        "account_data": None,
        "category_id": def_cat_id,
        "category_name": def_cat_name,
        "key_used": ai_result.get("key_used", "AI"),
        "chat_id": chat_id
    }

    # Delete the text prompt message and replace with the dedicated preview card
    if prompt_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
        except Exception:
            pass

    # Send the single preview card and save its message ID
    card_msg = await send_groq_preview_card(bot, chat_id, course_data)
    course_data["card_msg_id"] = card_msg.message_id
    course_data["is_photo"] = bool(card_msg.photo)

    await state.update_data(**course_data)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)


def format_groq_preview_text(data: Dict[str, Any], for_caption: bool = False) -> str:
    """Helper to format the Preview Card text with strict length guarding for Telegram limits."""
    live_rate = get_live_usd_rate()
    ch_p = int(data.get("price_channel_bdt", 150))
    ch_u = round(ch_p / live_rate, 2) if ch_p > 0 else 0.0
    acc_p = int(data.get("price_account_bdt", 350))
    acc_u = round(acc_p / live_rate, 2) if acc_p > 0 else 0.0

    ch_res = int(ch_p * 0.70) if ch_p > 0 else 0
    acc_res = int(acc_p * 0.70) if acc_p > 0 else 0

    if ch_p > 0:
        ch_price_line = f"• 📢 <b>VIP Channel:</b> <b>৳{ch_p} BDT</b> (${ch_u}) <i>(রিসেলার ৳{ch_res})</i>"
        if data.get("channel_target"):
            ch_target_val = html.escape(str(data["channel_target"]), quote=False)
            ch_title_val = html.escape(str(data.get("channel_title") or data["channel_target"]), quote=False)
            if data.get("channel_verified"):
                ch_stat = f"<code>{ch_target_val}</code> (<b>{ch_title_val}</b>) 🟢"
            else:
                ch_stat = f"<code>{ch_target_val}</code> ⚠️ <i>(বট পারমিশন চেক বাকি)</i>"
        else:
            ch_stat = "⚠️ <i>(সেট করা হয়নি — ইনভাইট বন্ধ)</i>"
    else:
        ch_price_line = "• 📢 <b>VIP Channel:</b> 🔴 <b>বন্ধ (অফ করা আছে)</b>"
        ch_stat = "⚪ <i>(অফ — চ্যানেল ইনভাইট লিংক বন্ধ)</i>"

    if acc_p > 0:
        acc_price_line = f"• 🔐 <b>Personal Account / Drive:</b> <b>৳{acc_p} BDT</b> (${acc_u}) <i>(রিসেলার ৳{acc_res})</i>"
        acc_stat = "✅ <i>(সেট হয়েছে)</i>" if data.get("account_data") else "⚠️ <i>(সেট করা হয়নি — ড্রাইভ/অ্যাকাউন্ট লিঙ্ক বাকি)</i>"
    else:
        acc_price_line = "• 🔐 <b>Personal Account / Drive:</b> 🔴 <b>বন্ধ (অফ করা আছে)</b>"
        acc_stat = "⚪ <i>(অফ — অ্যাকাউন্ট/ড্রাইভ ডেলিভারি বন্ধ)</i>"

    sales_url = data.get("sales_page_url", "")
    sales_url_display = (sales_url[:57] + "...") if len(sales_url) > 60 else sales_url

    title = data.get("title", "")
    title_display = (title[:87] + "...") if len(title) > 90 else title

    base_header = (
        "✨ <b>Groq AI কোর্স প্রিভিউ ও সুপার-স্পিড সেটআপ</b> ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>রিয়েল কোর্স টাইটেল:</b> <b>{html.escape(title_display, quote=False)}</b>\n"
        f"🌐 <b>অরিজিনাল সেলস পেজ:</b> <code>{html.escape(sales_url_display, quote=False)}</code>\n"
        f"📁 <b>ক্যাটাগরি:</b> <b>{html.escape(data.get('category_name', 'কোর্স'), quote=False)}</b>\n\n"
        "💳 <b>অ্যাক্সেস প্রাইসিং (খুচরা ও রিসেলার):</b>\n"
        f"{ch_price_line}\n"
        f"{acc_price_line}\n\n"
        "📦 <b>ডেলিভারি কনফিগারেশন:</b>\n"
        f"• 📢 VIP Telegram Channel: {ch_stat}\n"
        f"• 🔐 Account / Drive Vault: {acc_stat}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📝 <b>AI ডেসক্রিপশন প্রিভিউ:</b>\n"
    )
    base_footer = (
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>প্রয়োজনীয় প্রাইস বা ডেলিভারি পরিবর্তন করতে নিচের শর্টকাটে ক্লিক করুন:</i>"
    )

    max_total = 980 if for_caption else 3500
    available_desc = max(40, max_total - len(base_header) - len(base_footer))
    desc_raw = data.get("description", "")
    if len(desc_raw) > available_desc:
        desc_preview = render_safe_html_text(desc_raw[:available_desc]) + "..."
    else:
        desc_preview = render_safe_html_text(desc_raw)

    full_card = f"{base_header}{desc_preview}{base_footer}"
    return render_safe_html_text(full_card)


async def send_groq_preview_card(bot: Bot, chat_id: int, data: Dict[str, Any]) -> Message:
    """Sends the initial preview card (with photo if available)."""
    kb = get_groq_preview_kb(data)
    photo_url = data.get("photo_file_id")

    if photo_url and photo_url.startswith("http"):
        caption_text = format_groq_preview_text(data, for_caption=True)
        try:
            return await bot.send_photo(chat_id=chat_id, photo=photo_url, caption=caption_text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not send photo preview URL {photo_url}: {e}")

    full_text = format_groq_preview_text(data, for_caption=False)
    return await bot.send_message(chat_id=chat_id, text=full_text, reply_markup=kb, parse_mode="HTML")


async def edit_groq_card_in_place(bot: Bot, chat_id: int, card_msg_id: int, text: str, reply_markup: InlineKeyboardMarkup, is_photo: bool = True):
    """Edits the single active preview card in-place with zero chat clutter."""
    if is_photo:
        caption_safe = text[:1000] if len(text) > 1000 else text
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=card_msg_id, caption=caption_safe, reply_markup=reply_markup, parse_mode="HTML")
            return
        except Exception:
            pass
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=card_msg_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not edit card in place: {e}")


# =====================================================================
# 3. SHORTCUT EDIT ACTIONS (100% IN-PLACE SWITCHING)
# =====================================================================

@router.callback_query(F.data == "groq_back_to_preview")
async def handle_back_to_preview_in_place(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    data = await state.get_data()
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    text = format_groq_preview_text(data)
    kb = get_groq_preview_kb(data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_edit:ch_price", GroqAutoCourseState.review_and_shortcuts)
async def handle_shortcut_edit_ch_price(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.editing_ch_price)
    data = await state.get_data()
    cur = data.get("price_channel_bdt", 150)

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    cur_text = f"৳{cur} BDT" if cur > 0 else "🔴 বন্ধ (OFF)"
    prompt = (
        "💰 <b>VIP Channel Access মূল্য নির্ধারণ:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• বর্তমান সেট করা রেট: <code>{cur_text}</code>\n\n"
        "👇 <b>নতুন রেট সংখ্যায় লিখে চ্যাটে সেন্ড করুন (যেমন: 200):</b>\n"
        "💡 <i>(এই অপশনটি বন্ধ রাখতে সরাসরি <code>0</code> লিখে পাঠান)</i>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_ch_price)
async def handle_save_shortcut_ch_price(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    try:
        val = max(0, int(float((message.text or "").strip())))
    except ValueError:
        return

    await state.update_data(price_channel_bdt=val)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    updated_data = await state.get_data()

    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_edit:acc_price", GroqAutoCourseState.review_and_shortcuts)
async def handle_shortcut_edit_acc_price(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.editing_acc_price)
    data = await state.get_data()
    cur = data.get("price_account_bdt", 350)

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    cur_text = f"৳{cur} BDT" if cur > 0 else "🔴 বন্ধ (OFF)"
    prompt = (
        "💰 <b>Personal Account / Drive মূল্য নির্ধারণ:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• বর্তমান সেট করা রেট: <code>{cur_text}</code>\n\n"
        "👇 <b>নতুন রেট সংখ্যায় লিখে চ্যাটে সেন্ড করুন (যেমন: 450):</b>\n"
        "💡 <i>(এই অপশনটি বন্ধ রাখতে সরাসরি <code>0</code> লিখে পাঠান)</i>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_acc_price)
async def handle_save_shortcut_acc_price(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    try:
        val = max(0, int(float((message.text or "").strip())))
    except ValueError:
        return

    await state.update_data(price_account_bdt=val)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    updated_data = await state.get_data()

    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_edit:channel_target", GroqAutoCourseState.review_and_shortcuts)
async def handle_shortcut_edit_channel(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.editing_channel_target)
    data = await state.get_data()

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    bot_info = await bot.get_me()
    bot_uname = bot_info.username or "AllInOneProAccess_bot"

    prompt = (
        "📢 <b>VIP টেলিগ্রাম চ্যানেলের ID অথবা @Username সেট করুন:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>জরুরি:</b> <code>@{bot_uname}</code> কে আপনার চ্যানেলে <b>Administrator</b> বানিয়ে <b>'Invite Users via Link'</b> পারমিশন দিন।\n\n"
        "👇 <b>চ্যানেলের ইউজারনেম বা আইডি লিখে পাঠান (যেমন: @my_channel):</b>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_channel_target)
async def handle_save_shortcut_channel(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    target = (message.text or "").strip()
    if not target:
        return

    # Verify channel live
    from handlers.admin_panel import verify_telegram_channel_access
    chk = await verify_telegram_channel_access(bot, target)

    if chk.get("success"):
        ch_title = chk.get("title", target)
        test_link = chk.get("test_link", "")
        await state.update_data(
            channel_target=target,
            channel_title=ch_title,
            channel_verified=True,
            channel_test_link=test_link
        )
        confirm_msg = (
            f"✅ <b>চ্যানেল সফলভাবে কানেক্ট ও ভেরিফাই হয়েছে!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 <b>চ্যানেল:</b> <b>{html.escape(ch_title)}</b>\n"
            f"🆔 <b>টার্গেট:</b> <code>{html.escape(target)}</code>\n"
            f"🔑 <b>বট স্ট্যাটাস:</b> <code>Administrator (Invite Rights Active 🟢)</code>\n"
            f"🔗 <b>টেস্ট ইনভাইট লিংক:</b> {test_link}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        try:
            temp_m = await message.answer(confirm_msg, parse_mode="HTML")
            asyncio.create_task(_auto_del_msg(temp_m, 10))
        except Exception:
            pass
    else:
        bot_info = await bot.get_me()
        bot_uname = bot_info.username or "AllInOneProAccess_bot"
        err_msg = chk.get("message", "Unknown error")
        await state.update_data(
            channel_target=target,
            channel_title=chk.get("title", target),
            channel_verified=False,
            channel_error=err_msg
        )
        warn_msg = (
            f"⚠️ <b>চ্যানেল সতর্কবার্তা!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>সমস্যা:</b> {html.escape(err_msg)}\n\n"
            f"👉 <b>করণীয়:</b>\n"
            f"১. আপনার চ্যানেলে যান ➡️ Edit ➡️ Administrators ➡️ Add Admin\n"
            f"২. <code>@{bot_uname}</code> কে যুক্ত করে <b>'Invite Users via Link'</b> পারমিশন দিন।\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>(চ্যানেলটি সেভ করা হয়েছে। পারমিশন দিয়ে '🧪 টেস্ট ইনভাইট' বাটনে চাপ দিন)</i>"
        )
        try:
            temp_m = await message.answer(warn_msg, parse_mode="HTML")
            asyncio.create_task(_auto_del_msg(temp_m, 12))
        except Exception:
            pass

    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    updated_data = await state.get_data()

    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


async def _auto_del_msg(m: Message, sec: int = 10):
    await asyncio.sleep(sec)
    try:
        await m.delete()
    except Exception:
        pass


@router.callback_query(F.data == "groq_test_channel", GroqAutoCourseState.review_and_shortcuts)
async def handle_groq_test_channel_live(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target = data.get("channel_target")
    if not target:
        await call.answer("⚠️ কোনো চ্যানেল টার্গেট সেট করা নেই!", show_alert=True)
        return
    await call.answer("🔍 টেলিগ্রাম সার্ভারে চ্যানেল টেস্ট করা হচ্ছে...", show_alert=False)
    from handlers.admin_panel import verify_telegram_channel_access
    chk = await verify_telegram_channel_access(bot, target)
    if chk.get("success"):
        await state.update_data(
            channel_title=chk.get("title", target),
            channel_verified=True,
            channel_test_link=chk.get("test_link")
        )
        test_link = chk.get("test_link")
        await call.message.answer(
            f"✅ <b>চ্যানেল ভেরিফিকেশন টেস্ট সফল!</b>\n\n"
            f"📢 চ্যানেল: <b>{html.escape(chk.get('title', target))}</b>\n"
            f"🔑 বট স্ট্যাটাস: <code>Administrator 🟢</code>\n"
            f"🔗 <b>টেস্ট ইনভাইট লিংক:</b> {test_link}\n\n"
            f"<i>(লিংকটি টেস্টের জন্য তৈরি হয়েছে, কাস্টমার কিনলে স্বয়ংক্রিয়ভাবে নতুন ১-টাইম লিংক পাবে)</i>",
            parse_mode="HTML"
        )
    else:
        await state.update_data(channel_verified=False)
        await call.answer(f"❌ চ্যানেল কানেকশন ফেইল্ড!\n{chk.get('message')}", show_alert=True)


@router.callback_query(F.data == "groq_edit:account_data", GroqAutoCourseState.review_and_shortcuts)
async def handle_shortcut_edit_account_data(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.editing_account_data)
    data = await state.get_data()

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    prompt = (
        "🔐 <b>Personal Account অথবা Drive-এর ডেলিভারি তথ্য সেট করুন:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 কাস্টমার Account Access কিনলে তাকে ইনস্ট্যান্ট যে লিংক বা লগইন তথ্য দেওয়া হবে:\n\n"
        "👇 <b>Google Drive / Mega লিঙ্ক অথবা লগইন তথ্য লিখে পাঠান:</b>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_account_data)
async def handle_save_shortcut_account_data(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    acc_text = (message.text or "").strip()
    if not acc_text:
        return

    await state.update_data(account_data=acc_text)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    updated_data = await state.get_data()

    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_edit:category", GroqAutoCourseState.review_and_shortcuts)
@router.callback_query(F.data == "groq_edit:category", GroqAutoCourseState.selecting_category)
async def handle_shortcut_edit_category(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.selecting_category)
    data = await state.get_data()

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    cats = db.get_categories(parent_id=None)
    buttons = []
    for c in cats:
        subcats = db.get_subcategories(c["id"])
        sub_tag = f" (📂 {len(subcats)} সাব)" if subcats else ""
        btn_txt = f"{c.get('icon', '📁')} {c['name']}{sub_tag}"
        cb = f"groq_view_subcats:{c['id']}" if subcats else f"groq_sel_cat:{c['id']}"
        buttons.append([InlineKeyboardButton(text=btn_txt, callback_data=cb)])
        
    buttons.append([
        InlineKeyboardButton(text="➕ নতুন ক্যাটাগরি তৈরি করুন (New Category)", callback_data="groq_add_cat")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 প্রিভিউতে ফিরে যান (Cancel)", callback_data="groq_back_to_preview")
    ])

    prompt = (
        "📁 <b>কোর্সের জন্য ক্যাটাগরি ও সাব-ক্যাটাগরি নির্ধারণ:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 নিচের তালিকা থেকে ক্যাটাগরি সিলেক্ট করুন অথবা সরাসরি নতুন ক্যাটাগরি তৈরি করুন:"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, InlineKeyboardMarkup(inline_keyboard=buttons), is_photo)


@router.callback_query(F.data.startswith("groq_view_subcats:"), GroqAutoCourseState.selecting_category)
async def handle_groq_view_subcats(call: CallbackQuery, state: FSMContext, bot: Bot):
    cat_id = int(call.data.split(":")[1])
    cat = db.get_category(cat_id)
    subcats = db.get_subcategories(cat_id)
    data = await state.get_data()

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))
    await call.answer()

    buttons = []
    for sc in subcats:
        buttons.append([InlineKeyboardButton(text=f"{sc.get('icon', '📁')} {sc['name']}", callback_data=f"groq_sel_subcat:{sc['id']}:{cat_id}")])

    cat_name = cat['name'] if cat else 'ক্যাটাগরি'
    buttons.append([InlineKeyboardButton(text=f"✅ সরাসরি '{cat_name[:16]}' এ রাখুন", callback_data=f"groq_sel_cat:{cat_id}")])
    buttons.append([InlineKeyboardButton(text="➕ নতুন সাব-ক্যাটাগরি তৈরি করুন (New Subcat)", callback_data=f"groq_add_subcat:{cat_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 ক্যাটাগরি তালিকায় ব্যাক", callback_data="groq_edit:category")])

    prompt = (
        f"📂 <b>'{cat_name}' এর সাব-ক্যাটাগরি তালিকা:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 এই কোর্সের জন্য নির্দিষ্ট সাব-ক্যাটাগরি বেছে নিন অথবা নতুন তৈরি করুন:"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, InlineKeyboardMarkup(inline_keyboard=buttons), is_photo)


@router.callback_query(F.data.startswith("groq_sel_subcat:"), GroqAutoCourseState.selecting_category)
async def handle_save_shortcut_subcategory(call: CallbackQuery, state: FSMContext, bot: Bot):
    parts = call.data.split(":")
    subcat_id = int(parts[1])
    parent_cat_id = int(parts[2])

    subcat = db.get_category(subcat_id)
    parent = db.get_category(parent_cat_id)
    p_name = parent["name"] if parent else "কোর্স"
    s_name = subcat["name"] if subcat else "সাব-ক্যাটাগরি"
    full_display = f"{p_name[:10]} > {s_name[:10]}"

    await state.update_data(category_id=parent_cat_id, subcategory_id=subcat_id, category_name=full_display)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    await call.answer(f"সাব-ক্যাটাগরি সেট: {s_name}", show_alert=False)

    data = await state.get_data()
    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    text = format_groq_preview_text(data)
    kb = get_groq_preview_kb(data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data.startswith("groq_sel_cat:"), GroqAutoCourseState.selecting_category)
async def handle_save_shortcut_category(call: CallbackQuery, state: FSMContext, bot: Bot):
    cat_id = int(call.data.split(":")[1])
    cat = db.get_category(cat_id)
    cname = cat["name"] if cat else "কোর্স"
    await state.update_data(category_id=cat_id, subcategory_id=None, category_name=cname)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    await call.answer(f"ক্যাটাগরি সেট: {cname}", show_alert=False)

    data = await state.get_data()
    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    text = format_groq_preview_text(data)
    kb = get_groq_preview_kb(data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_add_cat", GroqAutoCourseState.selecting_category)
async def handle_groq_start_add_cat(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.adding_new_category)
    data = await state.get_data()
    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    prompt = (
        "➕ <b>নতুন ক্যাটাগরি তৈরি করুন:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>ক্যাটাগরির নাম লিখে পাঠান:</b>\n\n"
        "<i>(যেমন: 📱 Video Editing অথবা 💻 Programming — লেখার সাথে সাথে ক্যাটাগরি তৈরি হয়ে কোর্সে সিলেক্ট হয়ে যাবে)</i>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.adding_new_category)
async def handle_groq_save_new_cat(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    cat_name = message.text.strip()
    if not cat_name or len(cat_name) < 2:
        prompt = "❌ অনুগ্রহ করে সঠিক নাম লিখুন (কমপক্ষে ২ অক্ষর):"
        await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)
        return

    new_cat_id = db.add_category(name=cat_name, icon="📁", cat_type="course", parent_id=None)
    await state.update_data(category_id=new_cat_id, subcategory_id=None, category_name=cat_name)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)

    updated_data = await state.get_data()
    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data.startswith("groq_add_subcat:"), GroqAutoCourseState.selecting_category)
async def handle_groq_start_add_subcat(call: CallbackQuery, state: FSMContext, bot: Bot):
    cat_id = int(call.data.split(":")[1])
    parent = db.get_category(cat_id)
    p_name = parent["name"] if parent else "ক্যাটাগরি"
    await call.answer()
    await state.set_state(GroqAutoCourseState.adding_new_subcategory)
    await state.update_data(target_parent_cat_id=cat_id)

    data = await state.get_data()
    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    prompt = (
        f"➕ <b>'{p_name}' এর জন্য নতুন সাব-ক্যাটাগরি তৈরি করুন:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>সাব-ক্যাটাগরির নাম লিখে পাঠান:</b>\n\n"
        "<i>(যেমন: Premiere Pro, Python Masterclass ইত্যাদি — তৈরি হওয়ার পর সরাসরি সিলেক্ট হয়ে যাবে)</i>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.adding_new_subcategory)
async def handle_groq_save_new_subcat(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)
    parent_id = data.get("target_parent_cat_id", 1)

    try:
        await message.delete()
    except Exception:
        pass

    sub_name = message.text.strip()
    if not sub_name or len(sub_name) < 2:
        prompt = "❌ অনুগ্রহ করে সঠিক নাম লিখুন (কমপক্ষে ২ অক্ষর):"
        await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)
        return

    parent = db.get_category(parent_id)
    cat_type = parent.get("type", "course") if parent else "course"
    new_sub_id = db.add_category(name=sub_name, icon="📁", cat_type=cat_type, parent_id=parent_id)

    p_name = parent["name"] if parent else "কোর্স"
    full_display = f"{p_name[:10]} > {sub_name[:10]}"

    await state.update_data(category_id=parent_id, subcategory_id=new_sub_id, category_name=full_display)
    await state.set_state(GroqAutoCourseState.review_and_shortcuts)

    updated_data = await state.get_data()
    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


@router.callback_query(F.data == "groq_edit:content", GroqAutoCourseState.review_and_shortcuts)
async def handle_shortcut_edit_content(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(GroqAutoCourseState.editing_title)
    data = await state.get_data()

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    prompt = (
        "✏️ <b>কোর্স টাইটেল ও ডেসক্রিপশন এডিট:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• বর্তমান টাইটেল: <b>{html.escape(data.get('title', ''))}</b>\n\n"
        "👇 <b>নতুন টাইটেল লিখে পাঠান (অথবা বর্তমান টাইটেল রাখতে 'ok' লিখুন):</b>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_title)
async def handle_save_shortcut_title(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    txt = (message.text or "").strip()
    if txt and txt.lower() != "ok":
        await state.update_data(title=txt)

    await state.set_state(GroqAutoCourseState.editing_desc)
    prompt = (
        "📝 <b>ডেসক্রিপশন এডিট:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>নতুন ডেসক্রিপশন লিখে পাঠান (বর্তমান AI ডেসক্রিপশন রাখতে 'ok' লিখুন):</b>"
    )
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, prompt, get_cancel_to_preview_kb(), is_photo)


@router.message(GroqAutoCourseState.editing_desc)
async def handle_save_shortcut_desc(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    card_msg_id = data.get("card_msg_id")
    is_photo = data.get("is_photo", True)

    try:
        await message.delete()
    except Exception:
        pass

    txt = (message.text or "").strip()
    if txt and txt.lower() != "ok":
        await state.update_data(description=txt)

    await state.set_state(GroqAutoCourseState.review_and_shortcuts)
    updated_data = await state.get_data()

    text = format_groq_preview_text(updated_data)
    kb = get_groq_preview_kb(updated_data)
    await edit_groq_card_in_place(bot, chat_id, card_msg_id, text, kb, is_photo)


# =====================================================================
# 4. 1-CLICK PUBLISH (IN-PLACE SUCCESS SCREEN)
# =====================================================================

@router.callback_query(F.data == "groq_publish_course", GroqAutoCourseState.review_and_shortcuts)
async def handle_publish_groq_course(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    data = await state.get_data()
    await state.clear()
    await call.answer()

    ch_bdt = float(data.get("price_channel_bdt", 150) or 0)
    acc_bdt = float(data.get("price_account_bdt", 350) or 0)

    if ch_bdt <= 0 and acc_bdt <= 0:
        await call.answer("❌ চ্যানেল বা অ্যাকাউন্ট যেকোনো একটি অবশ্যই সক্রিয় রাখতে হবে (মূল্য ০ এর বেশি নির্ধারণ করুন)!", show_alert=True)
        return

    await state.clear()
    await call.answer()

    live_rate = get_live_usd_rate()
    ch_usd = round(ch_bdt / live_rate, 2) if ch_bdt > 0 else 0.0
    acc_usd = round(acc_bdt / live_rate, 2) if acc_bdt > 0 else 0.0

    r_ch_bdt = round(ch_bdt * 0.70, 2) if ch_bdt > 0 else 0.0
    r_acc_bdt = round(acc_bdt * 0.70, 2) if acc_bdt > 0 else 0.0

    if ch_bdt > 0 and acc_bdt > 0:
        ptype = "dual_access"
        final_price_bdt = ch_bdt
        final_price_usd = ch_usd
        final_reseller_bdt = r_ch_bdt
        final_reseller_usd = round(r_ch_bdt / live_rate, 2)
    elif ch_bdt > 0:
        ptype = "channel_link"
        final_price_bdt = ch_bdt
        final_price_usd = ch_usd
        final_reseller_bdt = r_ch_bdt
        final_reseller_usd = round(r_ch_bdt / live_rate, 2)
        acc_bdt = 0.0
        acc_usd = 0.0
        r_acc_bdt = 0.0
    else: # acc_bdt > 0 and ch_bdt <= 0
        ptype = "drive_link" if data.get("account_data") else "stock_account"
        final_price_bdt = acc_bdt
        final_price_usd = acc_usd
        final_reseller_bdt = r_acc_bdt
        final_reseller_usd = round(r_acc_bdt / live_rate, 2)
        ch_bdt = 0.0
        ch_usd = 0.0
        r_ch_bdt = 0.0

    prod_id = db.add_product(
        category_id=data.get("category_id", 1),
        subcategory_id=data.get("subcategory_id"),
        title=data["title"],
        description=data["description"],
        price_bdt=final_price_bdt,
        price_usd=final_price_usd,
        product_type=ptype,
        channel_id=data.get("channel_target") if ch_bdt > 0 else None,
        drive_link=data.get("account_data") if acc_bdt > 0 else None,
        photo_file_id=data.get("photo_file_id"),
        reseller_price_bdt=final_reseller_bdt,
        reseller_price_usd=final_reseller_usd,
        price_channel_bdt=ch_bdt,
        price_channel_usd=ch_usd,
        price_account_bdt=acc_bdt,
        price_account_usd=acc_usd,
        reseller_price_channel_bdt=r_ch_bdt,
        reseller_price_account_bdt=r_acc_bdt,
        is_in_stock=1,
        sales_page_url=data.get("sales_page_url"),
        channel_title=data.get("channel_title") if ch_bdt > 0 else None,
        channel_verified=1 if (data.get("channel_verified") and ch_bdt > 0) else 0
    )

    ch_summary = f"• 📢 VIP Channel: <b>৳{int(ch_bdt)} BDT</b> (${ch_usd}) <i>(রিসেলার ৳{int(r_ch_bdt)})</i>" if ch_bdt > 0 else "• 📢 VIP Channel: 🔴 <b>বন্ধ (OFF)</b>"
    acc_summary = f"• 🔐 Account / Drive: <b>৳{int(acc_bdt)} BDT</b> (${acc_usd}) <i>(রিসেলার ৳{int(r_acc_bdt)})</i>" if acc_bdt > 0 else "• 🔐 Account / Drive: 🔴 <b>বন্ধ (OFF)</b>"

    success_text = (
        "🎉🚀 <b>আলহামদুলিল্লাহ! কোর্সটি সফলভাবে পাবলিশ ও লাইভ হয়েছে!</b> 🚀🎉\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>কোর্স:</b> <b>{html.escape(data['title'])}</b>\n"
        f"🆔 <b>প্রোডাক্ট আইডি:</b> <code>#{prod_id}</code>\n"
        f"📂 <b>ক্যাটাগরি:</b> {html.escape(data.get('category_name', 'কোর্স'))}\n\n"
        "💳 <b>অ্যাক্সেস প্রাইসিং রেট:</b>\n"
        f"{ch_summary}\n"
        f"{acc_summary}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <i>কাস্টমাররা এখনই বট ক্যাটালগে এই কোর্স দেখতে ও ইনস্ট্যান্ট অর্ডার করতে পারবে!</i>"
    )

    buttons = [
        [InlineKeyboardButton(text="📢 সবাইকে নোটিফাই করুন (Broadcast)", callback_data=f"prod_bcast_prompt:{prod_id}")],
        [
            InlineKeyboardButton(text="👁️ ক্যাটালগে দেখুন", callback_data=f"prod:{prod_id}"),
            InlineKeyboardButton(text="➕ আরেকটি কোর্স অটো-অ্যাড", callback_data="admin_groq_auto_add")
        ],
        [InlineKeyboardButton(text="🏠 মেইন অ্যাডমিন প্যানেল", callback_data="admin_main_dashboard")]
    ]

    chat_id = data.get("chat_id", call.message.chat.id)
    card_msg_id = data.get("card_msg_id", call.message.message_id)
    is_photo = data.get("is_photo", bool(call.message.photo))

    await edit_groq_card_in_place(bot, chat_id, card_msg_id, success_text, InlineKeyboardMarkup(inline_keyboard=buttons), is_photo)
