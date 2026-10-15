# Reseller Hub and Wholesale Handler
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import html
import logging
from database.db import db
from keyboards.user_kb import get_reseller_hub_kb, get_cancel_fsm_kb, get_reseller_package_selection_kb
from config import ADMIN_USERNAME
from utils.notifier import notify_admin_reseller_app
from utils.emojis import em_tag, make_custom_button
from utils.i18n import t, localize_item_name
from utils.ui_nav import render_screen, get_cached_bot_info

logger = logging.getLogger(__name__)

router = Router()

class ResellerApplyState(StatesGroup):
    waiting_for_info = State()

async def get_reseller_hub_data(user_id: int, bot: Bot, username: str = None, first_name: str = None) -> tuple[str, InlineKeyboardMarkup]:
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, username, first_name)
        
    lang = db.get_user_language(user_id)
    is_perm_banned = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
    is_reseller = user.get("is_reseller", 0) >= 1
    min_dep = float(db.get_setting("reseller_min_deposit", "1000"))
    elite_dep = float(db.get_setting("reseller_elite_min_deposit", "2000"))
    fee = float(db.get_setting("reseller_activation_fee", "500"))
    usable_bal = max(0, int(min_dep - fee))
    quota_info = db.get_reseller_quota_info(user_id)
    
    if is_perm_banned:
        banned_texts = {
            "bn": (
                "❌ **আপনার রিসেলার অ্যাকাউন্ট স্থায়ীভাবে বাতিল (Deactivated) করা হয়েছে!**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ **কারণ:** মাসিক ন্যূনতম সেলস কোটা পূরণ করতে ব্যর্থ হয়েছেন।\n"
                "বটের পলিসি অনুযায়ী একবার অ্যাকাউন্ট ডিঅ্যাক্টিভ হলে তা আর কখনোই রিনিউ বা সক্রিয় করা যায় না।\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 আপনি সাধারণ ক্রেতা হিসেবে স্বাভাবিক মূল্যে কোর্স কিনতে পারবেন, কিন্তু পাইকারি ছাড় প্রযোজ্য হবে না।"
            ),
            "en": (
                "❌ **Your Reseller Account has been permanently deactivated!**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ **Reason:** Failed to achieve the minimum monthly sales quota.\n"
                "Per bot policy, once deactivated, reseller privileges cannot be reinstated.\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 You may still purchase courses as a regular customer, but wholesale discounts will no longer apply."
            ),
            "hi": (
                "❌ **आपका रीसेलर अकाउंट स्थायी रूप से निष्क्रिय (Deactivated) कर दिया गया है!**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ **कारण:** मासिक न्यूनतम बिक्री कोटा पूरा करने में विफल रहे।\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 आप सामान्य ग्राहक के रूप में खरीदारी कर सकते हैं, लेकिन थोक छूट लागू नहीं होगी।"
            )
        }
        return banned_texts.get(lang, banned_texts["en"]), get_reseller_hub_kb(is_banned=True, lang=lang)

    if is_reseller:
        stats = db.get_reseller_stats(user_id)
        reseller_code = user.get("reseller_code") or f"RS-{user_id % 10000:04d}"
        bot_info = await get_cached_bot_info(bot)
        bot_username = bot_info.username if bot_info else "AllInOneProAccess_bot"
        v_link = f"https://t.me/{bot_username}?start=verify_{reseller_code}"
        vip_pass = db.get_active_reseller_vip_pass(user_id)
        if vip_pass:
            vip_text_bn = (
                "🏆 <b>আপনার সক্রিয় টপ-সেলার রিওয়ার্ড পাস:</b>\n"
                f"• বিশেষ সুবিধা: পাইকারি রেটের উপরও <b>-৳{vip_pass['discount_bdt']:.0f} BDT</b> অতিরিক্ত ছাড়!\n"
                f"• অফার মেয়াদ: আর <code>{vip_pass['days_left']} দিন</code> বাকি\n"
                f"• ব্যবহারের সুযোগ: আর <code>{vip_pass['remaining_uses']} টি</code> অর্ডার বাকি\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
            )
            vip_text_en = (
                "🏆 <b>Active Top-Seller VIP Reward Pass:</b>\n"
                f"• Benefit: Extra <b>-৳{vip_pass['discount_bdt']:.0f} BDT</b> off wholesale rate!\n"
                f"• Valid for: <code>{vip_pass['days_left']} days</code> remaining\n"
                f"• Remaining uses: <code>{vip_pass['remaining_uses']} orders</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
            )
            vip_text_hi = (
                "🏆 <b>आपका सक्रिय टॉप-सेलर रिवॉर्ड पास:</b>\n"
                f"• विशेष छूट: थोक मूल्य पर भी <b>-৳{vip_pass['discount_bdt']:.0f} BDT</b> अतिरिक्त छूट!\n"
                f"• शेष दिन: <code>{vip_pass['days_left']} दिन</code>\n"
                f"• शेष उपयोग: <code>{vip_pass['remaining_uses']} ऑर्डर्स</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
            )
        else:
            vip_text_bn = "💡 <b>টপ-সেলার রিওয়ার্ড:</b> প্রতি মাসে সর্বোচ্চ সেল করা সেরা ৩ জন রিসেলার বিশেষ কুপন ও এক্সট্রা ডিসকাউন্ট পায়!\n━━━━━━━━━━━━━━━━━━━━\n"
            vip_text_en = "💡 <b>Top-Seller Reward:</b> Monthly Top 3 sellers receive exclusive extra discount VIP passes!\n━━━━━━━━━━━━━━━━━━━━\n"
            vip_text_hi = "💡 <b>टॉप-सेलर रिवॉर्ड:</b> हर महीने शीर्ष 3 सेलर्स को विशेष वीआईपी डिस्काउंट पास मिलता है!\n━━━━━━━━━━━━━━━━━━━━\n"

        tier = user.get("reseller_tier", 1) or 1
        perms = db.get_user_permissions(user_id)
        is_elite = tier >= 2 or perms.get("can_sell_account", False)
        
        tier_str_bn = "👑 Elite VIP পার্টনার (চ্যানেল + একাউন্ট)" if is_elite else "🥉 Standard পার্টনার (ভিআইপি চ্যানেল)"
        tier_str_en = "👑 Elite VIP Partner (Channel + Account)" if is_elite else "🥉 Standard Partner (VIP Channel Only)"
        tier_str_hi = "👑 Elite VIP पार्टनर (चैनल + अकाउंट)" if is_elite else "🥉 Standard पार्टनर (वीआईपी चैनल)"

        hub_texts = {
            "bn": (
                "💎 <b>ভেরিফাইড রিসেলার ড্যাশবোর্ড (Reseller Hub)</b>\n\n"
                "স্বাগতম পার্টনার! আপনি আমাদের অনুমোদিত পাইকারি রিসেলার।\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>আপনার রিসেলার কোড:</b> <code>{reseller_code}</code>\n"
                f"🎖️ <b>স্ট্যাটাস:</b> ✅ সক্রিয় রিসেলার | <code>{tier_str_bn}</code>\n"
                f"🎯 <b>চলতি মাসের সেলস:</b> <code>{quota_info['sales']} / {quota_info['target']} টি</code>\n"
                f"⏰ <b>কোটা সাইকেল বাকি:</b> <code>{quota_info['days_left']} দিন</code>\n"
                f"💰 <b>মোট সেভিংস/লাভ:</b> <code>৳{stats['total_savings_bdt']:.2f} BDT</code>\n"
                f"💳 <b>ওয়ালেট ব্যালেন্স:</b> <code>৳{user['balance_bdt']:.2f}</code> | <code>${user['balance_usd']:.2f}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"{vip_text_bn}"
                "🛡️ <b>আপনার পাবলিক ভেরিফিকেশন লিংক:</b>\n"
                f"<code>{v_link}</code>\n"
                "<i>(গ্রাহকদের ট্রাস্ট বাড়াতে এই লিংক দিন। লিংকে ঢুকলেই বট আপনার অফিসিয়াল অনুমোদন প্রমাণ করবে!)</i>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>মাসিক কোটা সতর্কতা:</b> সাইকেল শেষ হওয়ার আগে ন্যূনতম <code>{quota_info['target']}টি</code> সেল সম্পন্ন করতে হবে।\n\n"
                "👇 নিচে থেকে আপনার কাঙ্شتہ অপশন সিলেক্ট করুন:"
            ),
            "en": (
                "💎 <b>Verified VIP Reseller Dashboard</b>\n\n"
                "Welcome partner! You are an authorized wholesale reseller.\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>Reseller Code:</b> <code>{reseller_code}</code>\n"
                f"🎖️ <b>Status:</b> ✅ Active Reseller | <code>{tier_str_en}</code>\n"
                f"🎯 <b>Monthly Sales:</b> <code>{quota_info['sales']} / {quota_info['target']}</code>\n"
                f"⏰ <b>Cycle Days Left:</b> <code>{quota_info['days_left']} days</code>\n"
                f"💰 <b>Total Profit/Savings:</b> <code>৳{stats['total_savings_bdt']:.2f} BDT</code>\n"
                f"💳 <b>Wallet Balance:</b> <code>৳{user['balance_bdt']:.2f}</code> | <code>${user['balance_usd']:.2f}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"{vip_text_en}"
                "🛡️ <b>Your Public Verification Link:</b>\n"
                f"<code>{v_link}</code>\n"
                "<i>(Share with your buyers so they can verify your official license!)</i>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>Quota Notice:</b> Complete at least <code>{quota_info['target']}</code> sales before cycle ends.\n\n"
                "👇 Select an action below:"
            ),
            "hi": (
                "💎 <b>सत्यापित रीसेलर डैशबोर्ड (Reseller Hub)</b>\n\n"
                "स्वागत है पार्टनर! आप हमारे अधिकृत थोक रीसेलर हैं।\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>रीसेलर कोड:</b> <code>{reseller_code}</code>\n"
                f"🎖️ <b>स्थिति:</b> ✅ सक्रिय रीसेलर | <code>{tier_str_hi}</code>\n"
                f"🎯 <b>इस महीने की बिक्री:</b> <code>{quota_info['sales']} / {quota_info['target']}</code>\n"
                f"⏰ <b>चक्र के शेष दिन:</b> <code>{quota_info['days_left']} दिन</code>\n"
                f"💰 <b>कुल बचत/लाभ:</b> <code>৳{stats['total_savings_bdt']:.2f} BDT</code>\n"
                f"💳 <b>वॉलेट बैलेंस:</b> <code>৳{user['balance_bdt']:.2f}</code> | <code>${user['balance_usd']:.2f}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"{vip_text_hi}"
                "🛡️ <b>आपका सत्यापन लिंक:</b>\n"
                f"<code>{v_link}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "👇 नीचे दिए गए विकल्पों में से चुनें:"
            )
        }
        return hub_texts.get(lang, hub_texts["en"]), get_reseller_hub_kb(is_reseller=True, lang=lang, tier=tier)
    else:
        # Not a reseller yet
        pitch_texts = {
            "bn": (
                "🤝 <b>ভিআইপি রিসেলার প্রোগ্রাম — ঘরে বসেই আনলিমিটেড ইনকাম!</b>\n\n"
                "আমাদের সমস্ত <b>কোর্স (৯০%)</b> এবং <b>ডিজিটাল টুলস (১০%)</b> পাইকারি রেটে কিনে "
                "আপনার পেজ, গ্রুপ বা ক্লায়েন্টদের কাছে নিজের ইচ্ছামতো দামে সেল করতে পারেন!\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💎 <b>আমাদের ২টি পার্টনারশিপ প্যাকেজ:</b>\n"
                f"• 🥉 <b>Standard পার্টনার:</b> চ্যানেল এক্সেস কোর্স পাইকারি সেল (ডিপোজিট ৳{int(min_dep)})\n"
                f"• 👑 <b>Elite VIP পার্টনার:</b> ফুল এক্সেস — চ্যানেল + প্রাইভেট অ্যাকাউন্ট ও মেম্বারশিপ (ডিপোজিট ৳{int(elite_dep)})\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📈 <b>রিসেলার লাভের নমুনা:</b>\n"
                "• Premiere Pro VIP: খুচরা ৳350 ➡️ <b>রিসেলার রেট ৳245</b> (লাভ ৳105!)\n"
                "• MERN Web Dev: খুচরা ৳499 ➡️ <b>রিসেলার রেট ৳349</b> (লাভ ৳150!)\n"
                "• AI Prompt Mastery: খুচরা ৳399 ➡️ <b>রিসেলার রেট ৳279</b> (লাভ ৳120!)\n"
                "• Gemini 18M Link: খুচরা ৳75 ➡️ <b>রিসেলার রেট ৳52</b> (লাভ ৳23!)\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 <b>পার্টনারশিপ অ্যাক্টিভেশনের শর্তাবলী:</b>\n"
                f"১. ওয়ালেটে প্যাকেজ অনুযায়ী ন্যূনতম ডিপোজিট (Standard ৳{int(min_dep)} / Elite ৳{int(elite_dep)}) থাকতে হবে।\n"
                f"২. অ্যাডমিন অনুমোদনের পর <code>৳{int(fee)}</code> এককালীন ভেরিফাইড অ্যাক্টিভেশন ফি কর্তন হবে।\n"
                "৩. অবশিষ্ট ব্যালেন্স সম্পূর্ণ আপনার ওয়ালেটে থাকবে (যা দিয়ে সাথে সাথে পাইকারি রেটে কোর্স কিনবেন)।\n"
                f"৪. প্রতি মাসে ন্যূনতম <code>{quota_info['target']}টি</code> সফল সেল সম্পন্ন করতে হবে।\n"
                "৫. আপনার মার্কেটিং পেজ/গ্রুপ বা অডিয়েন্সের লিংক দিতে হবে।\n\n"
                "👇 বিস্তারিত প্যাকেজ দেখতে ও আবেদন করতে নিচে <b>📝 রিসেলার আবেদন</b> বাটনে ক্লিক করুন:"
            ),
            "en": (
                "🤝 <b>VIP Reseller Program — Unlimited Earning Potential!</b>\n\n"
                "Buy all our <b>Courses (90%)</b> and <b>Digital Tools (10%)</b> at wholesale rates "
                "and sell them to your audience at your own desired price!\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💎 <b>2 Partnership Packages Available:</b>\n"
                f"• 🥉 <b>Standard Partner:</b> Wholesale Channel Access courses (Min Deposit ৳{int(min_dep)})\n"
                f"• 👑 <b>Elite VIP Partner:</b> Full Access — Channel + Private Accounts & Logins (Min Deposit ৳{int(elite_dep)})\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📈 <b>Profit Examples:</b>\n"
                "• Premiere Pro VIP: Retail ৳350 ➡️ <b>Reseller ৳245</b> (Profit ৳105!)\n"
                "• MERN Web Dev: Retail ৳499 ➡️ <b>Reseller ৳349</b> (Profit ৳150!)\n"
                "• AI Prompt Mastery: Retail ৳399 ➡️ <b>Reseller ৳279</b> (Profit ৳120!)\n"
                "• Gemini 18M Link: Retail ৳75 ➡️ <b>Reseller ৳52</b> (Profit ৳23!)\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 <b>Activation Requirements:</b>\n"
                f"1. Minimum wallet balance per package (Standard ৳{int(min_dep)} / Elite ৳{int(elite_dep)} BDT).\n"
                f"2. Non-refundable Verified Partner Activation Fee: <code>৳{int(fee)} BDT</code> (deducted upon admin approval).\n"
                "3. Usable wholesale shopping balance remains in your wallet for purchasing courses.\n"
                f"4. Complete at least <code>{quota_info['target']}</code> sales per month.\n"
                "5. Provide marketing channel/community proof.\n\n"
                "👇 Click below to choose a package and apply:"
            ),
            "hi": (
                "🤝 <b>वीआईपी रीसेलर प्रोग्राम — घर बैठे असीमित कमाई!</b>\n\n"
                "हमारे सभी <b>कोर्सेस (90%)</b> और <b>डिजिटल टूल्स (10%)</b> थोक भाव पर खरीदें "
                "और अपनी पसंद के दाम पर बेचें!\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💎 <b>2 पार्टनरशिप पैकेज उपलब्ध हैं:</b>\n"
                f"• 🥉 <b>Standard Partner:</b> चैनल एक्सेस कोर्स थोक बिक्री (न्यूनतम ৳{int(min_dep)})\n"
                f"• 👑 <b>Elite VIP Partner:</b> पूर्ण एक्सेस — चैनल + निजी खाते और लॉगिन (न्यूनतम ৳{int(elite_dep)})\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📌 <b>सक्रियण शर्तें:</b>\n"
                f"1. वॉलेट में पैकेज अनुसार न्यूनतम बैलेंस (Standard ৳{int(min_dep)} / Elite ৳{int(elite_dep)}) होना चाहिए।\n"
                f"2. व्यवस्थापक अनुमोदन पर <code>৳{int(fee)}</code> गैर-वापसी योग्य सत्यापन शुल्क काटा जाएगा।\n"
                "3. शेष राशि आपकी थोक खरीदारी के लिए वॉलेट में उपलब्ध रहेगी।\n"
                f"4. प्रति माह न्यूनतम <code>{quota_info['target']}</code> बिक्री करनी होगी।\n"
                "5. मार्केटिंग पेज/ग्रुप का प्रमाण देना होगा।\n\n"
                "👇 आवेदन करने या पैकेज चुनने के लिए नीचे क्लिक करें:"
            )
        }
        return pitch_texts.get(lang, pitch_texts["en"]), get_reseller_hub_kb(is_reseller=False, lang=lang)

