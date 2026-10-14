# Notification System for Reseller Bot
import html
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS

logger = logging.getLogger("ResellerBot.Notifier")

def escape(text: str) -> str:
    """Safely escape text for Telegram HTML parse_mode."""
    if text is None:
        return ""
    return html.escape(str(text))

async def notify_admin_deposit(bot: Bot, trx: dict, user: dict, file_id: str = None, is_document: bool = False):
    """
    Sends prominent instant alert to admins with 1-click Approve / Reject / Dossier controls.
    """
    user_name = escape(user.get("full_name") or user.get("first_name") or "User")
    username_val = user.get("username")
    username = f"@{escape(username_val)}" if username_val else "N/A"
    method_name = escape(trx.get("method_name") or trx.get("method") or "Manual")
    amount = trx.get("amount", 0)
    currency = trx.get("currency", "BDT")
    trx_id_str = escape(trx.get("trx_id", ""))
    trx_db_id = trx.get("id")
    target_user_id = user.get("id") or user.get("user_id")

    caption = (
        f"🚨 <b>[নতুন ডিপোজিট রিকোয়েস্ট / DEPOSIT ALERT]</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>রিকোয়েস্ট নং:</b> <code>#{trx_db_id}</code>\n"
        f"👤 <b>ইউজার:</b> {user_name} ({username})\n"
        f"🆔 <b>ইউজার আইডি:</b> <code>{target_user_id}</code>\n"
        f"💳 <b>পেমেন্ট মেথড:</b> {method_name}\n"
        f"💰 <b>ডিপোজিট অ্যামাউন্ট:</b> <code>৳{amount} {currency}</code>\n"
        f"🔢 <b>TrxID:</b> <code>{trx_id_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>ভেরিফাই করে নিচের অ্যাকশন বাটনে চাপ দিন:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve (টাকা যোগ করুন)", callback_data=f"approve_dep:{trx_db_id}"),
            InlineKeyboardButton(text="❌ Reject (বাতিল)", callback_data=f"reject_dep:{trx_db_id}")
        ],
        [
            InlineKeyboardButton(text="👤 ইউজারের প্রোফাইল", callback_data=f"usr_ctl_view:{target_user_id}"),
            InlineKeyboardButton(text="💬 মেসেজ পাঠান", callback_data=f"usr_ctl_dm:{target_user_id}")
        ]
    ])

    for aid in ADMIN_IDS:
        if aid == 0:
            continue
        delivered = False
        if file_id:
            if is_document:
                try:
                    await bot.send_document(chat_id=aid, document=file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
                    delivered = True
                except Exception as e:
                    logger.warning(f"Could not send deposit document to admin {aid}: {e}")
            if not delivered:
                try:
                    await bot.send_photo(chat_id=aid, photo=file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
                    delivered = True
                except Exception as e:
                    logger.warning(f"Could not send deposit photo to admin {aid}: {e}")
        
        if not delivered:
            try:
                await bot.send_message(chat_id=aid, text=caption, reply_markup=kb, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Could not send deposit alert text to admin {aid}: {e}")


async def notify_admin_order(bot: Bot, order: dict, user: dict):
    """
    Sends prominent instant alert to admins when any user purchases an item.
    """
    user_name = escape(user.get("full_name") or user.get("first_name") or "User")
    username_val = user.get("username")
    username = f"@{escape(username_val)}" if username_val else "N/A"
    user_id = user.get("id") or user.get("user_id")
    order_id = order.get("id")
    title = escape(order.get("product_title", ""))
    amount = order.get("amount_paid", 0)
    currency = order.get("currency", "BDT")
    ptype = escape(order.get("product_type", "course"))
    is_reseller = order.get("is_reseller_order", False)
    rem_bal = order.get("remaining_balance", 0.0)
    is_manual = order.get("manual_delivery", False)
    manual_reason = escape(order.get("manual_reason", "ম্যানুয়াল প্রসেসিং প্রয়োজন"))

    role_badge = "💎 <b>রিসেলার পাইকারি ক্রয়</b>" if is_reseller else "👤 <b>খুচরা সাধারণ ক্রয়</b>"
    
    manual_block = ""
    if is_manual:
        manual_block = (
            f"\n\n🚨🚨 <b>[জরুরি: ক্রেতাকে অ্যাক্সেস লিংক দিতে হবে!]</b>\n"
            f"⚠️ <b>কারণ:</b> <i>{manual_reason}</i>\n"
            f"⚡ অনুগ্রহ করে অবিলম্বে নিচের বাটনে চাপ দিয়ে ক্রেতাকে ইনভাইট লিংক দিন।"
        )

    text = (
        f"🛍️ <b>[নতুন অর্ডার সম্পন্ন / NEW ORDER SALE]</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>অর্ডার নং:</b> <code>#{order_id}</code>\n"
        f"📦 <b>প্রোডাক্ট/কোর্স:</b> <b>{title}</b>\n"
        f"🏷️ <b>ধরন:</b> <code>{ptype}</code> | {role_badge}\n"
        f"💰 <b>পেইড অ্যামাউন্ট:</b> <code>৳{amount} {currency}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>ক্রেতা:</b> {user_name} ({username})\n"
        f"🆔 <b>ক্রেতার আইডি:</b> <code>{user_id}</code>\n"
        f"💳 <b>বর্তমান ওয়ালেট ব্যালেন্স:</b> <code>৳{rem_bal:.2f} BDT</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{manual_block}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 ক্রেতাকে মেসেজ পাঠান (DM)", callback_data=f"usr_ctl_dm:{user_id}"),
            InlineKeyboardButton(text="👤 ক্রেতার প্রোফাইল", callback_data=f"usr_ctl_view:{user_id}")
        ],
        [
            InlineKeyboardButton(text="📜 ইউজারের সব অর্ডার", callback_data=f"usr_ctl_orders:{user_id}")
        ]
    ])

    for aid in ADMIN_IDS:
        if aid == 0:
            continue
        try:
            await bot.send_message(chat_id=aid, text=text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Could not send order alert to admin {aid}: {e}")


async def notify_admin_reseller_app(bot: Bot, app_id: int, user: dict, info: str, balance: float):
    """
    Sends prominent instant alert to admins when a user submits a reseller application.
    """
    user_name = escape(user.get("full_name") or user.get("first_name") or "User")
    username_val = user.get("username")
    username = f"@{escape(username_val)}" if username_val else "N/A"
    user_id = user.get("id") or user.get("user_id")

    fee = 500.0
    remaining = max(0.0, balance - fee)
    text = (
        f"💎 <b>[নতুন রিসেলার আবেদন / RESELLER APPLICATION]</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>আবেদন নং:</b> <code>#{app_id}</code>\n"
        f"👤 <b>আবেদনকারী:</b> {user_name} ({username})\n"
        f"🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>\n"
        f"💰 <b>ওয়ালেট ব্যালেন্স:</b> <code>৳{balance:.2f} BDT</code> (>= ৳1,000 শর্ত পূরণ ✅)\n"
        f"🛡️ <b>অনুমোদনে ফি কর্তন হবে:</b> <code>৳{fee:.2f} BDT</code> (অটো-চার্জ)\n"
        f"💳 <b>অনুমোদনের পর ইউজারের থাকবে:</b> <code>৳{remaining:.2f} BDT</code> (শপিং ব্যালেন্স)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>মার্কেটিং প্রুফ / লিংক:</b>\n"
        f"<i>{escape(info)}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>অনুমোদন বা বাতিলের জন্য সরাসরি নিচে চাপ দিন:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Approve as Reseller", callback_data=f"approve_reseller_app:{app_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_reseller_app:{app_id}")
        ],
        [
            InlineKeyboardButton(text="👤 ইউজারের প্রোফাইল", callback_data=f"usr_ctl_view:{user_id}"),
            InlineKeyboardButton(text="💬 মেসেজ পাঠান", callback_data=f"usr_ctl_dm:{user_id}")
        ]
    ])

    for aid in ADMIN_IDS:
        if aid == 0:
            continue
        try:
            await bot.send_message(chat_id=aid, text=text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Could not send reseller app alert to admin {aid}: {e}")


async def notify_referral_rewards(bot: Bot, new_user_info: dict, res: dict):
    """
    Sends real-time high-converting celebration alerts to Tier-1, Tier-2 referrers, and new user.
    """
    new_name = escape(new_user_info.get("first_name") or "User")
    uname_str = f"(@{escape(new_user_info.get('username'))})" if new_user_info.get("username") else ""
    
    # 1. Tier-1 Direct Referrer Celebration Alert
    t1_id = res.get("t1_referrer_id")
    t1_bonus = res.get("t1_bonus", 10.0)
    t1_new_bal = res.get("t1_new_balance", 0.0)
    t1_count = res.get("t1_count", 1)
    
    if t1_id:
        t1_text = (
            f"🎉 <b>[নতুন রেফারেল বোনাস জমা হয়েছে!]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>নতুন মেম্বার:</b> {new_name} {uname_str}\n"
            f"💰 <b>টিয়ার-১ বোনাস:</b> <code>+৳{t1_bonus:.2f} BDT</code>\n"
            f"👥 <b>মোট ডিরেক্ট রেফারেল:</b> <code>{t1_count} জন</code>\n"
            f"💳 <b>আপনার ওয়ালেট ব্যালেন্স:</b> <code>৳{t1_new_bal:.2f} BDT</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <i>এই ব্যালেন্স দিয়ে যেকোনো কোর্স বা ডিজিটাল অ্যাকাউন্ট সম্পূর্ণ ফ্রিতে নিতে পারবেন!</i>"
        )
        try:
            await bot.send_message(chat_id=t1_id, text=t1_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not notify T1 referrer {t1_id}: {e}")

    # 2. Tier-2 Passive Commission Alert
    t2_id = res.get("t2_referrer_id")
    t2_bonus = res.get("t2_bonus", 0.0)
    t2_new_bal = res.get("t2_new_balance", 0.0)
    if t2_id and t2_bonus > 0:
        t2_text = (
            f"🚀 <b>[লেভেল-২ প্যাসিভ কমিশন এলার্ট!]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>আপনার সাব-রেফারেল টিম মেম্বার একজন নতুন ইউজার যুক্ত করেছে!</b>\n"
            f"💎 <b>আপনি পেয়েছেন ৫০% হাফ কমিশন:</b> <code>+৳{t2_bonus:.2f} BDT</code>\n"
            f"💳 <b>আপনার নতুন ওয়ালেট ব্যালেন্স:</b> <code>৳{t2_new_bal:.2f} BDT</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>ঘুমিয়ে থেকেও ইনকাম করুন — আপনার টিম যত বড় হবে, তত বেশি আনলিমিটেড কমিশন আসবে!</i>"
        )
        try:
            await bot.send_message(chat_id=t2_id, text=t2_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not notify T2 referrer {t2_id}: {e}")

    # 3. Milestone Celebration Alert
    milestone = res.get("milestone")
    if t1_id and milestone:
        m_text = (
            f"🏆 <b>[অভিনন্দন! নতুন রেফারেল মাইলস্টোন আনলক!]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎖️ <b>অর্জিত টাইটেল:</b> <b>{milestone['title']}</b>\n"
            f"🎁 <b>বাউন্টি ক্যাশ বোনাস:</b> <code>+৳{milestone['bonus']} BDT</code> ওয়ালেটে জমা হয়েছে!\n"
            f"✨ <b>বিশেষ সুবিধা:</b> {milestone['extra']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <i>আপনার অনবদ্য অবদানের জন্য ধন্যবাদ!</i>"
        )
        try:
            await bot.send_message(chat_id=t1_id, text=m_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not notify milestone to {t1_id}: {e}")
