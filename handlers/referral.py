# User Referral Hub and Viral Growth Engine Handlers
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db import db
from keyboards.user_kb import get_referral_hub_kb
from utils.ui_nav import render_screen, get_cached_bot_info
from utils.i18n import t

router = Router()

@router.message(Command("referral"))
@router.message(Command("ref"))
@router.message(F.text.in_([
    "Refer & Earn (ফ্রি কোর্স)", "👥 Refer & Earn (ফ্রি কোর্স)", "Refer & Earn", "👥 Refer & Earn", 
    "রেফার এবং ইনকাম", "👥 রেফার এবং ইনকাম", "Refer & Earn (Free Courses)", "👥 Refer & Earn (Free Courses)", 
    "রেফার এবং ইনকাম (Free Courses)", "👥 রেফার এবং ইনকাম (Free Courses)", "रेफर और कमाएं (Free Courses)", "👥 रेफर और कमाएं (Free Courses)", "রেফারেল", "রেফার"
]))
@router.callback_query(F.data == "nav_referral")
async def handle_referral_hub(event: Message | CallbackQuery, bot: Bot, state: FSMContext = None):
    if state:
        await state.clear()
    user_id = event.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, event.from_user.username, event.from_user.first_name)
        
    lang = db.get_user_language(user_id)
    stats = db.get_referral_stats(user_id)
    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    t1_bonus = stats.get("t1_bonus", 10.0)
    t2_bonus = round(t1_bonus * (stats.get("t2_pct", 50.0) / 100.0), 2)
    
    badges = {
        0: "🌱 Newbie Promoter",
        1: "🥉 Bronze Star",
        2: "🥈 Silver VIP",
        3: "🥇 Gold Ambassador"
    }
    badge_title = badges.get(stats.get("milestone_tier", 0), "🌱 Newbie Promoter")
    
    if lang == "en":
        text = (
            "🌟 <b>Referral Hub & Free Reward Center</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>Your Personal Referral Link:</b>\n"
            f"<code>{ref_link}</code>\n"
            "<i>(Tap code to copy or click the buttons below)</i>\n\n"
            "📊 <b>Your Live Performance & Balance:</b>\n"
            f"▫️ 👥 Direct Members (Tier-1): <b>{stats.get('t1_count', 0)} users</b> (Per invite: <code>+৳{t1_bonus:.0f}</code>)\n"
            f"▫️ 🌐 Passive Team (Tier-2): <b>{stats.get('t2_count', 0)} users</b> (Half bonus: <code>+৳{t2_bonus:.2f}</code>)\n"
            f"▫️ 💰 Total Earned from Referrals: <b>৳{stats.get('total_earned', 0.0):.2f} BDT</b>\n"
            f"▫️ 💳 Current Wallet Balance: <b>৳{stats.get('balance_bdt', 0.0):.2f} BDT</b>\n\n"
            f"🎖️ <b>Your Current Badge:</b> {badge_title}\n"
            f"🎯 <b>Next Milestone:</b> {stats.get('next_title')} ({stats.get('next_target')} users)\n"
            f"⚡ <b>Milestone Progress:</b> <code>{stats.get('progress_bar')}</code>\n"
            f"🎁 <i>(Only {stats.get('needed', 0)} more referrals to unlock extra +৳{stats.get('next_bonus', 0)} BDT bounty!)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>How to get free courses and digital tools?</b>\n"
            "1️⃣ Share your referral link with friends or groups.\n"
            f"2️⃣ When they join, you earn direct bonus and they receive a <b>৳{int(stats.get('welcome_bonus', 5.0))} BDT</b> welcome gift!\n"
            "3️⃣ As your team grows, you earn passive 50% commission for every indirect join.\n"
            "4️⃣ Use your earned wallet balance to instantly unlock any course from the catalog!"
        )
    else:
        text = (
            "🌟 <b>রেফারেল হাব ও ফ্রি রিওয়ার্ড আর্নিং সেন্টার</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>আপনার পার্সোনাল রেফারেল লিংক:</b>\n"
            f"<code>{ref_link}</code>\n"
            "<i>(ট্যাপ করলেই লিংক কপি হবে অথবা নিচের বাটনে চাপুন)</i>\n\n"
            "📊 <b>আপনার লাইভ পারফরম্যান্স ও ব্যালেন্স:</b>\n"
            f"▫️ 👥 সরাসরি মেম্বার (Tier-1): <b>{stats.get('t1_count', 0)} জন</b> (প্রতি রেফারে <code>+৳{t1_bonus:.0f}</code>)\n"
            f"▫️ 🌐 প্যাসিভ টিম মেম্বার (Tier-2): <b>{stats.get('t2_count', 0)} জন</b> (হাফ কমিশন <code>+৳{t2_bonus:.2f}</code>)\n"
            f"▫️ 💰 রেফারেল থেকে মোট আয়: <b>৳{stats.get('total_earned', 0.0):.2f} BDT</b>\n"
            f"▫️ 💳 বর্তমান ওয়ালেট ব্যালেন্স: <b>৳{stats.get('balance_bdt', 0.0):.2f} BDT</b>\n\n"
            f"🎖️ <b>আপনার বর্তমান ব্যাজ:</b> {badge_title}\n"
            f"🎯 <b>পরবর্তী মাইলস্টোন:</b> {stats.get('next_title')} ({stats.get('next_target')} জন)\n"
            f"⚡ <b>মাইলস্টোন প্রগ্রেস:</b> <code>{stats.get('progress_bar')}</code>\n"
            f"🎁 <i>(আর মাত্র {stats.get('needed', 0)} টি রেফারেল করলেই পাবেন এক্সট্রা +৳{stats.get('next_bonus', 0)} BDT ক্যাশ বাউন্টি!)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>কীভাবে কোর্স ও ডিজিটাল টুলস ফ্রিতে নিবেন?</b>\n"
            "1️⃣ নিচের বাটন দিয়ে বন্ধুদের সাথে আপনার রেফারেল লিংক শেয়ার করুন।\n"
            f"2️⃣ বন্ধু জয়েন করলেই আপনি পাবেন ডিরেক্ট বোনাস, এবং বন্ধু পাবে <b>৳{int(stats.get('welcome_bonus', 5.0))} BDT</b> গিফট!\n"
            "3️⃣ আপনার টিম বড় হলে প্রতি জয়েনিংয়ে পাবেন আজীবন ৫০% টিম কমিশন।\n"
            "4️⃣ অর্জিত ব্যালেন্স দিয়ে ক্যাটালগ থেকে যেকোনো কোর্স বা অ্যাকাউন্ট ইনস্ট্যান্ট আনলক করুন!"
        )
    
    kb = get_referral_hub_kb(bot_username, user_id, lang=lang)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer()
        await render_screen(event, text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("copy_ref:"))
