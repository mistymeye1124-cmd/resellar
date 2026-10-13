# Deposit Handler with Mandatory Screenshot and Fast Approval Admin Knock
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import html
from database.db import db
from keyboards.user_kb import (
    get_deposit_methods_kb,
    get_pending_deposit_kb,
    get_cancel_fsm_kb
)
from config import PAYMENT_CONFIG, ADMIN_USERNAME
from utils.notifier import notify_admin_deposit
from utils.i18n import t
from utils.emojis import em_tag
from utils.ui_nav import render_screen

router = Router()

class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_trx_id = State()
    waiting_for_screenshot = State()

@router.message(F.text.in_([
    "Add Balance (ডিপোজিট)", "💳 Add Balance (ডিপোজিট)", "Add Balance (Deposit)", "💳 Add Balance (Deposit)", 
    "बैलेंस जोड़ें (Deposit)", "💳 बैलेंस जोड़ें (Deposit)", "Add Balance", "💳 Add Balance", "ডিপোজিট", "Deposit"
]))
async def handle_deposit_menu(message: Message, state: FSMContext):
    await state.clear()
    lang = db.get_user_language(message.from_user.id)
    text = t("deposit_menu_text", lang)
    try:
        await message.answer(text, reply_markup=get_deposit_methods_kb(lang), parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=get_deposit_methods_kb(lang))

