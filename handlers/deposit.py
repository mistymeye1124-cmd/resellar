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
    "💳 অ্যাড ব্যালেন্স (Deposit)", "অ্যাড ব্যালেন্স (Deposit)", "💳 অ্যাড ব্যালেন্স", "অ্যাড ব্যালেন্স",
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
    lang = db.get_user_language(call.from_user.id)
    if method_key not in PAYMENT_CONFIG:
        await call.answer(t("deposit_invalid_method_alert", lang), show_alert=True)
        return
        
    if not db.is_gateway_active(method_key):
        await call.answer(t("deposit_method_maintenance_alert", lang), show_alert=True)
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
    
    lang = db.get_user_language(call.from_user.id)
    unit = ("BDT" if cfg["currency"] == "BDT" else "USDT ($)") if lang in ["en", "hi"] else ("টাকা" if cfg["currency"] == "BDT" else "USDT ($)")
    type_badge = ("🏪 <b>Agent Cash Out Number:</b>" if method_key in ["bkash", "nagad"] else "📌 <b>Account Number / Pay ID:</b>") if lang in ["en", "hi"] else ("🏪 <b>এজেন্ট ক্যাশ আউট নম্বর:</b>" if method_key in ["bkash", "nagad"] else "📌 <b>অ্যাকাউন্ট নম্বর / Pay ID:</b>")
    action_verb = ("Cash Out" if method_key in ["bkash", "nagad"] else "Send Money / Transfer") if lang in ["en", "hi"] else ("ক্যাশ আউট" if method_key in ["bkash", "nagad"] else "সেন্ড মানি / ট্রান্সফার")
    gateway_emoji = em_tag(method_key, "💳")
    
    if lang in ["en", "hi"]:
        text = (
            f"{gateway_emoji} <b>Payment Gateway: {html.escape(cfg['name'])}</b> {gateway_emoji}\n\n"
            f"{type_badge}\n"
            f"<pre>{html.escape(active_number)}</pre>\n"
            f"<i>(Tap the number above to copy instantly)</i>\n\n"
            f"📝 <b>Instructions:</b> {html.escape(active_instruction)}\n"
            f"⚠️ <b>Minimum Deposit:</b> <b>{int(min_dep) if min_dep.is_integer() else min_dep} {unit}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 Please enter the amount in <b>{unit}</b> that you {action_verb} below:\n"
            f"<i>(Example: 500 or 1000)</i>"
        )
    else:
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
    await render_screen(call, text, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")

@router.message(DepositState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    text = message.text.strip() if message.text else ""
    try:
        amount = float(text)
    except ValueError:
        err_msg = "❌ Invalid input! Please enter numbers only (e.g., 500 or 10):" if lang in ["en", "hi"] else "❌ ভুল ইনপুট! অনুগ্রহ করে শুধুমাত্র সংখ্যা লিখুন (যেমন: 500 বা 10):"
        await message.answer(err_msg, reply_markup=get_cancel_fsm_kb(lang=lang))
        return
        
    data = await state.get_data()
    min_dep = data.get("min_deposit", 50)
    currency = data.get("currency", "BDT")
    
    if amount < min_dep:
        min_msg = f"❌ Minimum deposit is <code>{min_dep} {currency}</code>. Please enter a valid amount:" if lang in ["en", "hi"] else f"❌ সর্বনিম্ন ডিপোজিট <code>{min_dep} {currency}</code>। সঠিক অ্যামাউন্ট লিখুন:"
        await message.answer(min_msg, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")
        return
        
    await state.update_data(amount=amount)
    await state.set_state(DepositState.waiting_for_trx_id)
    
    prompt_text = t("dep_amount_accepted", lang, amount=amount, currency=currency)
    await message.answer(
        prompt_text,
        reply_markup=get_cancel_fsm_kb(lang=lang),
        parse_mode="HTML"
    )

@router.message(DepositState.waiting_for_trx_id)
async def process_trx_id(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    trx_id = message.text.strip() if message.text else ""
    if len(trx_id) < 4:
        err_msg = "❌ Please enter a valid Transaction ID (TrxID):" if lang in ["en", "hi"] else "❌ সঠিক ও স্পষ্ট Transaction ID (TrxID) লিখুন:"
        await message.answer(err_msg, reply_markup=get_cancel_fsm_kb(lang=lang))
        return
        
    await state.update_data(trx_id=trx_id)
    await state.set_state(DepositState.waiting_for_screenshot)
    
    # MANDATORY SCREENSHOT PROMPT
    prompt_text = t("dep_screenshot_prompt", lang)
    await message.answer(
        prompt_text,
        reply_markup=get_cancel_fsm_kb(lang=lang),
        parse_mode="HTML"
    )

@router.message(DepositState.waiting_for_screenshot)
async def process_screenshot_input(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
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
        if lang in ["en", "hi"]:
            err_msg = (
                "❌ <b>Valid screenshot not found!</b>\n\n"
                "⚠️ To verify deposit, please send a clear <b>photo or screenshot image (.png/.jpg)</b>.\n"
                "To cancel, tap below or type /cancel:"
            )
        else:
            err_msg = (
                "❌ <b>সঠিক স্ক্রিনশট পাওয়া যায়নি!</b>\n\n"
                "⚠️ ডিপোজিট ভেরিফাই করতে পেমেন্ট সফল হওয়ার স্পষ্ট <b>স্ক্রিনশটের ছবি বা ইমেজ ফাইল (.png/.jpg)</b> পাঠান।\n"
                "বাতিল করতে চাইলে নিচের বাটনে চাপুন বা /cancel লিখুন:"
            )
        await message.answer(
            err_msg,
            reply_markup=get_cancel_fsm_kb(lang=lang),
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
    user_confirm_text = t(
        "dep_pending_receipt",
        lang,
        method_name=PAYMENT_CONFIG[method]['name'],
        amount=amount,
        currency=currency,
        trx_id=html.escape(trx_id),
        req_id=trx_db_id,
        admin=ADMIN_USERNAME
    )
    
    await message.answer(
        user_confirm_text,
        reply_markup=get_pending_deposit_kb(ADMIN_USERNAME, lang=lang),
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