async def handle_copy_ref_callback(call: CallbackQuery, bot: Bot):
    user_id = int(call.data.split(":")[1])
    lang = db.get_user_language(call.from_user.id)
    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    alert_txt = f"📋 Your referral link:\n{ref_link}" if lang == "en" else f"📋 আপনার রেফারেল লিংক:\n{ref_link}"
    await call.answer(alert_txt, show_alert=True)

@router.callback_query(F.data == "ref_leaderboard")
async def handle_referral_leaderboard(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    leaders = db.get_referral_leaderboard(limit=10)
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    if lang == "en":
        text = (
            "🏆 <b>Top Referral Leaderboard (Hall of Fame)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Live ranking of top promoters:\n\n"
        )
        if not leaders:
            text += "🌱 <i>No leaderboard records yet. Be the first to invite friends and top the charts!</i>\n"
        else:
            for idx, u in enumerate(leaders):
                medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
                uname = f"@{u['username']}" if u.get("username") else (u.get("first_name") or "User")
                t1 = u.get("referral_count_t1") or 0
                t2 = u.get("referral_count_t2") or 0
                earned = u.get("referral_earnings_bdt") or 0.0
                text += f"{medal} <b>{uname}</b>\n   👥 Direct: <code>{t1}</code> | 🌐 Team: <code>{t2}</code> | 💰 Earned: <code>৳{earned:.0f}</code>\n\n"
        text += (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 <i>Invite more friends to climb the leaderboard and unlock exclusive rewards!</i>"
        )
    else:
        text = (
            "🏆 <b>টপ রেফারেল লিডারবোর্ড (হল অব ফেম)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "সর্বোচ্চ রেফারেল অর্জনকারীদের লাইভ তালিকা:\n\n"
        )
        if not leaders:
            text += "🌱 <i>এখনও কোনো রেফারেল প্রতিযোগিতা শুরু হয়নি। আপনিই প্রথম রেফার করে শীর্ষে উঠুন!</i>\n"
        else:
            for idx, u in enumerate(leaders):
                medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
                uname = f"@{u['username']}" if u.get("username") else (u.get("first_name") or "User")
                t1 = u.get("referral_count_t1") or 0
                t2 = u.get("referral_count_t2") or 0
                earned = u.get("referral_earnings_bdt") or 0.0
                text += f"{medal} <b>{uname}</b>\n   👥 ডিরেক্ট: <code>{t1} জন</code> | 🌐 টিম: <code>{t2} জন</code> | 💰 আয়: <code>৳{earned:.0f}</code>\n\n"
        text += (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 <i>বেশি বেশি রেফার করুন এবং লিডারবোর্ডের শীর্ষে উঠে বিশেষ রিওয়ার্ড আনলক করুন!</i>"
        )
    
    from utils.emojis import make_custom_button
    buttons = [
        [
            make_custom_button(text=t("btn_back", lang), callback_data="nav_referral", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data.startswith("copy_ref"))
async def handle_copy_ref_callback(call: CallbackQuery, bot: Bot):
    lang = db.get_user_language(call.from_user.id)
    bot_info = await get_cached_bot_info(bot)
    bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{call.from_user.id}"
    alert_txt = f"📋 Your referral link:\n{ref_link}" if lang == "en" else f"📋 পার্সোনাল রেফারেল লিংক:\n{ref_link}"
    await call.answer(alert_txt, show_alert=True)

# --- REFERRAL POINTS & CURRENCY CONVERSIONS ---
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import get_live_usd_rate
from keyboards.user_kb import (
    get_points_conversion_kb,
    get_bdt_usd_conversion_kb
)
from utils.emojis import make_custom_button, em_tag

class ConversionState(StatesGroup):
    waiting_for_points = State()
    waiting_for_bdt = State()

@router.callback_query(F.data == "profile_conv_points")
async def handle_profile_conv_points(call: CallbackQuery):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    lang = db.get_user_language(user_id)
    available_points = user.get("referral_points", 0) or 0
    rate_bdt = float(db.get_setting("referral_t1_bonus", "10.0"))
    
    if available_points <= 0:
        alert_msg = "⚠️ You currently have no referral points!" if lang == "en" else "⚠️ আপনার কাছে বর্তমানে কোনো রেফারেল পয়েন্ট নেই!"
        await call.answer(alert_msg, show_alert=True)
        if lang == "en":
            no_pts_text = (
                "⚠️ <b>You currently have no referral points!</b>\n\n"
                "Share your referral link with friends or clients to earn points. "
                "Earned points can be converted directly into wallet balance or used to purchase courses!\n\n"
                f"• Per successful invite: <b>+1 Point</b> (Value: ৳{int(rate_bdt)} BDT)"
            )
            buttons = [
                [
                    make_custom_button(text="👥 Get Referral Link", callback_data="nav_referral", emoji_key="referral")
                ],
                [
                    make_custom_button(text=t("btn_profile", lang), callback_data="profile_refresh", emoji_key="back"),
                    make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
                ]
            ]
        else:
            no_pts_text = (
                "⚠️ <b>আপনার কাছে বর্তমানে কোনো রেফারেল পয়েন্ট নেই!</b>\n\n"
                "বন্ধু বা ক্লায়েন্টদের আপনার রেফারেল লিংক শেয়ার করে প্রতি রেফারে পয়েন্ট আর্ন করুন। "
                "অর্জিত পয়েন্ট সরাসরি ওয়ালেট ব্যালেন্সে কনভার্ট করা যায় অথবা পয়েন্ট দিয়ে সরাসরি কোর্স কেনা যায়!\n\n"
                f"• প্রতি সফল রেফারে: <b>+1 Point</b> (মূল্য: ৳{int(rate_bdt)} BDT)"
            )
            buttons = [
                [
                    make_custom_button(text="👥 রেফারেল লিংক নিন", callback_data="nav_referral", emoji_key="referral")
                ],
                [
                    make_custom_button(text="🔙 প্রোফাইল (Back)", callback_data="profile_refresh", emoji_key="back"),
                    make_custom_button(text="🏠 মূল মেনু (Home)", callback_data="main_menu", emoji_key="home")
                ]
            ]
        await render_screen(call, no_pts_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
        return

    await call.answer()
    kb = get_points_conversion_kb(available_points, rate_bdt, lang=lang)
    if lang == "en":
        text = (
            "💱 <b>Referral Points ➔ Cash (BDT) Conversion</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Convert your referral points directly to BDT wallet balance:\n\n"
            f"• Exchange Rate: <b>1 Point = ৳{int(rate_bdt)} BDT</b>\n"
            f"• Available Points: <b>{available_points} Pts</b>\n"
            f"• Potential Cash: <b>৳{int(available_points * rate_bdt)} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Select how many points to convert into cash:"
        )
    else:
        text = (
            "💱 <b>রেফারেল পয়েন্ট ➔ টাকা (BDT) কনভার্সন</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার রেফারেল পয়েন্ট সরাসরি BDT ওয়ালেট ব্যালেন্সে রূপান্তর করে ক্যাশ তৈরি করুন:\n\n"
            f"• বর্তমান রূপান্তর হার: <b>1 Point = ৳{int(rate_bdt)} BDT</b>\n"
            f"• আপনার বর্তমান পয়েন্ট: <b>{available_points} Pts</b>\n"
            f"• সম্ভাব্য মোট ক্যাশ: <b>৳{int(available_points * rate_bdt)} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 কত পয়েন্ট টাকায় রূপান্তর করতে চান নিচের অপশন থেকে বেছে নিন:"
        )
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("do_conv_pts:"))
async def handle_execute_points_conversion(call: CallbackQuery):
    param = call.data.split(":")[1]
    user_id = call.from_user.id
    user = db.get_user(user_id)
    lang = db.get_user_language(user_id)
    available_points = user.get("referral_points", 0) or 0
    
    if param == "all":
        pts = available_points
    else:
        try:
            pts = int(param)
        except ValueError:
            await call.answer("❌ Invalid request!" if lang == "en" else "❌ ভুল রিকোয়েস্ট!", show_alert=True)
            return

    if pts <= 0 or pts > available_points:
        alert_pts = f"❌ Insufficient points! You have {available_points} Pts." if lang == "en" else f"❌ অপর্যাপ্ত পয়েন্ট! আপনার আছে {available_points} Pts।"
        await call.answer(alert_pts, show_alert=True)
        return

    result = db.convert_referral_points_to_bdt(user_id, pts)
    if not result:
        alert_fail = "❌ Conversion failed. Please try again." if lang == "en" else "❌ কনভার্সন ব্যর্থ হয়েছে। আবার চেষ্টা করুন।"
        await call.answer(alert_fail, show_alert=True)
        return

    alert_succ = "🎉 Points successfully converted to cash!" if lang == "en" else "🎉 পয়েন্ট সফলভাবে টাকায় কনভার্ট হয়েছে!"
    await call.answer(alert_succ, show_alert=True)
    if lang == "en":
        text = (
            "🎉 <b>Points Conversion Successful!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Converted Points: <b>{result['points_converted']} Pts</b>\n"
            f"• Credited to Wallet: <b>+৳{result['bdt_credited']:.2f} BDT</b>\n"
            f"• Exchange Rate: <b>৳{result['rate_used']:.2f} / Point</b>\n"
            f"• Remaining Points: <b>{result['remaining_points']} Pts</b>\n"
            f"• New BDT Wallet Balance: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ You can now use your balance to buy any premium course!"
        )
    else:
        text = (
            "🎉 <b>পয়েন্ট কনভার্সন সফল হয়েছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• রূপান্তরকৃত পয়েন্ট: <b>{result['points_converted']} Pts</b>\n"
            f"• ওয়ালেটে যোগ হয়েছে: <b>+৳{result['bdt_credited']:.2f} BDT</b>\n"
            f"• এক্সচেঞ্জ রেট: <b>৳{result['rate_used']:.2f} / Point</b>\n"
            f"• অবশিষ্ট পয়েন্ট: <b>{result['remaining_points']} Pts</b>\n"
            f"• নতুন BDT ওয়ালেট ব্যালেন্স: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ এখন এই টাকা দিয়ে শপ থেকে যেকোনো প্রিমিয়াম কোর্স কিনতে পারেন!"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_profile", lang), callback_data="profile_refresh", emoji_key="profile"),
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data == "conv_pts_custom")
async def handle_conv_pts_custom_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(ConversionState.waiting_for_points)
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    if lang == "en":
        text = (
            "✏️ <b>Custom Points Conversion</b>\n\n"
            "Type the number of points you want to convert into cash (BDT):\n"
            "<i>(Example: 3 or 7)</i>"
        )
    else:
        text = (
            "✏️ <b>কাস্টম পয়েন্ট রূপান্তর</b>\n\n"
            "আপনি কত পয়েন্ট টাকায় (BDT) কনভার্ট করতে চান তা সংখ্যা লিখে পাঠান:\n"
            "<i>(উদাহরণস্বরূপ: 3 বা 7)</i>"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.message(ConversionState.waiting_for_points)
async def handle_conv_pts_custom_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    if not message.text or not message.text.strip().isdigit():
        err_msg = "❌ Please enter whole numbers only (e.g. 5):" if lang == "en" else "❌ অনুগ্রহ করে শুধুমাত্র পূর্ণসংখ্যা (যেমন: 5) লিখে পাঠান:"
        await message.answer(err_msg)
        return
    pts = int(message.text.strip())
    user = db.get_user(user_id)
    available_points = user.get("referral_points", 0) or 0
    if pts <= 0 or pts > available_points:
        insuf_msg = f"❌ Insufficient points! Your current balance: <b>{available_points} Pts</b>. Enter number again:" if lang == "en" else f"❌ অপর্যাপ্ত পয়েন্ট! আপনার বর্তমান ব্যালেন্স: <b>{available_points} Pts</b>। পুনরায় সংখ্যা লিখুন:"
        await message.answer(insuf_msg)
        return

    result = db.convert_referral_points_to_bdt(user_id, pts)
    await state.clear()
    if not result:
        fail_msg = "❌ Could not complete conversion. Please try again later." if lang == "en" else "❌ কনভার্সন সম্পন্ন করা যায়নি। অনুগ্রহ করে পরে চেষ্টা করুন।"
        await message.answer(fail_msg)
        return

    if lang == "en":
        text = (
            "🎉 <b>Points Conversion Successful!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Converted Points: <b>{result['points_converted']} Pts</b>\n"
            f"• Credited to Wallet: <b>+৳{result['bdt_credited']:.2f} BDT</b>\n"
            f"• Remaining Points: <b>{result['remaining_points']} Pts</b>\n"
            f"• New BDT Balance: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ Balance added, you can now purchase any course instantly."
        )
    else:
        text = (
            "🎉 <b>পয়েন্ট কনভার্সন সফল হয়েছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• রূপান্তরকৃত পয়েন্ট: <b>{result['points_converted']} Pts</b>\n"
            f"• ওয়ালেটে যোগ হয়েছে: <b>+৳{result['bdt_credited']:.2f} BDT</b>\n"
            f"• অবশিষ্ট পয়েন্ট: <b>{result['remaining_points']} Pts</b>\n"
            f"• নতুন BDT ব্যালেন্স: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ ব্যালেন্স যোগ হয়েছে, আপনি যেকোনো কোর্স এখনই কিনতে পারবেন।"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_profile", lang), callback_data="profile_refresh", emoji_key="profile"),
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data == "profile_conv_usd")
async def handle_profile_conv_usd(call: CallbackQuery):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
    lang = db.get_user_language(user_id)
    bal_bdt = float(user.get("balance_bdt") or 0.0)
    live_rate = get_live_usd_rate()

    if bal_bdt < 10.0:
        alert_msg = "⚠️ Insufficient BDT balance (minimum ৳10 required)!" if lang == "en" else "⚠️ আপনার BDT ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই (ন্যূনতম ৳১০ প্রয়োজন)!"
        await call.answer(alert_msg, show_alert=True)
        return

    await call.answer()
    kb = get_bdt_usd_conversion_kb(bal_bdt, live_rate, lang=lang)
    if lang == "en":
        text = (
            "💵 <b>BDT ➔ USD Wallet Conversion</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Convert your local BDT balance to USD at live market rate:\n\n"
            f"• Live Exchange Rate: <b>$1.00 USD = ৳{int(live_rate)} BDT</b>\n"
            f"• Current BDT Balance: <b>৳{bal_bdt:.2f} BDT</b>\n"
            f"• Potential USD Value: <b>${bal_bdt/live_rate:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Choose a quick conversion option below or enter custom amount:"
        )
    else:
        text = (
            "💵 <b>টাকা (BDT) ➔ ডলার (USD) ওয়ালেট কনভার্সন</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার BDT ব্যালেন্স লাইভ রেটে আন্তর্জাতিক ডলারে রূপান্তর করুন:\n\n"
            f"• লাইভ এক্সচেঞ্জ রেট: <b>$1.00 USD = ৳{int(live_rate)} BDT</b>\n"
            f"• আপনার BDT ব্যালেন্স: <b>৳{bal_bdt:.2f} BDT</b>\n"
            f"• সম্ভাব্য মোট ডলার: <b>${bal_bdt/live_rate:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 রূপান্তর করতে নিচের দ্রুত বাটন বেছে নিন অথবা কাস্টম লিখুন:"
        )
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("do_conv_usd:"))
async def handle_execute_usd_conversion(call: CallbackQuery):
    param = call.data.split(":")[1]
    user_id = call.from_user.id
    user = db.get_user(user_id)
    lang = db.get_user_language(user_id)
    bal_bdt = float(user.get("balance_bdt") or 0.0)
    live_rate = get_live_usd_rate()

    if param == "all":
        bdt_to_conv = bal_bdt
    else:
        try:
            target_usd = float(param)
            bdt_to_conv = target_usd * live_rate
        except ValueError:
            await call.answer("❌ Invalid request!" if lang == "en" else "❌ ভুল রিকোয়েস্ট!", show_alert=True)
            return

    if bdt_to_conv <= 0 or bdt_to_conv > bal_bdt:
        alert_bal = f"❌ Insufficient BDT balance! You have ৳{bal_bdt:.2f} BDT." if lang == "en" else f"❌ অপর্যাপ্ত BDT ব্যালেন্স! আপনার আছে ৳{bal_bdt:.2f} BDT।"
        await call.answer(alert_bal, show_alert=True)
        return

    result = db.convert_bdt_to_usd(user_id, bdt_to_conv)
    if not result:
        alert_fail = "❌ Conversion failed. Please try again." if lang == "en" else "❌ কনভার্সন ব্যর্থ হয়েছে। আবার চেষ্টা করুন।"
        await call.answer(alert_fail, show_alert=True)
        return

    alert_succ = "🎉 Converted BDT to USD successfully!" if lang == "en" else "🎉 টাকা সফলভাবে ডলারে রূপান্তর করা হয়েছে!"
    await call.answer(alert_succ, show_alert=True)
    if lang == "en":
        text = (
            "🎉 <b>USD Conversion Successful!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Deducted BDT: <b>-৳{result['bdt_deducted']:.2f} BDT</b>\n"
            f"• Credited USD: <b>+${result['usd_credited']:.2f} USD</b>\n"
            f"• Exchange Rate: <b>৳{result['rate_used']:.2f} / $1 USD</b>\n"
            f"• New BDT Balance: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            f"• New USD Balance: <b>${result['new_balance_usd']:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ You can now unlock any product priced in USD!"
        )
    else:
        text = (
            "🎉 <b>ডলার কনভার্সন সফল হয়েছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• কর্তনকৃত BDT: <b>-৳{result['bdt_deducted']:.2f} BDT</b>\n"
            f"• ওয়ালেটে যোগ হয়েছে: <b>+${result['usd_credited']:.2f} USD</b>\n"
            f"• ব্যবহৃত এক্সচেঞ্জ রেট: <b>৳{result['rate_used']:.2f} / $1 USD</b>\n"
            f"• নতুন BDT ব্যালেন্স: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            f"• নতুন USD ব্যালেন্স: <b>${result['new_balance_usd']:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ এখন আন্তর্জাতিক ডলারে মূল্যায়িত যেকোনো কোর্স আনলক করুন!"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_profile", lang), callback_data="profile_refresh", emoji_key="profile"),
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data == "conv_usd_custom")
async def handle_conv_usd_custom_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(ConversionState.waiting_for_bdt)
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    live_rate = get_live_usd_rate()
    if lang == "en":
        text = (
            "✏️ <b>Custom BDT ➔ USD Conversion</b>\n\n"
            f"Enter the amount in BDT you want to convert into USD:\n"
            f"<i>(Rate: $1 = ৳{int(live_rate)} BDT — Example: 125 or 250)</i>"
        )
    else:
        text = (
            "✏️ <b>কাস্টম টাকা ➔ ডলার কনভার্সন</b>\n\n"
            f"আপনি কত টাকা (BDT) ডলারে কনভার্ট করতে চান তা লিখে পাঠান:\n"
            f"<i>(রেট: $1 = ৳{int(live_rate)} BDT — উদাহরণ: 125 বা 250)</i>"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.message(ConversionState.waiting_for_bdt)
async def handle_conv_usd_custom_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    if not message.text:
        err_msg = "❌ Please enter amount in digits:" if lang == "en" else "❌ অনুগ্রহ করে টাকার পরিমাণ সংখ্যা আকারে লিখে পাঠান:"
        await message.answer(err_msg)
        return
    try:
        bdt_amount = float(message.text.strip())
    except ValueError:
        err_num = "❌ Please enter a valid number (e.g. 125):" if lang == "en" else "❌ অনুগ্রহ করে সঠিক সংখ্যা (যেমন: 125) লিখে পাঠান:"
        await message.answer(err_num)
        return

    user = db.get_user(user_id)
    bal_bdt = float(user.get("balance_bdt") or 0.0)
    if bdt_amount <= 0 or bdt_amount > bal_bdt:
        insuf_msg = f"❌ Insufficient BDT balance! Your wallet has <b>৳{bal_bdt:.2f} BDT</b>. Enter again:" if lang == "en" else f"❌ অপর্যাপ্ত BDT ব্যালেন্স! আপনার ওয়ালেটে আছে <b>৳{bal_bdt:.2f} BDT</b>। পুনরায় লিখুন:"
        await message.answer(insuf_msg)
        return

    result = db.convert_bdt_to_usd(user_id, bdt_amount)
    await state.clear()
    if not result:
        fail_msg = "❌ Could not complete conversion. Please try again later." if lang == "en" else "❌ কনভার্সন সম্পন্ন করা যায়নি। অনুগ্রহ করে পরে চেষ্টা করুন।"
        await message.answer(fail_msg)
        return

    if lang == "en":
        text = (
            "🎉 <b>USD Conversion Successful!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Deducted BDT: <b>-৳{result['bdt_deducted']:.2f} BDT</b>\n"
            f"• Credited USD: <b>+${result['usd_credited']:.2f} USD</b>\n"
            f"• New BDT Balance: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            f"• New USD Balance: <b>${result['new_balance_usd']:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = (
            "🎉 <b>ডলার কনভার্সন সফল হয়েছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• কর্তনকৃত BDT: <b>-৳{result['bdt_deducted']:.2f} BDT</b>\n"
            f"• ওয়ালেটে যোগ হয়েছে: <b>+${result['usd_credited']:.2f} USD</b>\n"
            f"• নতুন BDT ব্যালেন্স: <b>৳{result['new_balance_bdt']:.2f} BDT</b>\n"
            f"• নতুন USD ব্যালেন্স: <b>${result['new_balance_usd']:.2f} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    buttons = [
        [
            make_custom_button(text=t("btn_profile", lang), callback_data="profile_refresh", emoji_key="profile"),
            make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data == "profile_course_refs")
async def handle_profile_course_refs(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    stats = db.get_course_referral_stats(user_id)
    
    if lang == "en":
        text = (
            "📚 <b>Your Course-Specific Referral Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Detailed breakdown of members referred by specific courses:\n\n"
        )
        if not stats:
            text += (
                "🌱 <i>You haven't shared any specific course links yet.\n\n"
                "💡 Browse our Catalog, view any course, and tap <b>'🔗 Share & Earn with Link'</b> "
                "to get your unique trackable course referral link!</i>\n"
            )
        else:
            for idx, row in enumerate(stats, start=1):
                title = row.get("course_title") or f"Course #{row['course_id']}"
                cnt = row.get("referral_count") or 0
                text += f"<b>{idx}. {title}</b>\n   👥 Successful Referrals: <code>{cnt} users</code>\n\n"
    else:
        text = (
            "📚 <b>আপনার কোর্স-ভিত্তিক রেফারেল স্ট্যাটিস্টিক্স</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "কোন কোর্স শেয়ার করে আপনি কতজন মেম্বার এনেছেন তার বিস্তারিত হিসাব:\n\n"
        )
        if not stats:
            text += (
                "🌱 <i>আপনি এখনও কোনো নির্দিষ্ট কোর্সের রেফারেল লিংক শেয়ার করেননি।\n\n"
                "💡 কোর্স ক্যাটালগে গিয়ে পছন্দের কোর্সে ঢুকে <b>'🔗 এই কোর্সের রেফার লিংক'</b> বাটনে চাপ দিলে "
                "আপনার বিশেষ কোর্স লিংক পেয়ে যাবেন!</i>\n"
            )
        else:
            for idx, row in enumerate(stats, start=1):
                title = row.get("course_title") or f"কোর্স #{row['course_id']}"
                cnt = row.get("referral_count") or 0
                text += f"<b>{idx}. {title}</b>\n   👥 সফল রেফারেল: <code>{cnt} জন</code>\n\n"
            
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    buttons = [
        [make_custom_button(text=t("btn_courses", lang), callback_data="back_cats", emoji_key="courses")],
        [
            make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@router.callback_query(F.data == "profile_conv_history")
async def handle_profile_conv_history(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    history = db.get_user_conversion_history(user_id, limit=15)
    
    if lang == "en":
        text = (
            "📜 <b>Points & Currency Conversion History</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Audit ledger of your recent conversions:\n\n"
        )
        if not history:
            text += "🌱 <i>No previous conversion records found.</i>\n"
        else:
            for idx, h in enumerate(history, start=1):
                from_t = h["from_type"]
                to_t = h["to_type"]
                in_amt = h["amount_in"]
                out_amt = h["amount_out"]
                date_str = h["created_at"][:16]
                rate = h.get("rate_used") or 0.0
                
                in_fmt = f"{int(in_amt)} Pts" if from_t == "POINTS" else f"৳{in_amt:.2f} BDT"
                out_fmt = f"৳{out_amt:.2f} BDT" if to_t == "BDT" else f"${out_amt:.2f} USD"
                
                text += (
                    f"<b>#{idx} | {date_str}</b>\n"
                    f"• Conversion: <code>{in_fmt} ➔ {out_fmt}</code>\n"
                    f"• Rate: <code>{rate}</code>\n"
                    f"────────────────────────────\n"
                )
    else:
        text = (
            "📜 <b>পয়েন্ট ও কারেন্সি কনভার্সন হিস্ট্রি</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার সাম্প্রতিক রূপান্তর লেনদেনের হিসাব (Audit Ledger):\n\n"
        )
        if not history:
            text += "🌱 <i>আপনার কোনো পূর্ববর্তী কনভার্সন রেকর্ড পাওয়া যায়নি।</i>\n"
        else:
            for idx, h in enumerate(history, start=1):
                from_t = h["from_type"]
                to_t = h["to_type"]
                in_amt = h["amount_in"]
                out_amt = h["amount_out"]
                date_str = h["created_at"][:16]
                rate = h.get("rate_used") or 0.0
                
                in_fmt = f"{int(in_amt)} Pts" if from_t == "POINTS" else f"৳{in_amt:.2f} BDT"
                out_fmt = f"৳{out_amt:.2f} BDT" if to_t == "BDT" else f"${out_amt:.2f} USD"
                
                text += (
                    f"<b>#{idx} | {date_str}</b>\n"
                    f"• রূপান্তর: <code>{in_fmt} ➔ {out_fmt}</code>\n"
                    f"• রেট: <code>{rate}</code>\n"
                    f"────────────────────────────\n"
                )
            
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    buttons = [
        [
            make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    await render_screen(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