@router.callback_query(F.data == "add_balance_shortcut")
async def handle_deposit_shortcut(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    lang = db.get_user_language(call.from_user.id)
    text = t("deposit_menu_text", lang)
    await render_screen(call, text, reply_markup=get_deposit_methods_kb(lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("dep_method:"))
async def handle_select_method(call: CallbackQuery, state: FSMContext):
    method_key = call.data.split(":")[1]
    if method_key not in PAYMENT_CONFIG:
        await call.answer("মেথড পাওয়া যায়নি!", show_alert=True)
        return
        
    if not db.is_gateway_active(method_key):
        await call.answer("⚠️ এই পেমেন্ট মেথডটি সাময়িক রক্ষণাবেক্ষণের জন্য বন্ধ আছে। অনুগ্রহ করে অন্য মেথড বেছে নিন।", show_alert=True)
        return

    cfg = PAYMENT_CONFIG[method_key]
    db_key = "binance_pay_id" if method_key == "binance" else f"{method_key}_number"
    active_number = db.get_setting(db_key, cfg["number"])
    
    # Dynamic min deposit and instruction
    if cfg["currency"] == "BDT":
        min_dep = float(db.get_setting("min_deposit_bdt", cfg["min_deposit"]))
    else:
        min_dep = float(db.get_setting("min_deposit_usd", cfg["min_deposit"]))
        
    active_instruction = db.get_setting(f"{method_key}_instruction", cfg["instruction"])

    await state.update_data(method=method_key, currency=cfg["currency"], min_deposit=min_dep)
    await state.set_state(DepositState.waiting_for_amount)
    await call.answer()
    
    unit = "টাকা" if cfg["currency"] == "BDT" else "USDT ($)"
    type_badge = "🏪 <b>এজেন্ট ক্যাশ আউট নম্বর:</b>" if method_key in ["bkash", "nagad"] else "📌 <b>অ্যাকাউন্ট নম্বর / Pay ID:</b>"
    action_verb = "ক্যাশ আউট" if method_key in ["bkash", "nagad"] else "সেন্ড মানি / ট্রান্সফার"
    gateway_emoji = em_tag(method_key, "💳")
    
    text = (
        f"{gateway_emoji} <b>পেমেন্ট মেথড: {html.escape(cfg['name'])}</b> {gateway_emoji}\n\n"
        f"{type_badge}\n"
        f"<pre>{html.escape(active_number)}</pre>\n"
        f"<i>(নম্বরের উপর ১-ট্যাপ করলেই সাথে সাথে কপি হয়ে যাবে)</i>\n\n"
        f"📝 <b>নিয়মাবলী:</b> {html.escape(active_instruction)}\n"
        f"⚠️ <b>সর্বনিম্ন ডিপোজিট:</b> <b>{int(min_dep) if min_dep.is_integer() else min_dep} {unit}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 আপনি কত <b>{unit}</b> {action_verb} করেছেন তা নিচে লিখে সেন্ড করুন:\n"
        f"<i>(উদাহরণ: 500 অথবা 1000)</i>"
    )
    await render_screen(call, text, reply_markup=get_cancel_fsm_kb(), parse_mode="HTML")

@router.message(DepositState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        amount = float(text)
    except ValueError:
        await message.answer("❌ ভুল ইনপুট! অনুগ্রহ করে শুধুমাত্র সংখ্যা লিখুন (যেমন: 500 বা 10):", reply_markup=get_cancel_fsm_kb())
        return
        
    data = await state.get_data()
    min_dep = data.get("min_deposit", 50)
    currency = data.get("currency", "BDT")
    
    if amount < min_dep:
        await message.answer(f"❌ সর্বনিম্ন ডিপোজিট <code>{min_dep} {currency}</code>। সঠিক অ্যামাউন্ট লিখুন:", reply_markup=get_cancel_fsm_kb(), parse_mode="HTML")
        return
        
    await state.update_data(amount=amount)
    await state.set_state(DepositState.waiting_for_trx_id)
    
    await message.answer(
        f"✅ <b>অ্যামাউন্ট গৃহীত হয়েছে:</b> <code>{amount} {currency}</code>\n\n"
        f"👉 এখন আপনার পেমেন্টের <b>Transaction ID (TrxID)</b> লিখে সেন্ড করুন:\n"
        f"<i>(উদাহরণ: BL74920194 অথবা Binance Order ID)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(DepositState.waiting_for_trx_id)
async def process_trx_id(message: Message, state: FSMContext):
    trx_id = message.text.strip() if message.text else ""
    if len(trx_id) < 4:
        await message.answer("❌ সঠিক ও স্পষ্ট Transaction ID (TrxID) লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
        
    await state.update_data(trx_id=trx_id)
    await state.set_state(DepositState.waiting_for_screenshot)
    
    # MANDATORY SCREENSHOT PROMPT
    await message.answer(
        "📸 <b>বাধ্যতামূলক স্ক্রিনশট (Photo) আপলোড করুন:</b>\n\n"
        "⚠️ পেমেন্ট সফল হওয়ার স্পষ্ট স্ক্রিনশট (Photo) সেন্ড করুন।\n"
        "<b>স্ক্রিনশট ছাড়া আপনার ডিপোজিট ভেরিফাই হবে না!</b>\n\n"
        "👇 গ্যালারি থেকে পেমেন্টের স্ক্রিনশটটি এখনই সেন্ড করুন:",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(DepositState.waiting_for_screenshot)
async def process_screenshot_input(message: Message, state: FSMContext, bot: Bot):
    file_id = None
    is_doc = False

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        mime = (message.document.mime_type or "").lower()
        name = (message.document.file_name or "").lower()
        if mime.startswith("image/") or any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            file_id = message.document.file_id
            is_doc = True

    if not file_id:
        await message.answer(
            "❌ <b>সঠিক স্ক্রিনশট পাওয়া যায়নি!</b>\n\n"
            "⚠️ ডিপোজিট ভেরিফাই করতে পেমেন্ট সফল হওয়ার স্পষ্ট <b>স্ক্রিনশটের ছবি বা ইমেজ ফাইল (.png/.jpg)</b> পাঠান।\n"
            "বাতিল করতে চাইলে নিচের বাটনে চাপুন বা /cancel লিখুন:",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    method = data["method"]
    amount = data["amount"]
    currency = data["currency"]
    trx_id = data["trx_id"]
    user = message.from_user
    
    await state.clear()
    
    # 1. Save to Database
    trx_db_id = db.create_deposit_request(
        user_id=user.id,
        method=method,
        amount=amount,
        currency=currency,
        trx_id=trx_id,
        screenshot_file_id=file_id
    )
    
    # 2. Inform the User WITH MANDATORY FAST-APPROVE ADMIN KNOCK PROMPT
    user_confirm_text = (
        "⏳ <b>আপনার ডিপোজিট রিকোয়েস্ট সাবমিট হয়েছে এবং পেন্ডিং আছে!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>পেমেন্ট মেথড:</b> {PAYMENT_CONFIG[method]['name']}\n"
        f"💰 <b>অ্যামাউন্ট:</b> <code>{amount} {currency}</code>\n"
        f"🔢 <b>TrxID:</b> <code>{html.escape(trx_id)}</code>\n"
        f"🆔 <b>ডিপোজিট রিকোয়েস্ট নং:</b> <code>#{trx_db_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ <b>দ্রুত অ্যাপ্রুভ পেতে সরাসরি অ্যাডমিনকে নক দিন:</b>\n"
        f"👉 অ্যাডমিন আইডি: @{ADMIN_USERNAME}\n"
        "<i>অ্যাডমিন স্ক্রিনশট ও TrxID চেক করে অবিলম্বে ওয়ালেটে ব্যালেন্স যুক্ত করে দেবেন।</i>"
    )
    
    await message.answer(
        user_confirm_text,
        reply_markup=get_pending_deposit_kb(ADMIN_USERNAME),
        parse_mode="HTML"
    )
    
    # 3. Send Prompt Instant Alert to all Admins with attached Screenshot & 1-click action buttons
    trx_payload = {
        "id": trx_db_id,
        "method_name": PAYMENT_CONFIG[method]['name'],
        "amount": amount,
        "currency": currency,
        "trx_id": trx_id
    }
    user_payload = {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username
    }
    await notify_admin_deposit(bot, trx_payload, user_payload, file_id, is_document=is_doc)

# cancel_fsm callback is handled globally by core.router (registered first in bot.py)

