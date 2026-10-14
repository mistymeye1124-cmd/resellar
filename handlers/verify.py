# Reseller Verification Handler - Real-Time Trust & Scammer Prevention Engine
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import db
from keyboards.user_kb import get_reseller_verification_kb, get_cancel_fsm_kb
from config import OFFICIAL_CHANNEL
from utils.ui_nav import render_screen
from utils.i18n import t
import html

router = Router()

class VerifyResellerState(StatesGroup):
    waiting_for_reseller_id = State()

def generate_verification_certificate(target_user: dict, query: str, lang: str = "bn") -> str:
    """Generates official verified trust certificate or scammer warning."""
    clean_q = html.escape(query)
    if not target_user:
        if lang == "en":
            return (
                "🚨 <b>Scam Alert & Warning</b> 🚨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔍 <b>Searched ID / Code:</b> <code>{clean_q}</code>\n"
                "❌ <b>Result:</b> No record found in our database!\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ <b>Warning:</b>\n"
                "This reseller code or Telegram ID is NOT recognized by our platform! "
                "It may be a fraudulent claim or counterfeit merchant.\n\n"
                "🛑 <b>Do NOT send money or conduct transactions with this individual!</b>"
            )
        return (
            "🚨 <b>তীব্র প্রতারণা সতর্কতা (Scam Alert)</b> 🚨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>অনুসন্ধানকৃত আইডি/কোড:</b> <code>{clean_q}</code>\n"
            "❌ <b>ফলাফল:</b> ডাটাবেসে কোনো অস্তিত্ব পাওয়া যায়নি!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ <b>সতর্কবার্তা:</b>\n"
            "এই রিসেলার কোড বা টেলিগ্রাম আইডির কোনো স্বীকৃতি আমাদের <b>Pro Access BD</b> প্ল্যাটফর্মে নেই! "
            "এটি কোনো প্রতারক চক্রের ভুয়া দাবি বা অস্তিত্বহীন আইডি হতে পারে।\n\n"
            "🛑 <b>কোনো অবস্থাতেই এই ব্যক্তিকে টাকা পাঠাবেন না!</b>"
        )

    is_res = target_user.get("is_reseller", 0) == 1
    is_perm = target_user.get("reseller_deactivated_permanent", 0) == 1 or target_user.get("is_reseller", 0) == -1
    is_banned = target_user.get("is_banned", 0) == 1

    fname = html.escape(target_user.get("first_name", "N/A"))
    raw_uname = target_user.get("username")
    uname_str = f"<code>@{html.escape(raw_uname)}</code>" if raw_uname else "<code>N/A</code>"

    if is_perm or is_banned:
        if lang == "en":
            return (
                "⚠️ <b>Warning: Reseller License Deactivated</b> ⚠️\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>Reseller Code:</b> <code>{target_user.get('reseller_code', 'RS-N/A')}</code>\n"
                f"👤 <b>Name:</b> {fname}\n"
                f"📱 <b>Telegram:</b> {uname_str}\n"
                "🔴 <b>Status:</b> ❌ Terminated / Suspended\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🛑 <b>Notice:</b>\n"
                "This account was permanently deactivated due to policy violations or failing sales quotas. "
                "They do not possess authorization to sell our products or services.\n\n"
                "Do not conduct financial transactions with this user."
            )
        return (
            "⚠️ <b>সতর্কতা: রিসেলার লাইসেন্স বাতিলকৃত (Deactivated)</b> ⚠️\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>রিসেলার কোড:</b> <code>{target_user.get('reseller_code', 'RS-N/A')}</code>\n"
            f"👤 <b>নাম:</b> {fname}\n"
            f"📱 <b>টেলিগ্রাম:</b> {uname_str}\n"
            "🔴 <b>বর্তমান স্ট্যাটাস:</b> ❌ লাইসেন্স বাতিল / স্থগিত (Terminated)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛑 <b>জরুরি নোটিশ:</b>\n"
            "এই ব্যক্তির রিসেলার অনুমোদন পলিসি লঙ্ঘনের কারণে অথবা সেলস কোটা পূরণ না করায় <b>স্থগিত ও স্থায়ীভাবে বাতিল</b> করা হয়েছে। "
            "বর্তমানে এই ব্যক্তি আমাদের কোনো কোর্স বা সার্ভিস বিক্রি করার অধিকার রাখেন না।\n\n"
            "এর সাথে কোনো আর্থিক লেনদেন করবেন না! প্রতারিত হলে কর্তৃপক্ষ দায়ী থাকবে না।"
        )

    if is_res:
        joined_date = target_user.get("reseller_quota_start") or target_user.get("joined_at") or "2026-01-01"
        tier = target_user.get("reseller_tier", 1)
        perms = db.get_user_permissions(target_user.get("user_id", 0))
        is_elite = tier >= 2 or perms.get("can_sell_account", False)

        if lang == "en":
            tier_line = (
                "👑 <b>Partnership Tier:</b> <code>👑 Elite VIP Partner</code>\n"
                "🏷️ <b>Authorized Scope:</b> <b>VIP Channels + Personal Accounts</b>\n"
                if is_elite else
                "🥉 <b>Partnership Tier:</b> <code>🥉 Standard Partner</code>\n"
                "🏷️ <b>Authorized Scope:</b> <b>Official VIP Telegram Channels</b>\n"
            )
            return (
                "🛡️ <b>Official Verified Reseller Partner</b> 🛡️\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🎖️ <b>Recognition:</b> ✅ Authorized Official Reseller\n"
                f"{tier_line}"
                f"👤 <b>Reseller Name:</b> {fname}\n"
                f"🆔 <b>Verification Code:</b> <code>{target_user.get('reseller_code', 'RS-N/A')}</code>\n"
                f"📱 <b>Telegram Profile:</b> {uname_str}\n"
                "🟢 <b>Status:</b> ✅ Active & Authorized Merchant\n"
                f"📅 <b>Authorization Date:</b> <code>{str(joined_date)[:10]}</code>\n"
                "⭐ <b>Trust Score:</b> ⭐️⭐️⭐️⭐️⭐️ (100% Genuine)\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💬 <b>Official Guarantee:</b>\n"
                f"This individual is an officially registered reseller of <b>{OFFICIAL_CHANNEL}</b>. "
                "You may safely purchase courses and digital subscriptions through them.\n\n"
                "VIP access and instant delivery for all orders placed through this partner are backed by our bot."
            )

        tier_line_bn = (
            "👑 <b>পার্টনারশিপ লেভেল:</b> <code>👑 Elite VIP পার্টনার</code>\n"
            "🏷️ <b>অনুমোদিত বিক্রয়:</b> <b>ভিআইপি চ্যানেল + পার্সোনাল একাউন্ট</b>\n"
            if is_elite else
            "🥉 <b>পার্টনারশিপ লেভেল:</b> <code>🥉 Standard পার্টনার</code>\n"
            "🏷️ <b>অনুমোদিত বিক্রয়:</b> <b>অফিশিয়াল ভিআইপি চ্যানেল অ্যাক্সেস</b>\n"
        )
        return (
            "🛡️ <b>অফিশিয়াল ভেরিফাইড রিসেলার পার্টনার (Verified Partner)</b> 🛡️\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎖️ <b>স্বীকৃতি:</b> ✅ অনুমোদিত অফিশিয়াল পার্টনার\n"
            f"{tier_line_bn}"
            f"👤 <b>রিসেলার নাম:</b> {fname}\n"
            f"🆔 <b>ভেরিফিকেশন কোড:</b> <code>{target_user.get('reseller_code', 'RS-N/A')}</code>\n"
            f"📱 <b>টেলিগ্রাম প্রোফাইল:</b> {uname_str}\n"
            "🟢 <b>রানিং স্ট্যাটাস:</b> ✅ সক্রিয় ও অনুমোদিত (Active Merchant)\n"
            f"📅 <b>অনুমোদন তারিখ:</b> <code>{str(joined_date)[:10]}</code>\n"
            "⭐ <b>ট্রাস্ট স্কোর:</b> ⭐️⭐️⭐️⭐️⭐️ (100% Genuine)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💬 <b>কর্তৃপক্ষের নিশ্চয়তা:</b>\n"
            f"এই ব্যক্তি <b>{OFFICIAL_CHANNEL}</b> এর একজন অফিশিয়াল রেজিস্টার্ড রিসেলার। "
            "আপনি তাঁর কাছ থেকে নিশ্চিন্তে এবং সম্পূর্ণ নিরাপদে যেকোনো কোর্স বা ডিজিটাল টুলস কিনতে পারেন।\n\n"
            "তাঁর মাধ্যমে অর্ডার করা সমস্ত কোর্সের ১০০% ভিআইপি অ্যাক্সেস ও ডেলিভারি আমাদের বট স্বয়ংক্রিয়ভাবে নিশ্চিত করে।"
        )

    # Regular user, not a reseller
    if lang == "en":
        return (
            "ℹ️ <b>Regular User (Not an Authorized Reseller)</b> ℹ️\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name:</b> {fname}\n"
            f"🆔 <b>User ID:</b> <code>{target_user.get('user_id')}</code>\n"
            f"📱 <b>Username:</b> {uname_str}\n"
            "🟡 <b>Status:</b> Regular Customer Only\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>Notice:</b>\n"
            "This account is registered as a regular buyer, <b>not an authorized wholesale reseller partner</b>. "
            "Exercise caution if conducting third-party transactions."
        )
    return (
        "ℹ️ <b>সাধারণ ব্যবহারকারী (Not a Reseller)</b> ℹ️\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>নাম:</b> {fname}\n"
        f"🆔 <b>আইডি:</b> <code>{target_user.get('user_id')}</code>\n"
        f"📱 <b>ইউজারনেম:</b> {uname_str}\n"
        "🟡 <b>স্ট্যাটাস:</b> সাধারণ ক্রেতা (Regular Customer Only)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 <b>তথ্য:</b>\n"
        "এই অ্যাকাউন্টটি আমাদের ডাটাবেসে সাধারণ ক্রেতা হিসেবে নিবন্ধিত, কিন্তু তিনি কোনো <b>অনুমোদিত রিসেলার বা পাইকারি পার্টনার নন</b>। "
        "তাঁর সাথে রিসেলিং সংক্রান্ত কোনো বড় লেনদেন করলে নিজ দায়িত্বে সতর্কতার সাথে করবেন।"
    )