@router.message(F.text.in_([
    "Reseller Hub (রিসেলার প্যানেল)", "🤝 Reseller Hub (রিসেলার প্যানেল)", "Reseller Hub", "🤝 Reseller Hub", 
    "🤝 রিসেলার হাব", "রিসেলার হাব", "🤝 रीसेलर हब", "रीसेलर हब",
    "रीसेलर हब (Reseller Hub)", "🤝 रीसेलर हब (Reseller Hub)", "রিসেলার প্যানেল", "রিসেলার",
    "🤝 Reseller Hub (রিসেলার)", "Reseller Hub (রিসেলার)"
]))
async def handle_reseller_hub(message: Message):
    text, kb = await get_reseller_hub_data(
        message.from_user.id,
        message.bot,
        message.from_user.username,
        message.from_user.first_name
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "reseller_pricelist")
async def handle_reseller_pricelist(call: CallbackQuery):
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    products = db.get_all_active_products()
    
    if not products:
        alert_msg = "⚠️ No products loaded currently." if lang in ["en", "hi", "ur"] else "⚠️ বর্তমানে কোনো প্রোডাক্ট লোড করা নেই।"
        await call.answer(alert_msg, show_alert=True)
        return
        
    em_dia = em_tag("diamond", "💎")
    if lang in ["en", "hi", "ur"]:
        text = (
            f"{em_dia} <b>Reseller Wholesale Price List</b> {em_dia}\n\n"
            "<i>Comparison between regular retail prices and your wholesale rates:</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for idx, p in enumerate(products, start=1):
            clean_title = localize_item_name(p['title'], lang)
            ch_p = float(p.get("price_channel_bdt") or 0)
            acc_p = float(p.get("price_account_bdt") or 0)
            eff_bdt = ch_p if (ch_p > 0 and acc_p <= 0) else (acc_p if (acc_p > 0 and ch_p <= 0) else float(p.get("price_bdt") or 0))
            if eff_bdt <= 0 and (ch_p > 0 or acc_p > 0):
                eff_bdt = ch_p if ch_p > 0 else acc_p
            reg_bdt = int(eff_bdt)
            res_bdt = int(p["reseller_price_bdt"]) if p.get("reseller_price_bdt") else int(reg_bdt * 0.70)
            profit = reg_bdt - res_bdt
            text += (
                f"<b>#{idx} | {html.escape(clean_title)}</b>\n"
                f"🏷️ Retail Price: <code>৳{reg_bdt} BDT</code>\n"
                f"{em_dia} <b>Wholesale Price:</b> <b>৳{res_bdt} BDT</b> <i>(Profit: ৳{profit}!)</i>\n"
                "────────────────────────────\n"
            )
        text += "\n⚡ <b>Official Perk:</b> You can purchase at wholesale prices and resell to your clients at your own pricing."
    else:
        text = (
            f"{em_dia} <b>রিসেলার পাইকারি মূল্য তালিকা (Wholesale Price List)</b> {em_dia}\n\n"
            "<i>প্রতিটি প্রোডাক্টের সাধারণ খুচরা ও রিসেলার পাইকারি রেটের তুলনামূলক চার্ট:</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for idx, p in enumerate(products, start=1):
            ch_p = float(p.get("price_channel_bdt") or 0)
            acc_p = float(p.get("price_account_bdt") or 0)
            eff_bdt = ch_p if (ch_p > 0 and acc_p <= 0) else (acc_p if (acc_p > 0 and ch_p <= 0) else float(p.get("price_bdt") or 0))
            if eff_bdt <= 0 and (ch_p > 0 or acc_p > 0):
                eff_bdt = ch_p if ch_p > 0 else acc_p
            reg_bdt = int(eff_bdt)
            res_bdt = int(p["reseller_price_bdt"]) if p.get("reseller_price_bdt") else int(reg_bdt * 0.70)
            profit = reg_bdt - res_bdt
            text += (
                f"<b>#{idx} | {html.escape(p['title'])}</b>\n"
                f"🏷️ সাধারণ খুচরা রেট: <code>৳{reg_bdt} BDT</code>\n"
                f"{em_dia} <b>রিসেলার পাইকারি রেট:</b> <b>৳{res_bdt} BDT</b> <i>(নিট লাভ: ৳{profit}!)</i>\n"
                "────────────────────────────\n"
            )
        text += (
            "\n⚡ <b>অফিসিয়াল সুবিধা:</b> আপনি এই পাইকারি রেটে কিনে আপনার যেকোনো গ্রাহকের কাছে নিজের মূল্যে সেল করতে পারেন।"
        )
    
    back_txt = "🔙 Back to Reseller Hub" if lang in ["en", "hi", "ur"] else "🔙 রিসেলার হাব (Back)"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text=back_txt, callback_data="back_reseller_hub", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ])
    await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data == "reseller_copy_posts")
