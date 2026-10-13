# User Keyboards for Reseller Bot - 100% Premium Animated Custom Emojis
from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any, Optional
import urllib.parse
from config import ADMIN_USERNAME
from utils.i18n import t, localize_item_name
from utils.emojis import (
    make_custom_button,
    make_custom_reply_button
)

def get_main_reply_kb(lang: str = "bn", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Persistent reply keyboard at the bottom of the chat with native Telegram Premium animated emojis."""
    menu_label = "🏠 মূল মেনু" if lang == "bn" else ("🏠 Main Menu" if lang == "en" else "🏠 मुख्य मेनू")
    courses_label = t("btn_courses", lang)
    deposit_label = t("btn_deposit", lang)
    orders_label = t("btn_orders", lang)
    profile_label = t("btn_profile", lang)
    support_label = t("btn_support", lang)
    reseller_label = "🤝 রিসেলার হাব" if lang == "bn" else ("🤝 Reseller Hub" if lang == "en" else "🤝 रीसेलर हब")

    kb = [
        [
            make_custom_reply_button(menu_label, emoji_key="home"),
            make_custom_reply_button(courses_label, emoji_key="courses")
        ],
        [
            make_custom_reply_button(deposit_label, emoji_key="deposit"),
            make_custom_reply_button(orders_label, emoji_key="orders")
        ],
        [
            make_custom_reply_button(profile_label, emoji_key="profile"),
            make_custom_reply_button(support_label, emoji_key="support")
        ]
    ]
    if is_admin:
        kb.append([
            make_custom_reply_button("👑 Admin Panel", emoji_key="admin"),
            make_custom_reply_button(reseller_label, emoji_key="reseller")
        ])
    else:
        kb.append([
            make_custom_reply_button(reseller_label, emoji_key="reseller")
        ])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)

def get_reseller_verification_kb(username: Optional[str] = None, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons attached to a reseller verification certificate."""
    buttons = []
    if username:
        clean_user = username.lstrip("@")
        buttons.append([
            make_custom_button(
                text=f"Chat with @{clean_user}",
                url=f"https://t.me/{clean_user}",
                emoji_key="support"
            )
        ])
    buttons.append([
        make_custom_button(
            text="🔍 অন্য রিসেলার যাচাই" if lang == "bn" else ("🔍 Verify Another Reseller" if lang == "en" else "🔍 अन्य रीसेलर सत्यापन"),
            callback_data="verify_reseller_prompt",
            emoji_key="search"
        ),
        make_custom_button(
            text=t("btn_home", lang),
            callback_data="main_menu",
            emoji_key="home"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_dashboard_inline_kb(lang: str = "bn", is_admin: bool = False, admin_username: str = ADMIN_USERNAME) -> InlineKeyboardMarkup:
    """Modern single-screen app inline keyboard with 100% strict localization."""
    if lang == "en":
        shop_txt = "🛍️ Browse Store"
        prof_txt = "👤 My Profile"
        dep_txt = "💳 Deposit Balance"
        free_txt = "🎁 Free Rewards"
        ref_txt = "👥 Refer & Earn"
        ver_txt = "🛡️ Verify Reseller"
        res_txt = "💼 Reseller Hub"
        ord_txt = "📜 Order History"
        lang_txt = "🌐 Language"
        sup_txt = "💬 Support Helpdesk"
        adm_txt = "👑 Admin Dashboard"
    elif lang == "hi":
        shop_txt = "🛍️ स्टोर ब्राउज़ करें"
        prof_txt = "👤 मेरी प्रोफाइल"
        dep_txt = "💳 बैलेंस जोड़ें"
        free_txt = "🎁 फ्री रिवॉर्ड्स"
        ref_txt = "👥 रेफर और कमाएं"
        ver_txt = "🛡️ रीसेलर सत्यापन"
        res_txt = "💼 रीसेलर हब"
        ord_txt = "📜 ऑर्डर इतिहास"
        lang_txt = "🌐 भाषा (Language)"
        sup_txt = "💬 ग्राहक सहायता"
        adm_txt = "👑 एडमिन पैनल"
    else:
        shop_txt = "🛍️ শপ ব্রাউজ করুন"
        prof_txt = "👤 আমার প্রোফাইল"
        dep_txt = "💳 ব্যালেন্স ডিপোজিট"
        free_txt = "🎁 ফ্রি রিওয়ার্ডস"
        ref_txt = "👥 রেফার ও ইনকাম"
        ver_txt = "🛡️ রিসেলার সততা যাচাই"
        res_txt = "💼 রিসেলার হাব"
        ord_txt = "📜 আমার অর্ডারসমূহ"
        lang_txt = "🌐 ভাষা পরিবর্তন"
        sup_txt = "💬 কাস্টমার সাপোর্ট"
        adm_txt = "👑 অ্যাডমিন ড্যাশবোর্ড"

    buttons = [
        [
            make_custom_button(text=shop_txt, callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=prof_txt, callback_data="nav_profile", emoji_key="profile")
        ],
        [
            make_custom_button(text=dep_txt, callback_data="add_balance_shortcut", emoji_key="deposit"),
            make_custom_button(text=free_txt, callback_data="nav_free_claim", emoji_key="free_claim")
        ],
        [
            make_custom_button(text=ref_txt, callback_data="nav_referral", emoji_key="referral"),
            make_custom_button(text=ver_txt, callback_data="verify_reseller_prompt", emoji_key="verify")
        ],
        [
            make_custom_button(text=res_txt, callback_data="back_reseller_hub", emoji_key="reseller"),
            make_custom_button(text=ord_txt, callback_data="nav_orders", emoji_key="orders")
        ],
        [
            make_custom_button(text=lang_txt, callback_data="nav_lang", emoji_key="language"),
            make_custom_button(text=sup_txt, url=f"https://t.me/{admin_username}", emoji_key="support")
        ]
    ]
    if is_admin:
        buttons.append([
            make_custom_button(text=adm_txt, callback_data="admin_main_dashboard", emoji_key="admin")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_language_kb(lang: str = "bn") -> InlineKeyboardMarkup:
    """Inline keyboard for selecting user language with custom flag badges."""
    buttons = [
        [
            make_custom_button(text="বাংলা (Bengali)", callback_data="set_lang:bn", emoji_key="lang_bn"),
            make_custom_button(text="English", callback_data="set_lang:en", emoji_key="lang_en")
        ],
        [
            make_custom_button(text="हिन्दी (Hindi)", callback_data="set_lang:hi", emoji_key="lang_hi")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reseller_hub_kb(is_reseller: bool = False, is_banned: bool = False, admin_username: str = ADMIN_USERNAME, lang: str = "bn") -> InlineKeyboardMarkup:
    """Keyboards for Reseller Hub."""
    if is_banned:
        return InlineKeyboardMarkup(inline_keyboard=[
            [make_custom_button(text="Support (হেল্প লাইন)", url=f"https://t.me/{admin_username}", emoji_key="support")],
            [make_custom_button(text=t("btn_back", lang), callback_data="main_menu", emoji_key="back")]
        ])

    price_label = "Wholesale Price List (পাইকারি রেট শিট)" if lang != "hi" else "थोक मूल्य सूची (Wholesale Price List)"
    buttons = [
        [
            make_custom_button(text=price_label, callback_data="reseller_pricelist", emoji_key="diamond")
        ]
    ]
    if is_reseller:
        lb_label = "Leaderboard (রিসেলার তালিকা)" if lang == "en" else ("লিডারবোর্ড (সেরা রিসেলার)" if lang == "bn" else "लीडरबोर्ड")
        post_label = "Ready Marketing Posts" if lang == "en" else ("রেডি মার্কেটিং পোস্টস" if lang == "bn" else "रेडीमेड मार्केटिंग पोस्ट")
        order_label = "Order at Wholesale Rate" if lang == "en" else ("পাইকারি মূল্যে অর্ডার করুন" if lang == "bn" else "थोक भाव पर ऑर्डर करें")
        race_label = "Live Race & Challenge" if lang == "en" else ("সেলস চ্যালেঞ্জ ও লাইভ রেস" if lang == "bn" else "लाइव सेल्स रेस और चैलेंज")
        buttons.append([
            make_custom_button(text=race_label, callback_data="reseller_live_race", emoji_key="flag")
        ])
        buttons.append([
            make_custom_button(text=lb_label, callback_data="reseller_leaderboard", emoji_key="trophy"),
            make_custom_button(text=post_label, callback_data="reseller_copy_posts", emoji_key="broadcast")
        ])
        buttons.append([
            make_custom_button(text=order_label, callback_data="back_cats", emoji_key="cart")
        ])
    else:
        lb_label = "Leaderboard" if lang == "en" else ("রিসেলার লিডারবোর্ড" if lang == "bn" else "लीडरबोर्ड")
        apply_label = "Apply for Reseller Account" if lang == "en" else ("রিসেলার হতে আবেদন করুন" if lang == "bn" else "रीसेलर बनने के लिए आवेदन करें")
        knock_label = "Contact Admin (দ্রুত নক দিন)" if lang == "en" else ("দ্রুত অ্যাক্টিভেশন নক দিন 💬" if lang == "bn" else "एडमिन से संपर्क करें 💬")
        buttons.append([
            make_custom_button(text=lb_label, callback_data="reseller_leaderboard", emoji_key="trophy")
        ])
        buttons.append([
            make_custom_button(text=apply_label, callback_data="apply_reseller", emoji_key="edit")
        ])
        buttons.append([
            make_custom_button(text=knock_label, url=f"https://t.me/{admin_username}", emoji_key="zap")
        ])
        
    buttons.append([make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reseller_app_approval_kb(app_id: int) -> InlineKeyboardMarkup:
    """Admin approval buttons for reseller application."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            make_custom_button(text="Approve as Reseller (অনুমোদন)", callback_data=f"approve_reseller_app:{app_id}", emoji_key="check"),
            make_custom_button(text="Reject (বাতিল)", callback_data=f"reject_reseller_app:{app_id}", emoji_key="cross")
        ]
    ])

def get_categories_kb(categories: List[Dict[str, Any]], cat_type: str = "course", lang: str = "bn") -> InlineKeyboardMarkup:
    """Inline keyboard for browsing categories with automatic item localization."""
    buttons = []
    for cat in categories:
        btn_text = localize_item_name(cat['name'], lang)
        buttons.append([make_custom_button(text=btn_text, callback_data=f"cat:{cat['id']}", emoji_key="category")])
    
    buttons.append([make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subcategories_kb(subcategories: List[Dict[str, Any]], parent_cat_id: int, lang: str = "bn") -> InlineKeyboardMarkup:
    """Inline keyboard for browsing subcategories under an academy/parent category."""
    buttons = []
    for sc in subcategories:
        icon = sc.get("icon") or "📁"
        clean_name = localize_item_name(sc['name'], lang)
        btn_text = f"{icon} {clean_name}" if icon not in clean_name else clean_name
        buttons.append([make_custom_button(text=btn_text, callback_data=f"subcat:{sc['id']}", emoji_key="category")])
    
    buttons.append([
        make_custom_button(text=t("btn_back_cats", lang), callback_data="back_cats", emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_products_kb(products: List[Dict[str, Any]], category_id: int, subcategory_id: Optional[int] = None, parent_id: Optional[int] = None, lang: str = "bn") -> InlineKeyboardMarkup:
    """Inline keyboard for listing products under a category or subcategory with clean price formatting."""
    buttons = []
    for prod in products:
        clean_title = localize_item_name(prod['title'], lang)
        if lang in ["en", "hi"]:
            btn_text = f"{clean_title} — ${prod['price_usd']} / ৳{int(prod['price_bdt'])}"
        else:
            btn_text = f"{clean_title} — ৳{int(prod['price_bdt'])} / ${prod['price_usd']}"
        buttons.append([make_custom_button(text=btn_text, callback_data=f"prod:{prod['id']}", emoji_key="sparkle")])
    
    if subcategory_id and parent_id:
        back_btn = make_custom_button(text=t("btn_back_subcats", lang), callback_data=f"cat:{parent_id}", emoji_key="back")
    else:
        back_btn = make_custom_button(text=t("btn_back_cats", lang), callback_data="back_cats", emoji_key="back")

    buttons.append([
        back_btn,
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_detail_kb(product: Dict[str, Any], in_stock: bool, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons for product view."""
    buttons = []
    
    sales_page = product.get("sales_page_url")
    if sales_page:
        buttons.append([
            make_custom_button(
                text=t("btn_view_sales_page", lang),
                url=sales_page,
                emoji_key="channel"
            )
        ])
        
    if in_stock:
        has_dual = (float(product.get("price_channel_bdt") or 0) > 0 and float(product.get("price_account_bdt") or 0) > 0)
        if has_dual:
            from config import get_live_usd_rate
            live_rate = get_live_usd_rate()
            ch_bdt = int(product.get("price_channel_bdt") or 0)
            ch_usd = product.get("price_channel_usd") or round(ch_bdt / live_rate, 2)
            acc_bdt = int(product.get("price_account_bdt") or 0)
            acc_usd = product.get("price_account_usd") or round(acc_bdt / live_rate, 2)
            
            ch_label = f"📢 VIP Channel Access (${ch_usd} / ৳{ch_bdt})" if lang in ["en", "hi"] else f"📢 VIP Channel Access (৳{ch_bdt} / ${ch_usd})"
            acc_label = f"🔐 Account / Drive Access (${acc_usd} / ৳{acc_bdt})" if lang in ["en", "hi"] else f"🔐 Account / Drive Access (৳{acc_bdt} / ${acc_usd})"
            
            buttons.append([
                make_custom_button(
                    text=ch_label,
                    callback_data=f"buy_tier:{product['id']}:channel",
                    emoji_key="channel"
                )
            ])
            buttons.append([
                make_custom_button(
                    text=acc_label,
                    callback_data=f"buy_tier:{product['id']}:account",
                    emoji_key="box"
                )
            ])
        else:
            if lang in ["en", "hi"]:
                buy_text = f"🚀 Buy Now (${product['price_usd']} / ৳{int(product['price_bdt'])})"
            else:
                buy_text = f"🚀 এখনই কিনুন (৳{int(product['price_bdt'])} / ${product['price_usd']})"
            buy_cb = f"buy:{product['id']}"
            buttons.append([
                make_custom_button(
                    text=buy_text,
                    callback_data=buy_cb,
                    emoji_key="cart"
                )
            ])
        buttons.append([
            make_custom_button(
                text=t("btn_claim_ref", lang),
                callback_data=f"claim_ref:{product['id']}",
                emoji_key="free_claim"
            )
        ])
        buttons.append([
            make_custom_button(
                text=t("btn_share_course_ref", lang),
                callback_data=f"gen_course_ref:{product['id']}",
                emoji_key="broadcast"
            )
        ])
    else:
        buttons.append([
            make_custom_button(text=t("btn_out_of_stock", lang), callback_data="out_of_stock", emoji_key="cross")
        ])
    
    if product.get("subcategory_id"):
        back_cb = f"subcat:{product['subcategory_id']}"
    elif product.get("category_id"):
        back_cb = f"cat:{product['category_id']}"
    else:
        back_cb = "back_cats"
    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data=back_cb, emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_access_tier_selection_kb(product_id: int, ch_bdt: float, ch_usd: float, acc_bdt: float, acc_usd: float, lang: str = "bn") -> InlineKeyboardMarkup:
    """Choose between VIP Channel Access and Personal Account Access."""
    if lang in ["en", "hi"]:
        ch_text = f"📢 VIP Channel Access — ${ch_usd} / ৳{int(ch_bdt)}"
        acc_text = f"🔐 Personal Account / Drive — ${acc_usd} / ৳{int(acc_bdt)}"
    else:
        ch_text = f"📢 VIP Channel Access — ৳{int(ch_bdt)} / ${ch_usd}"
        acc_text = f"🔐 Personal Account / Drive — ৳{int(acc_bdt)} / ${acc_usd}"
    buttons = [
        [
            make_custom_button(
                text=ch_text,
                callback_data=f"buy_tier:{product_id}:channel",
                emoji_key="channel"
            )
        ],
        [
            make_custom_button(
                text=acc_text,
                callback_data=f"buy_tier:{product_id}:account",
                emoji_key="box"
            )
        ],
        [
            make_custom_button(text=t("btn_back", lang), callback_data=f"prod:{product_id}", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_referral_hub_kb(bot_username: str, user_id: int, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons for User Referral & Growth Center."""
    from database.db import db
    try:
        from aiogram.types import CopyTextButton
        has_copy = True
    except Exception:
        has_copy = False

    wb = int(float(db.get_setting("referral_welcome_bonus", "5.0")))
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    if lang == "en":
        bonus_str = f" get ৳{wb} Free Bonus and" if wb > 0 else ""
        share_msg = (
            "Hey! Get premium courses, AI accounts and digital tools from this Telegram bot!\n\n"
            f"Join now to{bonus_str} unlock your favorite courses:\n"
        )
    else:
        bonus_str = f" ৳{wb} ফ্রি বোনাস নিন ও" if wb > 0 else ""
        share_msg = (
            "ভাই এই টেলিগ্রাম বট থেকে প্রিমিয়াম কোর্স, AI অ্যাকাউন্ট ও সফটওয়্যার একদম ফ্রিতে পাওয়া যাচ্ছে!\n\n"
            f"এখনই জয়েন করে{bonus_str} পছন্দের কোর্স আনলক করুন:\n"
        )
    encoded_text = urllib.parse.quote(share_msg)
    encoded_url = urllib.parse.quote(ref_link)
    share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"
    
    if has_copy:
        copy_btn = make_custom_button(text=t("btn_copy_link", lang), copy_text=CopyTextButton(text=ref_link), emoji_key="box")
    else:
        copy_btn = make_custom_button(text=t("btn_copy_link", lang), callback_data=f"copy_ref:{user_id}", emoji_key="box")

    buttons = [
        [
            copy_btn,
            make_custom_button(text=t("btn_share_telegram", lang), url=share_url, emoji_key="broadcast")
        ],
        [
            make_custom_button(text=t("btn_leaderboard", lang), callback_data="ref_leaderboard", emoji_key="trophy"),
            make_custom_button(text=t("btn_browse_catalog", lang), callback_data="back_cats", emoji_key="courses")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_referral_progress_kb(product_id: int, bot_username: str, user_id: int, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons on course referral progress modal."""
    from database.db import db
    try:
        from aiogram.types import CopyTextButton
        has_copy = True
    except Exception:
        has_copy = False

    wb = int(float(db.get_setting("referral_welcome_bonus", "5.0")))
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    bonus_str = f" ৳{wb} ফ্রি স্টার্টার বোনাস নিন" if wb > 0 else " ফ্রি কোর্স নিন"
    share_msg = (
        "ভাই এই টেলিগ্রাম বটে জয়েন করে প্রিমিয়াম কোর্স ও টুলস একদম ফ্রিতে নিন!\n\n"
        f"আমার রেফারেল লিংক থেকে এখনই জয়েন করে{bonus_str}:\n"
    )
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_msg)}"
    
    if has_copy:
        copy_btn = make_custom_button(text=t("btn_copy_link", lang), copy_text=CopyTextButton(text=ref_link), emoji_key="box")
    else:
        copy_btn = make_custom_button(text=t("btn_copy_link", lang), callback_data=f"copy_ref:{user_id}", emoji_key="box")

    buttons = [
        [
            copy_btn,
            make_custom_button(text=t("btn_share_telegram", lang), url=share_url, emoji_key="broadcast")
        ],
        [
            make_custom_button(text=t("btn_add_balance", lang), callback_data="add_balance_shortcut", emoji_key="deposit")
        ],
        [
            make_custom_button(text=t("btn_back", lang), callback_data=f"prod:{product_id}", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_buy_confirm_kb(product_id: int, price_bdt: float, price_usd: float, has_coupon: bool = False, tier: str = "default", refs_needed: int = 0, user_pts: int = 0, lang: str = "bn") -> InlineKeyboardMarkup:
    """Confirm purchase with BDT or USD balance, or referral points, plus coupon application."""
    cb_suffix = f":{tier}" if tier != "default" else ""
    if lang in ["en", "hi"]:
        pay_bdt = f"Pay ৳{int(price_bdt)} (BDT)"
        pay_usd = f"Pay ${price_usd} (USD)"
    else:
        pay_bdt = f"৳{int(price_bdt)} পে করুন (BDT)"
        pay_usd = f"${price_usd} পে করুন (USD)"
    cancel_cb = f"buy_tier_select:{product_id}" if tier != "default" else f"prod:{product_id}"
    buttons = [
        [
            make_custom_button(text=pay_bdt, callback_data=f"confirm_buy:{product_id}:BDT{cb_suffix}", emoji_key="check"),
            make_custom_button(text=pay_usd, callback_data=f"confirm_buy:{product_id}:USD{cb_suffix}", emoji_key="check")
        ]
    ]
    if refs_needed > 0:
        if lang in ["en", "hi"]:
            pts_label = f"🎁 Pay {refs_needed} Pts (You have {user_pts} Pts ✅)" if user_pts >= refs_needed else f"🎁 Pay with Referrals ({refs_needed} Pts)"
        else:
            pts_label = f"🎁 {refs_needed} পয়েন্ট দিয়ে নিন (আপনার আছে {user_pts} Pts ✅)" if user_pts >= refs_needed else f"🎁 রেফারেল দিয়ে নিন ({refs_needed} Pts)"
        buttons.append([
            make_custom_button(text=pts_label, callback_data=f"confirm_buy:{product_id}:REF{cb_suffix}", emoji_key="free_claim")
        ])
    if not has_coupon:
        buttons.append([
            make_custom_button(text=t("btn_apply_coupon", lang), callback_data=f"apply_coupon:{product_id}{cb_suffix}", emoji_key="coupon")
        ])
    buttons.append([
        make_custom_button(text=t("btn_add_balance", lang), callback_data="add_balance_shortcut", emoji_key="deposit")
    ])
    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data=cancel_cb, emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_deposit_methods_kb(lang: str = "bn") -> InlineKeyboardMarkup:
    """Select deposit payment method with active gateway indicators."""
    from database.db import db
    bkash_active = db.is_gateway_active("bkash")
    nagad_active = db.is_gateway_active("nagad")
    rocket_active = db.is_gateway_active("rocket")
    binance_active = db.is_gateway_active("binance")

    if lang in ["en", "hi"]:
        maint_txt = "(Maintenance)"
        cashout_txt = "(Cash Out)"
        send_txt = "(Send Money)"
    else:
        maint_txt = "(সাময়িক বন্ধ)"
        cashout_txt = "(ক্যাশ আউট)"
        send_txt = "(সেন্ড মানি)"

    bkash_txt = f"bKash {cashout_txt}" if bkash_active else f"bKash {maint_txt}"
    nagad_txt = f"Nagad {cashout_txt}" if nagad_active else f"Nagad {maint_txt}"
    rocket_txt = f"Rocket {send_txt}" if rocket_active else f"Rocket {maint_txt}"
    binance_txt = "Binance Pay / USDT" if binance_active else f"Binance {maint_txt}"

    buttons = [
        [
            make_custom_button(text=bkash_txt, callback_data="dep_method:bkash", emoji_key="bkash"),
            make_custom_button(text=nagad_txt, callback_data="dep_method:nagad", emoji_key="nagad")
        ],
        [
            make_custom_button(text=rocket_txt, callback_data="dep_method:rocket", emoji_key="rocket"),
            make_custom_button(text=binance_txt, callback_data="dep_method:binance", emoji_key="binance")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_pending_deposit_kb(admin_username: str = ADMIN_USERNAME, lang: str = "bn") -> InlineKeyboardMarkup:
    """Displays prominent Contact Admin button for pending deposit approval."""
    contact_url = f"https://t.me/{admin_username}"
    buttons = [
        [
            make_custom_button(text=t("btn_fast_approval", lang), url=contact_url, emoji_key="zap")
        ],
        [
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_fsm_kb(lang: str = "bn") -> InlineKeyboardMarkup:
    """Cancel any ongoing input."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_custom_button(text=t("btn_cancel_home", lang), callback_data="cancel_fsm", emoji_key="cross")]
    ])

def get_free_claim_categories_kb(counts: Dict[str, int], lang: str = "bn") -> InlineKeyboardMarkup:
    """Category selector hub for free claim giveaways."""
    acc_cnt = counts.get("accounts", 0)
    ck_cnt = counts.get("cookies", 0)
    sub_cnt = counts.get("subscription", 0)
    ch_cnt = counts.get("channel", 0)
    drv_cnt = counts.get("tools_drive", 0)
    tot_cnt = counts.get("total", 0)

    if lang in ["en", "hi"]:
        acc_txt = f"🔐 Premium Accounts ({acc_cnt})"
        ck_txt = f"🍪 Browser Cookies ({ck_cnt})"
        sub_txt = f"👑 Subscriptions & Keys ({sub_cnt})"
        ch_txt = f"📢 VIP Channels ({ch_cnt})"
        drv_txt = f"💾 Tools & Cloud Drive ({drv_cnt})"
        tot_txt = f"🔥 All Active Giveaways ({tot_cnt})"
    else:
        acc_txt = f"🔐 প্রিমিয়াম একাউন্টস ({acc_cnt} টি)"
        ck_txt = f"🍪 ব্রাউজার কুকিজ ({ck_cnt} টি)"
        sub_txt = f"👑 সাবস্ক্রিপশন ও কি ({sub_cnt} টি)"
        ch_txt = f"📢 ভিআইপি চ্যানেল ({ch_cnt} টি)"
        drv_txt = f"💾 টুলস ও ক্লাউড ড্রাইভ ({drv_cnt} টি)"
        tot_txt = f"🔥 সব সক্রিয় গিভঅ্যাওয়ে ({tot_cnt} টি)"

    buttons = [
        [
            make_custom_button(text=acc_txt, callback_data="claim_cat:accounts", emoji_key="diamond"),
            make_custom_button(text=ck_txt, callback_data="claim_cat:cookies", emoji_key="sparkle")
        ],
        [
            make_custom_button(text=sub_txt, callback_data="claim_cat:subscription", emoji_key="crown"),
            make_custom_button(text=ch_txt, callback_data="claim_cat:channel", emoji_key="channel")
        ],
        [
            make_custom_button(text=drv_txt, callback_data="claim_cat:tools_drive", emoji_key="box")
        ],
        [
            make_custom_button(text=tot_txt, callback_data="claim_cat:all", emoji_key="fire")
        ],
        [
            make_custom_button(text=t("btn_refresh", lang), callback_data="nav_free_claim", emoji_key="refresh"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_free_claim_hub_kb(drops: List[Dict[str, Any]], category: str = "all", lang: str = "bn") -> InlineKeyboardMarkup:
    """Buttons for selecting an active free drop within a category."""
    buttons = []
    cat_icons = {
        "accounts": "🔐",
        "cookies": "🍪",
        "subscription": "👑",
        "channel": "📢",
        "tools_drive": "💾"
    }
    for d in drops:
        rem = d.get("remaining", 0)
        c_icon = cat_icons.get(d.get("giveaway_category", "accounts"), "🎁")
        btn_text = f"{c_icon} {d['title'][:20]} ({rem} টি বাকি)" if lang == "bn" else f"{c_icon} {d['title'][:20]} ({rem} left)"
        em_key = "fire" if rem > 0 else "cross"
        buttons.append([
            make_custom_button(text=btn_text, callback_data=f"view_free_drop:{d['id']}", emoji_key=em_key)
        ])
    
    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data="nav_free_claim", emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_claim_action_kb(
    drop_id: int,
    already_claimed: bool = False,
    remaining: int = 0,
    category: str = "accounts",
    site_link: str = "",
    lang: str = "bn",
    is_locked: bool = False,
    ref_link: str = "",
    drop_title: str = ""
) -> InlineKeyboardMarkup:
    """Action button on a specific free drop detail card with optional website portal button and viral share-to-unlock button."""
    import urllib.parse
    buttons = []
    if already_claimed:
        claimed_txt = "✅ ক্লেইম সম্পন্ন" if lang == "bn" else "✅ Claimed"
        buttons.append([
            make_custom_button(text=claimed_txt, callback_data="noop_claimed", emoji_key="check")
        ])
    elif remaining <= 0:
        full_txt = "❌ সব স্লট শেষ" if lang == "bn" else "❌ Slot Full"
        buttons.append([
            make_custom_button(text=full_txt, callback_data="noop_full", emoji_key="cross")
        ])
    elif is_locked:
        # Generate 1-click share URL
        clean_title = drop_title[:30] if drop_title else "Premium Giveaway"
        if lang == "bn":
            share_msg = f"🔥 দোস্ত! এই বটে '{clean_title}' সম্পূর্ণ ফ্রিতে দিচ্ছে!\n\nএখনই জয়েন করে ফ্রিতে ক্লেইম করে নে:\n"
        else:
            share_msg = f"🔥 Get '{clean_title}' completely FREE on this bot!\n\nJoin now to claim:\n"
        encoded_text = urllib.parse.quote(share_msg)
        encoded_url = urllib.parse.quote(ref_link)
        share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"
        
        copy_label = "📋 রেফারেল লিংক কপি করুন" if lang == "bn" else "📋 Copy Referral Link"
        try:
            from aiogram.types import CopyTextButton
            copy_btn = make_custom_button(text=copy_label, copy_text=CopyTextButton(text=ref_link), emoji_key="box")
        except Exception:
            copy_btn = make_custom_button(text=copy_label, callback_data="nav_referral", emoji_key="box")

        share_label = "📲 বন্ধুদের সাথে শেয়ার করুন" if lang == "bn" else "📲 Share with Friends"
        refresh_label = "🔄 রিফ্রেশ / চেক করুন" if lang == "bn" else "🔄 Refresh / Check"
        buttons.append([
            make_custom_button(text=share_label, url=share_url, emoji_key="broadcast")
        ])
        buttons.append([
            copy_btn,
            make_custom_button(text=refresh_label, callback_data=f"view_free_drop:{drop_id}", emoji_key="refresh")
        ])
    else:
        claim_text = "⚡ ক্লেইম করুন (Claim Free Slot) 🎁" if lang == "bn" else "⚡ Claim Free Slot Now 🎁"
        buttons.append([
            make_custom_button(text=claim_text, callback_data=f"execute_free_claim:{drop_id}", emoji_key="zap")
        ])

    if site_link and site_link.strip().startswith("http"):
        btn_text = "🌐 ওয়েবসাইটে প্রবেশ করুন" if lang == "bn" else "🌐 Visit Website"
        buttons.append([
            make_custom_button(text=btn_text, url=site_link.strip(), emoji_key="channel")
        ])

    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data=f"claim_cat:{category}", emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_profile_kb(user_id: int, available_points: int = 0, balance_bdt: float = 0.0, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons attached to My Profile card."""
    if lang == "bn":
        pts_txt = f"💱 পয়েন্ট ➔ টাকা ({available_points} Pts)"
        conv_curr_txt = "💵 টাকা ➔ ডলার (BDT ➔ USD)"
        crs_ref_txt = "📚 কোর্স রেফারেলস"
        hist_txt = "📜 কনভার্সন হিস্ট্রি"
        ref_hub_txt = "👥 রেফারেল হাব"
        refresh_txt = "🔄 রিফ্রেশ প্রোফাইল"
    else:
        pts_txt = f"💱 Points ➔ Cash ({available_points} Pts)"
        conv_curr_txt = "💵 Currency (BDT ➔ USD)"
        crs_ref_txt = "📚 Course Referrals"
        hist_txt = "📜 Conversion History"
        ref_hub_txt = "👥 Referral Hub"
        refresh_txt = "🔄 Refresh Profile"

    buttons = [
        [
            make_custom_button(
                text=pts_txt,
                callback_data="profile_conv_points",
                emoji_key="diamond"
            ),
            make_custom_button(
                text=conv_curr_txt,
                callback_data="profile_conv_usd",
                emoji_key="wallet"
            )
        ],
        [
            make_custom_button(
                text=crs_ref_txt,
                callback_data="profile_course_refs",
                emoji_key="courses"
            ),
            make_custom_button(
                text=hist_txt,
                callback_data="profile_conv_history",
                emoji_key="orders"
            )
        ],
        [
            make_custom_button(
                text=ref_hub_txt,
                callback_data="nav_referral",
                emoji_key="referral"
            ),
            make_custom_button(
                text=refresh_txt,
                callback_data="profile_refresh",
                emoji_key="refresh"
            )
        ],
        [
            make_custom_button(
                text=t("btn_home", lang),
                callback_data="main_menu",
                emoji_key="home"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_points_conversion_kb(available_points: int, rate_bdt: float, lang: str = "bn") -> InlineKeyboardMarkup:
    """Quick conversion buttons for Referral Points -> BDT."""
    buttons = []
    quick_opts = []
    if available_points >= 1:
        quick_opts.append(
            make_custom_button(
                text=f"1 Pts = ৳{int(rate_bdt)}",
                callback_data="do_conv_pts:1",
                emoji_key="sparkle"
            )
        )
    if available_points >= 5:
        quick_opts.append(
            make_custom_button(
                text=f"5 Pts = ৳{int(5 * rate_bdt)}",
                callback_data="do_conv_pts:5",
                emoji_key="sparkle"
            )
        )
    if quick_opts:
        buttons.append(quick_opts)
        
    quick_opts2 = []
    if available_points >= 10:
        quick_opts2.append(
            make_custom_button(
                text=f"10 Pts = ৳{int(10 * rate_bdt)}",
                callback_data="do_conv_pts:10",
                emoji_key="sparkle"
            )
        )
    if available_points > 1:
        all_label = f"সব {available_points} Pts = ৳{int(available_points * rate_bdt)}" if lang == "bn" else f"All {available_points} Pts = ৳{int(available_points * rate_bdt)}"
        quick_opts2.append(
            make_custom_button(
                text=all_label,
                callback_data="do_conv_pts:all",
                emoji_key="fire"
            )
        )
    if quick_opts2:
        buttons.append(quick_opts2)

    custom_label = "✏️ কাস্টম পরিমাণ লিখুন" if lang == "bn" else "✏️ Custom Amount"
    buttons.append([
        make_custom_button(
            text=custom_label,
            callback_data="conv_pts_custom",
            emoji_key="edit"
        )
    ])
    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_bdt_usd_conversion_kb(balance_bdt: float, live_rate: float, lang: str = "bn") -> InlineKeyboardMarkup:
    """Quick conversion buttons for BDT Balance -> USD Balance."""
    buttons = []
    quick_opts = []
    if balance_bdt >= live_rate:
        quick_opts.append(
            make_custom_button(
                text=f"৳{int(live_rate)} = $1 USD",
                callback_data="do_conv_usd:1",
                emoji_key="sparkle"
            )
        )
    if balance_bdt >= live_rate * 5:
        quick_opts.append(
            make_custom_button(
                text=f"৳{int(live_rate * 5)} = $5 USD",
                callback_data="do_conv_usd:5",
                emoji_key="sparkle"
            )
        )
    if quick_opts:
        buttons.append(quick_opts)

    quick_opts2 = []
    if balance_bdt >= live_rate * 10:
        quick_opts2.append(
            make_custom_button(
                text=f"৳{int(live_rate * 10)} = $10 USD",
                callback_data="do_conv_usd:10",
                emoji_key="sparkle"
            )
        )
    if balance_bdt >= 10:
        max_usd = round(balance_bdt / live_rate, 2)
        all_bal_label = f"সব টাকা ➔ ${max_usd} USD" if lang == "bn" else f"All Balance ➔ ${max_usd} USD"
        quick_opts2.append(
            make_custom_button(
                text=all_bal_label,
                callback_data="do_conv_usd:all",
                emoji_key="fire"
            )
        )
    if quick_opts2:
        buttons.append(quick_opts2)

    custom_usd_label = "✏️ কাস্টম ডলার লিখুন" if lang == "bn" else "✏️ Custom USD Amount"
    buttons.append([
        make_custom_button(
            text=custom_usd_label,
            callback_data="conv_usd_custom",
            emoji_key="edit"
        )
    ])
    buttons.append([
        make_custom_button(text=t("btn_back", lang), callback_data="profile_refresh", emoji_key="back"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_ref_share_kb(bot_username: str, user_id: int, product: Dict[str, Any], lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons for Course-Specific Referral Link."""
    try:
        from aiogram.types import CopyTextButton
        has_copy = True
    except Exception:
        has_copy = False

    clean_title = localize_item_name(product['title'], lang)
    course_link = f"https://t.me/{bot_username}?start=ref_{user_id}_c{product['id']}"
    if lang == "bn":
        share_msg = (
            f"🔥 বন্ধু, {clean_title} কোর্সটি টেলিগ্রামে সম্পূর্ণ অফিশিয়ালভাবে পাওয়া যাচ্ছে!\n\n"
            f"নিচের লিংকে ক্লিক করে সরাসরি কোর্সটি দেখে নাও:\n"
        )
    else:
        share_msg = (
            f"🔥 Hey! Check out {clean_title} on Telegram:\n\n"
            f"Click the link below to view details & access:\n"
        )
    encoded_text = urllib.parse.quote(share_msg)
    encoded_url = urllib.parse.quote(course_link)
    share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"

    copy_btn_text = t("btn_copy_link", lang)
    if has_copy:
        copy_btn = make_custom_button(text=copy_btn_text, copy_text=CopyTextButton(text=course_link), emoji_key="box")
    else:
        copy_btn = make_custom_button(text=copy_btn_text, callback_data=f"copy_course_ref:{product['id']}", emoji_key="box")

    share_btn_text = "টেলিগ্রামে শেয়ার" if lang == "bn" else "Share on Telegram"
    back_btn_text = "🔙 কোর্সে ফিরে যান" if lang == "bn" else "🔙 Back to Course"
    buttons = [
        [
            copy_btn,
            make_custom_button(text=share_btn_text, url=share_url, emoji_key="broadcast")
        ],
        [
            make_custom_button(text=back_btn_text, callback_data=f"prod:{product['id']}", emoji_key="back"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_search_results_kb(products: List[Dict[str, Any]], query: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Buttons for multiple search matches."""
    buttons = []
    for prod in products[:6]:
        c_title = localize_item_name(prod['title'], lang)
        btn_text = f"🎓 {c_title[:28]} — ৳{int(prod['price_bdt'])}"
        buttons.append([
            make_custom_button(text=btn_text, callback_data=f"prod:{prod['id']}", emoji_key="sparkle")
        ])
    req_txt = "🎯 অন্য কোর্স রিকোয়েস্ট করুন" if lang == "bn" else "🎯 Request Another Course"
    all_courses_txt = "🔙 সকল কোর্স ব্রাউজ করুন" if lang == "bn" else "🔙 Browse All Courses"
    buttons.append([
        make_custom_button(text=req_txt, callback_data="req_course_start", emoji_key="edit")
    ])
    buttons.append([
        make_custom_button(text=all_courses_txt, callback_data="back_cats", emoji_key="courses"),
        make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_not_found_kb(query: str, lang: str = "bn") -> InlineKeyboardMarkup:
    """Action buttons shown when a searched course or link is not in DB."""
    req_txt = "🎯 এই কোর্সের রিকোয়েস্ট পাঠান" if lang == "bn" else "🎯 Request This Course"
    admin_chat_txt = "💬 সরাসরি অ্যাডমিনকে জানান" if lang == "bn" else "💬 Live Admin Chat"
    all_courses_txt = "🎓 সকল কোর্স ব্রাউজ করুন" if lang == "bn" else "🎓 Browse All Courses"
    buttons = [
        [
            make_custom_button(text=req_txt, callback_data="quick_req_submit", emoji_key="edit")
        ],
        [
            make_custom_button(text=admin_chat_txt, url=f"https://t.me/{ADMIN_USERNAME}", emoji_key="support")
        ],
        [
            make_custom_button(text=all_courses_txt, callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_casual_guide_kb(lang: str = "bn") -> InlineKeyboardMarkup:
    """Helpful navigation card sent when user sends consecutive casual/greeting messages."""
    browse_txt = "🎓 কোর্স ক্যাটালগ দেখুন" if lang == "bn" else "🎓 Browse Courses"
    digital_txt = "⚡ ডিজিটাল শপ" if lang == "bn" else "⚡ Digital Store"
    req_txt = "🎯 যে কোর্সটি লাগবে রিকোয়েস্ট করুন" if lang == "bn" else "🎯 Request a Course"
    support_txt = "💬 সরাসরি সাপোর্ট অ্যাডমিন" if lang == "bn" else "💬 Live Support Admin"
    buttons = [
        [
            make_custom_button(text=browse_txt, callback_data="back_cats", emoji_key="courses"),
            make_custom_button(text=digital_txt, callback_data="cat:digital", emoji_key="digital")
        ],
        [
            make_custom_button(text=req_txt, callback_data="req_course_start", emoji_key="edit")
        ],
        [
            make_custom_button(text=support_txt, url=f"https://t.me/{ADMIN_USERNAME}", emoji_key="support"),
            make_custom_button(text=t("btn_home", lang), callback_data="main_menu", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_request_prompt_kb(lang: str = "bn") -> InlineKeyboardMarkup:
    """Buttons on course request input prompt."""
    buttons = [
        [
            make_custom_button(text=t("btn_cancel", lang), callback_data="cancel_course_req", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


