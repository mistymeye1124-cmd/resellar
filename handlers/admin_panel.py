# Admin Management Panel & Control Handlers - Ultra Smart & Powerful Admin Suite
import asyncio
import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import db
from keyboards.admin_kb import (
    get_admin_main_kb,
    get_stock_hub_kb,
    get_subadmins_list_kb,
    get_subadmin_detail_kb,
    get_user_control_kb,
    get_product_type_kb,
    get_deposit_approval_kb,
    get_reseller_pricing_shortcuts_kb,
    get_reseller_admin_menu_kb,
    get_admin_race_challenge_kb,
    get_reward_top_menu_kb,
    get_reward_discount_presets_kb,
    get_reward_duration_presets_kb,
    get_reward_uses_presets_kb,
    get_broadcast_target_kb,
    get_settings_hub_kb,
    get_settings_payment_kb,
    get_settings_referral_kb,
    get_settings_reseller_kb,
    get_settings_channel_kb,
    get_settings_texts_kb,
    get_admin_categories_kb,
    get_category_edit_kb,
    get_admin_subcategories_kb,
    get_subcategory_edit_kb,
    get_coupons_menu_kb,
    get_coupon_actions_kb,
    get_product_edit_options_kb,
    get_stock_manage_kb,
    get_admin_free_drops_kb,
    get_admin_drop_type_kb,
    get_admin_drop_detail_kb,
    get_admin_giveaway_category_select_kb,
    get_settings_emojis_kb,
    get_settings_backup_kb
)
from keyboards.user_kb import get_cancel_fsm_kb
from config import ADMIN_IDS, OFFICIAL_CHANNEL, USD_TO_BDT_RATE, PAYMENT_CONFIG, ADMIN_USERNAME, get_live_usd_rate
from utils.backup_manager import send_database_backup
from utils.emojis import render_premium_html, make_custom_button, apply_premium_emojis_to_keyboard

router = Router()

def is_super_admin(user_id: int) -> bool:
    return not ADMIN_IDS or ADMIN_IDS == [0] or user_id in ADMIN_IDS

def is_admin(user_id: int) -> bool:
    if is_super_admin(user_id):
        return True
    return db.is_sub_admin(user_id)

def has_admin_permission(user_id: int, perm_key: str) -> bool:
    if is_super_admin(user_id):
        return True
    role = db.get_sub_admin(user_id)
    if not role:
        return False
    return bool(role.get(perm_key, 0))

async def verify_telegram_channel_access(bot: Bot, channel_input: str) -> dict:
    """
    Verifies if channel exists and tests if bot has Administrator permissions
    to generate single-use invite links.
    """
    clean_input = channel_input.strip()
    target_chat = int(clean_input) if (clean_input.startswith("-100") or clean_input.isdigit() or (clean_input.startswith("-") and clean_input[1:].isdigit())) else clean_input
    
    try:
        chat = await bot.get_chat(target_chat)
    except Exception as e:
        return {
            "success": False,
            "error_type": "chat_not_found",
            "message": f"টেলিগ্রাম সার্ভারে এই চ্যানেল পাওয়া যায়নি ({e})"
        }
        
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=target_chat,
            name="Verification Test",
            member_limit=1
        )
        return {
            "success": True,
            "title": chat.title or str(target_chat),
            "type": chat.type,
            "channel_id": clean_input,
            "test_link": invite.invite_link
        }
    except Exception as e:
        return {
            "success": False,
            "error_type": "not_admin",
            "title": chat.title or str(target_chat),
            "message": f"বট এই চ্যানেলে Administrator নয় অথবা 'Invite Users via Link' পারমিশন নেই ({e})"
        }

# --- FSM STATES ---
class AddProductState(StatesGroup):
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_title = State()
    waiting_for_desc = State()
    waiting_for_price_bdt = State()
    waiting_for_reseller_discount = State()
    waiting_for_custom_reseller_price = State()
    waiting_for_type = State()
    
    # VIP Channel Single
    waiting_for_target = State()
    
    # Ready Stock / Account Single
    waiting_for_acc_site_link = State()
    waiting_for_acc_creds = State()
    waiting_for_acc_rules = State()
    
    # Dual Package Flow (Channel + Account)
    waiting_for_dual_ch_price = State()
    waiting_for_dual_ch_reseller_price = State()
    waiting_for_dual_channel_target = State()
    waiting_for_dual_acc_price = State()
    waiting_for_dual_acc_reseller_price = State()
    waiting_for_dual_acc_site_link = State()
    waiting_for_dual_acc_creds = State()
    waiting_for_dual_acc_rules = State()
    
    waiting_for_photo = State()

class EditProductState(StatesGroup):
    waiting_for_new_title = State()
    waiting_for_new_desc = State()
    waiting_for_new_price = State()
    waiting_for_new_resprice = State()
    waiting_for_new_sales_page = State()
    waiting_for_new_ch_price = State()
    waiting_for_new_acc_price = State()
    waiting_for_new_target = State()
    waiting_for_new_photo = State()
    waiting_for_new_channel = State()
    waiting_for_new_accdata = State()

class AddStockState(StatesGroup):
    waiting_for_product = State()
    waiting_for_items = State()

class BroadcastState(StatesGroup):
    target_group = State()
    waiting_for_message = State()

class BalanceManageState(StatesGroup):
    waiting_for_user_id = State()
    action_type = State() # 'add' or 'cut'
    waiting_for_amount = State()

class PromoteResellerState(StatesGroup):
    waiting_for_user_id = State()

class SearchUserState(StatesGroup):
    waiting_for_query = State()

class RewardCustomResellerState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_discount = State()
    waiting_for_days = State()
    waiting_for_max_uses = State()

class RewardTopCustomState(StatesGroup):
    top_n = State()
    waiting_for_discount = State()

class DirectDMState(StatesGroup):
    target_user_id = State()
    waiting_for_message = State()

class CreateCouponState(StatesGroup):
    waiting_for_code = State()
    waiting_for_discount = State()
    waiting_for_max_uses = State()

class EditSettingState(StatesGroup):
    waiting_for_value = State()

class EditChallengeState(StatesGroup):
    waiting_for_target = State()
    waiting_for_discount = State()
    waiting_for_slots = State()
    waiting_for_days = State()
    waiting_for_max_uses = State()

class CategoryAddState(StatesGroup):
    waiting_for_name = State()
    waiting_for_icon = State()
    waiting_for_type = State()

class CategoryEditState(StatesGroup):
    waiting_for_name = State()
    waiting_for_icon = State()

class SubcategoryAddState(StatesGroup):
    waiting_for_name = State()
    waiting_for_icon = State()

class SubcategoryEditState(StatesGroup):
    waiting_for_name = State()
    waiting_for_icon = State()