async def handle_reseller_marketing_posts(call: CallbackQuery):
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    
    if lang in ["en", "hi", "ur"]:
        marketing_template = (
            "📢 <b>Ready-to-Use Marketing Templates (Copy & Sell)</b>\n\n"
            "👇 Copy the formatted text below and post directly to your Facebook groups, page, or Telegram:\n\n"
            "<pre>🔥 Mega Offer! Premium Video Editing & Skill Development VIP Access!\n\n"
            "✅ Adobe Premiere Pro & After Effects Masterclass 2026\n"
            "✅ 500+ GB Presets, Sound Effects & Essential Packs\n"
            "✅ Lifetime Private VIP Channel Access\n"
            "✅ Works seamlessly on both Mobile & PC\n\n"
            "💰 Regular Price: ৳700 BDT\n"
            "⚡ Today's Special Price: Only ৳350 BDT!\n\n"
            "📥 Inbox us now for instant delivery!</pre>\n\n"
            "📌 <b>Pro-Tip:</b> When your customer pays you, simply purchase at wholesale price in this bot and send them the 1-time access link!"
        )
    else:
        marketing_template = (
            "📢 <b>রেডি-মেড মার্কেটিং পোস্টস (Copy & Sell Shortcut)</b>\n\n"
            "👇 নিচে দেওয়া ফরম্যাটটি সরাসরি কপি করে আপনার ফেসবুক গ্রুপ, পেজ বা টেলিগ্রামে পোস্ট করতে পারেন:\n\n"
            "<pre>🔥 ধামাকা অফার! প্রিমিয়াম ভিডিও এডিটিং ও স্কিল ডেভেলপমেন্ট কোর্স VIP অ্যাক্সেস!\n\n"
            "✅ Adobe Premiere Pro & After Effects Masterclass 2026\n"
            "✅ 500+ GB Presets, Sound Effects & Essential Packs\n"
            "✅ লাইফটাইম প্রাইভেট ভিআইপি চ্যানেল অ্যাক্সেস\n"
            "✅ মোবাইল ও পিসি উভয় ইউজারদের জন্য পারফেক্ট\n\n"
            "💰 নিয়মিত মূল্য: ৳৭০০ টাকা\n"
            "⚡ আজকের অফার মূল্য: মাত্র ৳৩৫০ টাকা!\n\n"
            "📥 ইনবক্স করুন সরাসরি অ্যাক্সেস পেতে!</pre>\n\n"
            "📌 <b>টিপ:</b> কাস্টমার আপনাকে টাকা দিলে আপনি বটে পাইকারি রেটে কিনে তার জন্য ১-টাইম অ্যাক্সেস লিংক নিয়ে তাকে দিয়ে দেবেন!"
        )
    
    back_txt = "🔙 Back to Reseller Hub" if lang in ["en", "hi", "ur"] else "🔙 রিসেলার হাব (Back)"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text=back_txt, callback_data="back_reseller_hub", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ])
    await render_screen(call, marketing_template, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data == "back_reseller_hub")
