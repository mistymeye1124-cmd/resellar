import html
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from database.db import db
from config import ADMIN_IDS, ADMIN_USERNAME

router = Router()

@router.callback_query(F.data.startswith("approve_dep:"))
async def handle_approve_deposit(call: CallbackQuery, bot: Bot):
    admin_id = call.from_user.id
    if not (not ADMIN_IDS or ADMIN_IDS == [0] or admin_id in ADMIN_IDS or db.is_sub_admin(admin_id)):
        await call.answer("❌ আপনার এই অ্যাকশনের পারমিশন নেই!", show_alert=True)
        return
        
    trx_id = int(call.data.split(":")[1])
    trx = db.approve_deposit(trx_id, admin_id)
    
    if not trx:
        await call.answer("⚠️ এই রিকোয়েস্টটি ইতিমধ্যে প্রসেস করা হয়েছে!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return
        
    await call.answer("✅ ডিপোজিট সফলভাবে অ্যাপ্রুভ করা হয়েছে!", show_alert=True)
    
    # Update admin message
    admin_name = html.escape(str(call.from_user.username or call.from_user.first_name or "Admin"))
    base_text = call.message.caption or call.message.text or ""
    new_text = base_text + f"\n\n━━━━━━━━━━━━━━━━━━━━\n✅ <b>APPROVED by @{admin_name}</b>"
    try:
        if call.message.caption:
            await call.message.edit_caption(caption=new_text, reply_markup=None, parse_mode="HTML")
        else:
            await call.message.edit_text(text=new_text, reply_markup=None, parse_mode="HTML")
    except Exception:
        await call.message.edit_reply_markup(reply_markup=None)
        
    # Notify user
    target_user_id = trx["user_id"]
    updated_user = db.get_user(target_user_id)
    curr_bdt = updated_user["balance_bdt"] if updated_user else 0.0
    curr_usd = updated_user["balance_usd"] if updated_user else 0.0
    
    user_notify_text = (
        "🎉 **অভিনন্দন! আপনার ডিপোজিট অনুমোদিত হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **যুক্ত হওয়া ব্যালেন্স:** `+{trx['amount']} {trx['currency']}`\n"
        f"🔢 **TrxID:** `{trx['trx_id']}`\n"
        f"💳 **বর্তমান ওয়ালেট ব্যালেন্স:**\n"
        f"• BDT: `৳{curr_bdt:.2f}`\n"
        f"• USD: `${curr_usd:.2f}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 এখন আপনি যেকোনো কোর্স বা প্রোডাক্ট অর্ডার করতে পারেন!"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=user_notify_text, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data.startswith("reject_dep:"))
async def handle_reject_deposit(call: CallbackQuery, bot: Bot):
    admin_id = call.from_user.id
    if not (not ADMIN_IDS or ADMIN_IDS == [0] or admin_id in ADMIN_IDS or db.is_sub_admin(admin_id)):
        await call.answer("❌ আপনার এই অ্যাকশনের পারমিশন নেই!", show_alert=True)
        return
        
    trx_id = int(call.data.split(":")[1])
    trx = db.reject_deposit(trx_id, admin_id)
    
    if not trx:
        await call.answer("⚠️ এই রিকোয়েস্টটি ইতিমধ্যে প্রসেস করা হয়েছে!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return
        
    await call.answer("❌ ডিপোজিট বাতিল করা হয়েছে।", show_alert=True)
    
    # Update admin message
    admin_name = html.escape(str(call.from_user.username or call.from_user.first_name or "Admin"))
    base_text = call.message.caption or call.message.text or ""
    new_text = base_text + f"\n\n━━━━━━━━━━━━━━━━━━━━\n❌ <b>REJECTED by @{admin_name}</b>"
    try:
        if call.message.caption:
            await call.message.edit_caption(caption=new_text, reply_markup=None, parse_mode="HTML")
        else:
            await call.message.edit_text(text=new_text, reply_markup=None, parse_mode="HTML")
    except Exception:
        await call.message.edit_reply_markup(reply_markup=None)
        
    # Notify user
    target_user_id = trx["user_id"]
    user_notify_text = (
        "❌ **আপনার ডিপোজিট রিকোয়েস্ট বাতিল করা হয়েছে!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **অ্যামাউন্ট:** `{trx['amount']} {trx['currency']}`\n"
        f"🔢 **TrxID:** `{trx['trx_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ **সম্ভাব্য কারণ:** ভুল TrxID অথবা পেমেন্টের স্পষ্ট স্ক্রিনশট ছিল না।\n\n"
        f"💬 যেকোনো সমস্যা বা দ্রুত সমাধানের জন্য অ্যাডমিনকে নক দিন:\n"
        f"👉 @{ADMIN_USERNAME}"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=user_notify_text, parse_mode="Markdown")
    except Exception:
        pass