class CreateFreeDropState(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_site_link = State()
    waiting_for_payload = State()
    waiting_for_slots = State()
    waiting_for_required_referrals = State()
    waiting_for_desc = State()
    waiting_for_instructions = State()

class EditFreeDropRefsState(StatesGroup):
    waiting_for_new_refs = State()

class SubAdminState(StatesGroup):
    waiting_for_user_id = State()


# --- DASHBOARD TEXT GENERATOR ---
def format_admin_dashboard_text(stats: dict, is_super: bool = True, perms: dict = None) -> str:
    dep_alert = ""
    if stats.get('pending_deposits', 0) > 0:
        dep_alert += f"\n🚨 <b>সতর্কতা:</b> <code>{stats['pending_deposits']} টি</code> নতুন ডিপোজিট স্ক্রিনশট অনুমোদনের অপেক্ষায় আছে!\n"
    if stats.get('pending_reseller_apps', 0) > 0:
        dep_alert += f"📝 <b>সতর্কতা:</b> <code>{stats['pending_reseller_apps']} টি</code> রিসেলার আবেদন পেন্ডিং আছে!\n"

    role_title = "⚡ <b>অ্যাডমিন মাস্টার কন্ট্রোল সেন্টার (Super Admin Hub)</b> ⚡" if is_super else "🛡️ <b>স্টাফ / সাব-এডমিন কন্ট্রোল প্যানেল (Staff Hub)</b> 🛡️"
    
    perm_summary = ""
    if not is_super and perms:
        active_p = []
        labels = {
            "can_manage_free_drops": "ফ্রি ড্রপস/লুট",
            "can_manage_stock": "স্টক অন/অফ",
            "can_manage_products": "কোর্স",
            "can_approve_deposits": "ডিপোজিট",
            "can_manage_resellers": "রিসেলার",
            "can_broadcast": "ব্রডকাস্ট",
            "can_manage_users": "ব্যালেন্স",
            "can_manage_coupons": "কুপন"
        }
        for k, v in labels.items():
            if perms.get(k):
                active_p.append(f"✅ {v}")
        perm_summary = f"🔰 <b>আপনার সক্রিয় পারমিশন:</b> {', '.join(active_p) if active_p else 'কোনোটি চালু নেই'}\n\n"

    shortcuts_text = (
        "⚡ <b>পাওয়ারফুল কমান্ড শর্টকাট:</b>\n"
        "• 🔍 <code>/find &lt;id/@username/RS-code&gt;</code> — ইউজার প্রোফাইল ও অ্যাকশন\n"
        "• 💰 <code>/addbalance &lt;id&gt; &lt;bdt&gt;</code> — ১-সেকেন্ডে ওয়ালেটে টাকা যোগ\n"
        "• ✂️ <code>/cutbalance &lt;id&gt; &lt;bdt&gt;</code> — ১-সেকেন্ডে টাকা কর্তন\n"
        "• 💎 <code>/setreseller &lt;id&gt;</code> — ১-সেকেন্ডে রিসেলার পদোন্নতি\n"
        "• 🚫 <code>/unreseller &lt;id&gt;</code> — রিসেলার পদ বাতিল\n"
        "• 🔓 <code>/reactivate &lt;id&gt;</code> — বাতিল হওয়া রিসেলারকে পুনরায় সুযোগ\n"
        "• 🏆 <code>/rewardtop &lt;count&gt; &lt;bdt&gt; &lt;days&gt; &lt;uses&gt;</code> — সেরা রিসেলারদের স্পেশাল ছাড় পাস\n"
        "• 🎁 <code>/rewardreseller &lt;id&gt; &lt;bdt&gt; &lt;days&gt; &lt;uses&gt;</code> — নির্দিষ্ট রিসেলারকে ছাড় পাস প্রদান\n"
        "• 📜 <code>/recent</code> — সর্বশেষ ১০টি লাইভ অর্ডার\n"
        "• 📢 <code>/blast &lt;বার্তা&gt;</code> — একসাথে সবার কাছে নোটিশ\n\n"
    ) if is_super else ""

    return (
        f"{role_title}\n"
        f"{dep_alert}\n"
        f"{perm_summary}"
        "📊 <b>লাইভ পারফরম্যান্স ও রিপোর্ট:</b>\n"
        f"• 👥 মোট রেজিস্টার্ড ইউজার: <code>{stats['total_users']}</code> জন\n"
        f"• 💎 সক্রিয় রিসেলার: <code>{stats.get('total_resellers', 0)} জন</code> (কোটা বাতিল: <code>{stats.get('deactivated_resellers', 0)}</code>)\n"
        f"• 📈 আজকের সেলস (24h): <code>৳{stats.get('today_sales_bdt', 0):.2f}</code> (<code>{stats.get('today_orders', 0)}</code> টি অর্ডার)\n"
        f"• 📦 সর্বমোট সম্পন্ন অর্ডার: <code>{stats['total_orders']}</code> টি\n"
        f"• 💰 মোট জমা (BDT): <code>৳{stats['total_deposit_bdt']:.2f}</code>\n"
        f"• 💵 মোট জমা (USD): <code>${stats['total_deposit_usd']:.2f}</code>\n"
        f"• 🎓 সক্রিয় কোর্স ও সার্ভিস: <code>{stats.get('active_products', 0)} টি</code>\n\n"
        f"{shortcuts_text}"
        "👇 নিচের মেনু থেকে অপশন নির্বাচন করুন:"
    )

def format_user_dossier_text(user: dict) -> str:
    user_id = user['user_id']
    profile = db.get_user_analytics_summary(user_id) or user
    quota_info = db.get_reseller_quota_info(user_id)
    
    is_res = profile.get("is_reseller", 0) == 1
    is_perm = profile.get("reseller_deactivated_permanent", 0) == 1 or profile.get("is_reseller", 0) == -1
    is_ban = profile.get("is_banned", 0) == 1
    
    res_status = "💎 Active Reseller" if is_res else ("🛑 Quota Banned" if is_perm else "👤 Regular User")
    ban_status = "🔴 BANNED" if is_ban else "🟢 ACTIVE"
    
    raw_u = profile.get('username')
    uname_str = f"@{html.escape(raw_u)}" if raw_u else "N/A"
    fname = html.escape(str(profile.get('first_name', 'N/A')))
    join_date = str(profile.get('joined_at', ''))[:10] or "N/A"
    
    # 1. Earnings & Referrals Breakdown
    ref_by_info = profile.get("referrer_info")
    if ref_by_info:
        r_uname = f"@{ref_by_info['username']}" if ref_by_info.get('username') else str(ref_by_info['user_id'])
        ref_by_str = f"<code>{html.escape(r_uname)}</code>"
    else:
        ref_by_str = "<i>অর্গানিক / সরাসরি</i>"
        
    t1_cnt = profile.get('referral_count_t1', 0)
    t2_cnt = profile.get('referral_count_t2', 0)
    ref_pts = profile.get('referral_points', 0)
    ref_earn_bdt = float(profile.get('referral_earnings_bdt', 0.0))
    free_drops_c = profile.get('free_drops_claimed', 0)
    
    # 2. Deposits Breakdown
    dep_bdt = float(profile.get('deposits_approved_bdt', 0.0))
    dep_usd = float(profile.get('deposits_approved_usd', 0.0))
    dep_cnt = profile.get('deposits_approved_count', 0)
    pending_dep = profile.get('deposits_pending_count', 0)
    last_dep = profile.get('last_deposit')
    if last_dep:
        last_dep_str = f"{last_dep['method'].upper()} ৳{int(last_dep['amount'])} ({str(last_dep['created_at'])[:10]})"
    else:
        last_dep_str = "কোনো হিস্টোরি নেই"
        
    # 3. Orders & Queue Breakdown
    orders_cnt = profile.get('orders_completed_count', 0)
    queue_orders = profile.get('orders_queue', [])
    pending_reqs = profile.get('pending_requests', [])
    total_queue = profile.get('total_queue_count', 0)
    
    if total_queue > 0:
        q_lines = []
        for q in queue_orders[:4]:
            q_lines.append(f"• ⏳ অর্ডার #{q['id']}: <b>{html.escape(q['product_title'][:20])}</b> ({q.get('status', 'pending')})")
        for req in pending_reqs[:3]:
            q_lines.append(f"• 📝 কোর্স রিকোয়েস্ট: <i>{html.escape(req['course_query'][:22])}</i> (পেন্ডিং)")
        if pending_dep > 0:
            q_lines.append(f"• 💳 ডিপোজিট ভেরিফিকেশন: <code>{pending_dep} টি কিউতে অপেক্ষারত</code>")
        queue_section = (
            f"\n🚨 <b>পেন্ডিং কিউ অর্ডার ও রিকোয়েস্ট ({total_queue} টি):</b>\n"
            + "\n".join(q_lines) + "\n"
        )
    else:
        queue_section = "\n⏳ <b>কিউ / পেন্ডিং অর্ডার:</b> <code>০ টি (কোনো কিউ নেই ✅)</code>\n"

    quota_line = ""
    if is_res:
        quota_line = (
            f"🎯 <b>মাসিক কোটা:</b> <code>{quota_info['sales']} / {quota_info['target']} টি সম্পন্ন</code> "
            f"(⏳ {quota_info['days_left']} দিন বাকি)\n"
        )
    elif is_perm:
        quota_line = "⚠️ <b>কোটা স্ট্যাটাস:</b> ৩০ দিনে কোটা পূরণ না করায় অ্যাকাউন্ট বাতিল করা হয়েছিল।\n"

    res_perm_section = ""
    if is_res:
        r_tier = profile.get("reseller_tier", 1) or 1
        tier_title = "👑 Elite VIP (Full Access)" if r_tier >= 2 else "🥉 Standard (Channel Only)"
        can_ch = "🟢 চালু (Active)" if profile.get("can_sell_channel", 1) else "🔴 বন্ধ (Disabled)"
        can_acc = "🟢 চালু (Active)" if profile.get("can_sell_account", 0) else "🔴 বন্ধ (Locked)"
        res_perm_section = (
            f"• রিসেলার টায়ার: <b>{tier_title}</b>\n"
            f"• চ্যানেল সেল পারমিশন: <b>{can_ch}</b>\n"
            f"• অ্যাকাউন্ট সেল পারমিশন: <b>{can_acc}</b>\n"
        )

    return (
        f"📊 <b>ইউজার ইন্টেলিজেন্স ও কমপ্লিট ডসিয়ার</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>ইউজার তথ্য:</b>\n"
        f"• নাম: <b>{fname}</b> | {uname_str}\n"
        f"• আইডি: <code>{user_id}</code> | যোগদানের তারিখ: <code>{join_date}</code>\n"
        f"• অ্যাকাউন্ট স্ট্যাটাস: <b>{ban_status}</b> | <b>{res_status}</b>\n"
        f"• রিসেলার কোড: <code>{profile.get('reseller_code') or 'N/A'}</code>\n"
        f"{res_perm_section}"
        f"• ভাষা: <code>{str(profile.get('language', 'bn')).upper()}</code>\n"
        f"{quota_line}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>ডিপোজিট বিবরণ (Deposit Overview):</b>\n"
        f"• মোট সফল ডিপোজিট: <b>৳{dep_bdt:.2f} BDT</b> | <b>${dep_usd:.2f} USD</b> ({dep_cnt} টি)\n"
        f"• পেন্ডিং ডিপোজিট (কিউতে): <code>{pending_dep} টি</code>\n"
        f"• বর্তমান ব্যালেন্স: <b>৳{profile.get('balance_bdt', 0.0):.2f} BDT</b> | <b>${profile.get('balance_usd', 0.0):.2f} USD</b>\n"
        f"• সর্বশেষ ডিপোজিট: <code>{last_dep_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>আর্নিং ও রেফারেল (Earnings Breakdown):</b>\n"
        f"• ডিরেক্ট রেফারেল (Tier 1): <b>{t1_cnt} জন</b> | সাব-রেফারেল (Tier 2): <b>{t2_cnt} জন</b>\n"
        f"• রেফারেল পয়েন্ট ব্যালেন্স: <b>{ref_pts} Pts</b>\n"
        f"• মোট রেফারেল আর্নিং: <b>৳{ref_earn_bdt:.2f} BDT</b>\n"
        f"• ফ্রি ড্রপ ক্লেইম: <b>{free_drops_c} টি</b>\n"
        f"• কার রেফারেল দিয়ে জয়েন: {ref_by_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>অর্ডার ও কিউ স্ট্যাটাস (Orders & Queue):</b>\n"
        f"• মোট সম্পন্ন অর্ডার: <b>{orders_cnt} টি</b>\n"
        f"• মোট কেনাকাটা / খরচ: <b>৳{float(profile.get('total_spent_bdt', 0.0)):.2f} BDT</b>\n"
        f"{queue_section}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>এই ইউজারের যেকোনো একশন নিতে নিচের বাটন ব্যবহার করুন:</i>"
    )

def format_users_directory_text(data: dict) -> str:
    users = data["users"]
    page = data["current_page"]
    total_pages = data["total_pages"]
    total_matching = data["total_matching"]
    f_type = data["filter_type"]
    g = data["global_stats"]
    
    filter_names = {
        "all": "🌟 সকল ইউজার",
        "resellers": "💎 রিসেলারগণ",
        "top_deposit": "💰 শীর্ষ ডিপোজিটকারী",
        "top_earners": "🎁 শীর্ষ আর্নার / রেফারেল",
        "top_buyers": "📦 শীর্ষ ক্রেতা",
        "in_queue": "⏳ কিউ / পেন্ডিং অর্ডারযুক্ত"
    }
    current_filter_label = filter_names.get(f_type, "🌟 সকল ইউজার")
    
    header = (
        f"👥 <b>ইউজার ডিরেক্টরি ও অ্যানালিটিক্স হাব</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>সার্বিক পরিসংখ্যান:</b>\n"
        f"• মোট ইউজার: <b>{g['total_users']} জন</b> | রিসেলার: <b>{g['total_resellers']} জন</b>\n"
        f"• মোট ডিপোজিট: <b>৳{g['total_deposited_bdt']:.0f} BDT</b> | মোট অর্ডার: <b>{g['total_orders']} টি</b>\n"
        f"• বর্তমানে কিউতে পেন্ডিং: <b>{g['total_queue']} টি</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 ফিল্টার: <b>{current_filter_label}</b> (মোট {total_matching} জন | পৃষ্ঠা: {page}/{total_pages})\n\n"
    )
    
    if not users:
        return header + "<i>এই ফিল্টারে কোনো ইউজার পাওয়া যায়নি।</i>"
        
    lines = []
    for idx, u in enumerate(users, start=1 + (page - 1) * data["per_page"]):
        raw_u = u.get('username')
        uname = f"@{raw_u}" if raw_u else "no_uname"
        fname = html.escape(str(u.get('first_name', 'N/A'))[:13])
        is_r = "💎" if u.get("is_reseller", 0) >= 1 else "👤"
        ban = "🔴" if u.get("is_banned", 0) == 1 else ""
        
        dep = int(u.get('total_deposited_bdt', 0))
        bal = int(u.get('balance_bdt', 0))
        ord_c = u.get('orders_count', 0)
        q_cnt = u.get('queue_orders_count', 0) + u.get('pending_deposits_count', 0) + u.get('pending_requests_count', 0)
        q_badge = f" • ⏳<b>{q_cnt} কিউ</b>" if q_cnt > 0 else ""
        
        lines.append(
            f"<b>#{idx} {is_r}{ban} {fname}</b> (<code>{u['user_id']}</code> | {uname})\n"
            f"   💰 ব্যালেন্স: <code>৳{bal}</code> | ডিপোজিট: <code>৳{dep}</code> | অর্ডার: <code>{ord_c}টি</code>{q_badge}"
        )
        
    body = "\n\n".join(lines)
    footer = "\n\n👉 <i>যেকোনো ইউজারের পূর্ণ বিবরণ দেখতে নিচের বাটনে ক্লিক করুন:</i>"
    return header + body + footer


def get_admin_dashboard_text(user_id: int = None) -> str:
    stats = db.get_extended_bot_stats()
    is_super = is_super_admin(user_id) if user_id else True
    perms = None if is_super else (db.get_sub_admin(user_id) if user_id else None)
    return format_admin_dashboard_text(stats, is_super=is_super, perms=perms)

# --- 1. PRIMARY DASHBOARD ENTRY ---
@router.message(Command("admin"))
@router.message(F.text.in_(["👑 Admin Panel", "Admin Panel", "admin", "Admin", "অ্যাডমিন প্যানেল", "প্যানেল"]))
async def handle_admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ আপনার অ্যাডমিন প্যানেলে অ্যাক্সেস নেই!")
        return
    await state.clear()
    stats = db.get_extended_bot_stats()
    is_super = is_super_admin(message.from_user.id)
    perms = None if is_super else db.get_sub_admin(message.from_user.id)
    await message.answer(
        format_admin_dashboard_text(stats, is_super=is_super, perms=perms),
        reply_markup=get_admin_main_kb(stats, is_super=is_super, permissions=perms),
        parse_mode="HTML"
    )

# --- 1.1 DATABASE BACKUP COMMAND & CALLBACK HANDLERS ---
@router.message(Command("backup"))
@router.message(F.text.in_(["/backup", "backup", "Backup", "ডাটাবেজ ব্যাকআপ"]))
async def handle_backup_command(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    status_msg = await message.answer("⏳ <b>ডাটাবেজ ব্যাকআপ ও আর্কাইভ তৈরি হচ্ছে...</b>", parse_mode="HTML")
    success = await send_database_backup(bot, chat_ids=[message.from_user.id], is_auto=False)
    if success:
        try:
            await status_msg.delete()
        except Exception:
            pass
    else:
        await status_msg.edit_text("❌ ডাটাবেজ ব্যাকআপ এক্সপোর্ট করতে সমস্যা হয়েছে। দয়া করে লগ চেক করুন।")

@router.callback_query(F.data == "admin_instant_db_backup")
async def handle_admin_instant_db_backup(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await call.answer("⏳ লাইভ ব্যাকআপ তৈরি ও পাঠানো হচ্ছে...", show_alert=False)
    success = await send_database_backup(bot, chat_ids=[call.from_user.id], is_auto=False)
    if success:
        await call.answer("✅ আপনার ইনবক্সে ডাটাবেজ ব্যাকআপ পাঠানো হয়েছে!", show_alert=True)
    else:
        await call.answer("❌ ব্যাকআপ তৈরিতে ত্রুটি হয়েছে!", show_alert=True)

@router.callback_query(F.data == "admin_test_backup_run")
async def handle_admin_test_backup_run(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await call.answer("🚀 সমস্ত অ্যাডমিনদের কাছে ব্যাকআপ পাঠানো হচ্ছে...", show_alert=False)
    success = await send_database_backup(bot, is_auto=True)
    if success:
        await call.answer("✅ সমস্ত অ্যাডমিনদের ইনবক্সে সফলভাবে ব্যাকআপ পাঠানো হয়েছে!", show_alert=True)
    else:
        await call.answer("❌ ব্যাকআপ প্রেরণে ত্রুটি হয়েছে!", show_alert=True)

@router.callback_query(F.data == "admin_main_dashboard")
async def handle_admin_main_dashboard(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    await call.answer()
    stats = db.get_extended_bot_stats()
    is_super = is_super_admin(call.from_user.id)
    perms = None if is_super else db.get_sub_admin(call.from_user.id)
    try:
        await call.message.edit_text(
            format_admin_dashboard_text(stats, is_super=is_super, perms=perms),
            reply_markup=get_admin_main_kb(stats, is_super=is_super, permissions=perms),
            parse_mode="HTML"
        )
    except Exception:
        await call.message.answer(
            format_admin_dashboard_text(stats, is_super=is_super, perms=perms),
            reply_markup=get_admin_main_kb(stats, is_super=is_super, permissions=perms),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "admin_close")
async def handle_close_admin(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.delete()


# --- 2. POWERFUL 1-LINE SHORTCUT COMMANDS ---

@router.message(Command("find"))
@router.message(Command("user"))
async def handle_cmd_find(message: Message):
    """Shortcut: /find <id|@username|reseller_code> to open instant user dossier!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("⚠️ ব্যবহার নিয়ম: `/find <ID / @username / RS-code>`\n_(যেমন: `/find 8387415921` বা `/find @proaccessteam`)_", parse_mode="Markdown")
        return
    
    query = args[1].strip()
    target_user = db.find_user(query)
    if not target_user:
        await message.answer(f"❌ কোনো ইউজার পাওয়া যায়নি: `{query}`", parse_mode="Markdown")
        return

    is_res = target_user.get("is_reseller", 0) == 1
    is_perm = target_user.get("reseller_deactivated_permanent", 0) == 1 or target_user.get("is_reseller", 0) == -1
    is_banned = target_user.get("is_banned", 0) == 1

    await message.answer(
        format_user_dossier_text(target_user),
        reply_markup=get_user_control_kb(target_user['user_id'], is_reseller=is_res, is_banned=is_banned, is_perm_deact=is_perm),
        parse_mode="HTML"
    )

@router.message(Command("addbalance"))
async def handle_cmd_addbalance(message: Message, bot: Bot):
    """Shortcut: /addbalance <id> <amount> to credit in 1 second!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 3 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/addbalance <USER_ID> <AMOUNT>`\n_(উদাহরণ: `/addbalance 123456789 500`)_", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    try:
        amount = float(args[2])
    except ValueError:
        await message.answer("❌ টাকার পরিমাণ সঠিক সংখ্যা নয়!")
        return

    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` ডাটাবেসে পাওয়া যায়নি।")
        return

    db.update_user_balance(target_id, amount, "BDT")
    updated = db.get_user(target_id)
    
    await message.answer(
        f"✅ **সফলভাবে ব্যালেন্স যোগ করা হয়েছে!**\n\n"
        f"👤 ইউজার: {user['first_name']} (`{target_id}`)\n"
        f"💰 যোগকৃত: `+৳{amount:.2f} BDT`\n"
        f"💳 বর্তমান ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
        parse_mode="Markdown"
    )
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"🎉 **আপনার অ্যাকাউন্টে ব্যালেন্স যোগ করা হয়েছে!**\n\n"
                 f"💰 যোগকৃত টাকা: `+৳{amount:.2f} BDT`\n"
                 f"💳 আপনার বর্তমান ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@router.message(Command("cutbalance"))
async def handle_cmd_cutbalance(message: Message, bot: Bot):
    """Shortcut: /cutbalance <id> <amount> to deduct in 1 second!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 3 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/cutbalance <USER_ID> <AMOUNT>`\n_(উদাহরণ: `/cutbalance 123456789 200`)_", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    try:
        amount = float(args[2])
    except ValueError:
        await message.answer("❌ টাকার পরিমাণ সঠিক সংখ্যা নয়!")
        return

    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` ডাটাবেসে পাওয়া যায়নি।")
        return

    db.update_user_balance(target_id, -amount, "BDT")
    updated = db.get_user(target_id)
    
    await message.answer(
        f"✂️ **সফলভাবে ব্যালেন্স কর্তন করা হয়েছে!**\n\n"
        f"👤 ইউজার: {user['first_name']} (`{target_id}`)\n"
        f"💰 কর্তনকৃত: `-৳{amount:.2f} BDT`\n"
        f"💳 বর্তমান ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
        parse_mode="Markdown"
    )
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"⚠️ **আপনার অ্যাকাউন্ট থেকে ব্যালেন্স কর্তন করা হয়েছে!**\n\n"
                 f"💰 কর্তনকৃত: `-৳{amount:.2f} BDT`\n"
                 f"💳 আপনার বর্তমান ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@router.message(Command("setreseller"))
async def handle_cmd_setreseller(message: Message, bot: Bot):
    """Shortcut: /setreseller <user_id> to promote in 1 second!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/setreseller <USER_ID>`\n_(উদাহরণ: `/setreseller 123456789`)_", parse_mode="Markdown")
        return
        
    target_id = int(args[1])
    target_user = db.get_user(target_id)
    if not target_user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` ডাটাবেসে পাওয়া যায়নি। ইউজারকে আগে বটে /start দিতে বলুন।", parse_mode="Markdown")
        return
        
    code = f"RS-{target_id % 10000:04d}"
    db.set_reseller_status(target_id, 1, code)
    
    await message.answer(
        f"✅ **সফল! ইউজারকে অফিশিয়াল রিসেলার পদে উন্নীত করা হয়েছে!**\n\n"
        f"👤 নাম: {target_user['first_name']}\n"
        f"🆔 আইডি: `{target_id}`\n"
        f"💎 রিসেলার কোড: `{code}`",
        parse_mode="Markdown"
    )
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"🎉 **অভিনন্দন! আপনার অ্যাকাউন্টকে অফিসিয়াল রিসেলারে আপগ্রেড করা হয়েছে!**\n\n"
                 f"🆔 আপনার রিসেলার কোড: `{code}`\n"
                 "এখন থেকে আপনি সমস্ত কোর্সে পাইকারি ছাড় পাবেন। মেনু থেকে **💼 Reseller Hub** চেক করুন!",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@router.message(Command("unreseller"))
async def handle_cmd_unreseller(message: Message, bot: Bot):
    """Shortcut: /unreseller <user_id> to demote reseller."""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/unreseller <USER_ID>`", parse_mode="Markdown")
        return
    target_id = int(args[1])
    db.set_reseller_status(target_id, 0)
    await message.answer(f"✅ ইউজার `{target_id}` এর রিসেলার পদ বাতিল করা হয়েছে।", parse_mode="Markdown")
    try:
        await bot.send_message(chat_id=target_id, text="⚠️ আপনার রিসেলার অ্যাক্সেস প্রত্যাহার করা হয়েছে।")
    except Exception:
        pass

@router.message(Command("reactivate"))
async def handle_cmd_reactivate(message: Message, bot: Bot):
    """Shortcut: /reactivate <user_id> to forgive and reset quota for permanent banned reseller."""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/reactivate <USER_ID>`", parse_mode="Markdown")
        return
    target_id = int(args[1])
    db.reactivate_reseller(target_id)
    await message.answer(f"🔓 ইউজার `{target_id}` এর রিসেলার কোটা সফলভাবে রিয়্যাক্টিভেট ও নতুন ৩০-দিনের সাইকেল চালু করা হয়েছে!", parse_mode="Markdown")
    try:
        await bot.send_message(chat_id=target_id, text="🎉 **আপনার রিসেলার অ্যাকাউন্ট রিয়্যাক্টিভেট করা হয়েছে!**\nআপনার জন্য নতুন ৩০ দিনের সাইকেল চালু হলো। শুভকামনা!", parse_mode="Markdown")
    except Exception:
        pass

@router.message(Command("rewardtop"))
async def handle_cmd_rewardtop(message: Message, bot: Bot):
    """Shortcut: /rewardtop [top_n=3] [discount_bdt=50] [days=7] [max_uses=10] to reward monthly top sellers!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    top_n = 3
    discount = 50.0
    days = 7
    max_uses = 10
    
    if len(args) >= 2 and args[1].isdigit():
        top_n = int(args[1])
    if len(args) >= 3:
        try:
            discount = float(args[2])
        except ValueError:
            pass
    if len(args) >= 4 and args[3].isdigit():
        days = int(args[3])
    if len(args) >= 5 and args[4].isdigit():
        max_uses = int(args[4])

    passes = db.reward_top_resellers(top_n=top_n, discount_bdt=discount, days_valid=days, max_uses=max_uses)
    if not passes:
        await message.answer("⚠️ রিওয়ার্ড দেওয়ার মতো কোনো রিসেলার ডাটা বা সেলস পাওয়া যায়নি।", parse_mode="Markdown")
        return

    sent_count = 0
    for p in passes:
        try:
            notify_text = (
                f"🏆 **অভিনন্দন! আপনি এই মাসের শীর্ষ রিসেলারদের তালিকায় স্থান পেয়েছেন!** 🎉\n\n"
                f"আপনার অসাধারণ সেলসের জন্য বিশেষ ভিআইপি রিওয়ার্ড পাস দেওয়া হলো:\n"
                f"• 🎟️ কুপন কোড: `{p['coupon_code']}`\n"
                f"• 💥 অতিরিক্ত পাইকারি ছাড়: `৳{discount:.0f} BDT` (প্রতিটি পণ্যে আরও কম দামে!)\n"
                f"• ⏳ অফার মেয়াদ: `{days} দিন`\n"
                f"• 📦 মোট ব্যবহার সীমা: `{max_uses} টি অর্ডার`\n\n"
                f"⚡ যেকোনো কোর্স কেনার সময় স্বয়ংক্রিয়ভাবে এই ছাড়টি বাদ যাবে। মেয়াদ বা অর্ডার লিমিট শেষ হলে সাধারণ রিসেলার রেট প্রযোজ্য হবে।"
            )
            await bot.send_message(chat_id=p["user_id"], text=notify_text, parse_mode="Markdown")
            sent_count += 1
        except Exception:
            pass

    admin_msg = (
        f"🏆 **সেরা {len(passes)} জন রিসেলারকে রিওয়ার্ড পাস প্রদান সম্পন্ন!**\n\n"
        f"• অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` / প্রোডাক্ট\n"
        f"• মেয়াদ: `{days} দিন`\n"
        f"• ব্যবহার সীমা: `{max_uses} টি অর্ডার`\n"
        f"• নোটিফিকেশন পৌঁছেছে: `{sent_count} জনের ইনবক্সে`\n\n"
        "📋 **রিওয়ার্ডপ্রাপ্ত রিসেলার তালিকা:**\n"
    )
    for p in passes:
        admin_msg += f"• #{p['rank']} [{p['coupon_code']}] {p.get('first_name')} (`{p['user_id']}`) — সেলস: `{p.get('sales', 0)} টি`\n"

    await message.answer(admin_msg, parse_mode="Markdown")

@router.message(Command("rewardreseller"))
async def handle_cmd_rewardreseller(message: Message, bot: Bot):
    """Shortcut: /rewardreseller <user_id> [discount_bdt=50] [days=7] [max_uses=10]"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer(
            "⚠️ ব্যবহার নিয়ম: `/rewardreseller <USER_ID> [ছাড়_BDT] [মেয়াদ_দিন] [অর্ডার_লিমিট]`\n"
            "_(উদাহরণ: `/rewardreseller 123456789 50 7 10`)_",
            parse_mode="Markdown"
        )
        return

    target_id = int(args[1])
    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` পাওয়া যায়নি।", parse_mode="Markdown")
        return
    if user.get("is_reseller", 0) < 1:
        await message.answer(f"⚠️ ইউজার {user['first_name']} (`{target_id}`) অনুমোদিত রিসেলার নন।", parse_mode="Markdown")
        return

    discount = 50.0
    days = 7
    max_uses = 10
    if len(args) >= 3:
        try:
            discount = float(args[2])
        except ValueError:
            pass
    if len(args) >= 4 and args[3].isdigit():
        days = int(args[3])
    if len(args) >= 5 and args[4].isdigit():
        max_uses = int(args[4])

    r_code = user.get("reseller_code", "RS")
    pass_code = f"VIP-{r_code}-{target_id % 1000}"
    p = db.create_reseller_vip_pass(
        user_id=target_id,
        discount_bdt=discount,
        days_valid=days,
        max_uses=max_uses,
        code=pass_code
    )

    try:
        notify_text = (
            f"🎉 **অভিনন্দন! আপনাকে বিশেষ ভিআইপি রিওয়ার্ড পাস প্রদান করা হয়েছে!** 🏆\n\n"
            f"• 🎟️ কুপন কোড: `{p['coupon_code']}`\n"
            f"• 💥 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` (প্রতিটি পণ্যে পাইকারি দামের চেয়েও কম!)\n"
            f"• ⏳ মেয়াদ: `{days} দিন`\n"
            f"• 📦 মোট ব্যবহার সীমা: `{max_uses} টি অর্ডার`\n\n"
            f"⚡ কেনাকাটা করার সময় এই অতিরিক্ত ছাড়টি সরাসরি মাইনাস হবে। মেয়াদ শেষ হলে পুনরায় সাধারণ রিসেলার মূল্য কার্যকর হবে।"
        )
        await bot.send_message(chat_id=target_id, text=notify_text, parse_mode="Markdown")
    except Exception:
        pass

    await message.answer(
        f"✅ **সফল! রিসেলারকে রিওয়ার্ড পাস দেওয়া হয়েছে!**\n\n"
        f"👤 রিসেলার: {user['first_name']} (`{target_id}`)\n"
        f"🎟️ পাস কোড: `{p['coupon_code']}`\n"
        f"💰 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT`\n"
        f"⏳ মেয়াদ: `{days} দিন`\n"
        f"📦 লিমিট: `{max_uses} টি অর্ডার`",
        parse_mode="Markdown"
    )

@router.message(Command("revokepass"))
async def handle_cmd_revokepass(message: Message):
    """Shortcut: /revokepass <pass_id> to cancel a VIP pass immediately."""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/revokepass <PASS_ID>`", parse_mode="Markdown")
        return
    pass_id = int(args[1])
    ok = db.revoke_vip_pass(pass_id)
    if ok:
        await message.answer(f"✅ ভিআইপি পাস `#{pass_id}` সফলভাবে বাতিল করা হয়েছে।", parse_mode="Markdown")
    else:
        await message.answer(f"❌ পাস `#{pass_id}` পাওয়া যায়নি বা ইতিমধ্যে নিষ্ক্রিয়।", parse_mode="Markdown")

@router.message(Command("resellers"))
async def handle_cmd_resellers(message: Message):
    if not is_admin(message.from_user.id):
        return
    resellers = db.get_all_resellers()
    if not resellers:
        await message.answer("⚠️ বর্তমানে কোনো অনুমোদিত রিসেলার নেই।", parse_mode="Markdown")
        return
        
    text = f"💎 **অনুমোদিত রিসেলার তালিকা (মোট {len(resellers)} জন):**\n\n"
    for idx, r in enumerate(resellers, start=1):
        text += (
            f"**{idx}. [{r.get('reseller_code', 'RS-N/A')}] {r['first_name']}**\n"
            f"🆔 ID: `{r['user_id']}` | @{r['username'] or 'N/A'}\n"
            f"📦 সম্পন্ন অর্ডার: `{r.get('reseller_orders_count', 0)} টি`\n"
            f"💰 মোট কেনাকাটা: `৳{r.get('reseller_total_spent', 0):.2f}`\n"
            f"💳 বর্তমান ব্যালেন্স: `৳{r['balance_bdt']:.2f}`\n"
            f"🔎 লেজার দেখতে: `/reseller {r['user_id']}`\n"
            f"───────────────────\n"
        )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("reseller"))
async def handle_cmd_single_reseller(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split() if message.text else []
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ ব্যবহার নিয়ম: `/reseller <USER_ID>`", parse_mode="Markdown")
        return
        
    target_id = int(args[1])
    user = db.get_user(target_id)
    if not user:
        await message.answer("❌ ইউজার পাওয়া যায়নি!", parse_mode="Markdown")
        return
        
    stats = db.get_reseller_stats(target_id)
    orders = db.get_user_orders(target_id)
    reseller_orders = [o for o in orders if o.get("is_reseller_order")]
    
    ledger_text = (
        f"📊 **রিসেলার বিস্তারিত লেজার: {user['first_name']}**\n\n"
        f"🆔 ইউজার আইডি: `{target_id}`\n"
        f"💎 রিসেলার কোড: `{user.get('reseller_code', 'RS-N/A')}`\n"
        f"💳 কারেন্ট ব্যালেন্স: `৳{user['balance_bdt']:.2f}` | `${user['balance_usd']:.2f}`\n"
        f"📦 মোট রিসেল অর্ডার: `{stats['orders_count']} টি`\n"
        f"💰 মোট কেনাকাটা: `৳{stats['total_spent']:.2f}`\n"
        f"💵 মোট সেভিংস: `৳{stats['total_savings_bdt']:.2f}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📜 **সর্বশেষ অর্ডারের তালিকা:**\n\n"
    )
    if not reseller_orders:
        ledger_text += "_এখনও কোনো পাইকারি অর্ডার করেননি।_"
    else:
        for idx, o in enumerate(reseller_orders[:8], start=1):
            ledger_text += (
                f"**{idx}. {o['product_title']}**\n"
                f"• পরিশোধিত: `{o['amount_paid']} {o['currency']}`\n"
                f"• তারিখ: `{o['created_at'][:16]}`\n"
                f"───────────────────\n"
            )
    await message.answer(ledger_text, parse_mode="Markdown")

@router.message(Command("recent"))
async def handle_cmd_recent_orders(message: Message):
    """Shortcut: /recent to view last 10 live orders across the bot!"""
    if not is_admin(message.from_user.id):
        return
    recent = db.get_recent_orders(10)
    if not recent:
        await message.answer("📦 এখনও কোনো অর্ডার রেকর্ড হয়নি।")
        return

    text = "📜 **সর্বশেষ ১০টি লাইভ অর্ডার লেজার:**\n\n"
    for idx, o in enumerate(recent, start=1):
        buyer = f"{o.get('first_name') or 'User'} (@{o.get('username') or 'N/A'})"
        text += (
            f"**{idx}. {o['product_title']}**\n"
            f"👤 ক্রেতা: {buyer} (`{o['user_id']}`)\n"
            f"💰 মূল্য: `{o['amount_paid']} {o['currency']}`\n"
            f"🕒 সময়: `{o['created_at'][:16]}`\n"
            f"───────────────────\n"
        )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("pending"))
async def handle_cmd_pending(message: Message, bot: Bot):
    """Shortcut: /pending to quickly review pending deposit screenshots!"""
    if not is_admin(message.from_user.id):
        return
    pending = db.get_pending_transactions()
    if not pending:
        await message.answer("✅ বর্তমানে কোনো পেন্ডিং ডিপোজিট নেই!", parse_mode="Markdown")
        return
    await message.answer(f"⏳ **মোট {len(pending)} টি পেন্ডিং ডিপোজিট পাওয়া গেছে:**", parse_mode="Markdown")
    for trx in pending[:5]:
        caption = (
            f"🆔 **ট্রানজেকশন নং:** `#{trx['id']}`\n"
            f"👤 **ইউজার আইডি:** `{trx['user_id']}`\n"
            f"💳 **মেথড:** {trx['method'].upper()}\n"
            f"💰 **অ্যামাউন্ট:** `{trx['amount']} {trx['currency']}`\n"
            f"🔢 **TrxID:** `{trx['trx_id']}`\n"
            f"📅 **তারিখ:** `{trx['created_at']}`"
        )
        try:
            await bot.send_photo(
                chat_id=message.from_user.id,
                photo=trx["screenshot_file_id"],
                caption=caption,
                reply_markup=get_deposit_approval_kb(trx["id"]),
                parse_mode="Markdown"
            )
        except Exception:
            await message.answer(caption, reply_markup=get_deposit_approval_kb(trx["id"]), parse_mode="Markdown")

@router.message(Command("blast"))
async def handle_cmd_blast(message: Message, bot: Bot):
    """Shortcut: /blast <text> to broadcast instantly to all users!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("⚠️ ব্যবহার নিয়ম: `/blast <আপনার নোটিশ বার্তা>`", parse_mode="Markdown")
        return
    bcast_text = args[1]
    uids = db.get_all_user_ids()
    sent = 0
    fail = 0
    status_msg = await message.answer(f"📢 ব্রডকাস্ট শুরু হচ্ছে... (মোট ইউজার: {len(uids)})")
    for uid in uids:
        try:
            await bot.send_message(chat_id=uid, text=bcast_text, parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            fail += 1
    await status_msg.edit_text(f"✅ **ব্রডকাস্ট সম্পন্ন!**\n• সফল: `{sent}` জন\n• ব্যর্থ: `{fail}` জন", parse_mode="Markdown")

@router.message(Command("blastreseller"))
async def handle_cmd_blastreseller(message: Message, bot: Bot):
    """Shortcut: /blastreseller <text> to broadcast to resellers only!"""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("⚠️ ব্যবহার নিয়ম: `/blastreseller <রিসেলারদের নোটিশ>`", parse_mode="Markdown")
        return
    bcast_text = args[1]
    rids = db.get_all_reseller_ids()
    sent = 0
    fail = 0
    status_msg = await message.answer(f"💎 রিসেলার ব্রডকাস্ট শুরু হচ্ছে... (মোট রিসেলার: {len(rids)})")
    for rid in rids:
        try:
            await bot.send_message(chat_id=rid, text=f"💎 **[VIP রিসেলার নোটিশ]**\n\n{bcast_text}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            fail += 1
# --- 2.9 USERS DIRECTORY & INTELLIGENCE CENTER ---

@router.message(Command("users"))
@router.message(F.text.in_(["/users", "Users", "ইউজার তালিকা", "ইউজার ডিরেক্টরি", "সকল ইউজার", "ইউজার"]))
async def handle_admin_users_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    data = db.get_paginated_users_directory(page=1, per_page=8, filter_type="all")
    text = format_users_directory_text(data)
    from keyboards.admin_kb import get_users_directory_kb
    kb = get_users_directory_kb(data["users"], data["current_page"], data["total_pages"], data["filter_type"])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_users_dir:"))
async def handle_admin_users_dir_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    filter_type = parts[2] if len(parts) > 2 else "all"
    
    data = db.get_paginated_users_directory(page=page, per_page=8, filter_type=filter_type)
    text = format_users_directory_text(data)
    from keyboards.admin_kb import get_users_directory_kb
    kb = get_users_directory_kb(data["users"], data["current_page"], data["total_pages"], data["filter_type"])
    
    await call.answer()
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")


# --- 3. SMART USER SEARCH & DOSSIER CONTROLS ---

@router.callback_query(F.data == "admin_search_user_prompt")
async def handle_admin_search_prompt_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(SearchUserState.waiting_for_query)
    await call.message.answer(
        "🔍 **স্মার্ট ইউজার সার্চ ইঞ্জিন**\n\n"
        "যেকোনো ইউজারের **আইডি**, **@ইউজারনেম** অথবা **রিসেলার কোড (RS-1001)** লিখে সেন্ড করুন:\n"
        "_(টিপ: সরাসরি কমান্ড ব্যবহার করতে পারেন: `/find 8387415921`)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(SearchUserState.waiting_for_query)
async def handle_search_user_query(message: Message, state: FSMContext):
    q = message.text.strip() if message.text else ""
    user = db.find_user(q)
    if not user:
        await message.answer(f"❌ ইউজার পাওয়া যায়নি: `{q}`\nআবার চেষ্টা করুন অথবা বাতিল করুন:", reply_markup=get_cancel_fsm_kb(), parse_mode="Markdown")
        return
    await state.clear()
    is_res = user.get("is_reseller", 0) == 1
    is_perm = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
    is_banned = user.get("is_banned", 0) == 1
    await message.answer(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(user['user_id'], is_reseller=is_res, is_banned=is_banned, is_perm_deact=is_perm),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_view:"))
async def handle_usr_ctl_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split(":")[1])
    target_user = db.get_user(target_id)
    if not target_user:
        await call.answer("❌ ইউজার ডাটাবেসে পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    is_res = target_user.get("is_reseller", 0) == 1
    is_perm = target_user.get("reseller_deactivated_permanent", 0) == 1 or target_user.get("is_reseller", 0) == -1
    is_banned = target_user.get("is_banned", 0) == 1
    perms = db.get_user_permissions(target_id)
    await call.message.answer(
        format_user_dossier_text(target_user),
        reply_markup=get_user_control_kb(
            target_user['user_id'],
            is_reseller=is_res,
            is_banned=is_banned,
            is_perm_deact=is_perm,
            reseller_tier=perms["reseller_tier"],
            can_sell_channel=perms["can_sell_channel"],
            can_sell_account=perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_addbal:"))
async def handle_usr_ctl_addbal(call: CallbackQuery, state: FSMContext):
    target_id = int(call.data.split(":")[1])
    await state.update_data(target_id=target_id, action_type="add")
    await state.set_state(BalanceManageState.waiting_for_amount)
    await call.answer()
    await call.message.answer(f"💰 আইডি `{target_id}` এর ওয়ালেটে **কত টাকা (BDT) যোগ করতে চান?**", reply_markup=get_cancel_fsm_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("usr_ctl_cutbal:"))
async def handle_usr_ctl_cutbal(call: CallbackQuery, state: FSMContext):
    target_id = int(call.data.split(":")[1])
    await state.update_data(target_id=target_id, action_type="cut")
    await state.set_state(BalanceManageState.waiting_for_amount)
    await call.answer()
    await call.message.answer(f"✂️ আইডি `{target_id}` এর ওয়ালেট থেকে **কত টাকা (BDT) কর্তন করতে চান?**", reply_markup=get_cancel_fsm_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("usr_ctl_reseller:"))
async def handle_usr_ctl_reseller(call: CallbackQuery, bot: Bot):
    target_id = int(call.data.split(":")[1])
    code = f"RS-{target_id % 10000:04d}"
    db.set_reseller_status(target_id, 1, code)
    await call.answer(f"রিসেলারে উন্নীত করা হয়েছে! ({code})", show_alert=True)
    try:
        await bot.send_message(chat_id=target_id, text=f"🎉 আপনার অ্যাকাউন্ট রিসেলারে আপগ্রেড করা হয়েছে! কোড: `{code}`", parse_mode="Markdown")
    except Exception:
        pass
    user = db.get_user(target_id)
    perms = db.get_user_permissions(target_id)
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(
            target_id,
            is_reseller=True,
            is_banned=user.get("is_banned", 0)==1,
            reseller_tier=perms["reseller_tier"],
            can_sell_channel=perms["can_sell_channel"],
            can_sell_account=perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_demote:"))
async def handle_usr_ctl_demote(call: CallbackQuery, bot: Bot):
    target_id = int(call.data.split(":")[1])
    db.set_reseller_status(target_id, 0)
    await call.answer("রিসেলার পদ বাতিল করা হয়েছে!", show_alert=True)
    try:
        await bot.send_message(chat_id=target_id, text="⚠️ আপনার রিসেলার অ্যাক্সেস প্রত্যাহার করা হয়েছে।")
    except Exception:
        pass
    user = db.get_user(target_id)
    perms = db.get_user_permissions(target_id)
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(
            target_id,
            is_reseller=False,
            is_banned=user.get("is_banned", 0)==1,
            reseller_tier=perms["reseller_tier"],
            can_sell_channel=perms["can_sell_channel"],
            can_sell_account=perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_tog_ch:"))
async def handle_usr_ctl_tog_ch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split(":")[1])
    db.toggle_user_permission(target_id, "can_sell_channel")
    user = db.get_user(target_id)
    perms = db.get_user_permissions(target_id)
    ch_state = "চালু 🟢" if perms["can_sell_channel"] else "বন্ধ 🔴"
    await call.answer(f"📢 চ্যানেল সেল পারমিশন: {ch_state}", show_alert=False)
    is_res = user.get("is_reseller", 0) == 1
    is_perm = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
    is_banned = user.get("is_banned", 0) == 1
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(
            target_id,
            is_reseller=is_res,
            is_banned=is_banned,
            is_perm_deact=is_perm,
            reseller_tier=perms["reseller_tier"],
            can_sell_channel=perms["can_sell_channel"],
            can_sell_account=perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_tog_acc:"))
async def handle_usr_ctl_tog_acc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split(":")[1])
    db.toggle_user_permission(target_id, "can_sell_account")
    user = db.get_user(target_id)
    perms = db.get_user_permissions(target_id)
    acc_state = "চালু 🟢" if perms["can_sell_account"] else "বন্ধ 🔴"
    await call.answer(f"🔐 অ্যাকাউন্ট সেল পারমিশন: {acc_state}", show_alert=False)
    is_res = user.get("is_reseller", 0) == 1
    is_perm = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
    is_banned = user.get("is_banned", 0) == 1
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(
            target_id,
            is_reseller=is_res,
            is_banned=is_banned,
            is_perm_deact=is_perm,
            reseller_tier=perms["reseller_tier"],
            can_sell_channel=perms["can_sell_channel"],
            can_sell_account=perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_tog_tier:"))
async def handle_usr_ctl_tog_tier(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split(":")[1])
    perms = db.get_user_permissions(target_id)
    new_tier = 1 if perms["reseller_tier"] >= 2 else 2
    db.set_reseller_tier(target_id, new_tier)
    user = db.get_user(target_id)
    updated_perms = db.get_user_permissions(target_id)
    tier_label = "👑 Elite VIP" if new_tier >= 2 else "🥉 Standard"
    await call.answer(f"👑 রিসেলার টায়ার: {tier_label} এ পরিবর্তিত!", show_alert=True)
    is_res = user.get("is_reseller", 0) == 1
    is_perm = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
    is_banned = user.get("is_banned", 0) == 1
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(
            target_id,
            is_reseller=is_res,
            is_banned=is_banned,
            is_perm_deact=is_perm,
            reseller_tier=updated_perms["reseller_tier"],
            can_sell_channel=updated_perms["can_sell_channel"],
            can_sell_account=updated_perms["can_sell_account"]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_reactivate:"))
async def handle_usr_ctl_reactivate(call: CallbackQuery, bot: Bot):
    target_id = int(call.data.split(":")[1])
    db.reactivate_reseller(target_id)
    await call.answer("রিসেলার কোটা রিয়্যাক্টিভেট করা হয়েছে!", show_alert=True)
    try:
        await bot.send_message(chat_id=target_id, text="🎉 **আপনার রিসেলার অ্যাকাউন্ট রিয়্যাক্টিভেট করা হয়েছে!**\nনতুন ৩০ দিনের সাইকেল চালু হয়েছে।", parse_mode="Markdown")
    except Exception:
        pass
    user = db.get_user(target_id)
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(target_id, is_reseller=True, is_banned=user.get("is_banned", 0)==1),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_ban:"))
async def handle_usr_ctl_ban(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    new_status = db.toggle_user_ban(target_id)
    msg = "ইউজার ব্যান করা হয়েছে!" if new_status == 1 else "ইউজার আনব্যান করা হয়েছে!"
    await call.answer(msg, show_alert=True)
    user = db.get_user(target_id)
    is_res = user.get("is_reseller", 0) == 1
    await call.message.edit_text(
        format_user_dossier_text(user),
        reply_markup=get_user_control_kb(target_id, is_reseller=is_res, is_banned=new_status==1),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usr_ctl_orders:"))
async def handle_usr_ctl_orders(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    orders = db.get_user_orders(target_id)
    await call.answer()
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 ইউজার ডসিয়ারে ফিরুন", callback_data=f"usr_ctl_view:{target_id}"),
            InlineKeyboardButton(text="👥 ইউজার ডিরেক্টরি", callback_data="admin_users_dir:1:all")
        ]
    ])
    
    if not orders:
        await call.message.answer(f"📦 ইউজার <code>{target_id}</code> এর কোনো অর্ডার হিস্টোরি নেই।", reply_markup=back_kb, parse_mode="HTML")
        return
        
    completed = [o for o in orders if o.get("status") == "completed"]
    queue = [o for o in orders if o.get("status") in ("pending", "in_queue", "processing")]
    
    text = f"📜 <b>অর্ডার হিস্টোরি ও লাইভ কিউ (ইউজার: <code>{target_id}</code>)</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    if queue:
        text += f"🚨 <b>বর্তমানে কিউ / পেন্ডিং অর্ডার ({len(queue)} টি):</b>\n"
        for q in queue:
            text += f"• ⏳ #{q['id']} | <b>{html.escape(q['product_title'])}</b> ({q['amount_paid']} {q['currency']}) - <code>{q.get('status', 'pending')}</code>\n"
        text += "────────────────────\n\n"
    else:
        text += "⏳ <b>কিউ অর্ডার:</b> <code>কোনো পেন্ডিং অর্ডার নেই (সব ডেলিভার্ড ✅)</code>\n\n"
        
    text += f"✅ <b>সম্পন্ন অর্ডারসমূহ (সর্বশেষ {min(10, len(completed))} টি):</b>\n"
    for idx, o in enumerate(completed[:10], start=1):
        tier_str = f" [{o.get('access_tier')}]" if o.get('access_tier') and o['access_tier'] != 'default' else ""
        text += (
            f"<b>{idx}. {html.escape(o['product_title'])}{tier_str}</b>\n"
            f"• মূল্য: <code>{o['amount_paid']} {o['currency']}</code> | স্ট্যাটাস: <code>{o.get('status', 'completed')}</code>\n"
            f"• তারিখ: <code>{str(o['created_at'])[:16]}</code>\n"
            f"────────────────────\n"
        )
    await call.message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("usr_ctl_dm:"))
async def handle_usr_ctl_dm_prompt(call: CallbackQuery, state: FSMContext):
    target_id = int(call.data.split(":")[1])
    await state.update_data(target_id=target_id)
    await state.set_state(DirectDMState.waiting_for_message)
    await call.answer()
    await call.message.answer(
        f"📩 **ইউজার `{target_id}` এর কাছে পাঠানোর জন্য মেসেজটি লিখুন:**\n"
        "_(মেসেজটি বটের মাধ্যমে সরাসরি ইউজারের ইনবক্সে পৌঁছে যাবে)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(DirectDMState.waiting_for_message)
async def handle_send_direct_dm(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data["target_id"]
    dm_text = message.text or message.caption or ""
    await state.clear()
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"📩 **[অ্যাডমিন থেকে বিশেষ বার্তা]**\n\n{dm_text}",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ ইউজার `{target_id}` এর ইনবক্সে সফলভাবে মেসেজ পাঠানো হয়েছে!", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
    except Exception as e:
        await message.answer(f"❌ মেসেজ পাঠানো যায়নি: {e}", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))


# --- 4. BALANCE MANAGER WIZARD ---

@router.callback_query(F.data == "admin_manage_balance")
async def handle_admin_manage_balance_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(BalanceManageState.waiting_for_user_id)
    await call.message.answer(
        "💰 **ইউজার ওয়ালেট ব্যালেন্স ম্যানেজার**\n\n"
        "যে ইউজারের ব্যালেন্স পরিবর্তন করতে চান তার **টেলিগ্রাম আইডি (Numeric ID)** লিখুন:\n"
        "_(টিপ: সরাসরি কমান্ড দিতে পারেন: `/addbalance 123456789 500` বা `/cutbalance 123456789 100`)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(BalanceManageState.waiting_for_user_id)
async def handle_balance_waiting_user_id(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("❌ শুধুমাত্র সংখ্যা (User ID) লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` ডাটাবেসে নেই।", reply_markup=get_cancel_fsm_kb())
        return
    await state.update_data(target_id=target_id, action_type="add")
    await state.set_state(BalanceManageState.waiting_for_amount)
    await message.answer(
        f"👤 ইউজার: {user['first_name']} (`{target_id}`)\n"
        f"💳 বর্তমান ব্যালেন্স: `৳{user['balance_bdt']:.2f} BDT`\n\n"
        "👉 **কত টাকা যোগ করতে চান?** (টাকা কর্তন করতে সংখ্যার আগে মাইনাস চিহ্ন দিন, যেমন: `-100`):",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(BalanceManageState.waiting_for_amount)
async def handle_balance_waiting_amount(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("❌ সঠিক সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        raw_val = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    target_id = data["target_id"]
    action_type = data.get("action_type", "add")
    await state.clear()

    delta = raw_val if action_type == "add" else -abs(raw_val)
    db.update_user_balance(target_id, delta, "BDT")
    updated = db.get_user(target_id)

    action_word = "যোগ" if delta >= 0 else "কর্তন"
    await message.answer(
        f"✅ **সফলভাবে ৳{abs(delta):.2f} টাকা {action_word} করা হয়েছে!**\n\n"
        f"👤 ইউজার: {updated['first_name']} (`{target_id}`)\n"
        f"💳 নতুন ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats()),
        parse_mode="Markdown"
    )
    try:
        notify_word = "যোগ করা হয়েছে" if delta >= 0 else "কর্তন করা হয়েছে"
        await bot.send_message(
            chat_id=target_id,
            text=f"📢 **আপনার ওয়ালেট ব্যালেন্স আপডেট হয়েছে!**\n\n"
                 f"💰 {notify_word}: `{delta:+.2f} BDT`\n"
                 f"💳 আপনার বর্তমান ব্যালেন্স: `৳{updated['balance_bdt']:.2f} BDT`",
            parse_mode="Markdown"
        )
    except Exception:
        pass


# --- 5. RESELLER RADAR & QUOTA RISK DETECTOR ---

@router.callback_query(F.data == "admin_resellers_menu")
async def handle_admin_resellers_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    stats = db.get_extended_bot_stats()
    at_risk = db.get_at_risk_resellers()
    text = (
        "💎 **রিসেলার ম্যানেজমেন্ট ড্যাশবোর্ড**\n\n"
        f"• মোট সক্রিয় রিসেলার: `{stats.get('total_resellers', 0)} জন`\n"
        f"• পেন্ডিং আবেদন: `{stats.get('pending_reseller_apps', 0)} টি`\n"
        f"• 🚨 কোটা ঝুঁকিপূর্ণ রিসেলার: `{len(at_risk)} জন` (বাকি সময় < ৭ দিন)\n\n"
        "⚡ **শর্টকাট কমান্ডসমূহ:**\n"
        "• `/resellers` — সমস্ত রিসেলারের সম্পূর্ণ তালিকা\n"
        "• `/reseller <USER_ID>` — নির্দিষ্ট রিসেলারের ব্যক্তিগত লেজার\n"
        "• `/setreseller <USER_ID>` — সরাসরি রিসেলার প্রমোশন\n"
        "• `/reactivate <USER_ID>` — বাতিল হওয়া রিসেলারকে পুনরায় সক্রিয় করা\n\n"
        "👇 নিচের মেনু থেকে অপশন বেছে নিন:"
    )
    await call.message.edit_text(text, reply_markup=get_reseller_admin_menu_kb(at_risk_count=len(at_risk)), parse_mode="Markdown")

@router.callback_query(F.data == "admin_reseller_risk_radar")
async def handle_reseller_risk_radar(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    at_risk = db.get_at_risk_resellers()
    if not at_risk:
        await call.message.answer("🎉 চমৎকার! কোনো রিসেলার এই মুহূর্তে কোটা ঝুঁকিতে নেই। সবার টার্গেট পূরণ অথবা সময় পর্যাপ্ত আছে।")
        return

    text = f"🚨 **কোটা ঝুঁকিপূর্ণ রিসেলার তালিকা (মোট {len(at_risk)} জন):**\n\n"
    for idx, r in enumerate(at_risk, start=1):
        text += (
            f"**{idx}. [{r['reseller_code']}] {r['first_name']}** (@{r['username'] or 'N/A'})\n"
            f"🆔 ID: `{r['user_id']}`\n"
            f"🎯 সেলস সম্পন্ন: `{r['sales']} / {r['target']} টি`\n"
            f"⏳ বাকি সময়: `{r['days_left']} দিন` (এর পর স্বয়ংক্রিয় বাতিল হবে!)\n"
            f"───────────────────\n"
        )
    text += "\n💡 এদের সবাইকে একসাথে নোটিশ পাঠাতে **'🔔 Send Quota Alert PMs'** বাটনে চাপুন।"
    await call.message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_alert_risk_resellers")
async def handle_alert_risk_resellers(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await call.answer("সতর্কবার্তা পাঠানো হচ্ছে...")
    at_risk = db.get_at_risk_resellers()
    if not at_risk:
        await call.message.answer("⚠️ ঝুঁকিপূর্ণ রিসেলার নেই।")
        return
    sent = 0
    for r in at_risk:
        try:
            alert_msg = (
                f"⚠️ **জরুরি নোটিশ: আপনার মাসিক রিসেলার কোটা সংক্রান্ত**\n\n"
                f"প্রিয় {r['first_name']},\n"
                f"আপনার মাসিক রিসেলার কোটা সাইকেল শেষ হতে আর মাত্র **`{r['days_left']} দিন`** বাকি আছে!\n"
                f"আপনার বর্তমান সেলস: `{r['sales']} / {r['target']} টি`।\n\n"
                f"পলিসি অনুযায়ী সময়সীমার মধ্যে ন্যূনতম `{r['target']} টি` সেলস সম্পন্ন করতে ব্যর্থ হলে আপনার রিসেলার স্ট্যাটাস স্বয়ংক্রিয়ভাবে বাতিল হয়ে যাবে। দ্রুত কোর্স সেল নিশ্চিত করুন!"
            )
            await bot.send_message(chat_id=r["user_id"], text=alert_msg, parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass
    await call.message.answer(f"✅ সফল! `{sent} জন` ঝুঁকিপূর্ণ রিসেলারের কাছে ব্যক্তিগত সতর্কবার্তা পাঠানো হয়েছে।")

@router.callback_query(F.data == "admin_list_resellers")
async def handle_admin_list_resellers_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    resellers = db.get_all_resellers()
    if not resellers:
        await call.message.answer("⚠️ বর্তমানে কোনো অনুমোদিত রিসেলার নেই।")
        return
    text = f"💎 **অনুমোদিত রিসেলার তালিকা (মোট {len(resellers)} জন):**\n\n"
    for idx, r in enumerate(resellers, start=1):
        text += (
            f"**{idx}. [{r.get('reseller_code', 'RS-N/A')}] {r['first_name']}**\n"
            f"🆔 ID: `{r['user_id']}` | @{r['username'] or 'N/A'}\n"
            f"📦 সম্পন্ন অর্ডার: `{r.get('reseller_orders_count', 0)} টি`\n"
            f"💰 মোট ব্যয়: `৳{r.get('reseller_total_spent', 0):.2f}`\n"
            f"💳 ব্যালেন্স: `৳{r['balance_bdt']:.2f}`\n"
            f"🔎 লেজার: `/reseller {r['user_id']}`\n"
            f"───────────────────\n"
        )
    await call.message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_pending_reseller_apps")
async def handle_admin_pending_apps_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    apps = db.get_pending_reseller_applications()
    if not apps:
        await call.message.answer("✅ বর্তমানে কোনো পেন্ডিং রিসেলার আবেদন নেই।")
        return
        
    from keyboards.user_kb import get_reseller_app_approval_kb
    for app in apps:
        req_tier = app.get("requested_tier", 1) or 1
        tier_title = "👑 Elite VIP (ফুল এক্সেস)" if req_tier >= 2 else "🥉 Standard (চ্যানেল পার্টনার)"
        app_text = (
            f"📝 **রিসেলার আবেদন নং: #{app['id']}**\n"
            f"👤 আবেদনকারী: {app['first_name']} (@{app['username'] or 'N/A'})\n"
            f"🆔 আইডি: `{app['user_id']}`\n"
            f"🎯 আবেদনকৃত প্যাকেজ: **{tier_title}**\n"
            f"💳 কারেন্ট ব্যালেন্স: `৳{app['balance_bdt']:.2f}`\n"
            f"📄 বিবরণ: _{app['info']}_\n"
            f"📅 তারিখ: `{app['created_at']}`"
        )
        await call.message.answer(app_text, reply_markup=get_reseller_app_approval_kb(app['id']), parse_mode="Markdown")

@router.callback_query(F.data == "admin_quick_promote_reseller")
async def handle_admin_quick_promote_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(PromoteResellerState.waiting_for_user_id)
    await call.message.answer(
        "➕ **১-ক্লিক রিসেলার প্রমোশন**\n\n"
        "যাকে রিসেলার বানাতে চান তার টেলিগ্রাম ইউজার আইডি (Numeric ID) লিখে সেন্ড করুন:\n"
        "_(টিপ: সরাসরি কমান্ড দিতে পারেন: `/setreseller 123456789`)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(PromoteResellerState.waiting_for_user_id)
async def handle_process_promote_reseller(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("❌ শুধুমাত্র সংখ্যা (User ID) লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` ডাটাবেসে পাওয়া যায়নি।", reply_markup=get_cancel_fsm_kb())
        return
        
    await state.clear()
    code = f"RS-{target_id % 10000:04d}"
    db.set_reseller_status(target_id, 1, code)
    
    await message.answer(
        f"✅ **সফল! {user['first_name']} এখন একজন অফিশিয়াল রিসেলার!**\n"
        f"💎 কোড: `{code}`",
        reply_markup=get_reseller_admin_menu_kb()
    )
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"🎉 **অভিনন্দন! আপনার অ্যাকাউন্টকে রিসেলার পদে উন্নীত করা হয়েছে!**\n\n"
                 f"🆔 আপনার রিসেলার কোড: `{code}`\n"
                 "এখন থেকে আপনি সমস্ত কোর্সে পাইকারি ছাড় পাবেন।",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@router.callback_query(F.data == "admin_race_challenge_hub")
async def handle_admin_race_challenge_hub(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    data = db.get_challenge_leaderboard()
    ch = data["challenge"]
    racers = data["racers"]

    winners = ch.get("winners", [])
    if winners:
        winners_list = []
        for w in winners:
            winners_list.append(
                f"• #{w['rank']} [{w.get('reseller_code', 'RS')}] {w.get('first_name', 'Reseller')} "
                f"(@{w.get('username') or 'N/A'}) — সেলস: `{w.get('sales_at_win', 0)}` | পাস: `{w.get('coupon_code', 'N/A')}`"
            )
        winners_text = "\n".join(winners_list)
    else:
        winners_text = "_এখনও কোনো বিজয়ী স্লট আনলক হয়নি।_"

    if racers:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        racers_list = []
        for idx, r in enumerate(racers[:10]):
            badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
            r_name = r.get("first_name", "Reseller")
            r_code = r.get("reseller_code", "RS")
            r_sales = r.get("reseller_monthly_sales", 0)
            status_tag = f"🏆 (বিজয়ী #{r['won_rank']})" if r.get("won_rank") else f"(টার্গেট বাকি: {max(0, ch['target_sales'] - r_sales)}টি)"
            racers_list.append(f"{badge} **[{r_code}] {r_name}** — `{r_sales} টি` {status_tag}")
        racers_text = "\n".join(racers_list)
    else:
        racers_text = "_কোনো রিসেলারের সক্রিয় অগ্রগতি নেই।_"

    text = (
        "🏁 **লাইভ সেলস রেস ও প্রতিযোগিতা কন্ট্রোল সেন্টার**\n\n"
        f"🏆 **চ্যালেঞ্জ টাইটেল:** {ch['title']}\n"
        f"🎯 **টার্গেট সেলস:** `{ch['target_sales']} টি`\n"
        f"🎁 **অতিরিক্ত রিওয়ার্ড ছাড়:** `৳{ch['discount_bdt']:.0f} BDT`\n"
        f"⏳ **পাস মেয়াদ:** `{ch['days_valid']} দিন` | ব্যবহার: `{ch['max_uses']} বার`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **স্লট ও কোটা স্ট্যাটাস:**\n"
        f"• মোট স্লট: `{ch['max_slots']} টি`\n"
        f"• পূরণকৃত স্লট: `{ch['claimed_slots']} টি`\n"
        f"• খালি স্লট: `{ch['remaining_slots']} টি`\n\n"
        "🎖️ **আনলক হওয়া বিজয়ী রিসেলারগণ:**\n"
        f"{winners_text}\n\n"
        "🏎️ **শীর্ষ প্রতিদ্বন্দ্বী রিসেলারগণ:**\n"
        f"{racers_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _নতুন মাসের সেলস রেস শুরু করতে নিচের 'Reset Race' বাটনে চাপুন।_"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_admin_race_challenge_kb(), parse_mode="Markdown")
    except Exception:
        await call.message.answer(text, reply_markup=get_admin_race_challenge_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_reset_race_confirm")
async def handle_admin_reset_race_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.reset_challenge()
    await call.answer("✅ সেলস রেস সফলভাবে রিসেট করা হয়েছে! নতুন রাউন্ড শুরু হয়েছে।", show_alert=True)
    await handle_admin_race_challenge_hub(call)

@router.callback_query(F.data == "admin_edit_race_rules")
async def handle_admin_edit_race_rules_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    ch = db.get_active_challenge()
    curr_target = ch["target_sales"] if ch else 10
    await state.set_state(EditChallengeState.waiting_for_target)
    await call.message.answer(
        f"🎯 **সেলস রেস চ্যালেঞ্জ টার্গেট সেলস নির্ধারণ করুন:**\n\n"
        f"রিসেলারদের পুরস্কার পেতে কতটি সফল কোর্স বিক্রি করতে হবে?\n"
        f"_(বর্তমানে: `{curr_target}` টি — যেমন: `10` বা `15`)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditChallengeState.waiting_for_target)
async def handle_race_target_save(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন (যেমন: 10):", reply_markup=get_cancel_fsm_kb())
        return
    target = int(message.text.strip())
    await state.update_data(target_sales=target)
    await state.set_state(EditChallengeState.waiting_for_discount)
    await message.answer(
        f"🎯 টার্গেট: `{target} টি` সেলস\n\n"
        "💥 **বিজয়ী রিসেলাররা প্রতিটি পণ্যে কত টাকা (BDT) অতিরিক্ত ছাড় পাবে?**\n"
        "_(যেমন: `50` বা `100` BDT)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditChallengeState.waiting_for_discount)
async def handle_race_discount_save(message: Message, state: FSMContext):
    try:
        disc = float(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: 50):", reply_markup=get_cancel_fsm_kb())
        return
    await state.update_data(discount_bdt=disc)
    await state.set_state(EditChallengeState.waiting_for_slots)
    await message.answer(
        f"💥 অতিরিক্ত ছাড়: `৳{disc:.0f} BDT`\n\n"
        "👥 **সর্বোচ্চ কতজন দ্রুততম রিসেলার এই পুরষ্কার জিততে পারবে (স্লট সংখ্যা)?**\n"
        "_(যেমন: `3` বা `5` জন)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditChallengeState.waiting_for_slots)
async def handle_race_slots_save(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন (যেমন: 3):", reply_markup=get_cancel_fsm_kb())
        return
    slots = int(message.text.strip())
    await state.update_data(max_slots=slots)
    await state.set_state(EditChallengeState.waiting_for_days)
    await message.answer(
        f"👥 বিজয়ী স্লট: `{slots} জন`\n\n"
        "⏳ **বিজয়ীদের রিওয়ার্ড পাসটির মেয়াদ কত দিন থাকবে?**\n"
        "_(যেমন: `7` বা `15` বা `30` দিন)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditChallengeState.waiting_for_days)
async def handle_race_days_save(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন (যেমন: 7):", reply_markup=get_cancel_fsm_kb())
        return
    days = int(message.text.strip())
    await state.update_data(days_valid=days)
    await state.set_state(EditChallengeState.waiting_for_max_uses)
    await message.answer(
        f"⏳ মেয়াদ: `{days} দিন`\n\n"
        "📦 **মেয়াদের মধ্যে সর্বোচ্চ কতটি অর্ডারে এই স্পেশাল ছাড় কার্যকর হবে?**\n"
        "_(যেমন: `10` বা `20` টি অর্ডার)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditChallengeState.waiting_for_max_uses)
async def handle_race_max_uses_save(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন (যেমন: 10):", reply_markup=get_cancel_fsm_kb())
        return
    max_uses = int(message.text.strip())
    data = await state.get_data()
    await state.clear()

    title = f"Sprint Challenge ({data['target_sales']} Sales)"
    new_ch = db.set_or_create_challenge(
        title=title,
        target_sales=data["target_sales"],
        max_slots=data["max_slots"],
        discount_bdt=data["discount_bdt"],
        days_valid=data["days_valid"],
        max_uses=max_uses
    )

    confirm_text = (
        "🏁 **সেলস রেস চ্যালেঞ্জের নতুন নিয়ম সফলভাবে কার্যকর হয়েছে!** 🎉\n\n"
        f"🏆 **চ্যালেঞ্জ:** {new_ch['title']}\n"
        f"🎯 **টার্গেট:** `{new_ch['target_sales']} টি সেলস`\n"
        f"💥 **অতিরিক্ত ছাড়:** `৳{new_ch['discount_bdt']:.0f} BDT`\n"
        f"👥 **বিজয়ী স্লট:** `{new_ch['max_slots']} জন`\n"
        f"⏳ **পাস মেয়াদ:** `{new_ch['days_valid']} দিন`\n"
        f"📦 **অর্ডার লিমিট:** `{new_ch['max_uses']} টি`\n\n"
        "রিসেলাররা তাদের ড্যাশবোর্ডে লাইভ রেসে এই নতুন টার্গেট দেখতে পাবে!"
    )
    await message.answer(confirm_text, reply_markup=get_admin_race_challenge_kb(), parse_mode="Markdown")

# --- 5.1 TOP RESELLERS VIP REWARD & COUPON PASS SYSTEM ---

@router.callback_query(F.data == "admin_reward_top_hub")
async def handle_admin_reward_top_hub(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    leaderboard = db.get_reseller_leaderboard(limit=10)
    text = (
        "🏆 **টপ রিসেলার রিওয়ার্ড ড্যাশবোর্ড (Super Reward System)**\n\n"
        "প্রতি মাসে সেরা রিসেলারদের স্পেশাল ছাড়ের কুপন/ভিআইপি পাস দিন।\n"
        "এই পাস অ্যাক্টিভ থাকা অবস্থায় তারা পাইকারি মূল্যের চেয়েও আরও কম রেটে প্রোডাক্ট পাবে!\n"
        "নির্দিষ্ট মেয়াদ বা অর্ডার সংখ্যা শেষ হলে স্বয়ংক্রিয়ভাবে স্বাভাবিক মূল্যে ফিরে যাবে।\n\n"
        "📊 **বর্তমান মাসিক সেলস লিডারবোর্ড (শীর্ষ ১০ জন):**\n"
    )
    if not leaderboard:
        text += "_এখনও কোনো রিসেলারের অর্ডার রেকর্ড হয়নি।_\n"
    else:
        for rank, r in enumerate(leaderboard, start=1):
            badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            text += f"{badge} **{r.get('first_name', 'Reseller')}** (`{r['user_id']}`) — `{r.get('reseller_monthly_sales', 0)} টি সেলস` (`৳{r.get('reseller_monthly_spent', 0):.0f}`)\n"
    
    text += "\n👇 নিচে থেকে সেরা রিসেলারদের রিওয়ার্ড নির্বাচন করুন:"
    await call.message.edit_text(text, reply_markup=get_reward_top_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("reward_top_n:"))
async def handle_reward_top_n_select(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    top_n = int(call.data.split(":")[1])
    await call.answer()
    await call.message.edit_text(
        f"🏆 **সেরা {top_n} জন রিসেলারের জন্য অতিরিক্ত ছাড় (BDT) নির্বাচন করুন:**\n\n"
        "_(প্রতিটি কেনাকাটায় তারা স্বাভাবিক পাইকারি মূল্যের চেয়ে আরও কত টাকা বেশি ছাড় পাবে?)_",
        reply_markup=get_reward_discount_presets_kb(top_n),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("rwd_disc:"))
async def handle_reward_discount_select(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    top_n = int(parts[1])
    disc_val = parts[2]
    
    if disc_val == "custom":
        await state.update_data(top_n=top_n)
        await state.set_state(RewardTopCustomState.waiting_for_discount)
        await call.answer()
        await call.message.answer(
            f"✍️ **সেরা {top_n} জনের জন্য প্রতি প্রোডাক্টে অতিরিক্ত কত টাকা (BDT) ছাড় দিতে চান লিখুন:**\n"
            "_(যেমন: 40 বা 75)_",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="Markdown"
        )
        return

    discount = float(disc_val)
    await call.answer()
    await call.message.edit_text(
        f"⏳ **সেরা {top_n} জন রিসেলারের জন্য অফার মেয়াদ (Days) নির্বাচন করুন:**\n\n"
        f"• অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` / প্রোডাক্ট\n"
        "_(এই সময় অতিবাহিত হলে স্বয়ংক্রিয়ভাবে স্বাভাবিক মূল্যে ফিরে যাবে)_",
        reply_markup=get_reward_duration_presets_kb(top_n, discount),
        parse_mode="Markdown"
    )

@router.message(RewardTopCustomState.waiting_for_discount)
async def handle_reward_top_custom_discount(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        discount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    top_n = data["top_n"]
    await state.clear()
    
    await message.answer(
        f"⏳ **সেরা {top_n} জন রিসেলারের জন্য মেয়াদের সময়সীমা (Days) নির্বাচন করুন:**\n\n"
        f"• কাস্টম অতিরিক্ত ছাড়: `৳{discount:.0f} BDT`\n",
        reply_markup=get_reward_duration_presets_kb(top_n, discount),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("rwd_dur:"))
async def handle_reward_duration_select(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    top_n = int(parts[1])
    discount = float(parts[2])
    days = int(parts[3])
    await call.answer()
    await call.message.edit_text(
        f"📦 **অর্ডার ব্যবহারের সর্বোচ্চ সীমা (Order Usage Limit) নির্বাচন করুন:**\n\n"
        f"• লক্ষ্য: সেরা `{top_n}` জন রিসেলার\n"
        f"• অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` / প্রোডাক্ট\n"
        f"• অফার মেয়াদ: `{days} দিন`\n\n"
        "_(মেয়াদ শেষ হলে অথবা এই কয়টি অর্ডার সম্পন্ন হলেই স্বয়ংক্রিয়ভাবে স্বাভাবিক রিসেলার রেট প্রযোজ্য হবে)_",
        reply_markup=get_reward_uses_presets_kb(top_n, discount, days),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("rwd_apply:"))
async def handle_reward_apply_action(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    top_n = int(parts[1])
    discount = float(parts[2])
    days = int(parts[3])
    max_uses = int(parts[4])
    await call.answer("রিওয়ার্ড পাস বিতরণ করা হচ্ছে...")
    
    passes = db.reward_top_resellers(top_n=top_n, discount_bdt=discount, days_valid=days, max_uses=max_uses)
    if not passes:
        await call.message.edit_text(
            "⚠️ **কোনো সক্রিয় রিসেলার বা সেলস ডাটা পাওয়া যায়নি!**\nরিওয়ার্ড পাস তৈরি করা সম্ভব হয়নি।",
            reply_markup=get_reward_top_menu_kb(),
            parse_mode="Markdown"
        )
        return

    sent_count = 0
    for p in passes:
        try:
            notify_text = (
                f"🏆 **অভিনন্দন! আপনি এই মাসের শীর্ষ রিসেলারদের তালিকায় স্থান পেয়েছেন!** 🎉\n\n"
                f"মাসিক সেরা পারফরম্যান্সের জন্য আপনাকে এক্সক্লুসিভ ভিআইপি পাস উপহার দেওয়া হলো:\n"
                f"• 🎟️ কুপন কোড: `{p['coupon_code']}`\n"
                f"• 💥 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` (প্রতিটি কেনাকাটায় পাইকারি দামের ওপর আরও ছাড়!)\n"
                f"• ⏳ মেয়াদ: `{days} দিন`\n"
                f"• 📦 সর্বোচ্চ অর্ডার লিমিট: `{max_uses} বার`\n\n"
                f"⚡ এখন কেনাকাটা করলেই স্বয়ংক্রিয়ভাবে এই অতিরিক্ত ছাড় বাদ যাবে। অফার শেষ হলে পুনরায় স্বাভাবিক রেট প্রযোজ্য হবে। শুভকামনা!"
            )
            await bot.send_message(chat_id=p["user_id"], text=notify_text, parse_mode="Markdown")
            sent_count += 1
        except Exception:
            pass

    confirm_text = (
        f"🎉 **সফল! সেরা {len(passes)} জন রিসেলারকে রিওয়ার্ড পাস দেওয়া হয়েছে!**\n\n"
        f"• অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` / কোর্স\n"
        f"• মেয়াদ: `{days} দিন`\n"
        f"• ব্যবহারের সীমা: `{max_uses} টি অর্ডার`\n"
        f"• নোটিফিকেশন পৌঁছেছে: `{sent_count} জনের ইনবক্সে`\n\n"
        "📋 **রিওয়ার্ডপ্রাপ্ত রিসেলারবৃন্দ:**\n"
    )
    for p in passes:
        confirm_text += f"• #{p['rank']} {p.get('first_name')} (`{p['user_id']}`) — কোড: `{p['coupon_code']}`\n"

    await call.message.edit_text(confirm_text, reply_markup=get_reward_top_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_active_vip_passes")
async def handle_admin_active_vip_passes(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    active_passes = db.list_active_vip_passes()
    if not active_passes:
        await call.message.edit_text(
            "📋 **বর্তমানে কোনো সক্রিয় ভিআইপি রিওয়ার্ড পাস নেই।**\n\n"
            "নতুন পাস বিতরণ করতে 'Reward Top Sellers' ব্যবহার করুন।",
            reply_markup=get_reward_top_menu_kb(),
            parse_mode="Markdown"
        )
        return

    text = f"📋 **সক্রিয় ভিআইপি রিওয়ার্ড পাসসমূহ (মোট {len(active_passes)} টি):**\n\n"
    buttons = []
    for p in active_passes[:10]:
        res_name = p.get('first_name') or 'Reseller'
        text += (
            f"🎟️ **কোড:** `{p['coupon_code']}`\n"
            f"👤 রিসেলার: {res_name} (`{p['user_id']}`)\n"
            f"💰 অতিরিক্ত ছাড়: `৳{int(p['discount_bdt'])} BDT`\n"
            f"⏳ বাকি মেয়াদ: `{p['days_left']} দিন` (মেয়াদ শেষ: {p['expires_at'][:10]})\n"
            f"📊 ব্যবহার: `{p['used_count']} / {p['max_uses']} বার` (বাকি: {p['remaining_uses']} টি)\n"
            f"───────────────────\n"
        )
        buttons.append([InlineKeyboardButton(text=f"❌ Revoke: {p['coupon_code']}", callback_data=f"revoke_pass:{p['id']}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back to Reward Hub", callback_data="admin_reward_top_hub")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("revoke_pass:"))
async def handle_revoke_vip_pass_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pass_id = int(call.data.split(":")[1])
    db.revoke_vip_pass(pass_id)
    await call.answer("ভিআইপি পাসটি সফলভাবে বাতিল করা হয়েছে!", show_alert=True)
    await handle_admin_active_vip_passes(call)

@router.callback_query(F.data == "reward_custom_reseller")
async def handle_reward_custom_reseller_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(RewardCustomResellerState.waiting_for_user_id)
    await call.message.answer(
        "✍️ **নির্দিষ্ট রিসেলারকে কাস্টম রিওয়ার্ড পাস দেওয়ার উইজার্ড**\n\n"
        "যে রিসেলারকে বিশেষ ছাড়ের কুপন/পাস দিতে চান তার **টেলিগ্রাম আইডি (Numeric ID)** লিখুন:\n"
        "_(টিপ: সরাসরি কমান্ড দিতে পারেন: `/rewardreseller 123456789 50 7 10`)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(RewardCustomResellerState.waiting_for_user_id)
async def handle_reward_custom_user_id(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("❌ শুধুমাত্র সংখ্যা (User ID) লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    target_id = int(text)
    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ইউজার আইডি `{target_id}` পাওয়া যায়নি।", reply_markup=get_cancel_fsm_kb())
        return
    if user.get("is_reseller", 0) < 1:
        await message.answer(f"⚠️ ইউজার {user['first_name']} (`{target_id}`) অনুমোদিত রিসেলার নন। আগে তাকে রিসেলার বানান (/setreseller)।", reply_markup=get_cancel_fsm_kb())
        return

    await state.update_data(target_id=target_id)
    await state.set_state(RewardCustomResellerState.waiting_for_discount)
    await message.answer(
        f"👤 রিসেলার: **{user['first_name']}** (`{target_id}`)\n\n"
        "👉 **প্রতিটি অর্ডারে কত টাকা (BDT) অতিরিক্ত ছাড় দিতে চান?**\n"
        "_(যেমন: 50 বা 100)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(RewardCustomResellerState.waiting_for_discount)
async def handle_reward_custom_discount(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        discount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    await state.update_data(discount=discount)
    await state.set_state(RewardCustomResellerState.waiting_for_days)
    await message.answer(
        f"💰 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT`\n\n"
        "👉 **এই অফার কত দিন মেয়াদে কার্যকর থাকবে?** (দিন লিখুন):\n"
        "_(যেমন: 7, 15, বা 30)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(RewardCustomResellerState.waiting_for_days)
async def handle_reward_custom_days(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    await state.update_data(days=days)
    await state.set_state(RewardCustomResellerState.waiting_for_max_uses)
    await message.answer(
        f"⏳ মেয়াদ: `{days} দিন`\n\n"
        "👉 **সর্বোচ্চ কতটি অর্ডারে এই ছাড় প্রযোজ্য হবে?** (অর্ডার সংখ্যা লিখুন):\n"
        "_(যেমন: 5, 10, বা 20)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(RewardCustomResellerState.waiting_for_max_uses)
async def handle_reward_custom_max_uses(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    target_id = data["target_id"]
    discount = data["discount"]
    days = data["days"]
    await state.clear()

    user = db.get_user(target_id)
    r_code = user.get("reseller_code", "RS")
    pass_code = f"VIP-{r_code}-{target_id % 1000}"
    p = db.create_reseller_vip_pass(
        user_id=target_id,
        discount_bdt=discount,
        days_valid=days,
        max_uses=max_uses,
        code=pass_code
    )

    try:
        notify_text = (
            f"🎉 **অভিনন্দন! আপনাকে বিশেষ ভিআইপি রিওয়ার্ড পাস প্রদান করা হয়েছে!** 🏆\n\n"
            f"• 🎟️ কুপন কোড: `{p['coupon_code']}`\n"
            f"• 💥 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT` (প্রতিটি কেনাকাটায় পাইকারি মূল্যের চেয়েও কমে!)\n"
            f"• ⏳ মেয়াদ: `{days} দিন`\n"
            f"• 📦 মোট ব্যবহার সীমা: `{max_uses} টি অর্ডার`\n\n"
            f"⚡ এখন থেকে যেকোনো কেনাকাটায় স্বয়ংক্রিয়ভাবে এই ছাড় বাদ যাবে। অফার শেষ হলে পুনরায় স্বাভাবিক পাইকারি রেট প্রযোজ্য হবে।"
        )
        await bot.send_message(chat_id=target_id, text=notify_text, parse_mode="Markdown")
    except Exception:
        pass

    await message.answer(
        f"🎉 **সফল! রিসেলারকে রিওয়ার্ড পাস প্রদান করা হয়েছে!**\n\n"
        f"👤 রিসেলার: {user['first_name']} (`{target_id}`)\n"
        f"🎟️ কোড: `{p['coupon_code']}`\n"
        f"💰 অতিরিক্ত ছাড়: `৳{discount:.0f} BDT`\n"
        f"⏳ মেয়াদ: `{days} দিন`\n"
        f"📦 ব্যবহারের সীমা: `{max_uses} টি অর্ডার`",
        reply_markup=get_reward_top_menu_kb(),
        parse_mode="Markdown"
    )


# --- 6. BROADCAST STUDIO ---

@router.callback_query(F.data == "admin_broadcast_hub")
async def handle_broadcast_hub(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await call.message.edit_text(
        "📢 **অফিশিয়াল ব্রডকাস্ট স্টুডিও**\n\n"
        "আপনি কাদের কাছে মেসেজ পাঠাতে চান সিলেক্ট করুন:",
        reply_markup=get_broadcast_target_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("bcast_target:"))
async def handle_broadcast_select_target(call: CallbackQuery, state: FSMContext):
    target = call.data.split(":")[1]
    await state.update_data(target_group=target)
    await state.set_state(BroadcastState.waiting_for_message)
    await call.answer()
    target_name = "সকল বটের সাধারণ ও রিসেলার ইউজারদের কাছে" if target == "all" else "শুধুমাত্র ভেরিফাইড রিসেলারদের কাছে"
    await call.message.answer(
        f"📢 **ব্রডকাস্ট লক্ষ্য:** `{target_name}`\n\n"
        "👉 আপনি যা পাঠাতে চান তা লিখে সেন্ড করুন (টেক্সট মেসেজ অথবা ছবি সহ ক্যাপশন):\n"
        "_(ছবি পাঠালে ছবির সাথে ক্যাপশনে টেক্সট দিতে পারবেন)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_broadcast_resellers")
async def handle_start_resellers_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(BroadcastState.waiting_for_message)
    await state.update_data(target_group="resellers")
    await call.message.answer(
        "📢 **শুধুমাত্র রিসেলারদের কাছে স্পেশাল মেসেজ/অফার পাঠাতে মেসেজটি লিখুন:**\n"
        "_(সাধারণ ইউজাররা এই মেসেজ পাবে না)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(BroadcastState.waiting_for_message)
async def handle_execute_broadcast(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_group = data.get("target_group", "all")
    await state.clear()

    recipients = db.get_all_user_ids() if target_group == "all" else db.get_all_reseller_ids()
    if not recipients:
        await message.answer("⚠️ কোনো প্রাপক ইউজার পাওয়া যায়নি।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return

    status_msg = await message.answer(f"📢 ব্রডকাস্ট পাঠানো শুরু হয়েছে... (মোট: {len(recipients)} জন)")
    sent = 0
    fail = 0

    photo_id = message.photo[-1].file_id if message.photo else None
    caption_text = message.caption or message.text or ""

    for uid in recipients:
        try:
            if photo_id:
                await bot.send_photo(chat_id=uid, photo=photo_id, caption=caption_text, parse_mode="Markdown")
            else:
                await bot.send_message(chat_id=uid, text=caption_text, parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            fail += 1

    await status_msg.edit_text(
        f"🎉 **ব্রডকাস্ট সম্পূর্ণ হয়েছে!**\n\n"
        f"• লক্ষ্য: `{target_group.upper()}`\n"
        f"• সফলভাবে পৌঁছেছে: `{sent}` জন\n"
        f"• ব্যর্থ হয়েছে: `{fail}` জন",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats()),
        parse_mode="Markdown"
    )


# --- 7. SHOWCASE TO CHANNEL (@ProAccessBD) ---

@router.callback_query(F.data == "admin_channel_post")
async def handle_channel_post_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    prods = db.get_all_products()
    if not prods:
        await call.message.answer("⚠️ কোনো প্রোডাক্ট নেই।")
        return
    buttons = []
    for p in prods[:10]:
        buttons.append([InlineKeyboardButton(text=f"📢 {p['title']} (৳{int(p['price_bdt'])})", callback_data=f"showcase_prod:{p['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Panel", callback_data="admin_main_dashboard")])
    await call.message.edit_text(
        f"📢 **চ্যানেল শোকেস টুল ({OFFICIAL_CHANNEL})**\n\n"
        "কোন কোর্সটি সরাসরি চ্যানেলে হাই-কনভার্টিং পোস্ট হিসেবে পাঠাতে চান নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("showcase_prod:"))
async def handle_execute_showcase(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer("চ্যানেলে পোস্ট পাঠানো হচ্ছে...")

    bot_info = await bot.get_me()
    bot_uname = bot_info.username
    buy_url = f"https://t.me/{bot_uname}?start=prod_{prod_id}"

    post_caption = (
        f"🔥 **{p['title']}**\n\n"
        f"{p['description'] or 'প্রিমিয়াম ভিআইপি অ্যাক্সেস ও লাইফটাইম রিসোর্স।'}\n\n"
        f"💰 **খুচরা মূল্য:** `৳{int(p['price_bdt'])} BDT` (${p['price_usd']})\n"
        f"💎 **রিসেলারদের পাইকারি রেট:** `৳{int(p['reseller_price_bdt'])} BDT`\n\n"
        f"⚡ অটোমেটিক ডেলিভারির মাধ্যমে এখনই অ্যাক্সেস নিতে নিচের বাটনে চাপুন 👇"
    )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 সরাসরি কিনতে বট ওপেন করুন", url=buy_url)],
        [InlineKeyboardButton(text="🤝 রিসেলার হতে যোগাযোগ করুন", url=f"https://t.me/{bot_uname}")]
    ])

    try:
        if p.get("photo_file_id"):
            await bot.send_photo(
                chat_id=OFFICIAL_CHANNEL,
                photo=p["photo_file_id"],
                caption=post_caption,
                reply_markup=inline_kb,
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(
                chat_id=OFFICIAL_CHANNEL,
                text=post_caption,
                reply_markup=inline_kb,
                parse_mode="Markdown"
            )
        await call.message.answer(f"🎉 **সফল! '{p['title']}' কোর্সটি {OFFICIAL_CHANNEL} চ্যানেলে পোস্ট করা হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
    except Exception as e:
        await call.message.answer(f"❌ চ্যানেলে পোস্ট করতে ব্যর্থ: {e}\n\n_(নিশ্চিত করুন বট {OFFICIAL_CHANNEL} চ্যানেলে অ্যাডমিন এবং মেসেজ পোস্ট করার অনুমতি আছে)_", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))


# --- 8. LIVE GATEWAY & SETTINGS MANAGEMENT ---

@router.callback_query(F.data.in_(["admin_settings_menu", "admin_settings"]))
async def handle_admin_settings_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    
    text = (
        "⚙️ **অ্যাডমিন মাস্টার সেটিংস কন্ট্রোল সেন্টার**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "বটের যাবতীয় সেটিংস ও রেট ৪টি নির্দিষ্ট ডিপার্টমেন্টে সাজানো হয়েছে।\n"
        "যে ক্যাটাগরির সেটিংস পরিবর্তন করতে চান নিচে ক্লিক করুন:\n\n"
        "1️⃣ 💳 **পেমেন্ট গেটওয়ে ও নম্বর সেটিংস**\n"
        "_(বিকাশ, নগদ, রকেট, বাইনান্স নম্বর ও অন/অফ সুইচ)_\n\n"
        "2️⃣ 🎁 **রেফারেল ও ভাইরাল গ্রোথ ইঞ্জিন**\n"
        "_(টিয়ার-১, টিয়ার-২ কমিশন, ওয়েলকাম গিফট ও ব্রোঞ্জ/সিলভার/গোল্ড মাইলস্টোন)_\n\n"
        "3️⃣ 💎 **রিসেলার ও ফাইন্যান্সিয়াল সেটিংস**\n"
        "_(ডলার রেট, রিসেলার লোড ও ৩০-দিনের সেলস কোটা)_\n\n"
        "4️⃣ 📢 **চ্যানেল ও সাপোর্ট সেটিংস**\n"
        "_(অফিসিয়াল টেলিগ্রাম চ্যানেল ও সাপোর্ট অ্যাডমিন আইডি)_\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 নিচের মেনু থেকে ক্যাটাগরি বেছে নিন:"
    )
    await call.message.edit_text(text, reply_markup=get_settings_hub_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("admin_set_cat:"))
async def handle_admin_settings_category(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    cat = call.data.split(":")[1]
    
    if cat == "payment":
        gateways = {
            "bkash": db.is_gateway_active("bkash"),
            "nagad": db.is_gateway_active("nagad"),
            "rocket": db.is_gateway_active("rocket"),
            "binance": db.is_gateway_active("binance")
        }
        bkash_num = db.get_setting("bkash_number", PAYMENT_CONFIG["bkash"]["number"])
        nagad_num = db.get_setting("nagad_number", PAYMENT_CONFIG["nagad"]["number"])
        rocket_num = db.get_setting("rocket_number", PAYMENT_CONFIG["rocket"]["number"])
        binance_id = db.get_setting("binance_pay_id", PAYMENT_CONFIG["binance"]["number"])

        text = (
            "💳 **পেমেন্ট গেটওয়ে ও নম্বর সেটিংস**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "লাইভ গেটওয়ে স্ট্যাটাস ও অ্যাকাউন্ট নম্বরসমূহ:\n\n"
            f"• 🔴 **bKash (Agent - Cash Out):** `{bkash_num}` ({'🟢 চালু' if gateways['bkash'] else '🔴 সাময়িক বন্ধ'})\n"
            f"• 🟠 **Nagad (Agent - Cash Out):** `{nagad_num}` ({'🟢 চালু' if gateways['nagad'] else '🔴 সাময়িক বন্ধ'})\n"
            f"• 🟣 **Rocket:** `{rocket_num}` ({'🟢 চালু' if gateways['rocket'] else '🔴 সাময়িক বন্ধ'})\n"
            f"• 🟡 **Binance Pay ID:** `{binance_id}` ({'🟢 চালু' if gateways['binance'] else '🔴 সাময়িক বন্ধ'})\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 নম্বর এডিট করতে বা কোনো গেটওয়ে বন্ধ/চালু করতে নিচের বাটনে চাপুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_payment_kb(gateways), parse_mode="Markdown")

    elif cat == "referral":
        t1_bonus = db.get_setting("referral_t1_bonus", "10")
        t2_pct = db.get_setting("referral_t2_percent", "50")
        welcome_bonus = db.get_setting("referral_welcome_bonus", "5")
        
        b_tgt = db.get_setting("ref_milestone_bronze_target", "10")
        b_bns = db.get_setting("ref_milestone_bronze_bonus", "25")
        s_tgt = db.get_setting("ref_milestone_silver_target", "25")
        s_bns = db.get_setting("ref_milestone_silver_bonus", "75")
        g_tgt = db.get_setting("ref_milestone_gold_target", "50")
        g_bns = db.get_setting("ref_milestone_gold_bonus", "200")
        
        telemetry = db.get_referral_bot_telemetry()
        top_u = telemetry.get("top_referrer")
        top_str = f"@{top_u['username']} ({top_u['referral_count_t1']} জন)" if top_u else "নেই"

        text = (
            "🎁 **রেফারেল ও ভাইরাল গ্রোথ ইঞ্জিন সেটিংস**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 **কমিশন ও ওয়েলকাম রেট:**\n"
            f"• 👤 টিয়ার-১ সরাসরি রেফারেল বোনাস: `৳{t1_bonus} BDT`\n"
            f"• 👥 টিয়ার-২ টিম প্যাসিভ কমিশন: `{t2_pct}%` (হাফ কমিশন)\n"
            f"• 🎉 নতুন ইউজার ওয়েলকাম গিফট: `৳{welcome_bonus} BDT`\n\n"
            "🏆 **গ্যামিফাইড মাইলস্টোন বাউন্টি:**\n"
            f"• 🥉 ব্রোঞ্জ স্টার: `{b_tgt} জন` রেফারেল -> `+৳{b_bns} BDT` এক্সট্রা ক্যাশ\n"
            f"• 🥈 সিলভার ভিআইপি: `{s_tgt} জন` রেফারেল -> `+৳{s_bns} BDT` এক্সট্রা ক্যাশ (+৫% ছাড়)\n"
            f"• 🥇 গোল্ড এম্বাসেডর: `{g_tgt} জন` রেফারেল -> `+৳{g_bns} BDT` মেগা ক্যাশ বাউন্টি\n\n"
            "📈 **প্ল্যাটফর্ম সার্বিক পরিসংখ্যান:**\n"
            f"• মোট রেফারেল জয়েনিং: `{telemetry['total_joins']} জন`\n"
            f"• মোট বোনাস বিতরণ: `৳{telemetry['total_payout']:.0f} BDT`\n"
            f"• শীর্ষ রেফারার: {top_str}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 যেকোনো মান পরিবর্তন করতে নিচের বাটনে ট্যাপ করুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_referral_kb(), parse_mode="Markdown")

    elif cat == "reseller":
        min_dep = db.get_setting("reseller_min_deposit", "1000")
        fee = db.get_setting("reseller_activation_fee", "500")
        quota = db.get_setting("reseller_monthly_quota", "5")
        quota_days = db.get_setting("reseller_quota_days", "30")
        usd_rate = db.get_setting("usd_to_bdt_rate", str(USD_TO_BDT_RATE))
        try:
            usable_val = float(min_dep) - float(fee)
        except Exception:
            usable_val = 500.0

        text = (
            "💎 **রিসেলার ও ফাইন্যান্সিয়াল সেটিংস**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• 💵 **ডলার এক্সচেঞ্জ রেট:** `1 USD = ৳{usd_rate} BDT`\n"
            f"• 💎 **আবেদনে ন্যূনতম ব্যালেন্স লোড:** `৳{min_dep} BDT`\n"
            f"• 🛡️ **অনুমোদনে কর্তনযোগ্য ভেরিফিকেশন ফি:** `৳{fee} BDT`\n"
            f"• 💳 **ইউজারের ব্যবহারযোগ্য পাইকারি ব্যালেন্স:** `৳{usable_val:.0f} BDT`\n"
            f"• 🎯 **রিসেলার সেলস কোটা টার্গেট:** `{quota} টি` কোর্স\n"
            f"• ⏳ **কোটা সাইকেল মেয়াদ:** `{quota_days} দিন`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 মান এডিট করতে বা কোটা স্ক্যান চালাতে বাটনে চাপুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_reseller_kb(), parse_mode="Markdown")

    elif cat == "channel":
        official_ch = db.get_setting("official_channel", OFFICIAL_CHANNEL)
        admin_un = db.get_setting("admin_username", ADMIN_USERNAME)

        text = (
            "📢 **অফিসিয়াল চ্যানেল ও সাপোর্ট সেটিংস**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• 📢 **অফিসিয়াল চ্যানেল:** `{official_ch}`\n"
            f"• 👤 **সাপোর্ট অ্যাডমিন ইউজারনেম:** `@{admin_un}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 পরিবর্তন করতে নিচের বাটনে চাপুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_channel_kb(), parse_mode="Markdown")

    elif cat == "texts":
        announcement = db.get_setting("welcome_announcement", "কোনো সক্রিয় নোটিশ নেই")
        min_dep = db.get_setting("min_deposit_bdt", "100")
        min_dep_usd = db.get_setting("min_deposit_usd", "1")
        bk_ins = db.get_setting("bkash_instruction", PAYMENT_CONFIG["bkash"]["instruction"])
        ng_ins = db.get_setting("nagad_instruction", PAYMENT_CONFIG["nagad"]["instruction"])
        rk_ins = db.get_setting("rocket_instruction", PAYMENT_CONFIG["rocket"]["instruction"])
        bn_ins = db.get_setting("binance_instruction", PAYMENT_CONFIG["binance"]["instruction"])
        policy = db.get_setting("reseller_policy_note", "ডিফল্ট পলিসি সক্রিয়")

        text = (
            "📝 **নোটিশ, নির্দেশিকা ও মিনিমাম ডিপোজিট সেটিংস**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• 📢 **ওয়েলকাম নোটিশ:** `{announcement}`\n"
            f"• 💰 **সর্বনিম্ন ডিপোজিট (BDT):** `৳{min_dep} BDT`\n"
            f"• 💵 **সর্বনিম্ন ডিপোজিট (USD):** `${min_dep_usd} USD`\n"
            f"• 🔴 **bKash নিয়ম:** `{bk_ins}`\n"
            f"• 🟠 **Nagad নিয়ম:** `{ng_ins}`\n"
            f"• 🟣 **Rocket নিয়ম:** `{rk_ins}`\n"
            f"• 🟡 **Binance নিয়ম:** `{bn_ins}`\n"
            f"• 📜 **রিসেলার পলিসি নোট:** `{policy}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 যেকোনো টেক্সট এডিট করতে নিচের বাটনে চাপুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_texts_kb(), parse_mode="Markdown")

    elif cat == "emojis":
        text = (
            "🎭 **Telegram Premium Custom Emojis কন্ট্রোল সেন্টার**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "বটের সমস্ত মেনু ও বাটন এখন Telegram Premium অ্যানিমেটেড কাস্টম ইমোজিতে সাজানো।\n\n"
            "• **মোট প্রিমিয়াম ইমোজি স্লট:** `30+ টি সক্রিয়`\n"
            "• **সরাসরি কমান্ড শর্টকাট:**\n"
            "  - `/getemoji` — যেকোনো মেসেজ/ইমোজি থেকে Custom Emoji ID বের করুন\n"
            "  - `/setemoji <name> <id>` — যেকোনো বাটনের কাস্টম ইমোজি আইডি পরিবর্তন করুন\n"
            "  - `/setemoji <name> 0` — ডিফল্ট আইডিতে রিসেট করুন\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 নিচের অপশন থেকে বিস্তারিত দেখুন বা পরিবর্তন করুন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_emojis_kb(), parse_mode="Markdown")

    elif cat == "backup":
        human_time = db.get_setting("last_daily_backup_human", "এখনও কোনো ব্যাকআপ রেকর্ড নেই")
        text = (
            "💾 <b>স্বয়ংক্রিয় ডাটাবেজ ব্যাকআপ ও ডিজাস্টার রিকভারি</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 <b>অটো-ব্যাকআপ শিডিউল:</b> 🟢 সক্রিয় (প্রতি ২৪ ঘণ্টায় স্বয়ংক্রিয়ভাবে Telegram-এ পাঠানো হয়)\n"
            f"🕒 <b>সর্বশেষ ব্যাকআপ সময়:</b> <code>{human_time}</code>\n"
            "🎯 <b>রিসিভার:</b> সমস্ত সুপার অ্যাডমিনদের টেলিগ্রাম ইনবক্স\n"
            "🛡️ <b>ফরম্যাট:</b> SQLite Consistent Snapshot (ZIP Archive)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <b>সুবিধাসমূহ:</b>\n"
            "• ডাটা কখনোই হারাবে না — প্রতিদিনের ডাটাবেজ স্বয়ংক্রিয়ভাবে আপনার টেলিগ্রামে এসে জমা থাকবে।\n"
            "• সার্ভার বা ভিপিএস ক্র্যাশ করলেও এই ফাইলটি দিয়ে যেকোনো সময় বট শূন্য ডাটা লসে পুনরায় চালু করা যাবে।\n"
            "• যেকোনো মুহূর্তে নিচের বাটনে চাপ দিয়ে সাথে সাথে লাইভ ব্যাকআপ ডাউনলোড করে নিতে পারেন।\n\n"
            "👇 আপনার কাঙ্ক্ষিত অপশন বেছে নিন:"
        )
        await call.message.edit_text(text, reply_markup=get_settings_backup_kb(), parse_mode="HTML")

@router.callback_query(F.data == "admin_view_emojis_map")
async def handle_admin_view_emojis_map(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    from utils.emojis import DEFAULT_CUSTOM_EMOJIS, get_custom_emoji_id
    lines = ["🎭 **সক্রিয় Telegram Premium Custom Emoji তালিকা:**\n━━━━━━━━━━━━━━━━━━━━"]
    for k in sorted(DEFAULT_CUSTOM_EMOJIS.keys()):
        eid = get_custom_emoji_id(k)
        lines.append(f"• `{k}` ➔ `{eid}`")
    lines.append("━━━━━━━━━━━━━━━━━━━━\n💡 পরিবর্তন করতে পাঠান: `/setemoji <নাম> <নতুন_আইডি>`")
    text = "\n".join(lines[:25])
    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "admin_guide_getemoji")
async def handle_admin_guide_getemoji(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    guide_text = (
        "🔍 **Telegram Premium Custom Emoji ইন্সপেক্টর গাইড**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "যেকোনো টেলিগ্রাম প্রিমিয়াম কাস্টম ইমোজির আইডি পাওয়ার সহজ উপায়:\n\n"
        "১. প্রিমিয়াম ইমোজি দিয়ে লেখা যেকোনো মেসেজে **Reply** করে লিখুন: `/getemoji`\n"
        "২. অথবা সরাসরি কমান্ডের সাথে ইমোজি পাঠিয়ে দিন: `/getemoji 💎 👑 ⚡`\n\n"
        "বট সাথে সাথে প্রতিটি ইমোজির ৬৪-বিট আইডি বের করে দেখিয়ে দিবে!\n"
        "তারপর `/setemoji <name> <id>` দিয়ে যেকোনো বাটনে সেট করে নিতে পারবেন।"
    )
    await call.message.answer(guide_text, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "admin_prompt_setemoji")
async def handle_admin_prompt_setemoji(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prompt_text = (
        "✍️ **Custom Emoji আইডি পরিবর্তনের নিয়ম:**\n\n"
        "ফরম্যাট: `/setemoji <নাম> <আইডি>`\n\n"
        "📌 **উদাহরণ:**\n"
        "• `/setemoji diamond 6271494293383286950`\n"
        "• `/setemoji free_claim 5397916757333654639`\n"
        "• `/setemoji courses 6032575759606878027`\n"
        "• রিসেট করতে: `/setemoji diamond 0`"
    )
    await call.message.answer(prompt_text, parse_mode="Markdown")
    await call.answer()

@router.message(Command("getemoji"))
@router.message(Command("emojiid"))
@router.message(Command("emojis"))
async def handle_get_emoji_id_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    target_msg = message.reply_to_message if message.reply_to_message else message
    entities = target_msg.entities or []
    
    found = []
    text = target_msg.text or ""
    
    from aiogram.enums import MessageEntityType
    for ent in entities:
        if ent.type == MessageEntityType.CUSTOM_EMOJI:
            char = text[ent.offset : ent.offset + ent.length] if text else "🎭"
            found.append((char, str(ent.custom_emoji_id)))
            
    if not found:
        await message.answer(
            "🔍 **Telegram Premium Custom Emoji Inspector**\n\n"
            "প্রিমিয়াম ইমোজিযুক্ত যেকোনো মেসেজে **Reply** করে `/getemoji` লিখুন অথবা কমান্ডের সাথে ইমোজি পাঠান।\n\n"
            "👉 _উদাহরণ:_ `/getemoji 💎 👑 ⚡`",
            parse_mode="Markdown"
        )
        return
        
    out = ["🔍 **শনাক্তকৃত Telegram Premium Custom Emojis:**\n━━━━━━━━━━━━━━━━━━━━"]
    for idx, (char, eid) in enumerate(found, 1):
        out.append(f"{idx}. {char} ➔ `{eid}`")
    out.append("━━━━━━━━━━━━━━━━━━━━\n💡 এই আইডি দিয়ে বাটনের ইমোজি বদলাতে লিখুন:\n`/setemoji <নাম> <আইডি>`")
    await message.answer("\n".join(out), parse_mode="Markdown")

@router.message(Command("setemoji"))
async def handle_set_emoji_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=2) if message.text else []
    if len(args) < 3:
        await message.answer(
            "⚠️ **ব্যবহারের নিয়ম:** `/setemoji <name> <emoji_id>`\n"
            "👉 _উদাহরণ:_ `/setemoji diamond 6271494293383286950`\n"
            "👉 _রিসেট:_ `/setemoji diamond 0`",
            parse_mode="Markdown"
        )
        return
    name = args[1].lower().strip()
    eid = args[2].strip()
    from utils.emojis import DEFAULT_CUSTOM_EMOJIS
    if name not in DEFAULT_CUSTOM_EMOJIS:
        valid_keys = ", ".join(f"`{k}`" for k in list(DEFAULT_CUSTOM_EMOJIS.keys())[:15])
        await message.answer(f"❌ অজানা ইমোজি নাম: `{name}`\n\nউপলব্ধ নামসমূহ:\n{valid_keys}...", parse_mode="Markdown")
        return
    if eid in ("0", "clear", "none", "off", "default"):
        db.set_setting(f"emoji_{name}", "")
        await message.answer(f"✅ `{name}` ইমোজি ডিফল্ট আইডিতে রিসেট করা হয়েছে।", parse_mode="Markdown")
    else:
        db.set_setting(f"emoji_{name}", eid)
        await message.answer(f"✅ `{name}` ইমোজির নতুন Telegram Premium ID সেট করা হয়েছে: `{eid}`", parse_mode="Markdown")

@router.callback_query(F.data.startswith("toggle_gw:"))
async def handle_toggle_gateway(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gw = call.data.split(":")[1]
    curr = db.is_gateway_active(gw)
    new_status = not curr
    db.set_gateway_active(gw, new_status)
    status_str = "চালু (Active)" if new_status else "সাময়িক বন্ধ (Paused)"
    await call.answer(f"{gw.upper()} এখন {status_str}!", show_alert=True)
    
    # Return to payment settings view
    gateways = {
        "bkash": db.is_gateway_active("bkash"),
        "nagad": db.is_gateway_active("nagad"),
        "rocket": db.is_gateway_active("rocket"),
        "binance": db.is_gateway_active("binance")
    }
    bkash_num = db.get_setting("bkash_number", PAYMENT_CONFIG["bkash"]["number"])
    nagad_num = db.get_setting("nagad_number", PAYMENT_CONFIG["nagad"]["number"])
    rocket_num = db.get_setting("rocket_number", PAYMENT_CONFIG["rocket"]["number"])
    binance_id = db.get_setting("binance_pay_id", PAYMENT_CONFIG["binance"]["number"])

    text = (
        "💳 **পেমেন্ট গেটওয়ে ও নম্বর সেটিংস**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "লাইভ গেটওয়ে স্ট্যাটাস ও অ্যাকাউন্ট নম্বরসমূহ:\n\n"
        f"• 🔴 **bKash (Agent - Cash Out):** `{bkash_num}` ({'🟢 চালু' if gateways['bkash'] else '🔴 সাময়িক বন্ধ'})\n"
        f"• 🟠 **Nagad (Agent - Cash Out):** `{nagad_num}` ({'🟢 চালু' if gateways['nagad'] else '🔴 সাময়িক বন্ধ'})\n"
        f"• 🟣 **Rocket:** `{rocket_num}` ({'🟢 চালু' if gateways['rocket'] else '🔴 সাময়িক বন্ধ'})\n"
        f"• 🟡 **Binance Pay ID:** `{binance_id}` ({'🟢 চালু' if gateways['binance'] else '🔴 সাময়িক বন্ধ'})\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 নম্বর এডিট করতে বা কোনো গেটওয়ে বন্ধ/চালু করতে নিচের বাটনে চাপুন:"
    )
    await call.message.edit_text(text, reply_markup=get_settings_payment_kb(gateways), parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_edit:"))
async def handle_set_edit_start(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    await state.update_data(setting_key=key)
    await state.set_state(EditSettingState.waiting_for_value)
    await call.answer()
    
    curr_val = db.get_setting(key, "N/A")
    
    prompts = {
        "welcome_announcement": f"📢 **বটের হোমপেজের নতুন ওয়েলকাম নোটিশ লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}` — ডিলিট করতে 0 লিখুন)_",
        "min_deposit_bdt": f"💰 **ইউজারদের জন্য সর্বনিম্ন ডিপোজিট কত টাকা (BDT) করতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 50 অথবা 100)_",
        "min_deposit_usd": f"💵 **Binance/USDT ইউজারদের জন্য সর্বনিম্ন ডিপোজিট কত ডলার ($) করতে চান?**\n_(বর্তমানে: ${curr_val} — যেমন: 1 অথবা 2)_",
        "bkash_instruction": f"💳 **bKash পেমেন্ট নির্দেশিকা লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}`)_",
        "nagad_instruction": f"💳 **Nagad পেমেন্ট নির্দেশিকা লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}`)_",
        "rocket_instruction": f"💳 **Rocket পেমেন্ট নির্দেশিকা লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}`)_",
        "binance_instruction": f"💳 **Binance Pay নির্দেশিকা লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}`)_",
        "reseller_policy_note": f"📜 **রিসেলার পলিসি ও শর্তাবলী নোট লিখে সেন্ড করুন:**\n_(বর্তমানে: `{curr_val}`)_",
        "reseller_min_deposit": f"💎 **রিসেলার অ্যাক্টিভেশনে ন্যূনতম লোড কত টাকা (BDT) করতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 1000 অথবা 1500)_",
        "reseller_activation_fee": f"🛡️ **রিসেলার অনুমোদনে ভেরিফায়েড অ্যাক্টিভেশন ফি কত টাকা (BDT) কর্তন করতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 500 অথবা 300)_",
        "reseller_monthly_quota": f"🎯 **রিসেলারদের সেলস কোটা টার্গেট (কোর্স সংখ্যা) কত করতে চান?**\n_(বর্তমানে: {curr_val} টি — যেমন: 5 অথবা 10)_",
        "reseller_quota_days": f"⏳ **রিসেলারদের কোটা সাইকেলের মেয়াদ কত দিন করতে চান?**\n_(বর্তমানে: {curr_val} দিন — যেমন: 30 অথবা 15)_",
        "usd_rate": f"💵 **1 USD এর জন্য নতুন BDT রেট কত করতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 127.0 বা 128.5)_",
        "bkash_number": f"💳 **নতুন bKash (Agent - Cash Out) নম্বর লিখুন:**\n_(বর্তমানে: `{curr_val}` — যেমন: 017XXXXXXXX)_",
        "nagad_number": f"💳 **নতুন Nagad (Agent - Cash Out) নম্বর লিখুন:**\n_(বর্তমানে: `{curr_val}` — যেমন: 018XXXXXXXX)_",
        "rocket_number": f"💳 **নতুন Rocket নম্বর লিখুন:**\n_(বর্তমানে: `{curr_val}` — যেমন: 019XXXXXXXX)_",
        "binance_pay_id": f"💳 **নতুন Binance Pay ID লিখুন:**\n_(বর্তমানে: `{curr_val}` — যেমন: 892612368)_",
        "referral_t1_bonus": f"🎁 **প্রতি সরাসরি (Tier-1) রেফারে কত টাকা (BDT) বোনাস দিতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 10 অথবা 15)_",
        "referral_t2_percent": f"👥 **সাব-রেফারেল (Tier-2) টিম কমিশন কত শতাংশ (%) দিতে চান?**\n_(বর্তমানে: {curr_val}% — যেমন: 50 মানে হাফ কমিশন)_",
        "referral_welcome_bonus": f"🎉 **রেফারেল লিংকে জয়েন করা নতুন মেম্বারকে কত টাকা (BDT) ওয়েলকাম গিফট দিতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 5 অথবা 0)_",
        "ref_milestone_bronze_target": f"🎯 **ব্রোঞ্জ (Bronze Star) অর্জনের জন্য কতটি রেফারেল টার্গেট করতে চান?**\n_(বর্তমানে: {curr_val} জন — যেমন: 10)_",
        "ref_milestone_bronze_bonus": f"🥉 **ব্রোঞ্জ মাইলস্টোন অর্জন করলে কত টাকা (BDT) ক্যাশ বাউন্টি দিতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 25)_",
        "ref_milestone_silver_target": f"🎯 **সিলভার (Silver VIP) অর্জনের জন্য কতটি রেফারেল টার্গেট করতে চান?**\n_(বর্তমানে: {curr_val} জন — যেমন: 25)_",
        "ref_milestone_silver_bonus": f"🥈 **সিলভার মাইলস্টোন অর্জন করলে কত টাকা (BDT) ক্যাশ বাউন্টি দিতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 75)_",
        "ref_milestone_gold_target": f"🎯 **গোল্ড (Gold Ambassador) অর্জনের জন্য কতটি রেফারেল টার্গেট করতে চান?**\n_(বর্তমানে: {curr_val} জন — যেমন: 50)_",
        "ref_milestone_gold_bonus": f"🥇 **গোল্ড মাইলস্টোন অর্জন করলে কত টাকা (BDT) ক্যাশ বাউন্টি দিতে চান?**\n_(বর্তমানে: ৳{curr_val} — যেমন: 200)_",
        "official_channel": f"📢 **অফিসিয়াল চ্যানেলের নতুন ইউজারনেম লিখুন:**\n_(বর্তমানে: `{curr_val}` — যেমন: @ProAccessBD)_",
        "admin_username": f"👤 **নতুন সাপোর্ট অ্যাডমিন ইউজারনেম লিখুন (@ ছাড়া বা সহ):**\n_(বর্তমানে: `{curr_val}` — যেমন: proaccessteam)_"
    }
    prompt = prompts.get(key, f"✍️ **{key} এর নতুন মান লিখুন:**\n_(বর্তমানে: `{curr_val}`)_")
    await call.message.answer(prompt, reply_markup=get_cancel_fsm_kb(), parse_mode="Markdown")

@router.message(EditSettingState.waiting_for_value)
async def handle_set_edit_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে মানটি টেক্সট আকারে লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    val = message.text.strip()
    data = await state.get_data()
    key = data["setting_key"]
    
    # Input validation
    int_keys = [
        "reseller_min_deposit", "reseller_activation_fee", "reseller_monthly_quota", "reseller_quota_days",
        "ref_milestone_bronze_target", "ref_milestone_silver_target", "ref_milestone_gold_target"
    ]
    float_keys = [
        "usd_rate", "min_deposit_bdt", "min_deposit_usd", "referral_t1_bonus", "referral_t2_percent", "referral_welcome_bonus",
        "ref_milestone_bronze_bonus", "ref_milestone_silver_bonus", "ref_milestone_gold_bonus"
    ]

    if key in int_keys and not val.isdigit():
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন (যেমন: 10 বা 50):", reply_markup=get_cancel_fsm_kb())
        return
        
    if key in float_keys:
        try:
            float(val)
        except ValueError:
            await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: 10 বা 127.5):", reply_markup=get_cancel_fsm_kb())
            return

    if key == "admin_username":
        val = val.lstrip("@").strip()
    if key == "official_channel":
        if not val.startswith("@"):
            val = "@" + val.strip()

    await state.clear()
    db.set_setting(key, val)
    if key == "usd_rate":
        db.set_setting("usd_to_bdt_rate", val)

    # Return button depending on category
    cat = "referral" if "referral" in key or "milestone" in key else (
        "payment" if "number" in key or "pay_id" in key else (
            "channel" if "channel" in key or "username" in key else (
                "texts" if "announcement" in key or "instruction" in key or "policy" in key or "min_deposit" in key else "reseller"
            )
        )
    )

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 এই ক্যাটাগরিতে ফিরে যান", callback_data=f"admin_set_cat:{cat}"),
            InlineKeyboardButton(text="⚙️ সেটিংস মেনু", callback_data="admin_settings")
        ]
    ])

    await message.answer(
        f"✅ **সেটিংস সফলভাবে আপডেট করা হয়েছে!**\n\n"
        f"📌 **সেটিংস নেম:** `{key}`\n"
        f"💎 **নতুন লাইভ মান:** `{val}`",
        reply_markup=confirm_kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_enforce_quotas_now")
async def handle_enforce_quotas_now(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await call.answer("কোটা স্ক্যান হচ্ছে...")
    deactivated = db.enforce_reseller_quotas()
    
    for uid in deactivated:
        try:
            await bot.send_message(
                chat_id=uid,
                text="❌ **আপনার রিসেলার অ্যাকাউন্ট স্থায়ীভাবে বাতিল (Deactivated) করা হয়েছে!**\n\n"
                     "কারণ: মাসিক ন্যূনতম সেলস কোটা পূরণ করতে ব্যর্থ হয়েছেন। নিয়মানুযায়ী এই সিদ্ধান্ত স্থায়ী।",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
    await call.message.answer(
        f"🔄 **কোটা স্ক্যান সম্পন্ন!**\n\n"
        f"⚠️ টার্গেট অপূর্ণ থাকায় `{len(deactivated)} জন` রিসেলারের অ্যাকাউন্ট স্থায়ীভাবে বাতিল করা হয়েছে।",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats())
    )


# --- 9. DEPOSIT APPROVALS & REJECTIONS ---

@router.callback_query(F.data == "admin_pending_deps")
async def handle_view_pending_deps(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    pending = db.get_pending_transactions()
    if not pending:
        await call.message.answer("✅ বর্তমানে কোনো পেন্ডিং ডিপোজিট নেই!", parse_mode="Markdown")
        return
        
    await call.message.answer(f"⏳ **মোট {len(pending)} টি পেন্ডিং ডিপোজিট পাওয়া গেছে:**", parse_mode="Markdown")
    for trx in pending[:5]:
        caption = (
            f"🆔 **ট্রানজেকশন নং:** `#{trx['id']}`\n"
            f"👤 **ইউজার আইডি:** `{trx['user_id']}`\n"
            f"💳 **মেথড:** {trx['method'].upper()}\n"
            f"💰 **অ্যামাউন্ট:** `{trx['amount']} {trx['currency']}`\n"
            f"🔢 **TrxID:** `{trx['trx_id']}`\n"
            f"📅 **তারিখ:** `{trx['created_at']}`"
        )
        try:
            await bot.send_photo(
                chat_id=call.from_user.id,
                photo=trx["screenshot_file_id"],
                caption=caption,
                reply_markup=get_deposit_approval_kb(trx["id"]),
                parse_mode="Markdown"
            )
        except Exception:
            await call.message.answer(caption, reply_markup=get_deposit_approval_kb(trx["id"]), parse_mode="Markdown")

@router.callback_query(F.data.startswith("approve_dep:"))
async def handle_approve_deposit(call: CallbackQuery, bot: Bot):
    trx_id = int(call.data.split(":")[1])
    res = db.approve_transaction(trx_id, call.from_user.id)
    if not res:
        await call.answer("ইতিমধ্যে রিভিউ করা হয়েছে বা পাওয়া যায়নি!", show_alert=True)
        return
        
    await call.answer("ডিপোজিট সফলভাবে অনুমোদিত হয়েছে!")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(f"✅ **অনুমোদিত!** ট্রানজেকশন #{trx_id} এর `{res['amount']} {res['currency']}` ইউজারের ব্যালেন্সে জমা হয়েছে।")
    
    try:
        db.get_user_language(res["user_id"])  # kept for potential future use
        notify_text = (
            f"🎉 **আপনার ডিপোজিট সফলভাবে অনুমোদিত হয়েছে!**\n\n"
            f"💰 জমার পরিমাণ: `{res['amount']} {res['currency']}`\n"
            f"💳 ট্রানজেকশন আইডি: `#{trx_id}`\n\n"
            f"আপনার ওয়ালেটে টাকা যোগ করা হয়েছে। এখন নিশ্চিন্তে কোর্স কিনতে পারবেন!"
        )
        await bot.send_message(chat_id=res["user_id"], text=notify_text, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data.startswith("reject_dep:"))
async def handle_reject_deposit(call: CallbackQuery, bot: Bot):
    trx_id = int(call.data.split(":")[1])
    res = db.reject_transaction(trx_id, call.from_user.id)
    if not res:
        await call.answer("ইতিমধ্যে রিভিউ করা হয়েছে বা পাওয়া যায়নি!", show_alert=True)
        return
        
    await call.answer("ডিপোজিট বাতিল করা হয়েছে!")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(f"❌ **প্রত্যাখ্যাত!** ট্রানজেকশন #{trx_id} বাতিল করা হয়েছে।")
    
    try:
        await bot.send_message(
            chat_id=res["user_id"],
            text=f"❌ **আপনার ডিপোজিট আবেদন বাতিল করা হয়েছে!**\n\n"
                 f"ট্রানজেকশন আইডি: `#{trx_id}`\n"
                 "কারণ: সঠিক স্ক্রিনশট বা TrxID পাওয়া যায়নি। সহায়তার জন্য অ্যাডমিনকে মেসেজ দিন।",
            parse_mode="Markdown"
        )
    except Exception:
        pass


# --- 10. RECENT ORDERS & COUPONS ---

@router.callback_query(F.data == "admin_recent_orders")
async def handle_admin_recent_orders_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    recent = db.get_recent_orders(10)
    if not recent:
        await call.message.answer("📦 এখনও কোনো অর্ডার রেকর্ড হয়নি।")
        return

    text = "📜 **সর্বশেষ ১০টি লাইভ অর্ডার লেজার:**\n\n"
    for idx, o in enumerate(recent, start=1):
        buyer = f"{o.get('first_name') or 'User'} (@{o.get('username') or 'N/A'})"
        text += (
            f"**{idx}. {o['product_title']}**\n"
            f"👤 ক্রেতা: {buyer} (`{o['user_id']}`)\n"
            f"💰 মূল্য: `{o['amount_paid']} {o['currency']}`\n"
            f"🕒 সময়: `{o['created_at'][:16]}`\n"
            f"───────────────────\n"
        )
    await call.message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_coupons_menu")
async def handle_admin_coupons_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    coupons = db.list_coupons()
    text = (
        f"🎟️ **কুপন ও ভাউচার ম্যানেজমেন্ট (মোট {len(coupons)} টি)**\n\n"
        "কাস্টমারদের বিশেষ ছাড় দিতে বা চ্যানেলে ফ্ল্যাশ ক্যাম্পেইনের জন্য প্রমোকোড তৈরি করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_coupons_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "coupon_list")
async def handle_coupon_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    coupons = db.list_coupons()
    if not coupons:
        await call.message.answer("⚠️ বর্তমানে কোনো কুপন তৈরি করা নেই।", reply_markup=get_coupons_menu_kb())
        return
        
    buttons = []
    for c in coupons[:15]:
        status_dot = "🟢" if c["is_active"] and c["used_count"] < c["max_uses"] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_dot} {c['code']} (-৳{int(c['discount_bdt'])}) | {c['used_count']}/{c['max_uses']}",
                callback_data=f"coupon_view:{c['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Coupons Menu", callback_data="admin_coupons_menu")])
    
    await call.message.edit_text(
        "🎟️ **সক্রিয় ও অতীত কুপন তালিকা:**\n\nযেকোনো কুপন ডিলিট বা চালু/বন্ধ করতে সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("coupon_view:"))
async def handle_coupon_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split(":")[1])
    coupons = db.list_coupons()
    c = next((item for item in coupons if item["id"] == cid), None)
    if not c:
        await call.answer("কুপন পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    
    status_str = "🟢 সক্রিয় (Active)" if c["is_active"] and c["used_count"] < c["max_uses"] else "🔴 নিষ্ক্রিয় (Inactive)"
    text = (
        f"🎟️ **কুপন বিস্তারিত: `{c['code']}`**\n\n"
        f"• স্ট্যাটাস: {status_str}\n"
        f"• ছাড়ের পরিমাণ: `৳{c['discount_bdt']} BDT`\n"
        f"• ব্যবহার হয়েছে: `{c['used_count']} / {c['max_uses']} বার`\n"
        f"• তৈরির তারিখ: `{c['created_at'][:16]}`\n\n"
        "👇 নিচের বাটন দিয়ে চালু/বন্ধ বা সম্পূর্ণ মুছে ফেলুন:"
    )
    await call.message.edit_text(text, reply_markup=get_coupon_actions_kb(cid, bool(c["is_active"])), parse_mode="Markdown")

@router.callback_query(F.data.startswith("coupon_toggle:"))
async def handle_coupon_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split(":")[1])
    db.toggle_coupon(cid)
    await call.answer("কুপন স্ট্যাটাস পরিবর্তিত হয়েছে!", show_alert=True)
    coupons = db.list_coupons()
    c = next((item for item in coupons if item["id"] == cid), None)
    if c:
        status_str = "🟢 সক্রিয় (Active)" if c["is_active"] and c["used_count"] < c["max_uses"] else "🔴 নিষ্ক্রিয় (Inactive)"
        text = (
            f"🎟️ **কুপন বিস্তারিত: `{c['code']}`**\n\n"
            f"• স্ট্যাটাস: {status_str}\n"
            f"• ছাড়ের পরিমাণ: `৳{c['discount_bdt']} BDT`\n"
            f"• ব্যবহার হয়েছে: `{c['used_count']} / {c['max_uses']} বার`\n"
            f"• তৈরির তারিখ: `{c['created_at'][:16]}`\n\n"
            "👇 নিচের বাটন দিয়ে চালু/বন্ধ বা সম্পূর্ণ মুছে ফেলুন:"
        )
        await call.message.edit_text(text, reply_markup=get_coupon_actions_kb(cid, bool(c["is_active"])), parse_mode="Markdown")

@router.callback_query(F.data.startswith("coupon_del:"))
async def handle_coupon_delete(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split(":")[1])
    db.hard_delete_coupon(cid)
    await call.answer("কুপন সম্পূর্ণ মুছে ফেলা হয়েছে!", show_alert=True)
    await handle_coupon_list(call)

@router.callback_query(F.data == "coupon_create")
async def handle_coupon_create_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(CreateCouponState.waiting_for_code)
    await call.message.answer("🎟️ **কুপন কোডের নাম লিখুন:**\n_(যেমন: VIP50 অথবা EID100)_", reply_markup=get_cancel_fsm_kb())

@router.message(CreateCouponState.waiting_for_code)
async def handle_coupon_code_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে কোড লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    code = message.text.strip().upper()
    await state.update_data(code=code)
    await state.set_state(CreateCouponState.waiting_for_discount)
    await message.answer(f"💰 কোড: `{code}`\n\n👉 এই কোডে কত টাকা (BDT) ছাড় দিতে চান লিখুন:\n_(যেমন: 50 বা 100)_", reply_markup=get_cancel_fsm_kb())

@router.message(CreateCouponState.waiting_for_discount)
async def handle_coupon_discount_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        disc = float(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    await state.update_data(discount=disc)
    await state.set_state(CreateCouponState.waiting_for_max_uses)
    await message.answer("👥 **সর্বোচ্চ কতজন এই কোড ব্যবহার করতে পারবে?**\n_(যেমন: 20 বা 100)_", reply_markup=get_cancel_fsm_kb())

@router.message(CreateCouponState.waiting_for_max_uses)
async def handle_coupon_max_uses_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র পূর্ণ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    await state.clear()
    
    db.create_coupon(code=data["code"], discount_bdt=data["discount"], max_uses=max_uses)
    await message.answer(
        f"🎉 **সফল! নতুন কুপন সক্রিয় হয়েছে!**\n\n"
        f"🎟️ কোড: `{data['code']}`\n"
        f"💰 ডিসকাউন্ট: `৳{data['discount']} BDT`\n"
        f"👥 লিমিট: `{max_uses} জন`\n\n"
        "কাস্টমাররা এখনই এই কোড ব্যবহার করতে পারবে!",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats())
    )


# --- 11. ADD PRODUCT WIZARD ---

@router.callback_query(F.data == "admin_add_prod")
async def handle_start_add_prod(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    course_cats = db.get_categories_by_type("course")
    digi_cats = db.get_categories_by_type("digital")
    all_cats = course_cats + digi_cats
    
    buttons = []
    for c in all_cats:
        buttons.append([InlineKeyboardButton(text=f"{c.get('icon', '📁')} {c['name']}", callback_data=f"sel_cat:{c['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")])
    
    await state.set_state(AddProductState.waiting_for_category)
    await call.message.answer(
        "➕ **নতুন কোর্স / প্রোডাক্ট যুক্ত করার উইজার্ড**\n\n"
        "প্রথমে নিচের তালিকা থেকে ক্যাটাগরি নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(F.data.startswith("sel_cat:"), AddProductState.waiting_for_category)
async def handle_select_category_prod(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[1])
    await state.update_data(category_id=cat_id)
    await call.answer()
    
    # Check if category has subcategories
    if db.has_subcategories(cat_id):
        subcats = db.get_subcategories(cat_id)
        sub_buttons = []
        for sc in subcats:
            sub_buttons.append([InlineKeyboardButton(text=f"{sc.get('icon', '📁')} {sc['name']}", callback_data=f"sel_subcat:{sc['id']}")])
        sub_buttons.append([InlineKeyboardButton(text="⏩ Skip (সাব-ক্যাটাগরি ছাড়া সরাসরি যোগ)", callback_data="sel_subcat:0")])
        sub_buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")])

        await state.set_state(AddProductState.waiting_for_subcategory)
        await call.message.answer(
            "📂 **এই ক্যাটাগরির অধীনে একাধিক বিষয় / সাব-ক্যাটাগরি রয়েছে!**\n\n"
            "কোর্সটি কোন সাব-ক্যাটাগরির অধীনে যুক্ত করতে চান নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=sub_buttons)
        )
        return

    await state.update_data(subcategory_id=None)
    await state.set_state(AddProductState.waiting_for_title)
    await call.message.answer(
        "✏️ **কোর্স / প্রোডাক্টের আকর্ষণীয় নাম (Title) লিখুন:**\n"
        "_(যেমন: Premiere Pro & After Effects Masterclass 2026)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.callback_query(F.data.startswith("sel_subcat:"), AddProductState.waiting_for_subcategory)
async def handle_select_subcategory_prod(call: CallbackQuery, state: FSMContext):
    subcat_id = int(call.data.split(":")[1])
    subcat_val = subcat_id if subcat_id > 0 else None
    await state.update_data(subcategory_id=subcat_val)
    await state.set_state(AddProductState.waiting_for_title)
    await call.answer()
    
    subcat_info = ""
    if subcat_val:
        sc = db.get_category(subcat_val)
        if sc:
            subcat_info = f"\n📁 নির্বাচিত সাব-ক্যাটাগরি: **{sc['name']}**"

    await call.message.answer(
        f"✏️{subcat_info}\n**কোর্স / প্রোডাক্টের আকর্ষণীয় নাম (Title) লিখুন:**\n"
        "_(যেমন: Complete MERN Stack Masterclass 2026)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(AddProductState.waiting_for_title)
async def handle_prod_title(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে নাম টেক্সট আকারে লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(AddProductState.waiting_for_desc)
    await message.answer(
        f"📝 কোর্স: **{title}**\n\n"
        "এখন বিস্তারিত বিবরণ (Description / Features) লিখুন:\n"
        "_(কি কি শিখবে, কত ঘণ্টার কোর্স, কোনো সফটওয়্যার রিসোর্স আছে কিনা ইত্যাদি)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(AddProductState.waiting_for_desc)
async def handle_prod_desc(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে বিবরণ টেক্সট আকারে লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    desc = message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddProductState.waiting_for_price_bdt)
    await message.answer(
        "💰 **সাধারণ কাস্টমারদের জন্য খুচরা বিক্রয়মূল্য BDT (টাকায়) লিখুন:**\n"
        "_(যেমন: 500 বা 1200)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(AddProductState.waiting_for_price_bdt)
async def handle_prod_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন (যেমন: 500):", reply_markup=get_cancel_fsm_kb())
        return
    text = message.text.strip()
    try:
        price_bdt = float(text)
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন (যেমন: 500):", reply_markup=get_cancel_fsm_kb())
        return
        
    await state.update_data(price_bdt=price_bdt)
    await state.set_state(AddProductState.waiting_for_reseller_discount)
    
    await message.answer(
        f"💎 সাধারণ মূল্য: `৳{price_bdt} BDT`\n\n"
        "⚡ **রিসেলারদের জন্য পাইকারি রেট নির্বাচন করুন:**\n"
        "_(শর্টকাট বাটন চাপুন যাতে হিসাব করতে না হয়, অথবা কাস্টম দাম দিন)_",
        reply_markup=get_reseller_pricing_shortcuts_kb(price_bdt),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("res_disc:"), AddProductState.waiting_for_reseller_discount)
async def handle_prod_reseller_discount(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    mode = parts[1]
    val = float(parts[2])
    
    if mode == "custom":
        await state.set_state(AddProductState.waiting_for_custom_reseller_price)
        await call.answer()
        await call.message.answer("✍️ রিসেলারদের জন্য পাইকারি রেট BDT (টাকায়) কত নির্ধারণ করতে চান লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
        
    reseller_price = val
    await state.update_data(reseller_price_bdt=reseller_price)
    await state.set_state(AddProductState.waiting_for_type)
    await call.answer()
    
    await call.message.answer(
        f"✅ রিসেলার রেট সেট হয়েছে: `৳{reseller_price} BDT`\n\n"
        "📦 **এই কোর্সের ডেলিভারি টাইপ নির্বাচন করুন:**",
        reply_markup=get_product_type_kb(),
        parse_mode="Markdown"
    )

@router.message(AddProductState.waiting_for_custom_reseller_price)
async def handle_prod_custom_reseller_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    text = message.text.strip()
    try:
        reseller_price = float(text)
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
        
    await state.update_data(reseller_price_bdt=reseller_price)
    await state.set_state(AddProductState.waiting_for_type)
    
    await message.answer(
        f"✅ রিসেলার রেট: `৳{reseller_price} BDT`\n\n"
        "📦 **এই কোর্সের ডেলিভারি টাইপ নির্বাচন করুন:**",
        reply_markup=get_product_type_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("prod_type:"), AddProductState.waiting_for_type)
async def handle_prod_type(call: CallbackQuery, state: FSMContext, bot: Bot):
    ptype = call.data.split(":")[1]
    await state.update_data(product_type=ptype)
    await call.answer()
    
    bot_info = await bot.get_me()
    bot_uname = bot_info.username or "AllInOneProAccess_bot"
    
    if ptype == "channel_link":
        await state.set_state(AddProductState.waiting_for_target)
        await call.message.answer(
            f"🔒 <b>প্রাইভেট চ্যানেলের ID অথবা @Username দিন:</b>\n\n"
            f"⚠️ <b>জরুরি নির্দেশিকা:</b>\n"
            f"১. আপনার চ্যানেলে গিয়ে <code>@{bot_uname}</code> কে <b>Administrator</b> হিসেবে যোগ করুন।\n"
            f"২. অ্যাডমিন রাইটসের মধ্যে <b>'Invite Users via Link'</b> পারমিশন অন রাখুন।\n\n"
            f"<i>(উদাহরণ: <code>@my_course_channel</code> অথবা <code>-1001234567890</code>)</i>\n\n"
            f"👉 আপনি চ্যানেল ইউজারনেম/আইডি পাঠানো মাত্রই বট স্বয়ংক্রিয়ভাবে লাইভ টেস্ট করবে।",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML"
        )
    elif ptype == "stock_account":
        await state.set_state(AddProductState.waiting_for_acc_site_link)
        await call.message.answer(
            "🌐 <b>ধাপ ১/৩: অ্যাকাউন্টের অফিসিয়াল লগইন পোর্টাল বা ওয়েবসাইট লিংক দিন:</b>\n\n"
            "<i>(যেমন: <code>https://chatgpt.com</code> বা <code>https://canva.com</code> — কোনো ওয়েবসাইট না থাকলে 'skip' লিখুন)</i>",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML"
        )
    elif ptype == "dual_access":
        await state.set_state(AddProductState.waiting_for_dual_ch_price)
        data = await state.get_data()
        default_price = data.get("price_bdt", 300)
        await call.message.answer(
            f"🔥 <b>ডুয়েল প্যাকেজ কনফিগারেশন (VIP Channel + Personal Account Access)</b>\n\n"
            f"এই কোর্সে একই সাথে ২টি আলাদা প্যাকেজ থাকবে এবং কাস্টমার নিজের পছন্দমতো সিলেক্ট করে কিনতে পারবে।\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 <b>ধাপ ১/৭: VIP Channel অ্যাক্সেসের সাধারণ খুচরা মূল্য (BDT) কত?</b>\n"
            f"<i>(যেমন: <code>{int(default_price)}</code> — কাস্টমার চ্যানেল নিলে এই রেট দেবে)</i>",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML"
        )
    elif ptype == "drive_link":
        await state.set_state(AddProductState.waiting_for_target)
        await call.message.answer(
            "☁️ **Google Drive / Mega / ক্লাউড লিংকটি দিন:**\n"
            "_(কেনার সাথে সাথে কাস্টমার এই লিংক পেয়ে যাবে)_",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="Markdown"
        )

# --- 1. CHANNEL ACCESS FLOW & VERIFICATION ---
@router.message(AddProductState.waiting_for_target)
async def handle_prod_channel_or_drive_target(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে লিংক বা ইউজারনেম পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    target = message.text.strip()
    data = await state.get_data()
    ptype = data.get("product_type")
    
    if ptype == "channel_link":
        await message.answer("🔍 টেলিগ্রাম সার্ভারে চ্যানেল ও বট অ্যাডমিন পারমিশন যাচাই করা হচ্ছে...")
        res = await verify_telegram_channel_access(bot, target)
        if res["success"]:
            await state.update_data(target=target)
            await state.set_state(AddProductState.waiting_for_photo)
            await message.answer(
                f"✅ <b>চ্যানেল সফলভাবে ভেরিফাই ও লিংক হয়েছে!</b>\n\n"
                f"📢 চ্যানেল: <b>{res['title']}</b>\n"
                f"🔑 বট অ্যাডমিন রাইটস ও ১-টাইম ইনভাইট লিংক তৈরি শতভাগ সক্রিয়!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🖼️ <b>কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:</b>\n"
                f"<i>(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)</i>",
                reply_markup=get_cancel_fsm_kb(),
                parse_mode="HTML"
            )
        else:
            bot_info = await bot.get_me()
            bot_uname = bot_info.username or "bot"
            await state.update_data(pending_channel_target=target, channel_next_step="photo")
            warn_text = (
                f"⚠️ <b>চ্যানেল চেক সতর্কবার্তা!</b>\n\n"
                f"📌 সমস্যা: {res['message']}\n\n"
                f"👉 <b>কীভাবে ঠিক করবেন:</b>\n"
                f"১. আপনার টেলিগ্রাম চ্যানেলে যান ➡️ Edit ➡️ Administrators ➡️ Add Administrator\n"
                f"২. <code>@{bot_uname}</code> কে সিলেক্ট করে <b>'Invite Users via Link'</b> পারমিশন অন করুন।\n\n"
                f"পারমিশন দেওয়া সম্পন্ন হলে নিচের বাটনে চাপ দিন:"
            )
            retry_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Re-check / আবার চেক করুন", callback_data="recheck_channel")],
                [InlineKeyboardButton(text="⏩ Skip / পরে অ্যাডমিন বানাবো (Save Anyway)", callback_data="skip_channel_check")],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")]
            ])
            await message.answer(warn_text, reply_markup=retry_kb, parse_mode="HTML")
    else:
        # Google Drive / Mega link
        await state.update_data(target=target)
        await state.set_state(AddProductState.waiting_for_photo)
        await message.answer(
            "🖼️ **কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:**\n"
            "_(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)_",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "recheck_channel")
async def handle_recheck_channel(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    data = await state.get_data()
    target = data.get("pending_channel_target") or data.get("target")
    if not target:
        await call.answer("❌ কোনো চ্যানেল পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer("🔄 যাচাই করা হচ্ছে...")
    res = await verify_telegram_channel_access(bot, target)
    if res["success"]:
        await state.update_data(target=target)
        next_step = data.get("channel_next_step", "photo")
        if next_step == "dual_account_price":
            await state.set_state(AddProductState.waiting_for_dual_acc_price)
            await call.message.edit_text(
                f"✅ <b>চ্যানেল সফলভাবে ভেরিফাই হয়েছে!</b>\n"
                f"📢 চ্যানেল: <b>{res['title']}</b>\n"
                f"🔑 বট অ্যাডমিন ও ১-টাইম ইনভাইট লিংক তৈরি শতভাগ সক্রিয়!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔐 <b>ধাপ ৩/৭: এবার Personal Account অ্যাক্সেসের সাধারণ খুচরা মূল্য (BDT) কত?</b>\n"
                f"<i>(যেমন: <code>350</code> — কাস্টমার পার্সোনাল অ্যাকাউন্ট নিলে এই রেট দেবে)</i>",
                parse_mode="HTML"
            )
        else:
            await state.set_state(AddProductState.waiting_for_photo)
            await call.message.edit_text(
                f"✅ <b>চ্যানেল সফলভাবে ভেরিফাই হয়েছে!</b>\n"
                f"📢 চ্যানেল: <b>{res['title']}</b>\n"
                f"🔑 বট অ্যাডমিন ও ১-টাইম ইনভাইট লিংক তৈরি শতভাগ সক্রিয়!\n\n"
                f"🖼️ <b>কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:</b>\n"
                f"<i>(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)</i>",
                parse_mode="HTML"
            )
    else:
        bot_info = await bot.get_me()
        bot_uname = bot_info.username or "bot"
        warn_text = (
            f"⚠️ <b>চ্যানেল চেক এখনও ব্যর্থ হয়েছে!</b>\n\n"
            f"📌 সমস্যা: {res['message']}\n\n"
            f"👉 সমাধান:\n"
            f"১. আপনার চ্যানেলে যান ➡️ Edit ➡️ Administrators\n"
            f"২. <code>@{bot_uname}</code> কে যোগ করে <b>'Invite Users via Link'</b> পারমিশন দিন।\n\n"
            f"অ্যাডমিন বানানোর পর নিচের বাটনে চাপ দিন:"
        )
        retry_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Re-check / আবার চেক করুন", callback_data="recheck_channel")],
            [InlineKeyboardButton(text="⏩ Skip / পরে অ্যাডমিন বানাবো (Save Anyway)", callback_data="skip_channel_check")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")]
        ])
        await call.message.edit_text(warn_text, reply_markup=retry_kb, parse_mode="HTML")

@router.callback_query(F.data == "skip_channel_check")
async def handle_skip_channel_check(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    data = await state.get_data()
    target = data.get("pending_channel_target") or data.get("target")
    await state.update_data(target=target)
    await call.answer("⏩ স্কিপ করা হয়েছে। পরে অ্যাডমিন বানিয়ে নিবেন।")
    next_step = data.get("channel_next_step", "photo")
    if next_step == "dual_account_price":
        await state.set_state(AddProductState.waiting_for_dual_acc_price)
        await call.message.edit_text(
            f"⚠️ চ্যানেল সেভ হয়েছে: <code>{target}</code> (ভেরিফিকেশন স্কিপড)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐 <b>ধাপ ৩/৭: এবার Personal Account অ্যাক্সেসের সাধারণ খুচরা মূল্য (BDT) কত?</b>\n"
            f"<i>(যেমন: <code>350</code> — কাস্টমার পার্সোনাল অ্যাকাউন্ট নিলে এই রেট দেবে)</i>",
            parse_mode="HTML"
        )
    else:
        await state.set_state(AddProductState.waiting_for_photo)
        await call.message.edit_text(
            f"⚠️ চ্যানেল সেভ হয়েছে: <code>{target}</code> (ভেরিফিকেশন স্কিপড)\n\n"
            f"🖼️ <b>কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:</b>\n"
            f"<i>(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)</i>",
            parse_mode="HTML"
        )

# --- 2. READY ACCOUNT FLOW (Mail:Pass + Portal + Rules) ---
@router.message(AddProductState.waiting_for_acc_site_link)
async def handle_prod_acc_site_link(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ টেক্সট লিখে পাঠান অথবা 'skip' লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    site_link = "" if message.text.strip().lower() == "skip" else message.text.strip()
    await state.update_data(acc_site_link=site_link)
    await state.set_state(AddProductState.waiting_for_acc_creds)
    await message.answer(
        "🔐 <b>ধাপ ২/৩: অ্যাকাউন্টের লগইন তথ্য (Email:Password বা Access Key) দিন:</b>\n\n"
        "<i>💡 টিপস: আপনি একসাথে একাধিক অ্যাকাউন্ট দিতে পারেন! প্রতি লাইনে ১টি করে অ্যাকাউন্ট দিলে ক্রেতা কেনার সাথে সাথে স্বয়ংক্রিয়ভাবে একটি করে ডেলিভারি পাবে।</i>\n\n"
        "<b>উদাহরণ:</b>\n"
        "<code>user1@gmail.com:pass123\nuser2@gmail.com:pass456</code>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_acc_creds)
async def handle_prod_acc_creds(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অ্যাকাউন্টের তথ্য লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    creds = message.text.strip()
    await state.update_data(acc_creds=creds)
    await state.set_state(AddProductState.waiting_for_acc_rules)
    await message.answer(
        "⚠️ <b>ধাপ ৩/৩: কাস্টমারের জন্য জরুরি নিয়ম, টিপস ও ওয়ারেন্টি পলিসি দিন:</b>\n\n"
        "<i>(যেমন: 'পাসওয়ার্ড বা ইমেইল পরিবর্তন নিষেধ। ১টি ডিভাইসে লগইন করবেন। ওয়ারেন্টি ৩০ দিন।' — কিছু না দিতে চাইলে 'skip' লিখুন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_acc_rules)
async def handle_prod_acc_rules(message: Message, state: FSMContext):
    rules = "" if not message.text or message.text.strip().lower() == "skip" else message.text.strip()
    await state.update_data(acc_rules=rules)
    await state.set_state(AddProductState.waiting_for_photo)
    await message.answer(
        "🖼️ <b>কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:</b>\n"
        "<i>(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

# --- 3. DUAL ACCESS FLOW (Channel + Account) ---
@router.message(AddProductState.waiting_for_dual_ch_price)
async def handle_dual_ch_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        ch_price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সংখ্যা লিখুন (যেমন: 250):", reply_markup=get_cancel_fsm_kb())
        return
        
    def_reseller = round(ch_price * 0.70, 2)
    await state.update_data(price_channel_bdt=ch_price, def_dual_ch_reseller=def_reseller)
    await state.set_state(AddProductState.waiting_for_dual_ch_reseller_price)
    await message.answer(
        f"📢 VIP Channel খুচরা মূল্য: <code>৳{ch_price:.0f} BDT</code>\n\n"
        f"💎 <b>VIP Channel-এর রিসেলার পাইকারি মূল্য (BDT) কত?</b>\n"
        f"<i>(৩০% ছাড়ে স্বাভাবিক রেট: <code>৳{def_reseller:.0f}</code> — এই রেট রাখতে চাইলে 'ok' লিখুন, অথবা নতুন সংখ্যা লিখুন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_ch_reseller_price)
async def handle_dual_ch_reseller_price(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = (message.text or "").strip().lower()
    if text == "ok":
        r_price = data.get("def_dual_ch_reseller", round(data.get("price_channel_bdt", 200) * 0.70, 2))
    else:
        try:
            r_price = float(text)
        except ValueError:
            r_price = data.get("def_dual_ch_reseller", round(data.get("price_channel_bdt", 200) * 0.70, 2))
            
    await state.update_data(reseller_price_channel_bdt=r_price)
    await state.set_state(AddProductState.waiting_for_dual_channel_target)
    bot_info = await bot.get_me()
    bot_uname = bot_info.username or "AllInOneProAccess_bot"
    await message.answer(
        f"🔒 <b>ধাপ ২/৭: VIP চ্যানেলের ID অথবা @Username দিন:</b>\n\n"
        f"⚠️ <b>জরুরি:</b> <code>@{bot_uname}</code> কে অবশ্যই চ্যানেলে <b>Administrator</b> বানিয়ে <b>'Invite Users via Link'</b> পারমিশন দিন।\n\n"
        f"<i>(উদাহরণ: <code>@my_channel</code> অথবা <code>-1001234567890</code>)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_channel_target)
async def handle_dual_channel_target(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("❌ চ্যানেলের ইউজারনেম বা আইডি দিন:", reply_markup=get_cancel_fsm_kb())
        return
    target = message.text.strip()
    await message.answer("🔍 টেলিগ্রাম সার্ভারে চ্যানেল ও পারমিশন যাচাই করা হচ্ছে...")
    res = await verify_telegram_channel_access(bot, target)
    if res["success"]:
        await state.update_data(target=target)
        await state.set_state(AddProductState.waiting_for_dual_acc_price)
        data = await state.get_data()
        default_acc_p = data.get("price_bdt", 350)
        await message.answer(
            f"✅ <b>চ্যানেল সফলভাবে ভেরিফাই হয়েছে!</b>\n"
            f"📢 চ্যানেল: <b>{res['title']}</b>\n"
            f"🔑 বট অ্যাডমিন ও ১-টাইম ইনভাইট লিংক তৈরি প্রস্তুত!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐 <b>ধাপ ৩/৭: Personal Account অ্যাক্সেসের সাধারণ খুচরা মূল্য (BDT) কত?</b>\n"
            f"<i>(যেমন: <code>{int(default_acc_p)}</code> — কাস্টমার পার্সোনাল অ্যাকাউন্ট নিলে এই রেট দেবে)</i>",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML"
        )
    else:
        bot_info = await bot.get_me()
        bot_uname = bot_info.username or "bot"
        await state.update_data(pending_channel_target=target, channel_next_step="dual_account_price")
        warn_text = (
            f"⚠️ <b>চ্যানেল চেক সতর্কবার্তা!</b>\n\n"
            f"📌 সমস্যা: {res['message']}\n\n"
            f"👉 সমাধান:\n"
            f"১. চ্যানেলে গিয়ে <code>@{bot_uname}</code> কে <b>Administrator</b> বানিয়ে 'Invite Users via Link' পারমিশন দিন।\n\n"
            f"পারমিশন দেওয়া হলে নিচের বাটনে চাপ দিন:"
        )
        retry_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Re-check / আবার চেক করুন", callback_data="recheck_channel")],
            [InlineKeyboardButton(text="⏩ Skip / পরে অ্যাডমিন বানাবো (Save Anyway)", callback_data="skip_channel_check")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")]
        ])
        await message.answer(warn_text, reply_markup=retry_kb, parse_mode="HTML")

@router.message(AddProductState.waiting_for_dual_acc_price)
async def handle_dual_acc_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        acc_price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: 350):", reply_markup=get_cancel_fsm_kb())
        return
    def_reseller = round(acc_price * 0.70, 2)
    await state.update_data(price_account_bdt=acc_price, def_dual_acc_reseller=def_reseller)
    await state.set_state(AddProductState.waiting_for_dual_acc_reseller_price)
    await message.answer(
        f"🔐 Personal Account খুচরা মূল্য: <code>৳{acc_price:.0f} BDT</code>\n\n"
        f"💎 <b>Personal Account-এর রিসেলার পাইকারি মূল্য (BDT) কত?</b>\n"
        f"<i>(৩০% ছাড়ে স্বাভাবিক রেট: <code>৳{def_reseller:.0f}</code> — এই রেট রাখতে চাইলে 'ok' লিখুন, অথবা নতুন সংখ্যা লিখুন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_acc_reseller_price)
async def handle_dual_acc_reseller_price(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (message.text or "").strip().lower()
    if text == "ok":
        r_price = data.get("def_dual_acc_reseller", round(data.get("price_account_bdt", 300) * 0.70, 2))
    else:
        try:
            r_price = float(text)
        except ValueError:
            r_price = data.get("def_dual_acc_reseller", round(data.get("price_account_bdt", 300) * 0.70, 2))
    await state.update_data(reseller_price_account_bdt=r_price)
    await state.set_state(AddProductState.waiting_for_dual_acc_site_link)
    await message.answer(
        "🌐 <b>ধাপ ৫/৭: Personal Account-এর অফিসিয়াল লগইন পোর্টাল বা সাইট লিংক দিন:</b>\n\n"
        "<i>(যেমন: <code>https://chatgpt.com</code> বা <code>https://adobe.com</code> — না থাকলে 'skip' লিখুন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_acc_site_link)
async def handle_dual_acc_site_link(message: Message, state: FSMContext):
    site_link = "" if not message.text or message.text.strip().lower() == "skip" else message.text.strip()
    await state.update_data(acc_site_link=site_link)
    await state.set_state(AddProductState.waiting_for_dual_acc_creds)
    await message.answer(
        "🔑 <b>ধাপ ৬/৭: অ্যাকাউন্টের লগইন তথ্য (Email:Password বা Access Key) দিন:</b>\n\n"
        "<i>(একাধিক অ্যাকাউন্ট থাকলে প্রতি লাইনে ১টি করে Mail:Pass দিন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_acc_creds)
async def handle_dual_acc_creds(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অ্যাকাউন্টের তথ্য লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    creds = message.text.strip()
    await state.update_data(acc_creds=creds)
    await state.set_state(AddProductState.waiting_for_dual_acc_rules)
    await message.answer(
        "⚠️ <b>ধাপ ৭/৭: কাস্টমারের জন্য জরুরি নিয়ম, টিপস ও ওয়ারেন্টি পলিসি দিন:</b>\n\n"
        "<i>(যেমন: 'পাসওয়ার্ড পরিবর্তন করবেন না। ১টি ডিভাইসে লগইন করবেন।' — স্কিপ করতে 'skip' লিখুন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(AddProductState.waiting_for_dual_acc_rules)
async def handle_dual_acc_rules(message: Message, state: FSMContext):
    rules = "" if not message.text or message.text.strip().lower() == "skip" else message.text.strip()
    await state.update_data(acc_rules=rules)
    await state.set_state(AddProductState.waiting_for_photo)
    await message.answer(
        "🖼️ <b>কোর্সের একটি ব্যানার ফটো (Photo) পাঠান:</b>\n"
        "<i>(ছবি না দিতে চাইলে 'skip' লিখে মেসেজ দিন)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

# --- 4. PHOTO & FINAL PRODUCT CREATION ---
@router.message(AddProductState.waiting_for_photo)
async def handle_prod_photo(message: Message, state: FSMContext):
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == "skip":
        photo_file_id = None
    else:
        await message.answer("❌ অনুগ্রহ করে ছবি পাঠান অথবা 'skip' লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
        
    data = await state.get_data()
    await state.clear()
    
    cat_id = data["category_id"]
    title = data["title"]
    desc = data["description"]
    ptype = data["product_type"]
    
    def build_account_delivery(site_link: str, cred_line: str, rules_text: str) -> str:
        parts = []
        if site_link:
            parts.append(f"🌐 Login Portal: {site_link}")
        if cred_line:
            parts.append(f"🔑 Account Access:\n{cred_line}")
        if rules_text:
            parts.append(f"⚠️ Important Rules / Warranty:\n{rules_text}")
        return "\n\n".join(parts) if parts else "অ্যাক্সেস তথ্য প্রসেস করা হয়েছে।"

    added_stock_count = 0
    
    if ptype == "dual_access":
        live_rate = get_live_usd_rate()
        ch_bdt = float(data.get("price_channel_bdt", data.get("price_bdt", 250)))
        ch_usd = round(ch_bdt / live_rate, 2)
        r_ch_bdt = float(data.get("reseller_price_channel_bdt", round(ch_bdt * 0.70, 2)))
        
        acc_bdt = float(data.get("price_account_bdt", data.get("price_bdt", 350)))
        acc_usd = round(acc_bdt / live_rate, 2)
        r_acc_bdt = float(data.get("reseller_price_account_bdt", round(acc_bdt * 0.70, 2)))
        
        main_price_bdt = min(ch_bdt, acc_bdt)
        main_price_usd = round(main_price_bdt / live_rate, 2)
        main_res_bdt = min(r_ch_bdt, r_acc_bdt)
        main_res_usd = round(main_res_bdt / live_rate, 2)
        
        channel_id = data.get("target")
        site_link = data.get("acc_site_link", "")
        raw_creds = data.get("acc_creds", "")
        rules = data.get("acc_rules", "")
        
        cred_lines = [line.strip() for line in raw_creds.split("\n") if line.strip()]
        first_cred = cred_lines[0] if cred_lines else raw_creds
        account_template = build_account_delivery(site_link, first_cred, rules)
        
        prod_id = db.add_product(
            category_id=cat_id,
            title=title,
            description=desc,
            price_bdt=main_price_bdt,
            price_usd=main_price_usd,
            product_type="channel_link", # Enables dual pricing display in catalog
            channel_id=channel_id,
            drive_link=account_template,
            photo_file_id=photo_file_id,
            reseller_price_bdt=main_res_bdt,
            reseller_price_usd=main_res_usd,
            price_channel_bdt=ch_bdt,
            price_channel_usd=ch_usd,
            price_account_bdt=acc_bdt,
            price_account_usd=acc_usd,
            reseller_price_channel_bdt=r_ch_bdt,
            reseller_price_account_bdt=r_acc_bdt,
            is_in_stock=1,
            subcategory_id=data.get("subcategory_id")
        )
        
        if cred_lines:
            stock_items_to_add = [build_account_delivery(site_link, c, rules) for c in cred_lines]
            added_stock_count = db.add_stock_items(prod_id, stock_items_to_add)

        confirm_text = (
            f"🎉 <b>অভিনন্দন! ডুয়েল প্যাকেজ কোর্স সফলভাবে যুক্ত হয়েছে!</b>\n\n"
            f"🆔 প্রোডাক্ট আইডি: <code>#{prod_id}</code>\n"
            f"📌 নাম: <b>{title}</b>\n"
            f"📦 ধরন: <b>🔥 Dual Package (Channel + Personal Account)</b>\n"
            f"• 📢 <b>VIP Channel:</b> ৳{int(ch_bdt)} BDT (${ch_usd}) | রিসেলার: ৳{int(r_ch_bdt)}\n"
            f"• 🔐 <b>Personal Account:</b> ৳{int(acc_bdt)} BDT (${acc_usd}) | রিসেলার: ৳{int(r_acc_bdt)}\n"
            f"• 🔑 অ্যাকাউন্ট স্টক জমা হয়েছে: <b>{added_stock_count} টি</b>\n\n"
            f"✅ ক্রেতারা এখন ক্যাটালগে এক পোস্টেই ২টি প্যাকেজ ও মূল্য দেখতে পাবে!"
        )

    elif ptype == "stock_account":
        live_rate = get_live_usd_rate()
        price_bdt = float(data["price_bdt"])
        price_usd = round(price_bdt / live_rate, 2)
        res_bdt = float(data["reseller_price_bdt"])
        res_usd = round(res_bdt / live_rate, 2)
        
        site_link = data.get("acc_site_link", "")
        raw_creds = data.get("acc_creds", "")
        rules = data.get("acc_rules", "")
        
        cred_lines = [line.strip() for line in raw_creds.split("\n") if line.strip()]
        first_cred = cred_lines[0] if cred_lines else raw_creds
        account_template = build_account_delivery(site_link, first_cred, rules)
        
        prod_id = db.add_product(
            category_id=cat_id,
            title=title,
            description=desc,
            price_bdt=price_bdt,
            price_usd=price_usd,
            product_type="stock_account",
            channel_id=None,
            drive_link=account_template,
            photo_file_id=photo_file_id,
            reseller_price_bdt=res_bdt,
            reseller_price_usd=res_usd,
            is_in_stock=1,
            subcategory_id=data.get("subcategory_id")
        )
        
        if cred_lines:
            stock_items_to_add = [build_account_delivery(site_link, c, rules) for c in cred_lines]
            added_stock_count = db.add_stock_items(prod_id, stock_items_to_add)

        confirm_text = (
            f"🎉 <b>অভিনন্দন! অ্যাকাউন্ট কোর্স সফলভাবে যুক্ত হয়েছে!</b>\n\n"
            f"🆔 প্রোডাক্ট আইডি: <code>#{prod_id}</code>\n"
            f"📌 নাম: <b>{title}</b>\n"
            f"💰 খুচরা মূল্য: <code>৳{price_bdt:.0f} BDT</code> (${price_usd})\n"
            f"💎 রিসেলার রেট: <code>৳{res_bdt:.0f} BDT</code> (${res_usd})\n"
            f"📦 ধরন: 🔐 Ready Stock Account\n"
            f"📊 মোট স্টক জমা হয়েছে: <b>{added_stock_count} টি অ্যাকাউন্ট</b>\n\n"
            f"⚡ কেনার সাথে সাথে কাস্টমার অটোমেটিক এই অ্যাক্সেস ও গাইডলাইন পেয়ে যাবে!"
        )

    else:
        # Standard channel_link or drive_link
        live_rate = get_live_usd_rate()
        price_bdt = float(data["price_bdt"])
        price_usd = round(price_bdt / live_rate, 2)
        res_bdt = float(data["reseller_price_bdt"])
        res_usd = round(res_bdt / live_rate, 2)
        target = data.get("target")
        channel_id = target if ptype == "channel_link" else None
        drive_link = target if ptype == "drive_link" else None
        
        prod_id = db.add_product(
            category_id=cat_id,
            title=title,
            description=desc,
            price_bdt=price_bdt,
            price_usd=price_usd,
            product_type=ptype,
            channel_id=channel_id,
            drive_link=drive_link,
            photo_file_id=photo_file_id,
            reseller_price_bdt=res_bdt,
            reseller_price_usd=res_usd,
            is_in_stock=1,
            subcategory_id=data.get("subcategory_id")
        )
        
        confirm_text = (
            f"🎉 <b>অভিনন্দন! কোর্সটি সফলভাবে যুক্ত হয়েছে!</b>\n\n"
            f"🆔 প্রোডাক্ট আইডি: <code>#{prod_id}</code>\n"
            f"📌 নাম: <b>{title}</b>\n"
            f"💰 খুচরা মূল্য: <code>৳{price_bdt:.0f} BDT</code> (${price_usd})\n"
            f"💎 রিসেলার রেট: <code>৳{res_bdt:.0f} BDT</code> (${res_usd})\n"
            f"📦 ধরন: <code>{ptype}</code>\n\n"
            f"⚡ <i>আপনি কি এখনই সকল ইউজারকে এই নতুন কোর্সের নোটিফিকেশন পাঠাতে চান?</i>"
        )

    post_add_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text="📢 সবাইকে নোটিফাই করুন (Broadcast)", callback_data=f"prod_bcast_prompt:{prod_id}", emoji_key="broadcast")
        ],
        [
            make_custom_button(text="👁️ ক্যাটালগে দেখুন", callback_data=f"prod:{prod_id}", emoji_key="cart"),
            make_custom_button(text="🔇 স্কিপ (ড্যাশবোর্ড)", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ])
    await message.answer(confirm_text, reply_markup=post_add_kb, parse_mode="HTML")


# --- 11B. SMART MULTILINGUAL NEW PRODUCT BROADCAST ENGINE ---

def format_product_broadcast_post(product: dict, lang: str = "bn") -> tuple:
    """
    Formats the ultra-compact, high-converting promotional post for new products.
    The course/product title is kept 100% UNCHANGED across all languages.
    Returns (rendered_html_text, reply_markup).
    """
    title = product.get("title", "Premium Course")
    price_bdt = int(product.get("price_bdt", 0))
    price_usd = product.get("price_usd", 0.0)
    res_bdt = int(product.get("reseller_price_bdt", 0))
    res_usd = product.get("reseller_price_usd", 0.0)
    prod_id = product.get("id")

    if lang == "en":
        text = (
            "🔥 <b>HOT DROP ALERT!</b> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>{html.escape(title)}</b>\n\n"
            f"💰 <b>Price:</b> <b>${price_usd}</b> <i>(৳{price_bdt} BDT)</i>\n"
            f"💎 <b>Reseller Rate:</b> <code>${res_usd}</code> <i>(Wholesale)</i>\n"
            "⚡ <b>Delivery:</b> 🟢 <code>Instant 24/7 Access</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>Grab your instant access below:</i>"
        )
        buy_text = f"🛍️ Order Now • ${price_usd}"
        cat_text = "📚 Browse Catalog"
    elif lang == "hi":
        text = (
            "🔥 <b>हॉट ड्रॉप अलर्ट!</b> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>{html.escape(title)}</b>\n\n"
            f"💰 <b>कीमत:</b> <b>৳{price_bdt}</b> <i>(${price_usd})</i>\n"
            f"💎 <b>रीसेलर रेट:</b> <code>৳{res_bdt}</code> <i>(थोक डिस्काउंट)</i>\n"
            "⚡ <b>डिलीवरी:</b> 🟢 <code>तुरंत ऑटो एक्सेस</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>स्टॉक खत्म होने से पहले अभी लें:</i>"
        )
        buy_text = f"🛍️ अभी खरीदें • ৳{price_bdt}"
        cat_text = "📚 कैटलॉग देखें"
    else:  # bn default
        text = (
            "🔥 <b>হট ড্রপ অ্যালার্ট! / HOT DROP</b> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>{html.escape(title)}</b>\n\n"
            f"💰 <b>রেগুলার মূল্য:</b> <b>৳{price_bdt}</b> <i>(${price_usd})</i>\n"
            f"💎 <b>রিসেলার রেট:</b> <code>৳{res_bdt}</code> <i>(পাইকারি ছাড়)</i>\n"
            "⚡ <b>ডেলিভারি:</b> 🟢 <code>ইনস্ট্যান্ট অটো অ্যাক্সেস</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>দেরি না করে এখনই সংগ্রহ করুন:</i>"
        )
        buy_text = f"🛍️ এখনই অর্ডার করুন • ৳{price_bdt}"
        cat_text = "📚 বটের মূল ক্যাটালগ"

    text = render_premium_html(text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text=buy_text, callback_data=f"prod:{prod_id}", emoji_key="cart")
        ],
        [
            make_custom_button(text=cat_text, callback_data="nav_courses", emoji_key="courses")
        ]
    ])
    kb = apply_premium_emojis_to_keyboard(kb)
    return text, kb


async def broadcast_new_product_task(bot: Bot, admin_id: int, product_id: int):
    """Background worker sending smart localized cards with rate limiting."""
    prod = db.get_product(product_id)
    if not prod:
        return

    users = db.get_active_users_for_broadcast()
    if not users:
        try:
            await bot.send_message(chat_id=admin_id, text="⚠️ কোনো সক্রিয় ইউজার পাওয়া যায়নি।")
        except Exception:
            pass
        return

    templates = {
        "bn": format_product_broadcast_post(prod, "bn"),
        "en": format_product_broadcast_post(prod, "en"),
        "hi": format_product_broadcast_post(prod, "hi")
    }

    sent_counts = {"bn": 0, "en": 0, "hi": 0}
    blocked_count = 0
    total_sent = 0
    photo_id = prod.get("photo_file_id")

    for u in users:
        uid = u["user_id"]
        ulang = u.get("language", "bn")
        if ulang not in templates:
            ulang = "bn"
        text, kb = templates[ulang]

        try:
            if photo_id:
                try:
                    await bot.send_photo(chat_id=uid, photo=photo_id, caption=text, reply_markup=kb, parse_mode="HTML")
                except Exception:
                    await bot.send_message(chat_id=uid, text=text, reply_markup=kb, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=uid, text=text, reply_markup=kb, parse_mode="HTML")

            sent_counts[ulang] += 1
            total_sent += 1
            await asyncio.sleep(0.04)
        except Exception as e:
            err_str = str(e).lower()
            if "forbidden" in err_str or "blocked" in err_str or "deactivated" in err_str:
                blocked_count += 1
            await asyncio.sleep(0.02)

    report_text = (
        "🎉 <b>নতুন প্রোডাক্ট ব্রডকাস্ট সফলভাবে সম্পন্ন হয়েছে!</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>কোর্স:</b> <b>{html.escape(prod['title'])}</b>\n"
        f"✅ <b>মোট সফল ডেলিভারি:</b> <code>{total_sent} জন ইউজার</code>\n"
        f"• 🇧🇩 বাংলা ভাষায়: <code>{sent_counts['bn']} জন</code>\n"
        f"• 🇬🇧 ইংরেজি ভাষায়: <code>{sent_counts['en']} জন</code>\n"
        f"• 🇮🇳 হিন্দি ভাষায়: <code>{sent_counts['hi']} জন</code>\n"
        f"🚫 <b>বট ব্লকড/নিষ্ক্রিয়:</b> <code>{blocked_count} জন</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>ইউজাররা এখন নোটিফিকেশন পেয়ে ক্যাটালগ ভিজিট করছে!</i>"
    )
    try:
        await bot.send_message(
            chat_id=admin_id,
            text=render_premium_html(report_text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [make_custom_button(text="🏠 অ্যাডমিন ড্যাশবোর্ড", callback_data="admin_main_dashboard", emoji_key="home")]
            ]),
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("prod_bcast_prompt:"))
async def handle_prod_bcast_prompt(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    prod_id = int(call.data.split(":")[1])
    prod = db.get_product(prod_id)
    if not prod:
        await call.message.answer("⚠️ প্রোডাক্ট পাওয়া যায়নি।")
        return

    users = db.get_active_users_for_broadcast()
    total_users = len(users)

    preview_text, _ = format_product_broadcast_post(prod, "bn")

    prompt_card = (
        "📢 <b>নতুন প্রোডাক্ট ব্রডকাস্ট কনফার্মেশন</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 মোট প্রাপক: <b>{total_users} জন ইউজার</b>\n"
        "🌐 মোড: <b>স্মার্ট অটো-ল্যাঙ্গুয়েজ (বাংলা, English ও हिन्दी)</b>\n"
        "✨ ফিচার: <b>অ্যানিমেটেড প্রিমিয়াম ইমোজি ও ডিরেক্ট বাই বাটন</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>ইউজাররা ঠিক এই ফরম্যাটে নিজস্ব ভাষায় প্রিমিয়াম কার্ড পাবে (বাংলা প্রিভিউ):</i>\n\n"
        f"{preview_text}"
    )

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text="🚀 এখনই সবার কাছে পাঠান (Send Now)", callback_data=f"prod_bcast_send:{prod_id}", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="❌ বাতিল করুন (Cancel)", callback_data="admin_main_dashboard", emoji_key="cross")
        ]
    ])

    await call.message.answer(prompt_card, reply_markup=confirm_kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("prod_bcast_send:"))
async def handle_prod_bcast_send(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    await call.answer("🚀 ব্রডকাস্ট ব্যাকগ্রাউন্ডে শুরু হচ্ছে...", show_alert=False)

    await call.message.edit_text(
        "⏳ <b>ব্রডকাস্ট প্রসেসিং শুরু হয়েছে...</b>\n\n"
        "বট ব্যাকগ্রাউন্ডে প্রতিটি ইউজারের নির্ধারিত ভাষায় অ্যানিমেটেড প্রিমিয়াম কার্ড পাঠাচ্ছে। "
        "সম্পন্ন হলে সরাসরি আপনাকে বিস্তারিত রিপোর্ট পাঠানো হবে।",
        parse_mode="HTML"
    )

    asyncio.create_task(broadcast_new_product_task(bot, call.from_user.id, prod_id))


# --- 12. STOCK UPLOAD (Bulk Accounts / Keys) ---

@router.callback_query(F.data == "admin_add_stock")
async def handle_start_add_stock(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    prods = db.get_all_products()
    stock_prods = [p for p in prods if p.get("product_type") == "stock_account"]
    
    if not stock_prods:
        await call.message.answer(
            "⚠️ কোনো 'Ready Stock' টাইপের প্রোডাক্ট পাওয়া যায়নি!\n"
            "আগে 'Add Course / Product' থেকে Ready Stock প্রোডাক্ট যোগ করুন।"
        )
        return
        
    buttons = []
    for p in stock_prods:
        buttons.append([InlineKeyboardButton(text=f"📦 {p['title']}", callback_data=f"sel_stock_p:{p['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")])
    
    await state.set_state(AddStockState.waiting_for_product)
    await call.message.answer(
        "📦 **স্টক আপলোড উইজার্ড**\n\n"
        "কোন প্রোডাক্টে অ্যাকাউন্ট বা কী (Stock Items) আপলোড করতে চান?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(F.data.startswith("sel_stock_p:"), AddStockState.waiting_for_product)
async def handle_select_stock_prod(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    await state.update_data(product_id=prod_id)
    await state.set_state(AddStockState.waiting_for_items)
    await call.answer()
    
    await call.message.answer(
        f"📦 প্রোডাক্ট: **{p['title']}**\n\n"
        "👉 এখন অ্যাকাউন্ট/কী-গুলো প্রতি লাইনে একটি করে পেস্ট করে পাঠান:\n\n"
        "_(উদাহরণ:_\n"
        "`user1@gmail.com:pass123`\n"
        "`user2@gmail.com:pass456`\n"
        "`LICENSE-KEY-XXXXX`_)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(AddStockState.waiting_for_items)
async def handle_save_stock_items(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে স্টক আইটেম টেক্সট আকারে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    raw_text = message.text.strip()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    if not lines:
        await message.answer("❌ কোনো আইটেম পাওয়া যায়নি! আবার পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
        
    data = await state.get_data()
    prod_id = data["product_id"]
    await state.clear()
    
    added_count = db.add_stock_items(prod_id, lines)
    p = db.get_product(prod_id)
    
    await message.answer(
        f"🎉 **সফলভাবে {added_count} টি স্টক আইটেম যুক্ত করা হয়েছে!**\n"
        f"📦 প্রোডাক্ট: {p['title']}\n"
        f"এখন স্বয়ংক্রিয়ভাবে একটি একটি করে ক্রেতাদের কাছে ডেলিভারি হবে।",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats()),
        parse_mode="Markdown"
    )


# --- 13. EDIT PRODUCTS & CATALOG MANAGER ---

@router.message(Command("findprod"))
async def handle_cmd_findprod(message: Message):
    """Shortcut: /findprod <name> to instantly find and edit any product."""
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("⚠️ ব্যবহার নিয়ম: `/findprod <নাম বা কিওয়ার্ড>`\n_(যেমন: `/findprod gemini` বা `/findprod python`)_", parse_mode="Markdown")
        return
    kw = args[1].strip().lower()
    prods = db.get_all_products()
    matched = [p for p in prods if kw in p["title"].lower()]
    if not matched:
        await message.answer(f"❌ কোনো প্রোডাক্ট পাওয়া যায়নি: `{kw}`", parse_mode="Markdown")
        return
        
    buttons = []
    for p in matched[:15]:
        status_dot = "🟢" if p["is_active"] else "🔴"
        has_channel = bool(p.get("channel_id") and str(p.get("channel_id")).strip() not in ["", "None", "0"])
        has_account = bool(p.get("drive_link") and str(p.get("drive_link")).strip() not in ["", "None", "0"])
        is_dual = p.get("product_type") == "dual_access" or (has_channel and has_account)

        if is_dual:
            delivery_badge = "🔥 Dual"
        elif has_channel:
            delivery_badge = "📢 Ch"
        elif has_account:
            delivery_badge = "🔐 Acc"
        else:
            delivery_badge = "⚠️ NoLink"

        raw_title = p['title'].strip()
        short_title = (raw_title[:18] + "..") if len(raw_title) > 20 else raw_title
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_dot} {short_title} | {delivery_badge} (৳{int(p['price_bdt'])})",
                callback_data=f"edit_p_select:{p['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Admin Main Panel", callback_data="admin_main_dashboard")])
    await message.answer(
        f"🔍 <b>'{kw}' এর জন্য {len(matched)} টি ফলাফল পাওয়া গেছে:</b>\n\nএডিট করতে প্রোডাক্ট সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_list_prods")
@router.callback_query(F.data.startswith("prods_page:"))
async def handle_admin_list_prods(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    if not has_admin_permission(call.from_user.id, "can_manage_products"):
        await call.answer("⛔ আপনার কোর্স ও প্রোডাক্ট পরিচালনার অনুমতি (Permission) নেই!", show_alert=True)
        return
    await call.answer()
    
    page = 0
    if call.data.startswith("prods_page:"):
        page = int(call.data.split(":")[1])

    prods = db.get_all_products()
    if not prods:
        await call.message.answer("⚠️ ক্যাটালগে বর্তমানে কোনো প্রোডাক্ট নেই।")
        return
        
    PAGE_SIZE = 10
    total_pages = (len(prods) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, total_pages - 1))
    start_idx = page * PAGE_SIZE
    page_items = prods[start_idx:start_idx + PAGE_SIZE]
    
    buttons = []
    for p in page_items:
        status_dot = "🟢" if p["is_active"] else "🔴"
        has_channel = bool(p.get("channel_id") and str(p.get("channel_id")).strip() not in ["", "None", "0"])
        has_account = bool(p.get("drive_link") and str(p.get("drive_link")).strip() not in ["", "None", "0"])
        is_dual = p.get("product_type") == "dual_access" or (has_channel and has_account)

        if is_dual:
            delivery_badge = "🔥 Dual"
        elif has_channel:
            delivery_badge = "📢 Ch"
        elif has_account:
            delivery_badge = "🔐 Acc"
        else:
            delivery_badge = "⚠️ NoLink"

        raw_title = p['title'].strip()
        short_title = (raw_title[:18] + "..") if len(raw_title) > 20 else raw_title
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_dot} {short_title} | {delivery_badge} (৳{int(p['price_bdt'])})",
                callback_data=f"edit_p_select:{p['id']}"
            )
        ])
    
    # Pagination row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"prods_page:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"prods_page:{page + 1}"))
    buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="➕ Add New Product", callback_data="admin_add_prod"),
        InlineKeyboardButton(text="🔙 Back to Admin", callback_data="admin_main_dashboard")
    ])
    
    await call.message.edit_text(
        f"📋 <b>কোর্স ও প্রোডাক্ট এডিটর (মোট {len(prods)} টি প্রোডাক্ট)</b>\n\n"
        "💡 <i>বাটন নির্দেশিকা:</i>\n"
        "• <code>🔥 Dual</code> = ভিআইপি চ্যানেল + অ্যাকাউন্ট ২টিই সংযুক্ত\n"
        "• <code>📢 Ch</code> = শুধু টেলিগ্রাম ভিআইপি চ্যানেল সংযুক্ত\n"
        "• <code>🔐 Acc</code> = শুধু অ্যাকাউন্ট ক্রেডেনশিয়াল / ড্রাইভ লিংক সংযুক্ত\n"
        "• <code>⚠️ NoLink</code> = কোনো ডেলিভারি লিংক সংযুক্ত নেই!\n\n"
        "👇 এডিট, চ্যানেল টেস্ট বা অ্যাক্সেস দেখতে কোর্স সিলেক্ট করুন:\n"
        "<i>(শর্টকাট: সরাসরি খুঁজতে <code>/findprod &lt;নাম&gt;</code> লিখুন)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("toggle_p_stock:"))
async def handle_toggle_p_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    new_state = db.toggle_product_stock(prod_id)
    alert_txt = "✅ প্রোডাক্টটি এখন 'ইন স্টক' (In Stock) সেট করা হয়েছে!" if new_state else "⚠️ প্রোডাক্টটি এখন 'আউট অব স্টক' (Out of Stock) করা হয়েছে!"
    await call.answer(alert_txt, show_alert=True)
    await handle_edit_p_select(call, target_prod_id=prod_id)

@router.callback_query(F.data.startswith("edit_p_select:"))
async def handle_edit_p_select(call: CallbackQuery, target_prod_id: int = None):
    prod_id = target_prod_id if target_prod_id is not None else int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    
    cat = db.get_category(p["category_id"]) if p.get("category_id") else None
    cat_name = f"{cat.get('icon', '📁')} {cat['name']}" if cat else "আনক্যাটাগোরাইজড 📁"
    stock_count = db.get_stock_count(prod_id)
    
    status_str = "🟢 সক্রিয় (Active)" if p["is_active"] else "🔴 নিষ্ক্রিয় (Inactive)"
    stock_active = bool(p.get("is_in_stock", 1) if p.get("is_in_stock") is not None else 1)
    stock_status_str = "🟢 ইন স্টক (In Stock)" if stock_active else "🔴 আউট অব স্টক (Out of Stock)"
    
    # VIP Channel status
    ch_id = p.get("channel_id")
    has_ch = bool(ch_id and str(ch_id).strip() not in ["", "None", "0"])
    ch_title = p.get("channel_title")
    if has_ch:
        ch_display = f"🟢 <code>{ch_id}</code>"
        if ch_title:
            ch_display += f" (<i>{ch_title}</i>)"
    else:
        ch_display = "⚪ <i>সংযুক্ত নেই ❌</i>"

    # Account / Drive status
    acc_data = p.get("drive_link")
    has_acc = bool(acc_data and str(acc_data).strip() not in ["", "None", "0"])
    if has_acc:
        preview_acc = (acc_data[:32] + "...") if len(acc_data) > 32 else acc_data
        acc_display = f"🟢 <code>{preview_acc}</code>"
    else:
        acc_display = "⚪ <i>সংযুক্ত নেই ❌</i>"
    
    sales_info = p.get("sales_page_url") or "দেওয়া নেই ❌"
    
    tier_info = "বন্ধ (Single Price)"
    if (p.get("price_channel_bdt") or 0) > 0 and (p.get("price_account_bdt") or 0) > 0:
        tier_info = f"চালু ✅ (📢 VIP: ৳{int(p['price_channel_bdt'])} | 🔐 Account: ৳{int(p['price_account_bdt'])})"
    
    type_map = {
        "channel_link": "📢 প্রাইভেট চ্যানেল লিংক",
        "dual_access": "🔥 ডুয়েল প্যাকেজ (Channel + Account)",
        "drive_link": "💾 গুগল ড্রাইভ লিংক",
        "stock_account": "🔐 স্টক অ্যাকাউন্ট / লাইসেন্স কি",
        "manual": "📩 ম্যানুয়াল ডেলিভারি"
    }
    type_str = type_map.get(p.get("product_type"), p.get("product_type"))

    text = (
        f"🛠️ <b>কোর্স ও ডেলিভারি এডিটর: {p['title']}</b>\n\n"
        f"📋 <b>সাধারণ তথ্য:</b>\n"
        f"• ক্যাটাগরি: <b>{cat_name}</b>\n"
        f"• স্ট্যাটাস: {status_str} | স্টক: <b>{stock_status_str}</b> ({stock_count} টি)\n"
        f"• খুচরা রেট: <code>৳{p['price_bdt']} BDT</code> (${p['price_usd']})\n"
        f"• রিসেলার রেট: <code>৳{p['reseller_price_bdt']} BDT</code> (${p['reseller_price_usd']})\n\n"
        f"📡 <b>ডেলিভারি ও অ্যাক্সেস স্ট্যাটাস:</b>\n"
        f"• প্যাকেজ মোড: <b>{type_str}</b>\n"
        f"• 📢 <b>VIP চ্যানেল:</b> {ch_display}\n"
        f"• 🔐 <b>অ্যাকাউন্ট / ড্রাইভ:</b> {acc_display}\n"
        f"• ডুয়েল প্রাইসিং: <code>{tier_info}</code>\n"
        f"• সেলস পেজ: <code>{sales_info}</code>\n"
        f"• ব্যানার ফটো: {'আছে ✅' if p.get('photo_file_id') else 'নেই ❌'}\n\n"
        "👇 <b>কী পরিবর্তন করতে চান অথবা টেস্ট করতে চান বেছে নিন:</b>"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_product_edit_options_kb(
            prod_id,
            bool(p["is_active"]),
            has_photo=bool(p.get("photo_file_id")),
            stock_count=stock_count,
            is_in_stock=stock_active
        ),
        parse_mode="HTML"
    )

# --- Category Change for Product ---
@router.callback_query(F.data.startswith("edit_p_category:"))
async def handle_edit_p_category(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    categories = db.get_all_categories()
    buttons = []
    for c in categories:
        buttons.append([
            InlineKeyboardButton(text=f"{c.get('icon', '📁')} {c['name']}", callback_data=f"p_set_cat:{prod_id}:{c['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")])
    await call.answer()
    await call.message.edit_text(
        "📁 **এই প্রোডাক্টটি কোন ক্যাটাগরিতে সরাতে চান?**\n\nনিচের তালিকা থেকে নতুন ক্যাটাগরি সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("p_set_cat:"))
async def handle_p_set_category_save(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    prod_id = int(parts[1])
    cat_id = int(parts[2])
    db.update_product_category(prod_id, cat_id)
    cat = db.get_category(cat_id)
    cat_title = cat['name'] if cat else "নতুন ক্যাটাগরি"
    await call.answer(f"ক্যাটাগরি পরিবর্তিত: {cat_title}!", show_alert=True)
    await handle_edit_p_select(call, target_prod_id=prod_id)

# --- Type Change for Product ---
@router.callback_query(F.data.startswith("edit_p_type:"))
async def handle_edit_p_type(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    types = [
        ("📢 প্রাইভেট চ্যানেল লিংক", "channel_link"),
        ("💾 গুগল ড্রাইভ লিংক", "drive_link"),
        ("🔐 স্টক অ্যাকাউন্ট / লাইসেন্স কি", "stock_account"),
        ("📩 ম্যানুয়াল ডেলিভারি", "manual")
    ]
    buttons = []
    for label, t_val in types:
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"p_set_type:{prod_id}:{t_val}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")])
    await call.answer()
    await call.message.edit_text(
        "🔄 **এই প্রোডাক্টের নতুন ডেলিভারি ধরন বেছে নিন:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("p_set_type:"))
async def handle_p_set_type_save(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    prod_id = int(parts[1])
    t_val = parts[2]
    db.update_product_type(prod_id, t_val)
    await call.answer("ডেলিভারি ধরন পরিবর্তিত হয়েছে!", show_alert=True)
    await handle_edit_p_select(call, target_prod_id=prod_id)

# --- Remove Banner Photo ---
@router.callback_query(F.data.startswith("edit_p_remphoto:"))
async def handle_edit_p_remphoto(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    db.remove_product_photo(prod_id)
    await call.answer("ব্যানার ছবি সফলভাবে মুছে ফেলা হয়েছে!", show_alert=True)
    await handle_edit_p_select(call, target_prod_id=prod_id)

# --- Stock Manager for Product ---
@router.callback_query(F.data.startswith("edit_p_stock:"))
async def handle_edit_p_stock_hub(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    stock_cnt = db.get_stock_count(prod_id)
    text = (
        f"📦 **স্টক ম্যানেজার: {p['title']}**\n\n"
        f"• বর্তমান অবশিষ্ঠ স্টক: `{stock_cnt} টি`\n\n"
        "👇 নতুন স্টক যোগ করতে, তালিকা দেখতে বা স্টক ক্লিয়ার করতে নিচের বাটন ব্যবহার করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_stock_manage_kb(prod_id, stock_cnt))

@router.callback_query(F.data.startswith("admin_prod_add_stock:"))
async def handle_admin_prod_add_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    await state.update_data(stock_prod_id=prod_id)
    await state.set_state(AddStockState.waiting_for_items)
    await call.answer()
    await call.message.answer(
        f"📦 **{p['title']} এর জন্য স্টক আইটেম যোগ করুন:**\n\n"
        "প্রতি লাইনে ১টি করে অ্যাকাউন্ট / কি / লিংক লিখে একসাথে সেন্ড করুন:\n\n"
        "_(উদাহরণ:_\n"
        "`user1@gmail.com:pass123`\n"
        "`user2@gmail.com:pass456`\n"
        "_বট প্রতিটি লাইন আলাদা করে স্টকে সাজিয়ে নিবে)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("admin_view_stock:"))
async def handle_admin_view_stock_items(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    items = db.get_product_stock_items(prod_id, limit=20)
    total_cnt = db.get_stock_count(prod_id)
    await call.answer()
    
    if not items:
        await call.message.answer(f"⚠️ **{p['title']}** এর কোনো অব্যবহৃত স্টক নেই। নতুন স্টক আপলোড করুন।")
        return
        
    text = f"📋 **{p['title']} এর স্টক তালিকা (মোট {total_cnt} টির মধ্যে প্রথম {len(items)} টি):**\n\n"
    for idx, it in enumerate(items, 1):
        text += f"`{idx}.` `{it['content']}`\n"
        
    buttons = [
        [
            InlineKeyboardButton(text="➕ Upload More Stock", callback_data=f"admin_prod_add_stock:{prod_id}"),
            InlineKeyboardButton(text="🗑️ Clear Stock", callback_data=f"admin_clear_stock_ask:{prod_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")
        ]
    ]
    await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("admin_clear_stock_ask:"))
async def handle_admin_clear_stock_prompt(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    stock_cnt = db.get_stock_count(prod_id)
    await call.answer()
    buttons = [
        [
            InlineKeyboardButton(text="⚠️ হ্যাঁ, সব অব্যবহৃত স্টক মুছে ফেলুন", callback_data=f"admin_clear_stock_yes:{prod_id}")
        ],
        [
            InlineKeyboardButton(text="❌ বাতিল", callback_data=f"edit_p_stock:{prod_id}")
        ]
    ]
    await call.message.edit_text(
        f"⚠️ **সতর্কতা!** আপনি কি নিশ্চিত যে **{p['title']}** এর বিদ্যমান `{stock_cnt} টি` অব্যবহৃত স্টক ডাটাবেস থেকে পার্মানেন্ট মুছে ফেলতে চান?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("admin_clear_stock_yes:"))
async def handle_admin_clear_stock_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    cleared = db.clear_product_stock(prod_id)
    await call.answer(f"সফলভাবে {cleared} টি স্টক আইটেম মুছে ফেলা হয়েছে!", show_alert=True)
    await handle_edit_p_select(call, target_prod_id=prod_id)

@router.callback_query(F.data.startswith("edit_p_title:"))
async def handle_edit_p_title_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_title)
    await call.answer()
    await call.message.answer("✏️ **কোর্সের নতুন নাম (Title) লিখে সেন্ড করুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(EditProductState.waiting_for_new_title)
async def handle_edit_p_title_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে টেক্সট আকারে লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    new_title = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    if not p:
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি বা মুছে ফেলা হয়েছে।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
    db.update_product(
        product_id=prod_id,
        title=new_title,
        description=p["description"],
        price_bdt=p["price_bdt"],
        price_usd=p["price_usd"],
        reseller_price_bdt=p["reseller_price_bdt"],
        reseller_price_usd=p["reseller_price_usd"],
        is_active=p["is_active"]
    )
    await message.answer(f"✅ **কোর্সের নাম পরিবর্তিত হয়েছে!**\nনতুন নাম: **{new_title}**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_desc:"))
async def handle_edit_p_desc_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_desc)
    await call.answer()
    await call.message.answer("📝 **কোর্সের নতুন বিবরণ (Description) লিখে সেন্ড করুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(EditProductState.waiting_for_new_desc)
async def handle_edit_p_desc_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে টেক্সট আকারে লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    new_desc = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    if not p:
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি বা মুছে ফেলা হয়েছে।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
    db.update_product(
        product_id=prod_id,
        title=p["title"],
        description=new_desc,
        price_bdt=p["price_bdt"],
        price_usd=p["price_usd"],
        reseller_price_bdt=p["reseller_price_bdt"],
        reseller_price_usd=p["reseller_price_usd"],
        is_active=p["is_active"]
    )
    await message.answer("✅ **কোর্সের বিবরণ সফলভাবে আপডেট হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_price:"))
async def handle_edit_p_price_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_price)
    await call.answer()
    await call.message.answer("💰 **নতুন সাধারণ খুচরা বিক্রয়মূল্য BDT (টাকায়) লিখুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(EditProductState.waiting_for_new_price)
async def handle_edit_p_price_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        new_price_bdt = float(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    if not p:
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি বা মুছে ফেলা হয়েছে।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
    new_usd = round(new_price_bdt / get_live_usd_rate(), 2)
    db.update_product(
        product_id=prod_id,
        title=p["title"],
        description=p["description"],
        price_bdt=new_price_bdt,
        price_usd=new_usd,
        reseller_price_bdt=p["reseller_price_bdt"],
        reseller_price_usd=p["reseller_price_usd"],
        is_active=p["is_active"]
    )
    await message.answer(f"✅ **মূল্য আপডেট হয়েছে!** নতুন খুচরা রেট: `৳{new_price_bdt} BDT` (${new_usd})", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_resprice:"))
async def handle_edit_p_resprice_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_resprice)
    await call.answer()
    await call.message.answer("💎 **রিসেলারদের জন্য নতুন পাইকারি রেট BDT (টাকায়) লিখুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(EditProductState.waiting_for_new_resprice)
async def handle_edit_p_resprice_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        new_res_bdt = float(message.text.strip())
    except ValueError:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    if not p:
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি বা মুছে ফেলা হয়েছে।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
    new_res_usd = round(new_res_bdt / get_live_usd_rate(), 2)
    db.update_product(
        product_id=prod_id,
        title=p["title"],
        description=p["description"],
        price_bdt=p["price_bdt"],
        price_usd=p["price_usd"],
        reseller_price_bdt=new_res_bdt,
        reseller_price_usd=new_res_usd,
        is_active=p["is_active"]
    )
    await message.answer(f"✅ **রিসেলার পাইকারি রেট আপডেট হয়েছে!** নতুন রেট: `৳{new_res_bdt} BDT` (${new_res_usd})", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_toggle:"))
async def handle_edit_p_toggle(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    new_status = 0 if p["is_active"] else 1
    db.update_product(
        product_id=prod_id,
        title=p["title"],
        description=p["description"],
        price_bdt=p["price_bdt"],
        price_usd=p["price_usd"],
        reseller_price_bdt=p["reseller_price_bdt"],
        reseller_price_usd=p["reseller_price_usd"],
        is_active=new_status
    )
    status_str = "🟢 সক্রিয় (Active)" if new_status else "🔴 নিষ্ক্রিয় (Inactive)"
    await call.answer(f"স্ট্যাটাস পরিবর্তিত: {status_str}", show_alert=True)
    await handle_edit_p_select(call)

@router.callback_query(F.data.startswith("edit_p_target:"))
async def handle_edit_p_target_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_target)
    await call.answer()
    await call.message.answer(
        "🔗 **কোর্সের নতুন টেলিগ্রাম চ্যানেল ID/Username অথবা Google Drive লিংক লিখে সেন্ড করুন:**\n\n"
        "_(যেমন: @vip_channel অথবা https://drive.google.com/...)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(EditProductState.waiting_for_new_target)
async def handle_edit_p_target_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে টেক্সট আকারে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    new_target = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    ptype = p.get("product_type", "channel_link")
    if ptype == "channel_link":
        db.update_product_target(prod_id, channel_id=new_target)
    else:
        db.update_product_target(prod_id, drive_link=new_target)
        
    await message.answer("✅ **ডেলিভারি টার্গেট লিংক/চ্যানেল সফলভাবে আপডেট হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("test_p_channel:"))
async def handle_test_p_channel(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    ch_id = p.get("channel_id")
    if not ch_id or str(ch_id).strip() in ["", "None", "0"]:
        await call.answer("⚠️ এই প্রোডাক্টে কোনো টেলিগ্রাম চ্যানেল সেট করা নেই! আগে '📢 চ্যানেল সেট/পরিবর্তন' করুন।", show_alert=True)
        return
        
    await call.answer("🔄 চ্যানেল ভেরিফিকেশন টেস্ট চলছে...")
    res = await verify_telegram_channel_access(bot, str(ch_id).strip())
    
    if res["success"]:
        db.update_product_channel(prod_id, channel_id=str(ch_id).strip(), channel_title=res["title"], channel_verified=1)
        test_card = (
            f"🧪 <b>টেলিগ্রাম চ্যানেল টেস্ট রিপোর্ট: সফল! ✅</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>কোর্স:</b> {p['title']}\n"
            f"📢 <b>চ্যানেল নাম:</b> <b>{res['title']}</b>\n"
            f"🆔 <b>চ্যানেল আইডি:</b> <code>{res['channel_id']}</code>\n"
            f"🟢 <b>বট অ্যাডমিন পারমিশন:</b> সক্রিয় (OK)\n\n"
            f"🔗 <b>১-টাইম টেস্ট ইনভাইট লিংক:</b>\n"
            f"{res['test_link']}\n\n"
            f"<i>(নোট: কাস্টমার পেমেন্ট করার পর স্বয়ংক্রিয়ভাবে ঠিক এই ধরনের সিঙ্গেল-ইউজ ইনভাইট লিংক পাবে।)</i>"
        )
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await call.message.answer(test_card, reply_markup=back_kb, parse_mode="HTML")
    else:
        db.update_product_channel(prod_id, channel_id=str(ch_id).strip(), channel_title=res.get("title"), channel_verified=0)
        bot_info = await bot.get_me()
        bot_uname = bot_info.username or "bot"
        err_card = (
            f"⚠️ <b>টেলিগ্রাম চ্যানেল টেস্ট রিপোর্ট: ব্যর্থ! ❌</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>কোর্স:</b> {p['title']}\n"
            f"🆔 <b>টার্গেট:</b> <code>{ch_id}</code>\n"
            f"📌 <b>সমস্যা:</b> {res['message']}\n\n"
            f"👉 <b>সমাধান:</b>\n"
            f"১. চ্যানেলে গিয়ে <code>@{bot_uname}</code> কে Administrator বানান।\n"
            f"২. <b>'Invite Users via Link'</b> পারমিশন চালু করুন।\n"
            f"৩. এরপর আবার এখানে এসে টেস্ট বাটনে চাপ দিন।"
        )
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 আবার টেস্ট করুন", callback_data=f"test_p_channel:{prod_id}")],
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await call.message.answer(err_card, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("view_p_accdata:"))
async def handle_view_p_accdata(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
        
    acc_data = p.get("drive_link")
    stock_count = db.get_stock_count(prod_id)
    
    if not acc_data and stock_count == 0:
        await call.answer("⚠️ এই প্রোডাক্টে কোনো অ্যাকাউন্ট ডাটা বা ড্রাইভ লিংক সংরক্ষিত নেই!", show_alert=True)
        return
        
    await call.answer()
    card = (
        f"🔐 <b>ডেলিভারি অ্যাকাউন্ট / ড্রাইভ ডাটা:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>কোর্স:</b> {p['title']}\n"
        f"📦 <b>মোট স্টক আইটেম:</b> {stock_count} টি\n\n"
        f"📝 <b>মূল ডেলিভারি টেমপ্লেট / লিংক:</b>\n"
        f"<code>{acc_data or 'দেওয়া নেই'}</code>\n\n"
        f"<i>(কাস্টমার পার্সোনাল অ্যাকাউন্ট / ড্রাইভ প্যাকেজ কিনলে এই তথ্য স্বয়ংক্রিয়ভাবে পাবে।)</i>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ডাটা পরিবর্তন করুন", callback_data=f"edit_p_accdata:{prod_id}")],
        [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
    ])
    await call.message.answer(card, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_p_channel:"))
async def handle_edit_p_channel_start(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_channel)
    await call.answer()
    
    bot_info = await bot.get_me()
    bot_uname = bot_info.username or "bot"
    
    current_ch = p.get("channel_id") or "কোনো চ্যানেল সংযুক্ত নেই"
    await call.message.answer(
        f"📢 <b>VIP টেলিগ্রাম চ্যানেল সেট / পরিবর্তন:</b>\n\n"
        f"🏷️ কোর্স: <b>{p['title']}</b>\n"
        f"📍 বর্তমান চ্যানেল: <code>{current_ch}</code>\n\n"
        f"👉 নতুন চ্যানেলের <b>@Username</b> অথবা <b>Channel ID</b> (যেমন: <code>-100...</code>) লিখে পাঠান।\n"
        f"<i>(চ্যানেল পুরোপুরি ডিসকানেক্ট / রিমুভ করতে <code>remove</code> লিখে পাঠান)</i>\n\n"
        f"⚠️ <b>মনে রাখবেন:</b> <code>@{bot_uname}</code> কে চ্যানেলে Administrator বানিয়ে 'Invite Users via Link' পারমিশন থাকতে হবে।",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(EditProductState.waiting_for_new_channel)
async def handle_edit_p_channel_save(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে চ্যানেলের ইউজারনেম বা আইডি টেক্সট আকারে লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    raw_input = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    
    p = db.get_product(prod_id)
    if not p:
        await state.clear()
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
        
    if raw_input.lower() in ["remove", "none", "0"]:
        db.update_product_channel(prod_id, channel_id=None, channel_title=None, channel_verified=0)
        await state.clear()
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await message.answer(
            f"✅ <b>'{p['title']}' থেকে VIP চ্যানেল সংযোগ সফলভাবে মুছে ফেলা হয়েছে!</b>",
            reply_markup=back_kb,
            parse_mode="HTML"
        )
        return
        
    await message.answer("🔍 টেলিগ্রাম সার্ভারে চ্যানেল ও অ্যাডমিন পারমিশন যাচাই করা হচ্ছে...")
    res = await verify_telegram_channel_access(bot, raw_input)
    
    if res["success"]:
        db.update_product_channel(prod_id, channel_id=raw_input, channel_title=res["title"], channel_verified=1)
        await state.clear()
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await message.answer(
            f"🎉 <b>আলহামদুলিল্লাহ! চ্যানেল সফলভাবে যুক্ত ও ভেরিফাই হয়েছে!</b>\n\n"
            f"🏷️ কোর্স: <b>{p['title']}</b>\n"
            f"📢 চ্যানেল নাম: <b>{res['title']}</b>\n"
            f"🆔 চ্যানেল আইডি: <code>{res['channel_id']}</code>\n"
            f"🟢 <b>বট অ্যাডমিন স্ট্যাটাস:</b> সক্রিয় (Single-use invite link ready)\n\n"
            f"🧪 <b>টেস্ট ইনভাইট লিংক:</b>\n{res['test_link']}",
            reply_markup=back_kb,
            parse_mode="HTML"
        )
    else:
        db.update_product_channel(prod_id, channel_id=raw_input, channel_title=res.get("title"), channel_verified=0)
        await state.clear()
        bot_info = await bot.get_me()
        bot_uname = bot_info.username or "bot"
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 আবার টেস্ট করুন", callback_data=f"test_p_channel:{prod_id}")],
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await message.answer(
            f"⚠️ <b>চ্যানেল সেভ হয়েছে, কিন্তু বটের অ্যাডমিন অ্যাক্সেস সক্রিয় হয়নি!</b>\n\n"
            f"🏷️ কোর্স: <b>{p['title']}</b>\n"
            f"🆔 টার্গেট: <code>{raw_input}</code>\n"
            f"📌 সমস্যা: {res['message']}\n\n"
            f"👉 <b>কী করবেন:</b>\n"
            f"১. চ্যানেলে গিয়ে <code>@{bot_uname}</code> কে Administrator বানান।\n"
            f"২. 'Invite Users via Link' পারমিশন চালু করুন।\n"
            f"৩. এরপর নিচের 'আবার টেস্ট করুন' বাটনে চাপ দিন।",
            reply_markup=back_kb,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("edit_p_accdata:"))
async def handle_edit_p_accdata_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_accdata)
    await call.answer()
    
    current_acc = p.get("drive_link") or "কোনো ডাটা নেই"
    await call.message.answer(
        f"🔐 <b>অ্যাকাউন্ট ডাটা / ড্রাইভ লিংক সেট / পরিবর্তন:</b>\n\n"
        f"🏷️ কোর্স: <b>{p['title']}</b>\n"
        f"📍 বর্তমান ডাটা:\n<code>{current_acc}</code>\n\n"
        f"👉 নতুন অ্যাকাউন্ট ক্রেডেনশিয়াল (ইমেইল:পাসওয়ার্ড), গুগল ড্রাইভ লিংক অথবা লগইন গাইড লিখে সেন্ড করুন।\n"
        f"<i>(ডাটা মুছে ফেলতে চাইলে <code>remove</code> লিখে পাঠান)</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )

@router.message(EditProductState.waiting_for_new_accdata)
async def handle_edit_p_accdata_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে টেক্সট আকারে লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    raw_input = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    p = db.get_product(prod_id)
    if not p:
        await message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
        
    if raw_input.lower() in ["remove", "none", "0"]:
        db.update_product_drive_link(prod_id, None)
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
        ])
        await message.answer(
            f"✅ <b>'{p['title']}' এর অ্যাকাউন্ট/ড্রাইভ ডাটা সফলভাবে মুছে ফেলা হয়েছে!</b>",
            reply_markup=back_kb,
            parse_mode="HTML"
        )
        return
        
    db.update_product_drive_link(prod_id, raw_input)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"edit_p_select:{prod_id}")]
    ])
    await message.answer(
        f"✅ <b>'{p['title']}' এর অ্যাকাউন্ট ডাটা / ড্রাইভ লিংক সফলভাবে আপডেট করা হয়েছে!</b>\n\n"
        f"📝 <b>নতুন ডাটা:</b>\n<code>{raw_input}</code>",
        reply_markup=back_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_p_photo:"))
async def handle_edit_p_photo_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_photo)
    await call.answer()
    await call.message.answer(
        "🖼️ **নতুন ব্যানার ফটোটি সেন্ড করুন (অথবা ছবি সরাতে 'remove' লিখুন):**",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(EditProductState.waiting_for_new_photo)
async def handle_edit_p_photo_save(message: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == "remove":
        photo_id = None
    else:
        await message.answer("❌ কোনো ফটো পাওয়া যায়নি। পরিবর্তন ছাড়াই রাখা হয়েছে।", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))
        return
        
    db.update_product_photo(prod_id, photo_id)
    await message.answer("✅ **কোর্সের ব্যানার ছবি সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_salespage:"))
async def handle_edit_p_salespage_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_sales_page)
    await call.answer()
    await call.message.answer(
        "🌐 **কোর্স সেলস পেজ বা কারিকুলাম লিঙ্ক লিখুন:**\n"
        "_(যেমন: `https://example.com/course` অথবা লিঙ্ক মুছে ফেলতে `remove` লিখে পাঠান)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditProductState.waiting_for_new_sales_page)
async def handle_edit_p_salespage_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে লিঙ্কটি টেক্সট আকারে দিন:", reply_markup=get_cancel_fsm_kb())
        return
    url = message.text.strip()
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    await state.clear()
    
    if url.lower() in ["remove", "none", "0"]:
        url = None
    elif not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    db.update_product_sales_page(prod_id, url)
    await message.answer("✅ **কোর্সের সেলস পেজ লিঙ্ক সফলভাবে আপডেট করা হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("edit_p_tiers:"))
async def handle_edit_p_tiers_start(call: CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split(":")[1])
    await state.update_data(edit_prod_id=prod_id)
    await state.set_state(EditProductState.waiting_for_new_ch_price)
    await call.answer()
    await call.message.answer(
        "📢 **১. VIP Channel Access এর খুচরা মূল্য (BDT) কত করতে চান?**\n"
        "_(যেমন: 350 — ডুয়েল প্রাইসিং বন্ধ রাখতে 0 লিখুন)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditProductState.waiting_for_new_ch_price)
async def handle_edit_p_ch_price_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        ch_bdt = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: 350):", reply_markup=get_cancel_fsm_kb())
        return
        
    await state.update_data(new_ch_bdt=ch_bdt)
    await state.set_state(EditProductState.waiting_for_new_acc_price)
    await message.answer(
        "🔐 **২. Personal Account / Drive Access এর খুচরা মূল্য (BDT) কত করতে চান?**\n"
        "_(যেমন: 550 — ডুয়েল প্রাইসিং বন্ধ রাখতে 0 লিখুন)_",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="Markdown"
    )

@router.message(EditProductState.waiting_for_new_acc_price)
async def handle_edit_p_acc_price_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ শুধুমাত্র সংখ্যা লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    try:
        acc_bdt = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: 550):", reply_markup=get_cancel_fsm_kb())
        return
        
    data = await state.get_data()
    prod_id = data["edit_prod_id"]
    ch_bdt = data["new_ch_bdt"]
    await state.clear()
    
    live_rate = get_live_usd_rate()
    ch_usd = round(ch_bdt / live_rate, 2)
    acc_usd = round(acc_bdt / live_rate, 2)
    
    db.update_product_tier_pricing(prod_id, ch_bdt, ch_usd, acc_bdt, acc_usd)
    await message.answer(
        f"✅ **ডুয়েল অ্যাক্সেস প্রাইসিং সফলভাবে আপডেট করা হয়েছে!**\n\n"
        f"• 📢 VIP Channel Access: `৳{int(ch_bdt)} BDT` (${ch_usd} USD)\n"
        f"• 🔐 Personal Account Access: `৳{int(acc_bdt)} BDT` (${acc_usd} USD)\n\n"
        f"_(রিসেলারদের জন্য স্বয়ংক্রিয়ভাবে ৩০% পাইকারি ছাড় নির্ধারিত হয়েছে)_",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats()),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("edit_p_delete:"))
async def handle_edit_p_delete_prompt(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    p = db.get_product(prod_id)
    if not p:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    
    text = (
        f"⚠️ **সতর্কতা! আপনি কি নিশ্চিতভাবে '{p['title']}' ডিলিট করতে চান?**\n\n"
        "ডিলিট করলে এই কোর্স এবং এর স্টক ডাটাবেস থেকে মুছে ফেলা হবে।"
    )
    del_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ হ্যাঁ, নিশ্চিত ডিলিট করুন", callback_data=f"confirm_p_del:{prod_id}")],
        [InlineKeyboardButton(text="❌ না, বাতিল", callback_data=f"edit_p_select:{prod_id}")]
    ])
    await call.message.edit_text(text, reply_markup=del_kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("confirm_p_del:"))
async def handle_confirm_p_del(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    db.delete_product_permanent(prod_id)
    await call.answer("প্রোডাক্ট সফলভাবে মুছে ফেলা হয়েছে!", show_alert=True)
    await call.message.edit_text("🗑️ **প্রোডাক্ট সফলভাবে পার্মানেন্টলি ডিলিট করা হয়েছে!**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))


# --- 14. CATEGORIES MANAGEMENT ---

@router.callback_query(F.data == "admin_cats_menu")
async def handle_admin_cats_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    cats = db.get_categories_by_type("course") + db.get_categories_by_type("digital")
    await call.message.edit_text(
        "📁 **ক্যাটাগরি ম্যানেজমেন্ট সেন্টার**\n\n"
        "কোর্স বা সার্ভিসের ক্যাটাগরি তৈরি, রিনেম ও সাজাতে নিচের তালিকা থেকে সিলেক্ট করুন:",
        reply_markup=get_admin_categories_kb(cats),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "cat_add_new")
async def handle_cat_add_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.answer()
    await state.set_state(CategoryAddState.waiting_for_name)
    await call.message.answer("📁 **নতুন ক্যাটাগরির নাম লিখুন:**\n_(যেমন: প্রফেশনাল স্পোকেন ইংলিশ)_", reply_markup=get_cancel_fsm_kb())

@router.message(CategoryAddState.waiting_for_name)
async def handle_cat_name_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে ক্যাটাগরির নাম লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(CategoryAddState.waiting_for_icon)
    await message.answer("🎨 **ক্যাটাগরির একটি ইমোজি / আইকন সেন্ড করুন:**\n_(যেমন: 🎬, 💼, 🤖)_", reply_markup=get_cancel_fsm_kb())

@router.message(CategoryAddState.waiting_for_icon)
async def handle_cat_icon_save(message: Message, state: FSMContext):
    icon = message.text.strip() if message.text else "📁"
    await state.update_data(icon=icon)
    await state.set_state(CategoryAddState.waiting_for_type)
    
    type_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 কোর্স ক্যাটাগরি (Courses)", callback_data="cat_type_sel:course")],
        [InlineKeyboardButton(text="⚡ ডিজিটাল সার্ভিস ক্যাটাগরি (Tools)", callback_data="cat_type_sel:digital")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_fsm")]
    ])
    await message.answer("📂 এটি কোন ধরনের ক্যাটাগরি?", reply_markup=type_kb)

@router.callback_query(F.data.startswith("cat_type_sel:"), CategoryAddState.waiting_for_type)
async def handle_cat_type_save(call: CallbackQuery, state: FSMContext):
    ctype = call.data.split(":")[1]
    data = await state.get_data()
    await state.clear()
    await call.answer()
    
    cid = db.add_category(name=data["name"], icon=data["icon"], cat_type=ctype)
    await call.message.answer(
        f"✅ **নতুন ক্যাটাগরি যুক্ত হয়েছে!**\n\n"
        f"আইডি: `#{cid}`\n"
        f"নাম: {data['icon']} {data['name']}\n"
        f"ধরন: `{ctype}`",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats())
    )

@router.callback_query(F.data.startswith("edit_cat_select:"))
async def handle_edit_cat_select(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    c = db.get_category(cat_id)
    if not c:
        await call.answer("ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    type_badge = "⚡ ডিজিটাল সার্ভিস / অ্যাকাউন্ট" if c.get("type") == "digital" else "🎓 কোর্স ক্যাটাগরি"
    text = (
        f"📁 **ক্যাটাগরি এডিটর: {c['icon']} {c['name']}**\n\n"
        f"• টাইপ: `{c['type']}` ({type_badge})\n"
        f"• অর্ডার পজিশন: `{c.get('order_num', 0)}`\n\n"
        "নিচের অ্যাকশন নির্বাচন করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_category_edit_kb(cat_id, c.get("type", "course")), parse_mode="Markdown")

@router.callback_query(F.data.startswith("cat_toggle_type:"))
async def handle_cat_toggle_type(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cat_id = int(call.data.split(":")[1])
    c = db.get_category(cat_id)
    if not c:
        await call.answer("ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
    new_type = "digital" if c["type"] == "course" else "course"
    db.update_category_type(cat_id, new_type)
    type_badge = "⚡ ডিজিটাল সার্ভিস / অ্যাকাউন্ট" if new_type == "digital" else "🎓 কোর্স ক্যাটাগরি"
    await call.answer(f"ক্যাটাগরি এখন {type_badge} হিসেবে সেট হয়েছে!", show_alert=True)
    text = (
        f"📁 **ক্যাটাগরি এডিটর: {c['icon']} {c['name']}**\n\n"
        f"• টাইপ: `{new_type}` ({type_badge})\n"
        f"• অর্ডার পজিশন: `{c.get('order_num', 0)}`\n\n"
        "নিচের অ্যাকশন নির্বাচন করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_category_edit_kb(cat_id, new_type), parse_mode="Markdown")

@router.callback_query(F.data.startswith("cat_edit_name:"))
async def handle_cat_rename_start(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[1])
    await state.update_data(cat_id=cat_id)
    await state.set_state(CategoryEditState.waiting_for_name)
    await call.answer()
    await call.message.answer("✏️ **ক্যাটাগরির নতুন নাম লিখুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(CategoryEditState.waiting_for_name)
async def handle_cat_rename_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে নাম লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    new_name = message.text.strip()
    data = await state.get_data()
    cat_id = data["cat_id"]
    await state.clear()
    c = db.get_category(cat_id)
    db.update_category(cat_id, name=new_name, icon=c["icon"])
    await message.answer(f"✅ ক্যাটাগরির নাম পরিবর্তিত হয়েছে: **{new_name}**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("cat_edit_icon:"))
async def handle_cat_reicon_start(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[1])
    await state.update_data(cat_id=cat_id)
    await state.set_state(CategoryEditState.waiting_for_icon)
    await call.answer()
    await call.message.answer("🎨 **নতুন ইমোজি / আইকন সেন্ড করুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(CategoryEditState.waiting_for_icon)
async def handle_cat_reicon_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে একটি ইমোজি বা আইকন সেন্ড করুন:", reply_markup=get_cancel_fsm_kb())
        return
    new_icon = message.text.strip()
    data = await state.get_data()
    cat_id = data["cat_id"]
    await state.clear()
    c = db.get_category(cat_id)
    db.update_category(cat_id, name=c["name"], icon=new_icon)
    await message.answer(f"✅ ক্যাটাগরির আইকন পরিবর্তিত হয়েছে: {new_icon}", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("cat_delete:"))
async def handle_cat_delete(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    db.delete_category(cat_id)
    await call.answer("ক্যাটাগরি মুছে ফেলা হয়েছে!", show_alert=True)
    await call.message.edit_text("🗑️ ক্যাটাগরি সফলভাবে ডিলিট করা হয়েছে!", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

# --- SUBCATEGORY MANAGEMENT HANDLERS ---

@router.callback_query(F.data.startswith("cat_add_sub:"))
async def handle_subcat_add_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    parent_cat_id = int(call.data.split(":")[1])
    parent = db.get_category(parent_cat_id)
    if not parent:
        await call.answer("মূল ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
    await state.update_data(parent_cat_id=parent_cat_id)
    await state.set_state(SubcategoryAddState.waiting_for_name)
    await call.answer()
    await call.message.answer(
        f"📁 **[{parent['name']}] এর অধীনে নতুন সাব-ক্যাটাগরির নাম লিখুন:**\n"
        "_(যেমন: Web Development, Graphic Design, Spoken English)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(SubcategoryAddState.waiting_for_name)
async def handle_subcat_name_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে সাব-ক্যাটাগরির নাম টেক্সট আকারে লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    name = message.text.strip()
    await state.update_data(subcat_name=name)
    await state.set_state(SubcategoryAddState.waiting_for_icon)
    await message.answer(
        "🎨 **সাব-ক্যাটাগরির জন্য একটি ইমোজি বা আইকন সেন্ড করুন:**\n"
        "_(যেমন: 💻, 🎨, 📈, 🤖)_",
        reply_markup=get_cancel_fsm_kb()
    )

@router.message(SubcategoryAddState.waiting_for_icon)
async def handle_subcat_icon_save(message: Message, state: FSMContext):
    icon = message.text.strip() if message.text else "📁"
    data = await state.get_data()
    parent_cat_id = data["parent_cat_id"]
    name = data["subcat_name"]
    await state.clear()
    
    parent = db.get_category(parent_cat_id)
    cat_type = parent.get("type", "course") if parent else "course"
    sub_id = db.add_category(name=name, icon=icon, cat_type=cat_type, parent_id=parent_cat_id)
    
    await message.answer(
        f"🎉 **সফল! নতুন সাব-ক্যাটাগরি যুক্ত হয়েছে!**\n\n"
        f"🏷️ নাম: {icon} {name}\n"
        f"🏫 মূল ক্যাটাগরি: **{parent['name'] if parent else 'N/A'}**\n"
        f"🆔 সাব-ক্যাটাগরি আইডি: `#{sub_id}`\n\n"
        "এখন এই সাব-ক্যাটাগরিতে যেকোনো কোর্স যোগ করতে পারবেন!",
        reply_markup=get_admin_main_kb(db.get_extended_bot_stats())
    )

@router.callback_query(F.data.startswith("cat_list_sub:"))
async def handle_subcat_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parent_cat_id = int(call.data.split(":")[1])
    parent = db.get_category(parent_cat_id)
    if not parent:
        await call.answer("ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    subcats = db.get_subcategories(parent_cat_id)
    
    text = (
        f"📁 <b>[{parent['name']}] এর সাব-ক্যাটাগরি সমূহ</b>\n\n"
        f"মোট সাব-ক্যাটাগরি: <b>{len(subcats)} টি</b>\n\n"
        "নিচে যেকোনো সাব-ক্যাটাগরিতে ক্লিক করে নাম বা আইকন এডিট করতে পারেন অথবা নতুন সাব-ক্যাটাগরি যোগ করতে পারেন:"
    )
    await call.message.edit_text(text, reply_markup=get_admin_subcategories_kb(subcats, parent_cat_id), parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_subcat_select:"))
async def handle_edit_subcat_select(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    subcat_id = int(call.data.split(":")[1])
    sc = db.get_category(subcat_id)
    if not sc:
        await call.answer("সাব-ক্যাটাগরি পাওয়া যায়নি!", show_alert=True)
        return
    await call.answer()
    parent = db.get_category(sc.get("parent_id")) if sc.get("parent_id") else None
    parent_name = parent["name"] if parent else "N/A"
    
    text = (
        f"📁 **সাব-ক্যাটাগরি এডিটর: {sc.get('icon', '📁')} {sc['name']}**\n\n"
        f"• মূল প্ল্যাটফর্ম: **{parent_name}**\n"
        f"• আইডি: `#{subcat_id}`\n\n"
        "নিচের অ্যাকশন নির্বাচন করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_subcategory_edit_kb(subcat_id, sc.get("parent_id", 0)), parse_mode="Markdown")

@router.callback_query(F.data.startswith("subcat_edit_name:"))
async def handle_subcat_rename_start(call: CallbackQuery, state: FSMContext):
    subcat_id = int(call.data.split(":")[1])
    await state.update_data(subcat_id=subcat_id)
    await state.set_state(SubcategoryEditState.waiting_for_name)
    await call.answer()
    await call.message.answer("✏️ **সাব-ক্যাটাগরির নতুন নাম লিখুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(SubcategoryEditState.waiting_for_name)
async def handle_subcat_rename_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে নাম লিখে পাঠান:", reply_markup=get_cancel_fsm_kb())
        return
    new_name = message.text.strip()
    data = await state.get_data()
    subcat_id = data["subcat_id"]
    await state.clear()
    sc = db.get_category(subcat_id)
    db.update_category(subcat_id, name=new_name, icon=sc["icon"])
    await message.answer(f"✅ সাব-ক্যাটাগরির নাম পরিবর্তিত হয়েছে: **{new_name}**", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("subcat_edit_icon:"))
async def handle_subcat_reicon_start(call: CallbackQuery, state: FSMContext):
    subcat_id = int(call.data.split(":")[1])
    await state.update_data(subcat_id=subcat_id)
    await state.set_state(SubcategoryEditState.waiting_for_icon)
    await call.answer()
    await call.message.answer("🎨 **নতুন ইমোজি / আইকন সেন্ড করুন:**", reply_markup=get_cancel_fsm_kb())

@router.message(SubcategoryEditState.waiting_for_icon)
async def handle_subcat_reicon_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে একটি ইমোজি বা আইকন সেন্ড করুন:", reply_markup=get_cancel_fsm_kb())
        return
    new_icon = message.text.strip()
    data = await state.get_data()
    subcat_id = data["subcat_id"]
    await state.clear()
    sc = db.get_category(subcat_id)
    db.update_category(subcat_id, name=sc["name"], icon=new_icon)
    await message.answer(f"✅ সাব-ক্যাটাগরির আইকন পরিবর্তিত হয়েছে: {new_icon}", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

@router.callback_query(F.data.startswith("subcat_delete:"))
async def handle_subcat_delete(call: CallbackQuery):
    subcat_id = int(call.data.split(":")[1])
    db.delete_category(subcat_id)
    await call.answer("সাব-ক্যাটাগরি মুছে ফেলা হয়েছে!", show_alert=True)
    await call.message.edit_text("🗑️ সাব-ক্যাটাগরি সফলভাবে ডিলিট করা হয়েছে!", reply_markup=get_admin_main_kb(db.get_extended_bot_stats()))

# ==========================================
# 🎁 FREE CLAIM DROPS (লুট/গিভঅ্যাওয়ে কন্ট্রোল)
# ==========================================

@router.callback_query(F.data == "admin_free_drops_menu")
@router.callback_query(F.data.startswith("admin_drop_filter:"))
async def handle_admin_free_drops_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    if not has_admin_permission(call.from_user.id, "can_manage_free_drops"):
        await call.answer("⛔ আপনার ফ্রি গিভঅ্যাওয়ে ড্রপ ম্যানেজ করার পারমিশন নেই!", show_alert=True)
        return
    await state.clear()
    
    current_cat = "all"
    if call.data and call.data.startswith("admin_drop_filter:"):
        current_cat = call.data.split(":")[1]
        
    cat_filter = None if current_cat == "all" else current_cat
    drops = db.get_all_free_drops(category=cat_filter, limit=25)
    counts = db.get_active_drop_counts_by_category()
    
    cat_names = {
        "all": "🔥 সকল ক্যাটাগরি",
        "accounts": "🔐 প্রিমিয়াম অ্যাকাউন্টস",
        "cookies": "🍪 ব্রাউজার কুকিজ",
        "subscription": "👑 সাবস্ক্রিপশন ও কি",
        "channel": "📢 ভিআইপি চ্যানেল",
        "tools_drive": "💾 টুলস ও ক্লাউড ড্রাইভ"
    }
    cur_cat_name = cat_names.get(current_cat, current_cat)
    
    text = (
        "🎁 **ফ্রি ড্রপ ও মাল্টি-ক্যাটাগরি গিভঅ্যাওয়ে হাব (Admin Control)** 🎁\n\n"
        "এখানে আপনি ও আপনার সাব-এডমিন টিম একসাথে একাধিক ভিন্ন ক্যাটাগরিতে গিভঅ্যাওয়ে চালাতে পারবেন:\n"
        "• 🔐 **Accounts:** Netflix, Prime, Canva সরাসরি আইডি-পাসওয়ার্ড\n"
        "• 🍪 **Cookies:** Cookie-Editor এক্সটেনশনের লাইভ সেশন কুকিজ\n"
        "• 👑 **Subscription:** সফটওয়্যার লাইসেন্স কি ও প্রোমো ভাউচার\n"
        "• 📢 **Channel:** ১ জন = ১ লিংক অটো মেম্বার লিমিট লিংক\n"
        "• 💾 **Tools / Drive:** মেগা / ক্লাউড সরাসরি ড্রাইভ লিংক\n\n"
        f"📂 **বর্তমান ফিল্টার:** `{cur_cat_name}`\n"
        f"📊 **মোট ড্রপ সংখ্যা:** `{len(drops)} টি` (সক্রিয়: `{counts.get('total', 0)} টি`)\n\n"
        "👇 নিচের তালিকা থেকে ড্রপ বিস্তারিত দেখুন, ফিল্টার পরিবর্তন করুন অথবা নতুন ড্রপ তৈরি করুন:"
    )
    await call.message.edit_text(text, reply_markup=get_admin_free_drops_kb(drops, current_cat=current_cat))
    await call.answer()

@router.callback_query(F.data == "admin_drop_create")
async def handle_admin_drop_create_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    if not has_admin_permission(call.from_user.id, "can_manage_free_drops"):
        await call.answer("⛔ আপনার গিভঅ্যাওয়ে ড্রপ তৈরি করার পারমিশন নেই!", show_alert=True)
        return
    await state.set_state(CreateFreeDropState.waiting_for_category)
    text = (
        "🎁 **নতুন গিভঅ্যাওয়ে ড্রপ তৈরি করুন** 🎁\n\n"
        "প্রথমে নির্ধারণ করুন এটি কোন ক্যাটাগরির গিভঅ্যাওয়ে হবে:\n\n"
        "🔐 **1. প্রিমিয়াম অ্যাকাউন্টস:** Netflix, Prime, Canva, VPN ইত্যাদি সরাসরি অ্যাকাউন্ট।\n"
        "🍪 **2. ব্রাউজার কুকিজ:** OTT ও AI সাইটগুলোর কুকিজ ফাইল (Cookie-Editor এর জন্য)।\n"
        "👑 **3. সাবস্ক্রিপশন ও কি:** লাইসেন্স কি, রিডিম কোড, ভাউচার।\n"
        "📢 **4. ভিআইপি চ্যানেল অ্যাক্সেস:** ১-জন ব্যবহারের প্রাইভেট চ্যানেল ইনভাইট লিংক।\n"
        "💾 **5. টুলস ও ড্রাইভ ভল্ট:** প্রিমিয়াম রিসোর্স বা ক্লাউড ফোল্ডার লিংক।\n\n"
        "👇 নিচের বাটন থেকে কাঙ্ক্ষিত ক্যাটাগরি বেছে নিন:"
    )
    await call.message.edit_text(text, reply_markup=get_admin_giveaway_category_select_kb())
    await call.answer()

@router.callback_query(F.data.startswith("drop_cat_sel:"))
async def handle_drop_cat_select(call: CallbackQuery, state: FSMContext):
    category = call.data.split(":")[1]
    await state.update_data(giveaway_category=category)
    await state.set_state(CreateFreeDropState.waiting_for_title)
    await call.answer()
    
    examples = {
        "accounts": "• `Netflix UHD 1-Month Profile Drop`\n• `Canva Pro Edu Lifetime Direct Login`\n• `Prime Video 4K 1-Month Account`",
        "cookies": "• `Netflix Premium 4K Session Cookie (Cookie-Editor)`\n• `ChatGPT Plus Live Session Cookie`\n• `Prime Video UHD Cookie Drop`",
        "subscription": "• `NordVPN 1-Year License Key Drop`\n• `Discord Nitro 3-Month Promo Code`\n• `Kaspersky Internet Security 1-Year Key`",
        "channel": "• `VIP Signal Private Channel (Free Entry)`\n• `Insider Secret Courses Channel (1-Time Link)`",
        "tools_drive": "• `500GB Premium Video Editing Mega Drive Pack`\n• `Full Stack Web Development Mega Vault`"
    }
    ex_text = examples.get(category, "• `Premium Giveaway Drop`")
    
    cat_names = {
        "accounts": "🔐 প্রিমিয়াম অ্যাকাউন্টস",
        "cookies": "🍪 ব্রাউজার কুকিজ",
        "subscription": "👑 সাবস্ক্রিপশন ও কি",
        "channel": "📢 ভিআইপি চ্যানেল অ্যাক্সেস",
        "tools_drive": "💾 টুলস ও ক্লাউড ড্রাইভ"
    }
    
    text = (
        f"📂 **নির্বাচিত ক্যাটাগরি:** `{cat_names.get(category, category)}`\n\n"
        "🎁 **এই ড্রপের একটি আকর্ষণীয় শিরোনাম / নাম (Title) দিন:**\n\n"
        f"উদাহরণ:\n{ex_text}"
    )
    await call.message.edit_text(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_title)
async def handle_drop_title_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে ড্রপের জন্য একটি সুন্দর নাম লিখুন:", reply_markup=get_cancel_fsm_kb())
        return
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(CreateFreeDropState.waiting_for_site_link)
    
    data = await state.get_data()
    category = data.get("giveaway_category", "accounts")
    
    site_examples = {
        "accounts": "• https://instructory.net\n• https://netflix.com\n• https://canva.com",
        "cookies": "• https://netflix.com\n• https://chatgpt.com\n• https://primevideo.com",
        "subscription": "• https://discord.com/billing/promotions\n• https://nordvpn.com",
        "channel": "• https://t.me/MyChannel",
        "tools_drive": "• https://drive.google.com"
    }
    ex = site_examples.get(category, "• https://example.com")
    
    text = (
        f"📌 <b>ড্রপের নাম:</b> <code>{html.escape(title)}</code>\n\n"
        "🌐 <b>এই গিভঅ্যাওয়েটি কোন ওয়েবসাইট বা সার্ভিসের? (Website URL / Portal Link):</b>\n\n"
        f"উদাহরণ:\n{ex}\n\n"
        "💡 ইউজাররা গিভঅ্যাওয়ে দেখার সময় ও ক্লেইম করার পর <b>'🌐 ওয়েবসাইটে প্রবেশ করুন'</b> বাটনে ১-ক্লিক করে সরাসরি এই সাইটে যেতে পারবে।\n\n"
        "👉 সাইটের সম্পূর্ণ লিংক দিন (অথবা সাইট লিংক না থাকলে <code>skip</code> বা <code>-</code> লিখুন):"
    )
    await message.answer(text, reply_markup=get_cancel_fsm_kb(), parse_mode="HTML")

@router.message(CreateFreeDropState.waiting_for_site_link)
async def handle_drop_site_link_save(message: Message, state: FSMContext):
    raw_link = message.text.strip() if message.text else ""
    site_link = ""
    if raw_link and raw_link.lower() not in ["skip", "-", "none", "no"]:
        if not raw_link.startswith("http://") and not raw_link.startswith("https://"):
            site_link = "https://" + raw_link
        else:
            site_link = raw_link
            
    await state.update_data(site_link=site_link)
    await state.set_state(CreateFreeDropState.waiting_for_payload)
    
    data = await state.get_data()
    category = data.get("giveaway_category", "accounts")
    title = data.get("title", "Giveaway")
    
    site_badge = f"\n🌐 <b>সাইট লিংক:</b> <code>{site_link}</code>" if site_link else "\n🌐 <b>সাইট লিংক:</b> <i>নেই (Skipped)</i>"
    
    text = (
        f"📌 <b>ড্রপের নাম:</b> <code>{html.escape(title)}</code>"
        f"{site_badge}\n\n"
        "🎁 <b>ড্রপের ডেলিভারি ধরন (Delivery Method) নির্বাচন করুন:</b>\n\n"
        "বট ক্লেইমকারী ইউজারদের ঠিক কিভাবে এই গিভঅ্যাওয়ে ডেলিভারি করবে তা নির্বাচন করুন:"
    )
    await message.answer(text, reply_markup=get_admin_drop_type_kb(category=category), parse_mode="HTML")

@router.callback_query(F.data.startswith("drop_type:"))
async def handle_drop_type_select(call: CallbackQuery, state: FSMContext):
    drop_type = call.data.split(":")[1]
    await state.update_data(drop_type=drop_type)
    await state.set_state(CreateFreeDropState.waiting_for_payload)
    await call.answer()
    
    data = await state.get_data()
    category = data.get("giveaway_category", "accounts")
    
    if drop_type == "channel_link":
        text = (
            "🔒 **প্রাইভেট চ্যানেলের Chat ID বা Username দিন:**\n\n"
            "উদাহরণ:\n"
            "• `-1001928374650` (প্রাইভেট চ্যানেল আইডি)\n"
            "• `@MySecretVIPChannel` (পাবলিক ইউজারনেম)\n\n"
            "⚠️ **জরুরী শর্ত:**\n"
            "বটকে অবশ্যই উক্ত চ্যানেলে অ্যাডমিন বানিয়ে **'Invite Users via Link'** পারমিশন দিতে হবে। "
            "ক্লেইম করার সাথে সাথে বট প্রতি ইউজারের জন্য আলাদা সিঙ্গেল-ইউজ (1-person) লিংক বানাবে!"
        )
    elif drop_type == "bulk_combo":
        if category == "cookies":
            text = (
                "🍪 **বাল্ক কুকিজ / ডাটা পেস্ট করুন:**\n\n"
                "প্রতি লাইনে ১টি করে কুকিজ কোড দিন:\n"
                "```\n"
                "cookie_code_for_user_1\n"
                "cookie_code_for_user_2\n"
                "```\n\n"
                "💡 বট স্বয়ংক্রিয়ভাবে প্রতি ক্লেইমকারীকে ১টি করে পৃথক কুকিজ কোড লাইভ ডেলিভারি দেবে।"
            )
        elif category == "subscription":
            text = (
                "👑 **বাল্ক লাইসেন্স কি / ভাউচার কোড পেস্ট করুন:**\n\n"
                "প্রতি লাইনে ১টি করে কি দিন:\n"
                "```\n"
                "KEY-AAAA-BBBB-CCCC\n"
                "KEY-DDDD-EEEE-FFFF\n"
                "```\n\n"
                "💡 বট প্রতি ক্লেইমকারীকে ১টি করে পৃথক ইউনিক কি ডেলিভারি দেবে।"
            )
        else:
            text = (
                "📦 **বাল্ক অ্যাকাউন্ট কম্বো (মেইল:পাসওয়ার্ড) পেস্ট করুন:**\n\n"
                "প্রতি লাইনে একটি করে অ্যাকাউন্ট/কি দিন:\n"
                "```\n"
                "user1@gmail.com:pass123\n"
                "user2@gmail.com:pass456\n"
                "```\n\n"
                "💡 বট স্বয়ংক্রিয়ভাবে প্রতি ক্লেইমকারীকে ১টি করে পৃথক কম্বো অ্যাকাউন্ট লাইভ ডেলিভারি দেবে।"
            )
    else: # direct_link
        if category == "cookies":
            text = (
                "🍪 **কমন কুকিজ কোড (JSON/Text) অথবা কুকিজ পেস্টবিন লিংক দিন:**\n\n"
                "ইউজাররা এটি কপি করে সরাসরি Cookie-Editor দিয়ে ইমপোর্ট করতে পারবে:"
            )
        elif category == "tools_drive":
            text = (
                "💾 **গুগল ড্রাইভ / মেগা ক্লাউড ডাউনলোড লিংকটি দিন:**\n\n"
                "যেমন: Google Drive ফোল্ডার, Mega.nz লিংক, ইত্যাদি:"
            )
        else:
            text = (
                "🔗 **সিক্রেট ড্রপ লিংকটি সেন্ড করুন:**\n\n"
                "যেমন: Google Drive, Mega Cloud, Telegram Post, বা যেকোনো সিক্রেট লিংক:"
            )
    await call.message.edit_text(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_payload)
async def handle_drop_payload_save(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ অনুগ্রহ করে সঠিক তথ্য প্রদান করুন:", reply_markup=get_cancel_fsm_kb())
        return
    data = await state.get_data()
    drop_type = data.get("drop_type", "direct_link")
    
    if drop_type == "bulk_combo":
        raw_lines = [line.strip() for line in message.text.strip().splitlines() if line.strip()]
        if not raw_lines:
            await message.answer("❌ কোনো ভ্যালিড আইটেম পাওয়া যায়নি। প্রতি লাইনে ১টি করে পেস্ট করুন:", reply_markup=get_cancel_fsm_kb())
            return
        await state.update_data(bulk_items=raw_lines, target_payload="")
        await state.set_state(CreateFreeDropState.waiting_for_slots)
        text = (
            f"✅ মোট `{len(raw_lines)} টি` আইটেম ডিটেক্ট করা হয়েছে!\n\n"
            f"🔢 **সর্বোচ্চ কতজন ইউজার ক্লেইম করতে পারবে? (Max Slots):**\n"
            f"(ডিফল্ট `{len(raw_lines)}` রাখতে চাইলে `{len(raw_lines)}` লিখুন):"
        )
        await message.answer(text, reply_markup=get_cancel_fsm_kb())
    else:
        payload = message.text.strip()
        await state.update_data(target_payload=payload)
        await state.set_state(CreateFreeDropState.waiting_for_slots)
        text = (
            "🔢 **সর্বোচ্চ কতজন ইউজার এই গিভঅ্যাওয়ে ক্লেইম করতে পারবে? (Max Slots):**\n\n"
            "(যেমন: `10`, `50`, `100` অথবা আনলিমিটেড হলে `9999` দিন):"
        )
        await message.answer(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_slots)
async def handle_drop_slots_save(message: Message, state: FSMContext):
    val = message.text.strip()
    if not val.isdigit() or int(val) <= 0:
        await message.answer("❌ অনুগ্রহ করে একটি ধনাত্মক পূর্ণসংখ্যা দিন (যেমন: 20 বা 50):", reply_markup=get_cancel_fsm_kb())
        return
    slots = int(val)
    await state.update_data(slots=slots)
    await state.set_state(CreateFreeDropState.waiting_for_required_referrals)
    
    text = (
        f"🔢 স্লট সংখ্যা: `{slots}` জন।\n\n"
        "👥 **ভাইরাল রেফারেল শর্ত (Share-to-Unlock Gate) নির্ধারণ করুন:**\n\n"
        "এই গিভঅ্যাওয়েটি ক্লেইম করার জন্য একজন সাধারণ ইউজারকে ন্যূনতম কয়জন বন্ধুকে রেফার/ইনভাইট করাতে হবে?\n\n"
        "👉 **সবার জন্য সরাসরি সম্পূর্ণ ফ্রি রাখতে:** `0` লিখুন (অথবা `skip`)\n"
        "👉 **রেফারেল বাধ্যতামূলক করতে:** সংখ্যাটি লিখুন (যেমন: `1`, `2`, `3` বা `5` জন)\n\n"
        "💡 *নোট: আপনি যদি ৩ লেখেন, তবে ইউজার ৩ জন বন্ধুকে জয়েন না করানো পর্যন্ত ক্লেইম করতে পারবে না এবং বটের ১-ক্লিক শেয়ার বাটন পাবে।*"
    )
    await message.answer(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_required_referrals)
async def handle_drop_referrals_save(message: Message, state: FSMContext):
    val_raw = message.text.strip().lower()
    if val_raw in ["skip", "free", "-", "none", "auto", "0"]:
        req_refs = 0
    elif val_raw.isdigit():
        req_refs = int(val_raw)
    else:
        await message.answer("❌ অনুগ্রহ করে সঠিক সংখ্যা লিখুন (যেমন: 0 সবার জন্য ফ্রি, অথবা 1, 2, 3):", reply_markup=get_cancel_fsm_kb())
        return

    await state.update_data(required_referrals=req_refs)
    await state.set_state(CreateFreeDropState.waiting_for_desc)
    
    ref_status = f"`{req_refs} জন রেফারেল প্রয়োজন` 🔒 (Viral Lock Active)" if req_refs > 0 else "`সবার জন্য সম্পূর্ণ ফ্রি` 🟢 (0 Ref)"
    text = (
        f"✅ আনলক শর্ত: {ref_status}\n\n"
        "📝 **এই গিভঅ্যাওয়ের বিবরণ ও সংক্ষিপ্ত নোট (Description) দিন:**\n"
        "(ইউজাররা ক্লেইম করার সময় দেখতে পাবে। কিছু না লিখতে চাইলে `skip` লিখুন):"
    )
    await message.answer(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_desc)
async def handle_drop_desc_and_next(message: Message, state: FSMContext):
    desc_raw = message.text.strip()
    desc = "" if desc_raw.lower() in ["skip", "-", "none"] else desc_raw
    await state.update_data(description=desc)
    await state.set_state(CreateFreeDropState.waiting_for_instructions)
    
    data = await state.get_data()
    category = data.get("giveaway_category", "accounts")
    
    guide_hints = {
        "cookies": "কুকিজের ক্ষেত্রে Cookie-Editor দিয়ে কিভাবে ইমপোর্ট করবে তা বোঝাতে পারেন।",
        "accounts": "লগইন নিয়ম এবং পাসওয়ার্ড না বদলানোর সতর্কবার্তা দিতে পারেন।",
        "subscription": "রিডিম পেজ লিংক এবং কি এক্টিভেট করার নিয়ম দিতে পারেন।",
        "channel": "লিংকে ক্লিক করে জয়েন করার নিয়ম দিতে পারেন।",
        "tools_drive": "ফাইল কপি করার নিয়ম বা ড্রাইভ ব্যবহারের নির্দেশিকা দিতে পারেন।"
    }
    hint = guide_hints.get(category, "কিভাবে ব্যবহার করবে তার নির্দেশিকা দিন।")
    
    text = (
        "📖 **ব্যবহারের নির্দেশিকা ও গাইড (How-to-Use Guide) দিন:**\n\n"
        f"💡 {hint}\n\n"
        "ইউজার ড্রপ ক্লেইম করার সাথে সাথে এই গাইডটি দেখতে পাবে।\n\n"
        "👉 **স্বয়ংক্রিয় প্রমিত বাংলা গাইড ব্যবহার করতে চাইলে সরাসরি `auto` বা `skip` লিখুন:**\n"
        "(অন্যথায় আপনার নিজস্ব কাস্টম গাইড টেক্সট এখানে লিখে পাঠান)"
    )
    await message.answer(text, reply_markup=get_cancel_fsm_kb())

@router.message(CreateFreeDropState.waiting_for_instructions)
async def handle_drop_instructions_and_finish(message: Message, state: FSMContext):
    inst_raw = message.text.strip()
    instructions = "" if inst_raw.lower() in ["auto", "skip", "-", "none", "default"] else inst_raw
    
    data = await state.get_data()
    await state.clear()
    
    title = data.get("title", "Free Giveaway Drop")
    category = data.get("giveaway_category", "accounts")
    site_link = data.get("site_link", "")
    drop_type = data.get("drop_type", "direct_link")
    slots = data.get("slots", 10)
    desc = data.get("description", "")
    bulk_items = data.get("bulk_items", None)
    target_payload = data.get("target_payload", "")
    required_referrals = data.get("required_referrals", 0)
    
    channel_id = target_payload if drop_type == "channel_link" else None
    direct_link = target_payload if drop_type == "direct_link" else None
    
    drop_id = db.create_free_drop(
        title=title,
        drop_type=drop_type,
        max_claims=slots,
        description=desc,
        channel_id=channel_id,
        direct_link=direct_link,
        bulk_items=bulk_items,
        giveaway_category=category,
        instructions=instructions,
        site_link=site_link,
        required_referrals=required_referrals
    )
    
    cat_names = {
        "accounts": "🔐 প্রিমিয়াম অ্যাকাউন্টস",
        "cookies": "🍪 ব্রাউজার কুকিজ",
        "subscription": "👑 সাবস্ক্রিপশন ও কি",
        "channel": "📢 ভিআইপি চ্যানেল",
        "tools_drive": "💾 টুলস ও ক্লাউড ড্রাইভ"
    }
    
    type_badge = {
        "channel_link": "🔒 Private Channel (1-Use Invite)",
        "bulk_combo": f"📦 Bulk Item Combo ({len(bulk_items) if bulk_items else 0} items)",
        "direct_link": "🔗 Secret Direct Link"
    }.get(drop_type, drop_type)
    
    site_badge = f"\n🌐 **সাইট লিংক:** `{site_link}`" if site_link else ""
    ref_badge = f"\n🔒 **আনলক শর্ত:** `{required_referrals} জন রেফারেল প্রয়োজন`" if required_referrals > 0 else "\n🟢 **আনলক শর্ত:** `সবার জন্য সম্পূর্ণ ফ্রি (0 Ref)`"
    
    success_text = (
        "🎉 **ফ্রি গিভঅ্যাওয়ে ড্রপ সফলভাবে পাবলিশ হয়েছে!** 🎉\n\n"
        f"🆔 **ড্রপ আইডি:** `#{drop_id}`\n"
        f"📂 **ক্যাটাগরি:** `{cat_names.get(category, category)}`\n"
        f"📌 **শিরোনাম:** **{title}**\n"
        f"🏷️ **ধরন:** `{type_badge}`\n"
        f"👥 **মোট স্লট:** `{slots} জন`"
        f"{ref_badge}"
        f"{site_badge}\n"
        f"📝 **বিবরণ:** {desc or 'নেই'}\n"
        f"📖 **গাইড:** {'কাস্টম গাইড সেভড' if instructions else 'স্বয়ংক্রিয় প্রমিত গাইড সক্রিয়'}\n\n"
        "🚀 ইউজাররা এখন `🎁 Free Claim (গিভঅ্যাওয়ে)` মেনু থেকে সরাসরি ক্লেইম করতে পারবে!\n"
        "📢 আপনি চাইলে নিচের বাটন দিয়ে সমস্ত ইউজারকে এখনই ব্রডকাস্ট অ্যালার্ট পাঠাতে পারেন।"
    )
    await message.answer(success_text, reply_markup=get_admin_drop_detail_kb(drop_id, is_active=True))

@router.callback_query(F.data.startswith("admin_drop_detail:"))
async def handle_admin_drop_detail(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    if not drop:
        await call.answer("ড্রপ খুঁজে পাওয়া যায়নি!", show_alert=True)
        return
        
    status_str = "🟢 সক্রিয় (Active)" if drop["is_active"] else "🔴 বন্ধ (Closed/Ended)"
    remaining = max(0, drop["max_claims"] - drop["claimed_count"])
    
    cat_names = {
        "accounts": "🔐 প্রিমিয়াম অ্যাকাউন্টস",
        "cookies": "🍪 ব্রাউজার কুকিজ",
        "subscription": "👑 সাবস্ক্রিপশন ও কি",
        "channel": "📢 ভিআইপি চ্যানেল",
        "tools_drive": "💾 টুলস ও ক্লাউড ড্রাইভ"
    }
    cat_badge = cat_names.get(drop.get("giveaway_category", "accounts"), drop.get("giveaway_category", "accounts"))
    
    req_r = drop.get("required_referrals", 0)
    ref_gate_str = f"🔒 `{req_r} জন রেফারেল প্রয়োজন` (Viral Lock)" if req_r > 0 else "🟢 `সবার জন্য সম্পূর্ণ ফ্রি (0 Ref)`"
    
    text = (
        f"🎁 **ড্রপ বিস্তারিত তথ্য — #{drop['id']}**\n\n"
        f"📌 **শিরোনাম:** **{drop['title']}**\n"
        f"📂 **ক্যাটাগরি:** `{cat_badge}`\n"
        f"⚡ **স্ট্যাটাস:** {status_str}\n"
        f"🏷️ **টাইপ:** `{drop['drop_type']}`\n"
        f"👥 **আনলক শর্ত:** {ref_gate_str}\n"
        f"👥 **ক্লেইম সম্পন্ন:** `{drop['claimed_count']} / {drop['max_claims']} জন`\n"
        f"🔥 **অবশিষ্ট স্লট:** `{remaining} জন`\n"
    )
    if drop.get("site_link"):
        text += f"🌐 **সাইট লিংক:** `{drop['site_link']}`\n"
    text += (
        f"📝 **বিবরণ:** {drop['description'] or 'নেই'}\n"
        f"📖 **গাইড:** {drop['instructions'] or 'স্বয়ংক্রিয় গাইড'}\n"
        f"📅 **তৈরির সময়:** `{drop['created_at']}`\n"
    )
    if drop["channel_id"]:
        text += f"🎯 **টার্গেট চ্যানেল:** `{drop['channel_id']}`\n"
    if drop["direct_link"]:
        text += f"🔗 **ডিরেক্ট লিংক:** `{drop['direct_link']}`\n"
        
    await call.message.edit_text(text, reply_markup=get_admin_drop_detail_kb(drop_id, is_active=bool(drop["is_active"])))
    await call.answer()

@router.callback_query(F.data.startswith("drop_edit_refs:"))
async def handle_admin_drop_edit_refs_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    if not drop:
        await call.answer("ড্রপ খুঁজে পাওয়া যায়নি!", show_alert=True)
        return
        
    await state.update_data(editing_drop_id=drop_id)
    await state.set_state(EditFreeDropRefsState.waiting_for_new_refs)
    await call.answer()
    
    current_refs = drop.get("required_referrals", 0)
    cur_str = f"`{current_refs} জন রেফার`" if current_refs > 0 else "`সবার জন্য ফ্রি (0 Ref)`"
    text = (
        f"🔒 **ড্রপ #{drop_id} — ভাইরাল রেফারেল শর্ত পরিবর্তন**\n\n"
        f"📌 ড্রপ: **{drop['title']}**\n"
        f"বর্তমান শর্ত: {cur_str}\n\n"
        "নতুন শর্ত নির্ধারণ করতে সংখ্যা লিখুন:\n"
        "👉 **সবার জন্য সম্পূর্ণ ফ্রি করতে:** `0` লিখুন\n"
        "👉 **রেফারেল বাধ্যতামূলক করতে:** সংখ্যাটি লিখুন (যেমন: `1`, `2`, `3` বা `5` জন):"
    )
    await call.message.edit_text(text, reply_markup=get_cancel_fsm_kb())

@router.message(EditFreeDropRefsState.waiting_for_new_refs)
async def handle_save_new_drop_refs(message: Message, state: FSMContext):
    val_raw = message.text.strip().lower()
    if val_raw in ["skip", "free", "-", "none", "auto", "0"]:
        new_refs = 0
    elif val_raw.isdigit():
        new_refs = int(val_raw)
    else:
        await message.answer("❌ অনুগ্রহ করে সঠিক সংখ্যা লিখুন (যেমন: 0 সবার জন্য ফ্রি, অথবা 1, 2, 3):", reply_markup=get_cancel_fsm_kb())
        return
        
    data = await state.get_data()
    drop_id = data.get("editing_drop_id")
    await state.clear()
    
    if drop_id:
        db.update_free_drop_referrals(drop_id, new_refs)
        drop = db.get_free_drop(drop_id)
        status_txt = f"`{new_refs} জন রেফারেল প্রয়োজন` 🔒 (Viral Lock Active)" if new_refs > 0 else "`সবার জন্য সম্পূর্ণ ফ্রি` 🟢 (0 Ref)"
        await message.answer(
            f"✅ ড্রপ #{drop_id}-এর রেফারেল আনলক শর্ত সফলভাবে পরিবর্তিত হয়েছে:\n{status_txt}",
            reply_markup=get_admin_drop_detail_kb(drop_id, is_active=bool(drop["is_active"] if drop else True))
        )

@router.callback_query(F.data.startswith("admin_drop_close:"))
async def handle_admin_drop_close(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    drop_id = int(call.data.split(":")[1])
    db.close_free_drop(drop_id)
    await call.answer("ড্রপটি বন্ধ করা হয়েছে! নতুন কেউ আর ক্লেইম করতে পারবে না।", show_alert=True)
    
    drop = db.get_free_drop(drop_id)
    if drop:
        remaining = max(0, drop["max_claims"] - drop["claimed_count"])
        text = (
            f"🎁 **ড্রপ বিস্তারিত তথ্য — #{drop['id']}**\n\n"
            f"📌 **শিরোনাম:** **{drop['title']}**\n"
            f"⚡ **স্ট্যাটাস:** 🔴 বন্ধ (Closed)\n"
            f"👥 **ক্লেইম সম্পন্ন:** `{drop['claimed_count']} / {drop['max_claims']} জন`\n"
            f"🔥 **অবশিষ্ট স্লট:** `{remaining} জন`\n"
        )
        await call.message.edit_text(text, reply_markup=get_admin_drop_detail_kb(drop_id, is_active=False))

@router.callback_query(F.data.startswith("admin_drop_claims:"))
async def handle_admin_drop_claims_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    claims = db.get_drop_claims(drop_id, limit=30)
    
    title = drop['title'] if drop else f"#{drop_id}"
    text = f"👥 **ক্লেইমকারী তালিকা — {title}**\n\n"
    if not claims:
        text += "এখনও পর্যন্ত কেউ এই ড্রপটি ক্লেইম করেনি।"
    else:
        text += f"মোট ক্লেইম: `{len(claims)} টি` (সর্বশেষ ৩০ জনের তালিকা):\n\n"
        for idx, c in enumerate(claims, 1):
            u_name = f"@{c['username']}" if c.get('username') else (c.get('first_name') or f"User {c['user_id']}")
            text += f"{idx}. {u_name} (`{c['user_id']}`) — `{c['claimed_at'][:16]}`\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Drop", callback_data=f"admin_drop_detail:{drop_id}")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("admin_drop_bcast:"))
async def handle_admin_drop_broadcast(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("অনুমতি নেই!", show_alert=True)
        return
    drop_id = int(call.data.split(":")[1])
    drop = db.get_free_drop(drop_id)
    if not drop or not drop["is_active"]:
        await call.answer("ড্রপটি সক্রিয় নেই!", show_alert=True)
        return
        
    await call.answer("📢 ব্রডকাস্ট শুরু হচ্ছে...", show_alert=False)
    remaining = max(0, drop["max_claims"] - drop["claimed_count"])
    
    cat_names = {
        "accounts": "🔐 প্রিমিয়াম অ্যাকাউন্টস",
        "cookies": "🍪 ব্রাউজার কুকিজ",
        "subscription": "👑 সাবস্ক্রিপশন ও কি",
        "channel": "📢 ভিআইপি চ্যানেল",
        "tools_drive": "💾 টুলস ও ক্লাউড ড্রাইভ"
    }
    cat_badge = cat_names.get(drop.get("giveaway_category", "accounts"), "🎁 গিভঅ্যাওয়ে")
    
    bcast_text = (
        "🎁 <b>ধামাকা ফ্রি গিভঅ্যাওয়ে ড্রপ! (Free Claim Alert)</b> 🎁\n\n"
        f"📂 <b>ক্যাটাগরি:</b> <code>{cat_badge}</code>\n"
        f"📌 <b>{html.escape(drop['title'])}</b>\n\n"
        f"⚡ লিমিটেড ফ্রি স্লট: <b>{remaining} জন মাত্র!</b>\n"
        "🏃‍♂️ <i>\"যে আগে আসবে সে আগে পাবে\" (First-Come, First-Served)</i>\n\n"
    )
    if drop.get("site_link"):
        site_u = drop["site_link"]
        bcast_text += f"🌐 <b>অফিসিয়াল সাইট:</b> <a href=\"{site_u}\">{html.escape(site_u)}</a>\n\n"
    if drop.get("description"):
        bcast_text += f"{html.escape(drop['description'])}\n\n"
    bcast_text += "👇 দ্রুত আপনার ফ্রি গিফট ক্লেইম করতে নিচের বাটনে চাপ দিন:"
    
    bcast_buttons = [
        [InlineKeyboardButton(text="⚡ এখনই ফ্রি ক্লেইম করুন 🎁", callback_data=f"view_free_drop:{drop_id}")]
    ]
    if drop.get("site_link") and drop["site_link"].startswith("http"):
        bcast_buttons.append([InlineKeyboardButton(text="🌐 ওয়েবসাইট দেখুন (Open Site)", url=drop["site_link"])])
    bcast_buttons.append([InlineKeyboardButton(text="🎁 অন্যান্য ফ্রি গিভঅ্যাওয়ে", callback_data="nav_free_claim")])
    bcast_kb = InlineKeyboardMarkup(inline_keyboard=bcast_buttons)
    
    users = db.get_all_users()
    total = len(users)
    sent = 0
    
    status_msg = await call.message.answer(f"📢 ব্রডকাস্ট পাঠানো শুরু হয়েছে... (মোট ইউজার: {total})")
    
    for u in users:
        uid = u["user_id"]
        try:
            await bot.send_message(uid, bcast_text, reply_markup=bcast_kb, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.04) # Telegram safe rate
        except Exception:
            pass
            
    await status_msg.edit_text(f"✅ ড্রপ ব্রডকাস্ট সম্পন্ন!\nমোট পাঠানো হয়েছে: `{sent}/{total}` জন ইউজারের কাছে।")


# ==============================================================================
# --- 13. DEDICATED STOCK MANAGER HUB (1-CLICK IN / OUT TOGGLE) ---
# ==============================================================================

@router.callback_query(F.data == "admin_stock_hub")
@router.callback_query(F.data.startswith("admin_stock_page:"))
async def handle_admin_stock_hub(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    if not has_admin_permission(call.from_user.id, "can_manage_stock"):
        await call.answer("⛔ আপনার স্টক কন্ট্রোল করার অনুমতি (Permission) নেই!", show_alert=True)
        return
    await call.answer()
    
    page = 0
    if call.data.startswith("admin_stock_page:"):
        try:
            page = int(call.data.split(":")[1])
        except (ValueError, IndexError):
            page = 0

    all_prods = db.get_all_products()
    if not all_prods:
        await call.message.edit_text(
            "⚠️ ক্যাটালগে বর্তমানে কোনো প্রোডাক্ট নেই।",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Back to Admin", callback_data="admin_main_dashboard")
            ]])
        )
        return

    in_stock_cnt = sum(1 for p in all_prods if (p.get("is_in_stock", 1) if p.get("is_in_stock") is not None else 1) == 1)
    out_stock_cnt = len(all_prods) - in_stock_cnt
    
    PAGE_SIZE = 8
    total_pages = max(1, (len(all_prods) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start_idx = page * PAGE_SIZE
    page_prods = all_prods[start_idx:start_idx + PAGE_SIZE]
    
    text = (
        "⚡ **স্টক কন্ট্রোল ম্যানেজার (Stock In / Out Hub)**\n\n"
        "এখানে আপনার সকল কোর্সের বর্তমান স্টক এক ক্লিকে অন/অফ করতে পারবেন।\n"
        "গ্রাহক কোনো স্টক-আউট (Out of Stock) কোর্স কিনতে পারবে না।\n\n"
        f"📊 **মোট কোর্স:** `{len(all_prods)}` টি | 🟢 **ইন-স্টক:** `{in_stock_cnt}` টি | 🔴 **আউট-অব-স্টক:** `{out_stock_cnt}` টি\n\n"
        "👇 _যেকোনো কোর্সের বাটনে ট্যাপ করে সাথে সাথে স্টক ইন বা আউট করুন:_"
    )
    
    await call.message.edit_text(
        text,
        reply_markup=get_stock_hub_kb(page_prods, page=page, total_pages=total_pages),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("stk_hub_tgl:"))
async def handle_stk_hub_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    if not has_admin_permission(call.from_user.id, "can_manage_stock"):
        await call.answer("⛔ আপনার স্টক পরিবর্তনের অনুমতি নেই!", show_alert=True)
        return
    parts = call.data.split(":")
    prod_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    
    prod = db.get_product(prod_id)
    if not prod:
        await call.answer("প্রোডাক্ট পাওয়া যায়নি!", show_alert=True)
        return
    
    new_state = db.toggle_product_stock(prod_id)
    toast = f"✅ '{prod['title']}' এখন ইন স্টক (In Stock)!" if new_state else f"⚠️ '{prod['title']}' এখন আউট অব স্টক (Out of Stock)!"
    await call.answer(toast, show_alert=False)
    
    all_prods = db.get_all_products()
    PAGE_SIZE = 8
    total_pages = max(1, (len(all_prods) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start_idx = page * PAGE_SIZE
    page_prods = all_prods[start_idx:start_idx + PAGE_SIZE]
    
    in_stock_cnt = sum(1 for p in all_prods if (p.get("is_in_stock", 1) if p.get("is_in_stock") is not None else 1) == 1)
    out_stock_cnt = len(all_prods) - in_stock_cnt
    
    text = (
        "⚡ **স্টক কন্ট্রোল ম্যানেজার (Stock In / Out Hub)**\n\n"
        "এখানে আপনার সকল কোর্সের বর্তমান স্টক এক ক্লিকে অন/অফ করতে পারবেন।\n"
        "গ্রাহক কোনো স্টক-আউট (Out of Stock) কোর্স কিনতে পারবে না।\n\n"
        f"📊 **মোট কোর্স:** `{len(all_prods)}` টি | 🟢 **ইন-স্টক:** `{in_stock_cnt}` টি | 🔴 **আউট-অব-স্টক:** `{out_stock_cnt}` টি\n\n"
        "👇 _যেকোনো কোর্সের বাটনে ট্যাপ করে সাথে সাথে স্টক ইন বা আউট করুন:_"
    )
    
    try:
        await call.message.edit_text(
            text,
            reply_markup=get_stock_hub_kb(page_prods, page=page, total_pages=total_pages),
            parse_mode="Markdown"
        )
    except Exception:
        pass


# ==============================================================================
# --- 14. SUB-ADMIN ROLES & GRANULAR PERMISSIONS (RBAC) ---
# ==============================================================================

@router.callback_query(F.data == "admin_subadmins_menu")
async def handle_admin_subadmins_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিন সাব-এডমিন টিম পরিচালনা করতে পারেন!", show_alert=True)
        return
    await call.answer()
    
    subadmins = db.get_all_sub_admins()
    text = (
        "👑 **সাব-এডমিন ও টিম পারমিশন প্যানেল (RBAC Manager)**\n\n"
        "এখানে আপনি আপনার টিমের সদস্যদের সাব-এডমিন হিসেবে যুক্ত করতে পারবেন এবং প্রতিটি সদস্যকে আলাদা আলাদা অনুমতি দিতে পারবেন।\n"
        "যাকে যে অনুমতি (ON) করবেন, সে কেবল সেই ফিচারগুলো পরিচালনা করতে পারবে।\n\n"
        f"👥 **বর্তমান সাব-এডমিন সংখ্যা:** `{len(subadmins)}` জন\n\n"
        "👇 নতুন কাউকে যুক্ত করতে অথবা পারমিশন এডিট করতে নিচে সিলেক্ট করুন:"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_subadmins_list_kb(subadmins),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "subadm_add_prompt")
async def handle_subadm_add_prompt(call: CallbackQuery, state: FSMContext):
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিনের অনুমতি আছে!", show_alert=True)
        return
    await call.answer()
    await state.set_state(SubAdminState.waiting_for_user_id)
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Cancel", callback_data="admin_subadmins_menu")
    ]])
    await call.message.edit_text(
        "➕ **নতুন সাব-এডমিন যুক্ত করুন**\n\n"
        "যাকে সাব-এডমিন বানাতে চান, তার **Telegram User ID** পাঠান (অথবা তার যেকোনো মেসেজ এখানে ফরওয়ার্ড করুন):\n\n"
        "_(ইউজার আইডি পেতে ইউজারকে বলুন @userinfobot এ স্টার্ট দিতে অথবা ড্যাশবোর্ডের `/find` দিয়ে খুঁজে নিতে পারেন)_",
        reply_markup=cancel_kb,
        parse_mode="Markdown"
    )

@router.message(SubAdminState.waiting_for_user_id)
async def handle_subadm_user_id_input(message: Message, state: FSMContext, bot: Bot):
    if not is_super_admin(message.from_user.id):
        await state.clear()
        return

    text_input = message.text.strip() if message.text else ""
    target_id = None
    target_name = ""
    target_uname = ""
    
    if message.forward_from:
        target_id = message.forward_from.id
        target_name = message.forward_from.first_name or ""
        target_uname = message.forward_from.username or ""
    elif text_input.isdigit():
        target_id = int(text_input)
    else:
        clean_u = text_input.lstrip("@").strip()
        user_row = db.get_user_by_username(clean_u)
        if user_row:
            target_id = user_row["user_id"]
            target_name = user_row.get("first_name", "")
            target_uname = user_row.get("username", "")
        else:
            await message.answer("⚠️ সঠিক Telegram User ID দিন (যেমন: `123456789`) অথবা ফরওয়ার্ড মেসেজ পাঠান।", reply_markup=get_cancel_fsm_kb())
            return

    if is_super_admin(target_id):
        await message.answer("⚠️ এই ইউজার ইতিমধ্যে প্রধান সুপার এডমিন হিসেবে আছেন!")
        await state.clear()
        return

    if not target_name or not target_uname:
        db_u = db.get_user(target_id)
        if db_u:
            target_name = target_name or db_u.get("first_name", "")
            target_uname = target_uname or db_u.get("username", "")
        if not target_name:
            try:
                tg_chat = await bot.get_chat(target_id)
                target_name = tg_chat.first_name or ""
                target_uname = tg_chat.username or ""
            except Exception:
                target_name = f"Staff-{target_id}"

    db.add_sub_admin(
        user_id=target_id,
        name=target_name,
        username=target_uname,
        added_by=message.from_user.id,
        can_manage_free_drops=1,
        can_manage_stock=0,
        can_manage_products=0,
        can_approve_deposits=0,
        can_manage_resellers=0,
        can_broadcast=0,
        can_manage_users=0,
        can_manage_coupons=0
    )
    await state.clear()
    
    sub = db.get_sub_admin(target_id)
    
    try:
        await bot.send_message(
            target_id,
            "🎉 **অভিনন্দন! আপনাকে ProAccess বটে সাব-এডমিন হিসেবে নিযুক্ত করা হয়েছে!**\n\n"
            "আপনার অনুমোদিত কন্ট্রোল প্যানেল দেখতে /admin কমান্ড দিন।",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ **সফলভাবে সাব-এডমিন যুক্ত করা হয়েছে!**\n\n"
        f"👤 নাম: **{target_name}**\n"
        f"🆔 আইডি: `{target_id}`\n"
        f"🔗 ইউজারনেম: `@{target_uname or 'N/A'}`\n\n"
        f"ডিফল্টভাবে **ফ্রি ড্রপস (Free Drops)** অনুমতি চালু করা হয়েছে।\n"
        f"অন্যান্য পারমিশন চালু বা বন্ধ করতে নিচের সুইচগুলো ব্যবহার করুন:",
        reply_markup=get_subadmin_detail_kb(sub),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("subadm_view:"))
async def handle_subadm_view(call: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিনের অনুমতি আছে!", show_alert=True)
        return
    await call.answer()
    
    target_id = int(call.data.split(":")[1])
    sub = db.get_sub_admin(target_id)
    if not sub:
        await call.answer("সাব-এডমিন পাওয়া যায়নি!", show_alert=True)
        return
    
    display_name = sub.get("name") or "Staff Member"
    u_tag = f"@{sub['username']}" if sub.get("username") else "N/A"
    
    text = (
        f"👤 **সাব-এডমিন প্রোফাইল: {display_name}**\n"
        f"🆔 ইউজার আইডি: `{target_id}`\n"
        f"🔗 ইউজারনেম: `{u_tag}`\n"
        f"📅 নিয়োগের তারিখ: `{sub.get('created_at', 'N/A')}`\n\n"
        "⚙️ **অনুমতি তালিকা (Role Permissions):**\n"
        "সবুজ (✅) মানে চালু, লাল (❌) মানে বন্ধ। ট্যাপ করে যেকোনো পারমিশন চালু বা বন্ধ করুন:"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_subadmin_detail_kb(sub),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("subadm_perm_tgl:"))
async def handle_subadm_perm_toggle(call: CallbackQuery):
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিনের অনুমতি আছে!", show_alert=True)
        return
    parts = call.data.split(":")
    target_id = int(parts[1])
    perm_key = parts[2]
    
    new_state = db.toggle_admin_permission(target_id, perm_key)
    perm_labels = {
        "can_manage_free_drops": "ফ্রি ড্রপস/লুট",
        "can_manage_stock": "স্টক অন/অফ",
        "can_manage_products": "কোর্স ও ক্যাটাগরি",
        "can_approve_deposits": "ডিপোজিট অনুমোদন",
        "can_manage_resellers": "রিসেলার রাডার",
        "can_broadcast": "ব্রডকাস্ট ও চ্যানেল",
        "can_manage_users": "ইউজার ব্যালেন্স",
        "can_manage_coupons": "ডিসকাউন্ট কুপন"
    }
    label = perm_labels.get(perm_key, perm_key)
    toast = f"✅ '{label}' অনুমতি চালু করা হয়েছে!" if new_state else f"⚠️ '{label}' অনুমতি বন্ধ করা হয়েছে!"
    await call.answer(toast, show_alert=False)
    
    sub = db.get_sub_admin(target_id)
    if not sub:
        return
    
    display_name = sub.get("name") or "Staff Member"
    u_tag = f"@{sub['username']}" if sub.get("username") else "N/A"
    
    text = (
        f"👤 **সাব-এডমিন প্রোফাইল: {display_name}**\n"
        f"🆔 ইউজার আইডি: `{target_id}`\n"
        f"🔗 ইউজারনেম: `{u_tag}`\n"
        f"📅 নিয়োগের তারিখ: `{sub.get('created_at', 'N/A')}`\n\n"
        "⚙️ **অনুমতি তালিকা (Role Permissions):**\n"
        "সবুজ (✅) মানে চালু, লাল (❌) মানে বন্ধ। ট্যাপ করে যেকোনো পারমিশন চালু বা বন্ধ করুন:"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=get_subadmin_detail_kb(sub),
            parse_mode="Markdown"
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("subadm_remove_confirm:"))
async def handle_subadm_remove_confirm(call: CallbackQuery):
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিনের অনুমতি আছে!", show_alert=True)
        return
    await call.answer()
    target_id = int(call.data.split(":")[1])
    sub = db.get_sub_admin(target_id)
    if not sub:
        await call.answer("সাব-এডমিন পাওয়া যায়নি!", show_alert=True)
        return
    
    name = sub.get("name") or str(target_id)
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ হ্যাঁ, নিশ্চিত রিমুভ করুন", callback_data=f"subadm_remove:{target_id}"),
            InlineKeyboardButton(text="❌ বাতিল", callback_data=f"subadm_view:{target_id}")
        ]
    ])
    await call.message.edit_text(
        f"⚠️ **আপনি কি নিশ্চিত যে `{name}` (ID: `{target_id}`) কে সাব-এডমিন থেকে বাতিল করবেন?**\n\n"
        "বাতিল করার পর তিনি আর কোনো এডমিন সুবিধা বা প্যানেল দেখতে পাবেন না।",
        reply_markup=confirm_kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("subadm_remove:"))
async def handle_subadm_remove(call: CallbackQuery):
    if not is_super_admin(call.from_user.id):
        await call.answer("⛔ কেবল সুপার এডমিনের অনুমতি আছে!", show_alert=True)
        return
    target_id = int(call.data.split(":")[1])
    db.remove_sub_admin(target_id)
    await call.answer("🗑️ সাব-এডমিন সফলভাবে বাতিল করা হয়েছে!", show_alert=True)
    
    subadmins = db.get_all_sub_admins()
    text = (
        "👑 **সাব-এডমিন ও টিম পারমিশন প্যানেল (RBAC Manager)**\n\n"
        "সদস্যকে সফলভাবে রিমুভ করা হয়েছে।\n\n"
        f"👥 **বর্তমান সাব-এডমিন সংখ্যা:** `{len(subadmins)}` জন\n\n"
        "👇 নতুন কাউকে যুক্ত করতে অথবা পারমিশন এডিট করতে নিচে সিলেক্ট করুন:"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_subadmins_list_kb(subadmins),
        parse_mode="Markdown"
    )