async def handle_back_reseller_hub(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    await call.answer()
    text, kb = await get_reseller_hub_data(
        call.from_user.id,
        call.bot,
        call.from_user.username,
        call.from_user.first_name
    )
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "reseller_leaderboard")
async def handle_reseller_leaderboard(call: CallbackQuery):
    await call.answer()
    lang = db.get_user_language(call.from_user.id)
    leaders = db.get_reseller_leaderboard(limit=10)
    
    if lang in ["en", "hi", "ur"]:
        text = (
            "🏆 <b>Top Resellers Leaderboard</b>\n\n"
            "Top performing partners this month:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
        if not leaders:
            text += "<i>No sales recorded yet this month. Be the first top seller!</i>\n"
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, leader in enumerate(leaders):
                badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
                name = leader.get("first_name", "Reseller")
                code = leader.get("reseller_code", "RS-N/A")
                sales = leader.get("reseller_monthly_sales", 0)
                text += f"{badge} <b>[{code}] {name}</b> — <code>{sales} successful sales</code>\n"
        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 <b>Monthly Bonus:</b> Top 3 resellers receive special cashback and free VIP reward passes at month-end!"
        )
    else:
        text = (
            "🏆 <b>সেরা রিসেলার লিডারবোর্ড (Top Resellers Ranking)</b>\n\n"
            "চলতি মাসের সফল রিসেলারদের তালিকা:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
        if not leaders:
            text += "<i>এখনও এই মাসের সেলস রেকর্ড শুরু হয়নি। আপনিই হোন প্রথম টপ সেলার!</i>\n"
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, leader in enumerate(leaders):
                badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
                name = leader.get("first_name", "Reseller")
                code = leader.get("reseller_code", "RS-N/A")
                sales = leader.get("reseller_monthly_sales", 0)
                text += f"{badge} <b>[{code}] {name}</b> — <code>{sales} টি সফল সেল</code>\n"
        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 <b>মাসিক বোনাস:</b> মাসের শেষে শীর্ষ ৩ জন রিসেলারের জন্য রয়েছে বিশেষ নগদ ক্যাশব্যাক ও ফ্রি ভিআইপি অ্যাক্সেস!"
        )
    
    back_txt = "🔙 Back to Reseller Hub" if lang in ["en", "hi", "ur"] else "🔙 রিসেলার হাব (Back)"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text=back_txt, callback_data="back_reseller_hub", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ])
    await render_screen(call, text, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data == "reseller_live_race")