@router.message(Command("verify"))
async def handle_cmd_verify(message: Message, state: FSMContext):
    """Handles /verify and /verify <id|code|@username> directly."""
    lang = db.get_user_language(message.from_user.id)
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) > 1:
        query = args[1].strip()
        target = db.verify_reseller(query)
        cert = generate_verification_certificate(target, query, lang=lang)
        uname = target.get("username") if target else None
        try:
            await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang), parse_mode="HTML")
        except Exception:
            await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang))
        return

    await state.set_state(VerifyResellerState.waiting_for_reseller_id)
    if lang == "en":
        prompt_text = (
            "🛡️ <b>Reseller Trust Verification Portal</b>\n\n"
            "Enter the seller's <b>Reseller Code (e.g. <code>RS-1002</code>)</b>, <b>Telegram @username</b>, or <b>Numeric ID</b>:\n\n"
            "<i>We will verify their authentication status in real-time from our database.</i>"
        )
    else:
        prompt_text = (
            "🛡️ <b>রিসেলার সততা যাচাইকরণ পোর্টাল (Reseller Verification)</b>\n\n"
            "আপনি যার কাছ থেকে কোর্স কিনছেন তাঁর দেওয়া <b>রিসেলার কোড (যেমন: <code>RS-1002</code>)</b>, <b>টেলিগ্রাম @ইউজারনেম</b> অথবা <b>আইডি</b> লিখে সেন্ড করুন:\n\n"
            "<i>আমরা রিয়েল-টাইমে ডাটাবেস যাচাই করে জানিয়ে দিব তিনি আমাদের অফিশিয়াল অথোরাইজড রিসেলার কিনা।</i>"
        )
    await message.answer(prompt_text, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")

@router.message(F.text.in_([
    "Verify Reseller (রিসেলার যাচাই)", "🛡️ Verify Reseller (রিসেলার যাচাই)", 
    "Verify Reseller", "🛡️ Verify Reseller", 
    "रीसेलर सत्यापन (Verify Reseller)", "🛡️ रीसेलर सत्यापन (Verify Reseller)",
    "রিসেলার যাচাই", "verify", "Verify"
]))
async def handle_verify_button_click(message: Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    await state.set_state(VerifyResellerState.waiting_for_reseller_id)
    if lang == "en":
        prompt_text = (
            "🛡️ <b>Reseller Trust Verification Portal</b>\n\n"
            "Enter the seller's <b>Reseller Code (e.g. <code>RS-1002</code>)</b>, <b>Telegram @username</b>, or <b>Numeric ID</b>:\n\n"
            "<i>We will verify their authentication status in real-time from our database.</i>"
        )
    else:
        prompt_text = (
            "🛡️ <b>রিসেলার সততা যাচাইকরণ পোর্টাল (Reseller Verification)</b>\n\n"
            "আপনি যার কাছ থেকে কোর্স কিনছেন তাঁর দেওয়া <b>রিসেলার কোড (যেমন: <code>RS-1002</code>)</b>, <b>টেলিগ্রাম @ইউজারনেম</b> অথবা <b>আইডি</b> লিখে সেন্ড করুন:\n\n"
            "<i>আমরা রিয়েল-টাইমে ডাটাবেস যাচাই করে জানিয়ে দিব তিনি আমাদের অফিশিয়াল অথোরাইজড রিসেলার কিনা।</i>"
        )
    await message.answer(prompt_text, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")

@router.callback_query(F.data == "verify_reseller_prompt")
async def handle_verify_cb_prompt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    await state.set_state(VerifyResellerState.waiting_for_reseller_id)
    if lang == "en":
        prompt_text = (
            "🛡️ <b>Reseller Trust Verification Portal</b>\n\n"
            "Send the reseller's <b>Code (RS-1001)</b>, <b>@username</b>, or <b>Numeric ID</b>:"
        )
    else:
        prompt_text = (
            "🛡️ <b>রিসেলার সততা যাচাইকরণ পোর্টাল</b>\n\n"
            "রিসেলারের <b>কোড (RS-1001)</b>, <b>@ইউজারনেম</b> অথবা <b>আইডি</b> লিখে মেসেজ দিন:"
        )
    await render_screen(call, prompt_text, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")

@router.message(VerifyResellerState.waiting_for_reseller_id)
async def handle_process_verify_input(message: Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    query = message.text.strip() if message.text else ""
    if not query or query.lower() in ["/cancel", "cancel", "বাতিল", "বাতিল করুন"]:
        await state.clear()
        cancel_txt = "❌ Verification process cancelled." if lang == "en" else "❌ রিসেলার সততা যাচাইকরণ প্রক্রিয়াটি বাতিল করা হয়েছে।"
        await message.answer(cancel_txt)
        return
    if query.startswith("/"):
        await state.clear()
        return

    await state.clear()
    
    target = db.verify_reseller(query)
    cert = generate_verification_certificate(target, query, lang=lang)
    uname = target.get("username") if target else None
    
    try:
        await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang), parse_mode="HTML")
    except Exception:
        await message.answer(cert, reply_markup=get_reseller_verification_kb(uname, lang=lang))
