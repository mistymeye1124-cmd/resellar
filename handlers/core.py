# Universal Core & Global Commands Router
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database.db import db
from keyboards.user_kb import get_main_dashboard_inline_kb, get_main_reply_kb
from utils.ui_nav import render_screen
from utils.i18n import t
import html

router = Router()

def is_admin(user_id: int) -> bool:
    from handlers.start import is_admin as _is_admin
    return _is_admin(user_id)

CANCEL_WORDS = [
    "/cancel", "cancel", "বাতিল", "বাতিল করুন", "বন্ধ", "বন্ধ করুন", "stop", "/stop"
]

# --- 1. ABSOLUTE TOP PRIORITY: /start & Escape from ANY state ---

@router.message(CommandStart())
async def handle_core_start(message: Message, state: FSMContext):
    """Guarantees /start always resets any FSM state and delivers fresh bot dashboard."""
    await state.clear()
    from handlers.start import handle_start
    await handle_start(message, state)

@router.message(Command("cancel"))
@router.message(F.text.casefold().in_(CANCEL_WORDS))
async def handle_global_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await state.clear()
    user_id = message.from_user.id

    # If admin was in an admin panel flow, route back to admin dashboard
    if is_admin(user_id) and current_state and any(tag in str(current_state).lower() for tag in ["admin", "prod", "cat", "drop", "stock", "groq", "coupon"]):
        from handlers.admin_panel import get_admin_dashboard_text
        from keyboards.admin_kb import get_admin_main_dashboard_kb
        text = get_admin_dashboard_text()
        await message.answer(text, reply_markup=get_admin_main_dashboard_kb(), parse_mode="HTML")
        return

    from handlers.start import format_main_dashboard_text
    lang = db.get_user_language(user_id)
    text = t("global_cancelled_msg", lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(user_id))
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "cancel_fsm")
async def handle_cancel_fsm_cb(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    await state.clear()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    await call.answer(t("global_cancelled_alert", lang))

    if is_admin(user_id) and current_state and any(tag in str(current_state).lower() for tag in ["admin", "prod", "cat", "drop", "stock", "groq", "coupon"]):
        from handlers.admin_panel import handle_admin_main_dashboard
        await handle_admin_main_dashboard(call, state)
        return

    from handlers.start import format_main_dashboard_text
    text = format_main_dashboard_text(user_id, call.from_user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(user_id))
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

# --- 2. GLOBAL SHORTCUT COMMANDS (Available everywhere with auto-state clear) ---

@router.message(Command("admin"))
async def handle_core_admin(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if is_admin(user_id):
        from handlers.admin_panel import get_admin_dashboard_text
        from keyboards.admin_kb import get_admin_main_dashboard_kb
        text = get_admin_dashboard_text()
        await message.answer(text, reply_markup=get_admin_main_dashboard_kb(), parse_mode="HTML")
    else:
        from handlers.start import handle_start
        await handle_start(message, state)

@router.message(Command("menu"))
@router.message(F.text.in_([
    "Menu", "মেনু", "Main Menu", "মূল মেনু", "হোম", "Home",
    "🏠 মূল মেনু (Start / Menu)", "🏠 Main Menu (Start)", "🏠 मुख्य मेनू (Start)",
    "মূল মেনু (Start / Menu)", "Main Menu (Start)", "Start", "স্টার্ট", "🏠 Start"
]))
async def handle_core_menu_click(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import format_main_dashboard_text
    user = message.from_user
    lang = db.get_user_language(user.id)
    text = format_main_dashboard_text(user.id, user, lang)
    kb = get_main_dashboard_inline_kb(lang, is_admin=is_admin(user.id))
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.message(Command("courses"))
@router.message(Command("shop"))
async def handle_cmd_courses(message: Message, state: FSMContext):
    await state.clear()
    from handlers.catalog import handle_browse_courses
    await handle_browse_courses(message)

@router.message(Command("deposit"))
@router.message(Command("balance"))
async def handle_cmd_deposit(message: Message, state: FSMContext):
    await state.clear()
    from handlers.deposit import handle_deposit_menu
    await handle_deposit_menu(message, state)

@router.message(Command("profile"))
async def handle_cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import handle_profile
    await handle_profile(message)

@router.message(Command("orders"))
async def handle_cmd_orders(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import handle_my_purchases
    await handle_my_purchases(message)

@router.message(Command("free"))
@router.message(Command("claim"))
async def handle_cmd_free(message: Message, state: FSMContext):
    await state.clear()
    from handlers.free_claim import handle_free_claim_cmd
    await handle_free_claim_cmd(message)

@router.message(Command("verify"))
async def handle_cmd_verify(message: Message, state: FSMContext):
    await state.clear()
    from handlers.verify import handle_cmd_verify
    await handle_cmd_verify(message)

@router.message(Command("help"))
@router.message(Command("support"))
async def handle_cmd_help(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import handle_support
    await handle_support(message)

@router.message(Command("reseller"))
@router.message(Command("resellers"))
async def handle_cmd_reseller(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if is_admin(user_id):
        from handlers.admin_panel import handle_cmd_resellers
        await handle_cmd_resellers(message)
    else:
        from handlers.reseller import handle_reseller_hub
        await handle_reseller_hub(message)

# --- 3. UNIVERSAL FSM ESCAPE GUARD FOR ANY TELEGRAM SLASH COMMAND ---
@router.message(F.text.startswith("/"))
async def handle_unknown_command_in_fsm(message: Message, state: FSMContext):
    """If user types ANY command starting with '/' while inside an FSM state, clear state and return home."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        from handlers.start import handle_start
        await handle_start(message, state)