async def handle_reseller_live_race(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    data = db.get_challenge_leaderboard()
    ch = data["challenge"]
    racers = data["racers"]

    user = db.get_user(user_id)
    user_sales = user.get("reseller_monthly_sales", 0) if user else 0
    target = max(1, ch["target_sales"])

    pct = min(100, int((user_sales / target) * 100))
    filled_blocks = int(pct / 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

    # Check if user already won
    user_won_record = next((w for w in ch.get("winners", []) if w["user_id"] == user_id), None)
    if lang in ["en", "hi", "ur"]:
        if user_won_record:
            user_status_note = (
                f"🏆 <b>Congratulations!</b> You unlocked the VIP Reward Pass as Winner #{user_won_record['rank']}!\n"
                f"🎟️ Coupon Code: `{user_won_record.get('coupon_code', 'N/A')}`\n"
            )
        elif ch["remaining_slots"] <= 0:
            user_status_note = "🔒 <b>Notice:</b> All winner slots for this round are filled! Stay tuned for the next race."
        else:
            needed = max(0, target - user_sales)
            user_status_note = f"⚡ You only need <b><code>{needed}</code></b> more sales to win!"
    else:
        if user_won_record:
            user_status_note = (
                f"🏆 <b>অভিনন্দন!</b> আপনি #{user_won_record['rank']} বিজয়ী হিসেবে রিওয়ার্ড পাস আনলক করেছেন!\n"
                f"🎟️ কুপন কোড: `{user_won_record.get('coupon_code', 'N/A')}`\n"
            )
        elif ch["remaining_slots"] <= 0:
            user_status_note = "🔒 <b>সতর্কতা:</b> এই রাউন্ডের সমস্ত বিজয়ী স্লট পূরণ হয়ে গেছে! পরবর্তী রাউন্ডের জন্য প্রস্তুত থাকুন।"
        else:
            needed = max(0, target - user_sales)
            user_status_note = f"⚡ বিজয়ী হতে আপনার আর মাত্র <b><code>{needed} টি</code></b> সফল সেল প্রয়োজন!"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    racer_rows = []
    if not racers:
        racer_rows.append("_No reseller sales recorded yet._" if lang in ["en", "hi", "ur"] else "_এখনও কোনো রিসেলারের সেলস রেকর্ড হয়নি।_")
    else:
        for idx, r in enumerate(racers[:10]):
            badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
            r_name = r.get("first_name", "Reseller")
            r_code = r.get("reseller_code", "RS")
            r_sales = r.get("reseller_monthly_sales", 0)
            if r.get("won_rank"):
                tag = f" — `{r_sales}` 🏆 <b>(Winner #{r['won_rank']})</b>" if lang in ["en", "hi", "ur"] else f" — `{r_sales} টি` 🏆 <b>(বিজয়ী #{r['won_rank']})</b>"
            else:
                left = max(0, target - r_sales)
                tag = f" — `{r_sales}` _({left} remaining)_" if lang in ["en", "hi", "ur"] else f" — `{r_sales} টি` _(আর {left}টি বাকি)_"
            racer_rows.append(f"{badge} **[{r_code}] {r_name}**{tag}")

    racers_text = "\n".join(racer_rows)

    if lang in ["en", "hi", "ur"]:
        text = (
            "🏁 <b>Live Sales Race & Challenge Tracker</b> 🏁\n\n"
            f"🏆 <b>Challenge:</b> {ch['title']}\n"
            f"🎯 <b>Target:</b> `{ch['target_sales']} Sales`\n"
            "🎁 <b>Exclusive Winner Reward Pass:</b>\n"
            f"• 💥 Extra <b>-৳{ch['discount_bdt']:.0f} BDT</b> discount below wholesale prices!\n"
            f"• ⏳ Pass Validity: `{ch['days_valid']} days`\n"
            f"• 📦 Total Order Uses: `{ch['max_uses']} orders`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>Slot Status:</b>\n"
            f"• Total Winner Slots: `{ch['max_slots']}`\n"
            f"• Claimed Slots: `{ch['claimed_slots']}`\n"
            f"• Available Slots: `{ch['remaining_slots']}` {'🔥 Race Active!' if ch['remaining_slots'] > 0 else '🔒 Slots Filled'}\n\n"
            "👤 <b>Your Progress:</b>\n"
            f"• Completed Sales: `{user_sales} / {ch['target_sales']}` ({pct}%)\n"
            f"• Progress Bar: `[{bar}] {pct}%`\n"
            f"{user_status_note}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏎️ <b>Top Racers in Race:</b>\n"
            f"{racers_text}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ The first {ch['max_slots']} sellers to hit the target automatically unlock the VIP reward pass!"
        )
    else:
        text = (
            "🏁 <b>সেলস চ্যালেঞ্জ ও লাইভ রেস (Live Sales Race)</b> 🏁\n\n"
            f"🏆 <b>চ্যালেঞ্জ:</b> {ch['title']}\n"
            f"🎯 <b>টার্গেট:</b> `{ch['target_sales']} টি সেলস`\n"
            "🎁 <b>বিজয়ীদের জন্য এক্সক্লুসিভ রিওয়ার্ড পাস:</b>\n"
            f"• 💥 পাইকারি মূল্যের চেয়েও অতিরিক্ত <b>-৳{ch['discount_bdt']:.0f} BDT</b> ছাড়!\n"
            f"• ⏳ পাসের মেয়াদ: `{ch['days_valid']} দিন`\n"
            f"• 📦 মোট ব্যবহার সীমা: `{ch['max_uses']} টি অর্ডার`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>স্লট স্ট্যাটাস:</b>\n"
            f"• মোট বিজয়ী স্লট: `{ch['max_slots']} টি`\n"
            f"• দখলকৃত স্লট: `{ch['claimed_slots']} টি`\n"
            f"• অবশিষ্ট ফাঁকা স্লট: `{ch['remaining_slots']} টি` {'🔥 রেস রানিং!' if ch['remaining_slots'] > 0 else '🔒 স্লট পূর্ণ'}\n\n"
            "👤 <b>আপনার বর্তমান অগ্রগতি:</b>\n"
            f"• আপনার সম্পন্ন সেলস: `{user_sales} / {ch['target_sales']} টি` ({pct}%)\n"
            f"• প্রগ্রেস: `[{bar}] {pct}%`\n"
            f"{user_status_note}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏎️ <b>লাইভ রেসার ট্র্যাকার (Top Racers in Race):</b>\n"
            f"{racers_text}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ সবার আগে টার্গেট স্পর্শকারী প্রথম {ch['max_slots']} জন স্বয়ংক্রিয়ভাবে ভিআইপি রিওয়ার্ড পাস আনলক করবেন!"
        )

    back_txt = "🔙 Back to Reseller Hub" if lang in ["en", "hi", "ur"] else "🔙 রিসেলার হাব (Back)"
    race_kb = InlineKeyboardMarkup(inline_keyboard=[
        [make_custom_button(text="🔄 Refresh Race" if lang in ["en", "hi", "ur"] else "🔄 Refresh Race (লাইভ আপডেট)", callback_data="reseller_live_race", emoji_key="refresh")],
        [make_custom_button(text="🛒 Buy Wholesale" if lang in ["en", "hi", "ur"] else "🛒 Buy Wholesale / পাইকারি অর্ডার", callback_data="back_cats", emoji_key="cart")],
        [
            make_custom_button(text=back_txt, callback_data="back_reseller_hub", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ])

    await render_screen(call, text, reply_markup=race_kb, parse_mode="HTML")

@router.callback_query(F.data == "apply_reseller")
async def handle_start_apply(call: CallbackQuery, state: FSMContext):
    if state:
        await state.clear()
    await call.answer()
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
        
    std_dep = int(float(db.get_setting("reseller_min_deposit", "1000")))
    elite_dep = int(float(db.get_setting("reseller_elite_min_deposit", "2000")))
    fee = int(float(db.get_setting("reseller_activation_fee", "500")))
    curr_bal = float(user.get("balance_bdt") or 0.0)
    std_rem = max(0, std_dep - fee)
    elite_rem = max(0, elite_dep - fee)

    if lang in ["en", "hi", "ur"]:
        pkg_text = (
            "🤝 <b>Choose Your Reseller Partnership Package</b>\n\n"
            "Select the partnership tier that matches your business model:\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🥉 <b>Package 1: Standard Partner (Channel Access)</b>\n"
            "• <b>Scope:</b> Wholesale access to all Channel Access courses\n"
            "• <b>Permissions:</b> Channel links only (Account logins restricted)\n"
            f"• <b>Required Balance:</b> <code>৳{std_dep:,} BDT</code>\n"
            f"• <b>One-Time Fee:</b> <code>৳{fee:,} BDT</code> (deducted upon approval)\n"
            f"• <b>Shopping Balance:</b> <code>৳{std_rem:,} BDT</code> remains in wallet\n\n"
            "👑 <b>Package 2: Elite VIP Partner (Full Access)</b>\n"
            "• <b>Scope:</b> Full wholesale access to both Channels & Personal Accounts\n"
            "• <b>Permissions:</b> Channels + Premium Accounts/Credentials Unlocked\n"
            f"• <b>Required Balance:</b> <code>৳{elite_dep:,} BDT</code>\n"
            f"• <b>One-Time Fee:</b> <code>৳{fee:,} BDT</code> (deducted upon approval)\n"
            f"• <b>Shopping Balance:</b> <code>৳{elite_rem:,} BDT</code> remains in wallet\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💳 <b>Your Current Balance:</b> <code>৳{curr_bal:,.2f} BDT</code>\n\n"
            "👇 <i>Select a package below to submit your application:</i>"
        )
    else:
        pkg_text = (
            "🤝 <b>রিসেলার পার্টনারশিপ প্যাকেজ নির্বাচন করুন</b>\n\n"
            "আমাদের সাথে পার্টনার হিসেবে কাজ করার জন্য ২টি বিশেষ প্যাকেজ রয়েছে। আপনার প্রয়োজনীয়তা অনুযায়ী পছন্দের প্যাকেজ বেছে নিন:\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🥉 <b>প্যাকেজ ১: Standard পার্টনার (চ্যানেল এক্সেস)</b>\n"
            "• <b>কাজের পরিধি:</b> সমস্ত চ্যানেল এক্সেস কোর্স পাইকারি রেটে কেনার সুযোগ\n"
            "• <b>অনুমতি:</b> শুধুমাত্র চ্যানেল লিংক এক্সেস (অ্যাকাউন্ট ক্রেডেনশিয়াল লক থাকবে)\n"
            f"• <b>ন্যূনতম ব্যালেন্স:</b> <code>৳{std_dep:,} BDT</code>\n"
            f"• <b>অ্যাক্টিভেশন ফি:</b> <code>৳{fee:,} BDT</code> (অনুমোদনের পর কর্তন হবে)\n"
            f"• <b>শপিং ব্যালেন্স:</b> <code>৳{std_rem:,} BDT</code> (ওয়ালেটে ব্যবহারের জন্য থাকবে)\n\n"
            "👑 <b>প্যাকেজ ২: Elite VIP পার্টনার (ফুল এক্সেস)</b>\n"
            "• <b>কাজের পরিধি:</b> সমস্ত কোর্স + প্রিমিয়াম পার্সোনাল অ্যাকাউন্ট / লগইন ক্রেডেনশিয়াল\n"
            "• <b>অনুমতি:</b> উভয় চ্যানেল এবং ফুল অ্যাকাউন্ট এক্সেস সম্পূর্ণ আনলক\n"
            f"• <b>ন্যূনতম ব্যালেন্স:</b> <code>৳{elite_dep:,} BDT</code>\n"
            f"• <b>অ্যাক্টিভেশন ফি:</b> <code>৳{fee:,} BDT</code> (অনুমোদনের পর কর্তন হবে)\n"
            f"• <b>শপিং ব্যালেন্স:</b> <code>৳{elite_rem:,} BDT</code> (ওয়ালেটে ব্যবহারের জন্য থাকবে)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💳 <b>আপনার বর্তমান ব্যালেন্স:</b> <code>৳{curr_bal:,.2f} BDT</code>\n\n"
            "👇 <i>যে প্যাকেজে আবেদন করতে চান, নিচে সেই বাটনে ক্লিক করুন:</i>"
        )
    
    kb = get_reseller_package_selection_kb(lang=lang, std_dep=std_dep, elite_dep=elite_dep)
    await render_screen(call, pkg_text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("apply_reseller_tier:"))
async def handle_start_apply_tier(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    lang = db.get_user_language(user_id)
    user = db.get_user(user_id)
    if not user:
        user = db.register_or_update_user(user_id, call.from_user.username, call.from_user.first_name)
        
    parts = call.data.split(":")
    tier = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    
    std_dep = int(float(db.get_setting("reseller_min_deposit", "1000")))
    elite_dep = int(float(db.get_setting("reseller_elite_min_deposit", "2000")))
    fee = int(float(db.get_setting("reseller_activation_fee", "500")))
    curr_bal = float(user.get("balance_bdt") or 0.0)
    
    min_dep = elite_dep if tier >= 2 else std_dep
    tier_title_bn = "👑 Elite VIP পার্টনার (ফুল এক্সেস)" if tier >= 2 else "🥉 Standard পার্টনার (চ্যানেল এক্সেস)"
    tier_title_en = "👑 Elite VIP Partner (Full Access)" if tier >= 2 else "🥉 Standard Partner (Channel Access)"
    tier_title = tier_title_en if lang in ["en", "hi", "ur"] else tier_title_bn
    
    # Balance Gate Check for this specific tier
    if curr_bal < min_dep:
        alert_popup = f"⚠️ Minimum ৳{min_dep:,} BDT balance required for {tier_title}!" if lang in ["en", "hi", "ur"] else f"⚠️ {tier_title} আবেদনের জন্য ওয়ালেটে ন্যূনতম ৳{min_dep:,} ব্যালেন্স প্রয়োজন!"
        await call.answer(alert_popup, show_alert=True)
        need_amount = int(min_dep - curr_bal)
        usable_after = max(0, int(min_dep - fee))
        
        if lang in ["en", "hi", "ur"]:
            alert_text = (
                f"⚠️ <b>Minimum balance of ৳{min_dep:,} BDT required for {tier_title}!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>Selected Package:</b> {tier_title}\n"
                f"💳 <b>Your Current Balance:</b> <code>৳{curr_bal:,.2f} BDT</code>\n"
                f"💰 <b>Required Minimum Balance:</b> <code>৳{min_dep:,} BDT</code>\n"
                f"📌 <b>Balance Shortage:</b> <code>৳{need_amount:,} BDT</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📊 <b>Fee & Shopping Balance Breakdown:</b>\n"
                f"• <b>One-Time Activation Fee:</b> <code>৳{fee:,} BDT</code> (Deducted upon admin approval)\n"
                f"• <b>Usable Wholesale Shopping Balance:</b> <code>৳{usable_after:,} BDT</code> (Remains in wallet for shopping)\n\n"
                "🛡️ <i>This security policy filters non-serious applicants and protects genuine resellers.</i>\n\n"
                "👇 Please add funds to your wallet using the button below and re-apply:"
            )
            gate_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Add Balance", callback_data="add_balance_shortcut")],
                [InlineKeyboardButton(text="🔄 Change Package", callback_data="apply_reseller")],
                [
                    InlineKeyboardButton(text="🔙 Back to Reseller Hub", callback_data="back_reseller_hub"),
                    InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
                ]
            ])
        else:
            alert_text = (
                f"⚠️ <b>{tier_title} আবেদনের জন্য ওয়ালেটে ন্যূনতম ৳{min_dep:,} ব্যালেন্স প্রয়োজন!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>নির্বাচিত প্যাকেজ:</b> {tier_title}\n"
                f"💳 <b>আপনার বর্তমান ব্যালেন্স:</b> <code>৳{curr_bal:,.2f} BDT</code>\n"
                f"💰 <b>প্রয়োজনীয় ন্যূনতম ব্যালেন্স:</b> <code>৳{min_dep:,} BDT</code>\n"
                f"📌 <b>ঘাটতি ব্যালেন্স:</b> <code>৳{need_amount:,} BDT</code>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📊 <b>ব্যালেন্স ও ফি বন্টন নিয়মাবলী:</b>\n"
                f"• <b>ভেরিফাইড পার্টনার অ্যাক্টিভেশন ফি:</b> <code>৳{fee:,} BDT</code> (নন-রিফান্ডেবল — অনুমোদনের পর স্বয়ংক্রিয়ভাবে কর্তন হবে)\n"
                f"• <b>ব্যবহারযোগ্য পাইকারি শপিং ব্যালেন্স:</b> <code>৳{usable_after:,} BDT</code> (আপনার ওয়ালেটে থাকবে, যা দিয়ে পাইকারি রেটে কোর্স কিনতে পারবেন)\n\n"
                "🛡️ <i>ভুয়া আবেদনকারী ও নন-সিরিয়াস ইউজার ফিল্টার করতে এই সিকিউরিটি পলিসি কার্যকর করা হয়েছে।</i>\n\n"
                "👇 অনুগ্রহ করে নিচের বাটনে চাপ দিয়ে ওয়ালেটে ব্যালেন্স লোড করে পুনরায় আবেদন করুন:"
            )
            gate_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Add Balance (ব্যালেন্স লোড করুন)", callback_data="add_balance_shortcut")],
                [InlineKeyboardButton(text="🔄 প্যাকেজ পরিবর্তন (Change Package)", callback_data="apply_reseller")],
                [
                    InlineKeyboardButton(text="🔙 রিসেলার হাব (Back)", callback_data="back_reseller_hub"),
                    InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")
                ]
            ])
        await render_screen(call, alert_text, reply_markup=gate_kb, parse_mode="HTML")
        return

    await call.answer()
    await state.set_state(ResellerApplyState.waiting_for_info)
    await state.update_data(requested_tier=tier)
    
    usable_after = max(0.0, curr_bal - fee)
    if lang in ["en", "hi", "ur"]:
        prompt = (
            f"📝 <b>{tier_title} Application Form (Verified Balance: ৳{curr_bal:.2f} ✅)</b>\n\n"
            f"💡 <b>Note:</b> Upon approval, a one-time verification fee of <code>৳{fee}</code> will be deducted, leaving <code>৳{usable_after:.2f}</code> as your active wholesale shopping balance.\n\n"
            "Please send the following details in a single message:\n"
            "1. Link to your Facebook page/group or Telegram/WhatsApp channel\n"
            "2. How do you plan to market and sell courses, and your experience?\n\n"
            "<i>(Applications with inaccurate or insufficient info will not be approved)</i>"
        )
    else:
        prompt = (
            f"📝 <b>{tier_title} আবেদন ফর্ম (ভেরিফাইড ব্যালেন্স: ৳{curr_bal:.2f} ✅)</b>\n\n"
            f"💡 <b>মনে রাখবেন:</b> অ্যাডমিন অনুমোদন দিলে আপনার ওয়ালেট থেকে এককালীন <code>৳{fee}</code> ভেরিফিকেশন ফি কর্তন হবে এবং অবশিষ্ট <code>৳{usable_after:.2f}</code> শপিং ব্যালেন্স হিসেবে থাকবে।\n\n"
            "অনুগ্রহ করে নিচের তথ্যগুলো এক মেসেজে লিখে পাঠান:\n"
            "১. আপনার ফেসবুক পেজ, গ্রুপ বা টেলিগ্রাম/হোয়াটসঅ্যাপ চ্যানেলের লিংক\n"
            "২. আপনি কীভাবে কোর্স মার্কেটিং ও সেল করবেন এবং আপনার অভিজ্ঞতা?\n\n"
            "<i>(সঠিক ও স্পষ্ট তথ্য না দিলে আবেদন গ্রহণযোগ্য হবে না)</i>"
        )
    await render_screen(call, prompt, reply_markup=get_cancel_fsm_kb(lang=lang), parse_mode="HTML")

@router.message(ResellerApplyState.waiting_for_info)
async def handle_process_apply(message: Message, state: FSMContext, bot: Bot):
    info = message.text.strip() if message.text else "N/A"
    user = message.from_user
    db_user = db.get_user(user.id)
    lang = db.get_user_language(user.id)
    curr_bal = float(db_user.get("balance_bdt") or 0.0) if db_user else 0.0
    
    state_data = await state.get_data()
    requested_tier = int(state_data.get("requested_tier", 1))
    await state.clear()
    
    # Save application with balance snapshot and requested tier
    app_id = db.submit_reseller_application(user.id, info, curr_bal, requested_tier=requested_tier)
    fee = float(db.get_setting("reseller_activation_fee", "500"))
    usable_after = max(0.0, curr_bal - fee)
    
    tier_title_bn = "👑 Elite VIP পার্টনার" if requested_tier >= 2 else "🥉 Standard পার্টনার"
    tier_title_en = "👑 Elite VIP Partner" if requested_tier >= 2 else "🥉 Standard Partner"
    tier_title = tier_title_en if lang in ["en", "hi", "ur"] else tier_title_bn

    if lang in ["en", "hi", "ur"]:
        confirm_text = (
            f"🎉 <b>Your {tier_title} Application has been submitted!</b>\n\n"
            f"🆔 Application ID: <code>#{app_id}</code>\n"
            f"🎯 Requested Package: <b>{tier_title}</b>\n"
            f"💰 Verified Balance: <code>৳{curr_bal:.2f} BDT</code>\n"
            f"🛡️ Fee Upon Approval: <code>৳{fee:.2f} BDT</code>\n"
            f"💳 Balance Remaining: <code>৳{usable_after:.2f} BDT</code>\n\n"
            "Our admin will review your marketing channels and approve your application shortly.\n\n"
            f"⚡ <b>For instant verification, ping the admin directly:</b>\n"
            f"👉 @{ADMIN_USERNAME}"
        )
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💬 Ping Admin (@{ADMIN_USERNAME})", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
        ])
    else:
        confirm_text = (
            f"🎉 <b>আপনার {tier_title} আবেদন সফলভাবে সাবমিট হয়েছে!</b>\n\n"
            f"🆔 আবেদন নং: <code>#{app_id}</code>\n"
            f"🎯 আবেদনকৃত প্যাকেজ: <b>{tier_title}</b>\n"
            f"💰 বর্তমান ভেরিফাইড ব্যালেন্স: <code>৳{curr_bal:.2f} BDT</code>\n"
            f"🛡️ অনুমোদনে কর্তনযোগ্য ফি: <code>৳{fee:.2f} BDT</code>\n"
            f"💳 অনুমোদনের পর অবশিষ্ট থাকবে: <code>৳{usable_after:.2f} BDT</code>\n\n"
            "অ্যাডমিন আপনার প্রোফাইল ও মার্কেটিং লিংক যাচাই করে দ্রুত অনুমোদন করবেন।\n\n"
            f"⚡ <b>দ্রুত অনুমোদনের জন্য সরাসরি অ্যাডমিনকে নক দিতে পারেন:</b>\n"
            f"👉 @{ADMIN_USERNAME}"
        )
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💬 নক অ্যাডমিন (@{ADMIN_USERNAME})", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton(text="🏠 মূল মেনু (Home)", callback_data="main_menu")]
        ])
    await message.answer(confirm_text, reply_markup=confirm_kb, parse_mode="HTML")
    
    # Notify Admin Instantly with interactive action buttons and requested tier
    user_payload = {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username
    }
    await notify_admin_reseller_app(bot, app_id, user_payload, info, curr_bal, requested_tier=requested_tier)

@router.callback_query(F.data.startswith("approve_reseller_app:"))
async def handle_approve_reseller_app(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    app_id = int(parts[1])
    tier = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    res_data = db.approve_reseller_application(app_id, tier=tier)
    
    if not res_data:
        await call.answer("⚠️ এই আবেদনটি ইতিমধ্যে প্রসেস করা হয়েছে বা ইউজার পাওয়া যায়নি!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return
        
    user_id = res_data["user_id"]
    code = res_data["reseller_code"]
    fee = res_data["fee_deducted"]
    remaining_bal = res_data["remaining_balance"]

    tier_stamp = "👑 ELITE VIP RESELLER (ALL ACCESS)" if tier >= 2 else "🥉 STANDARD RESELLER (CHANNEL PARTNER)"
    await call.answer(f"💎 রিসেলার অনুমোদন সম্পন্ন! ({'Elite' if tier >= 2 else 'Standard'})", show_alert=True)
    base_text = call.message.text or call.message.caption or ""
    approved_stamp = (
        "\n\n━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>APPROVED AS {tier_stamp}!</b>\n"
        f"🆔 <b>রিসেলার কোড:</b> <code>{code}</code>\n"
        f"💸 <b>অ্যাক্টিভেশন ফি কর্তন:</b> <code>৳{fee:.2f} BDT</code>\n"
        f"💳 <b>ইউজারের অবশিষ্ট ব্যালেন্স:</b> <code>৳{remaining_bal:.2f} BDT</code>"
    )
    await call.message.edit_text(base_text + approved_stamp, reply_markup=None, parse_mode="HTML")
    
    # Notify User
    quota = db.get_setting("reseller_monthly_quota", "5")
    tier_desc = "👑 Elite VIP পার্টনার (চ্যানেল + পার্সোনাল অ্যাকাউন্ট ফুল অ্যাক্সেস)" if tier >= 2 else "🥉 স্ট্যান্ডার্ড পার্টনার (চ্যানেল অ্যাক্সেস)"
    congrats = (
        f"🎉 <b>অভিনন্দন! আপনার {tier_desc} আবেদন অনুমোদিত হয়েছে!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>আপনার অফিসিয়াল রিসেলার কোড:</b> <code>{code}</code>\n"
        f"💸 <b>ভেরিফাইড পার্টনার ফি কর্তন:</b> <code>৳{fee:.2f} BDT</code>\n"
        f"💳 <b>আপনার অবশিষ্ট শপিং ব্যালেন্স:</b> <code>৳{remaining_bal:.2f} BDT</code>\n"
        f"🎯 <b>মাসিক সেলস কোটা:</b> ন্যূনতম <code>{quota} টি</code> সেল\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ এখন থেকে আপনি সমস্ত কোর্স ও ডিজিটাল প্রোডাক্টে <b>বিশেষ পাইকারি ছাড়</b> পাচ্ছেন!\n"
        f"💡 আপনার ওয়ালেটে থাকা অবশিষ্ট <b>৳{remaining_bal:.2f}</b> দিয়ে এখনই পাইকারি রেটে কোর্স অর্ডার করতে পারবেন।\n\n"
        "👉 এখনই মূল মেনু থেকে <b>🤝 Reseller Hub (রিসেলার প্যানেল)</b> ওপেন করে আপনার পাইকারি রেট শিট ও পাবলিক ভেরিফিকেশন লিংক দেখুন।"
    )
    try:
        await bot.send_message(chat_id=user_id, text=congrats, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Could not notify approved reseller {user_id}: {e}")

@router.callback_query(F.data.startswith("reject_reseller_app:"))
async def handle_reject_reseller_app(call: CallbackQuery, bot: Bot):
    app_id = int(call.data.split(":")[1])
    user_id = db.reject_reseller_application(app_id)
    
    if not user_id:
        await call.answer("⚠️ এই আবেদনটি ইতিমধ্যে প্রসেস করা হয়েছে!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
        return

    await call.answer("আবেদন বাতিল করা হয়েছে।", show_alert=True)
    base_text = call.message.text or call.message.caption or ""
    await call.message.edit_text(base_text + "\n\n━━━━━━━━━━━━━━━━━━━━\n❌ <b>REJECTED</b>", reply_markup=None, parse_mode="HTML")

    # Notify User respectfully and reassuring that their money is untouched
    target_user = db.get_user(user_id)
    cur_bal = float(target_user.get("balance_bdt") or 0.0) if target_user else 0.0
    reject_msg = (
        "ℹ️ <b>রিসেলার আবেদন আপডেট</b>\n\n"
        "দুঃখিত, পর্যালোচনার পর আপনার রিসেলার আবেদনটি এই মুহূর্তে অনুমোদন করা সম্ভব হয়নি।\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>আপনার ওয়ালেট ব্যালেন্স:</b> <code>৳{cur_bal:.2f} BDT</code> (১০০% অক্ষত ও সুরক্ষিত)\n"
        "📌 <i>কোনো প্রকার ফি বা চার্জ কাটা হয়নি। আপনি এই ব্যালেন্স দিয়ে সাধারণ মূল্যে কেনাকাটা করতে পারেন।</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"বিস্তারিত জানতে বা পুনরায় পর্যালোচনার জন্য অ্যাডমিনকে নক দিতে পারেন:\n"
        f"👉 @{ADMIN_USERNAME}"
    )
    try:
        await bot.send_message(chat_id=user_id, text=reject_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Could not notify rejected applicant {user_id}: {e}")

@router.callback_query(F.data == "reseller_upgrade_info")
async def handle_reseller_upgrade_info(call: CallbackQuery):
    lang = db.get_user_language(call.from_user.id)
    await call.answer()
    if lang in ["en", "hi", "ur"]:
        text = (
            "👑 <b>Elite VIP Reseller Partnership Benefits & Upgrade</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Upgrade from Standard to Elite VIP to unlock full selling power:\n\n"
            "✨ <b>Exclusive Advantages:</b>\n"
            "• 🔐 <b>Personal Account & Drive Access:</b> Permission to sell individual personal accounts and Google Drive direct links.\n"
            "• 💎 <b>Maximum Wholesale Profit Margin:</b> Earn highest profits on premium software, AI accounts & courses.\n"
            "• 🛡️ <b>Official Elite VIP Badge:</b> Displayed publicly on your verification certificate to establish complete buyer trust.\n"
            "• ⚡ <b>Priority Admin Dispatch:</b> Instant stock fulfillment for your VIP orders.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 <b>How to Upgrade:</b>\n"
            "Contact Admin directly to request an Elite VIP tier upgrade:"
        )
    else:
        text = (
            "👑 <b>Elite VIP রিসেলার পার্টনারশিপ সুবিধা ও আপগ্রেড</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "স্ট্যান্ডার্ড পার্টনার থেকে Elite VIP-তে আপগ্রেড করে আপনার ব্যবসার পরিধি বড় করুন:\n\n"
            "✨ <b>Elite VIP এর এক্সক্লুসিভ সুবিধাসমূহ:</b>\n"
            "• 🔐 <b>পার্সোনাল অ্যাকাউন্ট ও ড্রাইভ সেল:</b> একক ক্লায়েন্টদের জন্য ব্যক্তিগত অ্যাকাউন্ট ও ড্রাইভ অ্যাক্সেস বিক্রির পূর্ণ অধিকার।\n"
            "• 💎 <b>সর্বোচ্চ পাইকারি লাভ:</b> এআই টুলস ও প্রিমিয়াম সফটওয়্যারে সর্বোচ্চ মার্জিন ইনকাম।\n"
            "• 🛡️ <b>অফিশিয়াল Elite VIP সিল:</b> পাবলিক ভেরিফিকেশন সার্টিফিকেটে 'Elite VIP Partner' ব্যাজ, যা কাস্টমারের মনে ১০০% ট্রাস্ট তৈরি করে।\n"
            "• ⚡ <b>ফাস্ট-ট্র্যাক সার্ভিস:</b> অর্ডারের স্টক ও ডেলিভারিতে সর্বোচ্চ প্রায়োরিটি।\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 <b>আপগ্রেড করার নিয়ম:</b>\n"
            "এলিট টায়ারে আপগ্রেডের জন্য সরাসরি অ্যাডমিনের সাথে যোগাযোগ করুন:"
        )
    from keyboards.user_kb import make_custom_button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text="⚡ অ্যাডমিনের সাথে যোগাযোগ (DM)", url=f"https://t.me/{ADMIN_USERNAME}", emoji_key="zap")
        ],
        [
            make_custom_button(text=t("btn_back", lang), callback_data="reseller_hub", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ])
    await render_screen(call, text, reply_markup=kb, parse_mode="HTML")


