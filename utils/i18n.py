# Multi-Language Localization Engine (Bangla, English, Hindi)
import re
from typing import Dict

LANGUAGES = {
    "bn": "🇧🇩 বাংলা",
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिंदी"
}

def localize_item_name(name: str, lang: str = "bn") -> str:
    """Intelligently localizes category and product titles if they contain dual language tags.
    Example: 'All Premium Courses (কোর্স ভল্ট)' -> 'All Premium Courses' (en) or 'All Premium Courses (কোর্স ভল্ট)' (bn).
    """
    if not name:
        return ""
    if lang in ["en", "hi"]:
        # Remove parenthetical Bengali text at end (e.g. '(কোর্স ভল্ট)')
        clean = re.sub(r'\s*\([\u0980-\u09FF\s&/,\-–—]+\)$', '', name).strip()
        # Handle slash separated: "English / বাংলা"
        if " / " in clean:
            parts = clean.split(" / ")
            ascii_parts = [p for p in parts if any(c.isascii() and c.isalpha() for c in p)]
            if ascii_parts:
                return ascii_parts[0].strip()
        return clean if clean else name
    return name

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Main Navigation Buttons
    "btn_home": {
        "bn": "🏠 মূল মেনু",
        "en": "🏠 Main Menu",
        "hi": "🏠 मुख्य मेनू"
    },
    "btn_courses": {
        "bn": "🎓 Browse Courses (কোর্স সমূহ)",
        "en": "🎓 Browse Courses",
        "hi": "🎓 कोर्सेस देखें (Courses)"
    },
    "btn_digital": {
        "bn": "⚡ Digital Tools & Accounts",
        "en": "⚡ Digital Tools & Accounts",
        "hi": "⚡ डिजिटल टूल्स (Tools & Accounts)"
    },
    "btn_deposit": {
        "bn": "💳 Add Balance (ডিপোজিট)",
        "en": "💳 Add Balance (Deposit)",
        "hi": "💳 बैलेंस जोड़ें (Deposit)"
    },
    "btn_reseller": {
        "bn": "🤝 Reseller Hub (রিসেলার প্যানেল)",
        "en": "🤝 Reseller Hub",
        "hi": "🤝 रीसेलर हब (Reseller Hub)"
    },
    "btn_orders": {
        "bn": "📦 My Purchases (অর্ডার)",
        "en": "📦 My Purchases",
        "hi": "📦 मेरी खरीदारी (Orders)"
    },
    "btn_profile": {
        "bn": "👤 My Profile (প্রোফাইল)",
        "en": "👤 My Profile",
        "hi": "👤 मेरी प्रोफाइल (Profile)"
    },
    "btn_language": {
        "bn": "🌐 Language (ভাষা)",
        "en": "🌐 Language",
        "hi": "🌐 भाषा (Language)"
    },
    "btn_support": {
        "bn": "💬 Support & Help (হেল্প)",
        "en": "💬 Support & Help",
        "hi": "💬 सपोर्ट और सहायता (Help)"
    },
    "btn_verify_reseller": {
        "bn": "🛡️ Verify Reseller (রিসেলার যাচাই)",
        "en": "🛡️ Verify Reseller",
        "hi": "🛡️ रीसेलर सत्यापन (Verify Reseller)"
    },
    "btn_referral": {
        "bn": "👥 Refer & Earn (ফ্রি কোর্স)",
        "en": "👥 Refer & Earn (Free Courses)",
        "hi": "👥 रेफर और कमाएं (Free Courses)"
    },
    "btn_free_claim": {
        "bn": "🎁 Free Claim (গিভঅ্যাওয়ে)",
        "en": "🎁 Free Rewards",
        "hi": "🎁 फ्री रिवॉर्ड्स"
    },

    # Common Action Buttons
    "btn_back": {
        "bn": "🔙 পেছনে যান",
        "en": "🔙 Back",
        "hi": "🔙 वापस जाएं"
    },
    "btn_back_cats": {
        "bn": "🔙 ক্যাটাগরি তালিকা",
        "en": "🔙 Categories",
        "hi": "🔙 श्रेणियां"
    },
    "btn_back_subcats": {
        "bn": "🔙 সাব-ক্যাটাগরি",
        "en": "🔙 Sub-categories",
        "hi": "🔙 उप-श्रेणियां"
    },
    "btn_cancel": {
        "bn": "❌ বাতিল করুন",
        "en": "❌ Cancel",
        "hi": "❌ रद्द करें"
    },
    "btn_cancel_home": {
        "bn": "❌ বাতিল / হোম",
        "en": "❌ Cancel / Home",
        "hi": "❌ रद्द / होम"
    },
    "btn_buy_now": {
        "bn": "🚀 Buy Now",
        "en": "🚀 Buy Now",
        "hi": "🚀 अभी खरीदें"
    },
    "btn_out_of_stock": {
        "bn": "❌ স্টক শেষ (Out of Stock)",
        "en": "❌ Out of Stock",
        "hi": "❌ आउट ऑफ स्टॉक"
    },
    "btn_apply_coupon": {
        "bn": "🎟️ কুপন কোড ব্যবহার করুন",
        "en": "🎟️ Apply Promo Coupon",
        "hi": "🎟️ कूपन कोड दर्ज करें"
    },
    "btn_add_balance": {
        "bn": "💳 ব্যালেন্স যোগ করুন",
        "en": "💳 Add Balance",
        "hi": "💳 बैलेंस जोड़ें"
    },
    "btn_claim_ref": {
        "bn": "🎁 রেফারেল পয়েন্ট দিয়ে নিন",
        "en": "🎁 Claim with Referrals",
        "hi": "🎁 रेफरल से क्लेम करें"
    },
    "btn_share_course_ref": {
        "bn": "🔗 এই কোর্সের রেফার লিংক",
        "en": "🔗 Share & Earn with Link",
        "hi": "🔗 शेयर और कमाएं"
    },
    "btn_view_sales_page": {
        "bn": "🌐 সেলস পেইজ ও কারিকুলাম",
        "en": "🌐 Sales Page & Curriculum",
        "hi": "🌐 सेल्स पेज और विवरण"
    },
    "btn_vip_channel_access": {
        "bn": "📢 VIP Channel Access",
        "en": "📢 VIP Channel Access",
        "hi": "📢 VIP चैनल एक्सेस"
    },
    "btn_personal_account_access": {
        "bn": "🔐 Personal Account / Drive",
        "en": "🔐 Personal Account / Drive",
        "hi": "🔐 पर्सनल अकाउंट / ड्राइव"
    },
    "btn_copy_link": {
        "bn": "📋 লিংক কপি করুন",
        "en": "📋 Copy Link",
        "hi": "📋 लिंक कॉपी करें"
    },
    "btn_share_telegram": {
        "bn": "🚀 টেলিগ্রামে শেয়ার করুন",
        "en": "🚀 Share on Telegram",
        "hi": "🚀 टेलीग्राम पर शेयर करें"
    },
    "btn_browse_catalog": {
        "bn": "🎓 কোর্স ক্যাটালগ",
        "en": "🎓 Browse Catalog",
        "hi": "🎓 कोर्स कैटलॉग"
    },
    "btn_leaderboard": {
        "bn": "🏆 লিডারবোর্ড",
        "en": "🏆 Leaderboard",
        "hi": "🏆 लीडरबोर्ड"
    },
    "btn_refresh": {
        "bn": "🔄 রিফ্রেশ",
        "en": "🔄 Refresh",
        "hi": "🔄 रीफ्रेश"
    },

    # Main Dashboard Single-Screen Text
    "dashboard_notice_title": {
        "bn": "📢 <b>বিশেষ নোটিশ:</b>",
        "en": "📢 <b>Official Notice:</b>",
        "hi": "📢 <b>आधिकारिक सूचना:</b>"
    },

    # Welcome Message
    "welcome_msg": {
        "bn": (
            "👋 **স্বাগতম, {name}!**\n\n"
            "আমাদের প্রিমিয়াম **কোর্স ও ডিজিটাল প্রডাক্টস শপে** আপনাকে স্বাগতম।\n\n"
            "✨ **আমাদের বিশেষত্ব:**\n"
            "• ৯০% হাই-ভ্যালু ভিডিও এডিটিং, গ্রাফিক্স, কোডিং ও এআই কোর্স\n"
            "• ১০% প্রিমিয়াম ডিজিটাল টুলস ও অ্যাকাউন্টের অ্যাক্সেস\n"
            "• পার্সোনাল ওয়ান-টাইম প্রাইভেট চ্যানেল অ্যাক্সেস লিঙ্ক\n"
            "• **রিসেলার প্রোগ্রাম:** পাইকারি মূল্যে কিনে আনলিমিটেড ইনকামের সুযোগ!\n\n"
            "👇 ব্রাউজ করতে নিচের মেনু থেকে অপশন নির্বাচন করুন:"
        ),
        "en": (
            "👋 **Welcome, {name}!**\n\n"
            "Welcome to our premium **Course & Digital Product Store**.\n\n"
            "✨ **Highlights:**\n"
            "• 90% High-Value Video Editing, Graphic Design, Web Dev & AI Courses\n"
            "• 10% Premium Digital Tools & Accounts\n"
            "• Instant 1-Time Single-Use VIP Access Links\n"
            "• **Reseller Program:** Buy at wholesale rates and earn unlimited profit!\n\n"
            "👇 Choose an option from the menu below:"
        ),
        "hi": (
            "👋 **स्वागत है, {name}!**\n\n"
            "हमारे प्रीमियम **कोर्स और डिजिटल प्रोडक्ट स्टोर** में आपका स्वागत है।\n\n"
            "✨ **मुख्य विशेषताएं:**\n"
            "• 90% हाई-वैल्यू वीडियो एडिटिंग, ग्राफिक डिजाइन, कोडिंग और AI कोर्सेस\n"
            "• 10% प्रीमियम डिजिटल टूल्स और अकाउंट्स\n"
            "• इंस्टेंट 1-टाइम प्राइवेट वीआईपी एक्सेस लिंक्स\n"
            "• **रीसेलर प्रोग्राम:** थोक भाव पर खरीदें और असीमित कमाई करें!\n\n"
            "👇 नीचे दिए गए मेनू से विकल्प चुनें:"
        )
    },

    # Catalog & Shop Screens
    "shop_all_cats_text": {
        "bn": (
            "🛍️ <b>প্রিমিয়াম শপ — সকল ক্যাটাগরি ও প্ল্যাটফর্ম</b> 🛍️\n\n"
            "আমাদের ডিজিটাল স্টোরে প্রিমিয়াম একাডেমি কোর্স, টুলস ও অ্যাকাউন্ট সাজানো আছে।\n"
            "👇 আপনার পছন্দের প্ল্যাটফর্ম বা ক্যাটাগরি বেছে নিন:"
        ),
        "en": (
            "🛍️ <b>PREMIUM STORE — ALL CATEGORIES & PLATFORMS</b> 🛍️\n\n"
            "Browse our curated catalog of masterclasses, AI subscriptions, and software access.\n"
            "👇 Select your desired department or category:"
        ),
        "hi": (
            "🛍️ <b>प्रीमियम स्टोर — सभी श्रेणियां और प्लेटफॉर्म</b> 🛍️\n\n"
            "प्रीमियम कोर्सेस, एआई टूल्स और सत्यापित डिजिटल अकाउंट्स।\n"
            "👇 अपनी पसंदीदा श्रेणी चुनें:"
        )
    },
    "shop_courses_text": {
        "bn": (
            "🎓 <b>প্রিমিয়াম কোর্স স্টোর — কারিকুলাম ও ক্যাটাগরি</b> 🎓\n\n"
            "আমাদের ডিজিটাল শপে সেরা ইন্সট্রাক্টরদের শীর্ষ কোর্সগুলো সাজানো আছে।\n"
            "👇 আপনার পছন্দের ক্যাটাগরি বেছে নিন:"
        ),
        "en": (
            "🎓 <b>PREMIUM COURSES — CURRICULUM & TRACKS</b> 🎓\n\n"
            "Full curriculum masterclasses with lifetime cloud drive & VIP channels.\n"
            "👇 Select a course category below:"
        ),
        "hi": (
            "🎓 <b>प्रीमियम कोर्सेस — पाठ्यक्रम और श्रेणियां</b> 🎓\n\n"
            "लाइफटाइम एक्सेस के साथ शीर्ष कोर्सेस।\n"
            "👇 नीचे दी गई श्रेणी चुनें:"
        )
    },
    "shop_digital_text": {
        "bn": (
            "⚡ <b>ডিজিটাল একাউন্টস ও এআই টুলস হাব</b> ⚡\n\n"
            "ওটিটি প্ল্যাটফর্ম, ভিপিএন, এআই টুলস ও প্রিমিয়াম সফটওয়্যার লাইসেন্স।\n"
            "👇 আপনার প্রয়োজনীয় ক্যাটাগরি নির্বাচন করুন:"
        ),
        "en": (
            "⚡ <b>DIGITAL ACCOUNTS & AI SUBSCRIPTION HUB</b> ⚡\n\n"
            "OTT platforms, VPNs, AI tools, and verified software licenses.\n"
            "👇 Select your category below:"
        ),
        "hi": (
            "⚡ <b>डिजिटल अकाउंट्स और एआई टूल्स</b> ⚡\n\n"
            "ओटीटी, वीपीएन और एआई टूल्स।\n"
            "👇 अपनी श्रेणी चुनें:"
        )
    },
    "cat_no_products": {
        "bn": (
            "⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো কোর্স/প্রোডাক্ট সক্রিয় নেই।\n"
            "খুব শীঘ্রই নতুন কোর্স ও স্টক যুক্ত করা হবে!"
        ),
        "en": (
            "⚠️ There are currently no active products in this category.\n"
            "New stock and masterclasses will be added shortly!"
        ),
        "hi": (
            "⚠️ इस श्रेणी में वर्तमान में कोई उत्पाद सक्रिय नहीं है।\n"
            "जल्द ही नया स्टॉक जोड़ा जाएगा!"
        )
    },
    "cat_products_count_prompt": {
        "bn": (
            "📦 মোট উপলব্ধ প্রোডাক্ট: <b>{count} টি</b>\n"
            "👉 বিস্তারিত ও কিনতে নিচে ক্লিক করুন:"
        ),
        "en": (
            "📦 Available Products: <b>{count}</b>\n"
            "👉 Tap below for complete details & access:"
        ),
        "hi": (
            "📦 उपलब्ध उत्पाद: <b>{count}</b>\n"
            "👉 विवरण देखने के लिए नीचे क्लिक करें:"
        )
    },
    "subcat_selector_prompt": {
        "bn": (
            "📚 <b>বিষয়ভিত্তিক কোর্স ট্র্যাক ও সাব-ক্যাটাগরি:</b>\n"
            "👇 আপনি কোন বিষয়ের কোর্স খুঁজছেন নিচে বেছে নিন:"
        ),
        "en": (
            "📚 <b>Specialized Course Tracks & Sub-Categories:</b>\n"
            "👇 Choose your desired track below:"
        ),
        "hi": (
            "📚 <b>कोर्स ट्रैक्स और उप-श्रेणियां:</b>\n"
            "👇 अपना विषय चुनें:"
        )
    },
    "subcat_empty_notice": {
        "bn": (
            "⚠️ এই সাব-ক্যাটাগরিতে বর্তমানে কোনো কোর্স সক্রিয় নেই।\n"
            "খুব শীঘ্রই নতুন কোর্স ও স্টক যুক্ত করা হবে!"
        ),
        "en": (
            "⚠️ No active courses found in this sub-category currently.\n"
            "Check back soon for upcoming drops!"
        ),
        "hi": (
            "⚠️ इस उप-श्रेणी में वर्तमान में कोई कोर्स नहीं है।"
        )
    },

    # Language Selection Prompt
    "lang_select_prompt": {
        "bn": "🌐 **আপনার পছন্দের ভাষা নির্বাচন করুন / Select your language / अपनी भाषा चुनें:**",
        "en": "🌐 **Select your preferred language / আপনার পছন্দের ভাষা নির্বাচন করুন / अपनी भाषा चुनें:**",
        "hi": "🌐 **अपनी पसंदीदा भाषा चुनें / Select your language / আপনার পছন্দের ভাষা নির্বাচন করুন:**"
    },
    "lang_updated": {
        "bn": "✅ ভাষা সফলভাবে **বাংলা** তে পরিবর্তন করা হয়েছে!",
        "en": "✅ Language has been successfully changed to **English**!",
        "hi": "✅ भाषा सफलतापूर्वक **हिंदी** में बदल दी गई है!"
    },

    # Profile Ledger
    "profile_ledger": {
        "bn": (
            "👤 **আপনার ইউজার প্রোফাইল ও লেজার**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🆔 **ইউজার আইডি:** `{user_id}`\n"
            "👤 **নাম:** {name}\n"
            "🏷️ **ইউজারনেম:** `{username}`\n"
            "🎖️ **অ্যাকাউন্ট টাইপ:** {account_type}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 **ওয়ালেট ব্যালেন্স:**\n"
            "• BDT: `৳{balance_bdt:.2f}`\n"
            "• USD: `${balance_usd:.2f}`\n\n"
            "📊 **মোট কেনাকাটা:** `৳{total_spent_bdt:.2f}` (${total_spent_usd:.2f})\n"
            "📦 **মোট সম্পন্ন অর্ডার:** `{orders_count} টি`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "en": (
            "👤 **Your User Profile & Account Ledger**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🆔 **User ID:** `{user_id}`\n"
            "👤 **Name:** {name}\n"
            "🏷️ **Username:** `{username}`\n"
            "🎖️ **Account Type:** {account_type}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 **Wallet Balance:**\n"
            "• BDT: `৳{balance_bdt:.2f}`\n"
            "• USD: `${balance_usd:.2f}`\n\n"
            "📊 **Total Purchases:** `৳{total_spent_bdt:.2f}` (${total_spent_usd:.2f})\n"
            "📦 **Completed Orders:** `{orders_count}`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "hi": (
            "👤 **आपकी प्रोफाइल और खाता विवरण**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🆔 **यूजर आईडी:** `{user_id}`\n"
            "👤 **नाम:** {name}\n"
            "🏷️ **यूजरनेम:** `{username}`\n"
            "🎖️ **अकाउंट प्रकार:** {account_type}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 **वॉलेट बैलेंस:**\n"
            "• BDT: `৳{balance_bdt:.2f}`\n"
            "• USD: `${balance_usd:.2f}`\n\n"
            "📊 **कुल खरीदारी:** `৳{total_spent_bdt:.2f}` (${total_spent_usd:.2f})\n"
            "📦 **सफल ऑर्डर्स:** `{orders_count}`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
    },

    # Reseller Badge in Profile
    "reseller_badge_active": {
        "bn": "💎 ভেরিফাইড রিসেলার",
        "en": "💎 Verified VIP Reseller",
        "hi": "💎 वेरीफाइड वीआईपी रीसेलर"
    },
    "reseller_badge_regular": {
        "bn": "সাধারণ ক্রেতা",
        "en": "Verified Customer",
        "hi": "सत्यापित ग्राहक"
    },

    # Support Message
    "support_msg": {
        "bn": (
            "💬 **কাস্টমার সাপোর্ট ও হেল্পডেস্ক**\n\n"
            "যেকোনো প্রশ্ন, কোর্স সম্পর্কিত তথ্য বা পেমেন্ট ভেরিফিকেশনের জন্য সরাসরি আমাদের সাথে যোগাযোগ করুন:\n\n"
            "👨‍💻 **সাপোর্ট অ্যাডমিন:** @{admin}\n"
            "📢 **অফিসিয়াল চ্যানেল:** {channel}\n\n"
            "⚡ যে কোনো জরুরি প্রয়োজনে সরাসরি ইনবক্স করতে নিচের বাটনে চাপুন:"
        ),
        "en": (
            "💬 **Customer Support & Help Desk**\n\n"
            "For any inquiries, course access assistance, or deposit queries, please contact us directly:\n\n"
            "👨‍💻 **Support Admin:** @{admin}\n"
            "📢 **Official Channel:** {channel}\n\n"
            "⚡ Click the button below to message support directly:"
        ),
        "hi": (
            "💬 **ग्राहक सहायता और हेल्पडेस्क**\n\n"
            "किसी भी सवाल, कोर्स से जुड़ी जानकारी या पेमेंट वेरिफिकेशन के लिए हमसे सीधे संपर्क करें:\n\n"
            "👨‍💻 **सपोर्ट एडमिन:** @{admin}\n"
            "📢 **ऑफिशियल चैनल:** {channel}\n\n"
            "⚡ सहायता के लिए नीचे दिए गए बटन पर क्लिक करें:"
        )
    },

    # Deposit Screen
    "deposit_menu_text": {
        "bn": (
            '<tg-emoji emoji-id="5395542928909150340">💰</tg-emoji> <b>ক্যাশিয়ার ডিপোজিট ও ব্যালেন্স রিচার্জ মেনু</b> <tg-emoji emoji-id="5395542928909150340">💰</tg-emoji>\n'
            '<i>আপনার ওয়ালেটে ইনস্ট্যান্ট ব্যালেন্স যোগ করতে পছন্দের পেমেন্ট মেথডটি নির্বাচন করুন:</i>\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            '• <tg-emoji emoji-id="6237941149873478197">💳</tg-emoji> <b>bKash (Agent):</b> বিকাশ ক্যাশ আউট (Cash Out - BDT)\n'
            '• <tg-emoji emoji-id="6235269688805301565">💳</tg-emoji> <b>Nagad (Agent):</b> নগদ ক্যাশ আউট (Cash Out - BDT)\n'
            '• <tg-emoji emoji-id="6235282831405227077">💳</tg-emoji> <b>Rocket (Personal):</b> রকেট সেন্ড মানি (Send Money - BDT)\n'
            '• <tg-emoji emoji-id="6235545537374855311">💳</tg-emoji> <b>Binance Pay:</b> USDT ডিপোজিট (0% ফি, ডলার ব্যালেন্স)\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
            '⚡ <b>সুপারফাস্ট ভেরিফিকেশন:</b> টাকা পাঠানোর পর TrxID ও স্ক্রিনশট সাবমিট করলেই ব্যালেন্স যোগ হয়ে যাবে।\n\n'
            '👇 <b>নিচের বাটন থেকে পেমেন্ট মেথড বেছে নিন:</b>'
        ),
        "en": (
            '<tg-emoji emoji-id="5395542928909150340">💰</tg-emoji> <b>Cashier Deposit & Balance Top-Up</b> <tg-emoji emoji-id="5395542928909150340">💰</tg-emoji>\n'
            '<i>Select your preferred payment gateway to add instant funds to your wallet:</i>\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            '• <tg-emoji emoji-id="6237941149873478197">💳</tg-emoji> <b>bKash (Agent):</b> Cash Out (BDT)\n'
            '• <tg-emoji emoji-id="6235269688805301565">💳</tg-emoji> <b>Nagad (Agent):</b> Cash Out (BDT)\n'
            '• <tg-emoji emoji-id="6235282831405227077">💳</tg-emoji> <b>Rocket (Personal):</b> Send Money (BDT)\n'
            '• <tg-emoji emoji-id="6235545537374855311">💳</tg-emoji> <b>Binance Pay:</b> USDT Deposit (0% Fee, USD)\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
            '⚡ <b>Instant Verification:</b> Submit TrxID and payment screenshot to auto-credit your balance.\n\n'
            '👇 <b>Choose a payment gateway below:</b>'
        ),
        "hi": (
            '<tg-emoji emoji-id="5395542928909150340">💰</tg-emoji> <b>बैलेंस जोड़ें / डिपॉजिट मेनू</b> <tg-emoji emoji-id="5395542928909150340">💰</tg-emoji>\n\n'
            '• <tg-emoji emoji-id="6237941149873478197">💳</tg-emoji> <b>bKash:</b> कैश आउट (Cash Out - BDT)\n'
            '• <tg-emoji emoji-id="6235269688805301565">💳</tg-emoji> <b>Nagad:</b> कैश आउट (Cash Out - BDT)\n'
            '• <tg-emoji emoji-id="6235282831405227077">💳</tg-emoji> <b>Rocket:</b> सेंड मनी (BDT)\n'
            '• <tg-emoji emoji-id="6235545537374855311">💳</tg-emoji> <b>Binance Pay:</b> USDT डिपॉजिट (USD)\n\n'
            '👇 <b>नीचे दिए गए विकल्पों में से चुनें:</b>'
        )
    },

    # Fast Approval Message
    "fast_approval_notice": {
        "bn": "⚡ **দ্রুত অ্যাপ্রুভ পেতে সরাসরি অ্যাডমিনকে নক দিন:**\n👉 @{admin}",
        "en": "⚡ **For faster deposit approval, contact admin directly:**\n👉 @{admin}",
        "hi": "⚡ **तेज़ अप्रूवल के लिए सीधे एडमिन से संपर्क करें:**\n👉 @{admin}"
    },
    "btn_fast_approval": {
        "bn": "⚡ দ্রুত অ্যাপ্রুভ পেতে অ্যাডমিন নক 💬",
        "en": "⚡ Knock Admin for Fast Approval 💬",
        "hi": "⚡ तुरंत अप्रूवल के लिए संपर्क करें 💬"
    },

    # Deposit Step Inputs
    "dep_amount_input_prompt": {
        "bn": (
            "👉 আপনি কত <b>{unit}</b> {action} করেছেন তা নিচে লিখে সেন্ড করুন:\n"
            "<i>(উদাহরণ: 500 অথবা 1000)</i>"
        ),
        "en": (
            "👉 Please enter the amount in <b>{unit}</b> that you {action}:\n"
            "<i>(Example: 500 or 1000)</i>"
        ),
        "hi": (
            "👉 आपने कितनी राशि <b>{unit}</b> भेजी है, कृपया नीचे दर्ज करें:\n"
            "<i>(उदाहरण: 500 या 1000)</i>"
        )
    },
    "dep_amount_accepted": {
        "bn": (
            "✅ <b>অ্যামাউন্ট গৃহীত হয়েছে:</b> <code>{amount} {currency}</code>\n\n"
            "👉 এখন আপনার পেমেন্টের <b>Transaction ID (TrxID)</b> লিখে সেন্ড করুন:\n"
            "<i>(উদাহরণ: BL74920194 অথবা Binance Order ID)</i>"
        ),
        "en": (
            "✅ <b>Amount recorded:</b> <code>{amount} {currency}</code>\n\n"
            "👉 Now send your payment <b>Transaction ID (TrxID) / Order ID</b>:\n"
            "<i>(Example: BL74920194 or Binance Order ID)</i>"
        ),
        "hi": (
            "✅ <b>राशि दर्ज:</b> <code>{amount} {currency}</code>\n\n"
            "👉 अब अपना <b>Transaction ID (TrxID)</b> भेजें:"
        )
    },
    "dep_screenshot_prompt": {
        "bn": (
            "📸 <b>বাধ্যতামূলক স্ক্রিনশট (Photo) আপলোড করুন:</b>\n\n"
            "⚠️ পেমেন্ট সফল হওয়ার স্পষ্ট স্ক্রিনশট (Photo) সেন্ড করুন।\n"
            "<b>স্ক্রিনশট ছাড়া আপনার ডিপোজিট ভেরিফাই হবে না!</b>\n\n"
            "👇 গ্যালারি থেকে পেমেন্টের স্ক্রিনশটটি এখনই সেন্ড করুন:"
        ),
        "en": (
            "📸 <b>Upload Payment Proof Screenshot:</b>\n\n"
            "⚠️ Please send a clear photo/screenshot showing the completed transaction.\n"
            "<b>Deposits cannot be verified without proof!</b>\n\n"
            "👇 Send your screenshot photo now:"
        ),
        "hi": (
            "📸 <b>भुगतान का स्क्रीनशॉट अपलोड करें:</b>\n\n"
            "⚠️ कृपया सफल भुगतान का स्पष्ट स्क्रीनशॉट भेजें।\n"
            "👇 अभी स्क्रीनशॉट फोटो भेजें:"
        )
    },
    "dep_pending_receipt": {
        "bn": (
            "⏳ <b>আপনার ডিপোজিট রিকোয়েস্ট সাবমিট হয়েছে এবং পেন্ডিং আছে!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>পেমেন্ট মেথড:</b> {method_name}\n"
            "💰 <b>অ্যামাউন্ট:</b> <code>{amount} {currency}</code>\n"
            "🔢 <b>TrxID:</b> <code>{trx_id}</code>\n"
            "🆔 <b>ডিপোজিট রিকোয়েস্ট নং:</b> <code>#{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>দ্রুত অ্যাপ্রুভ পেতে সরাসরি অ্যাডমিনকে নক দিন:</b>\n"
            "👉 অ্যাডমিন আইডি: @{admin}\n"
            "<i>অ্যাডমিন স্ক্রিনশট ও TrxID চেক করে অবিলম্বে ওয়ালেটে ব্যালেন্স যুক্ত করে দেবেন।</i>"
        ),
        "en": (
            "⏳ <b>Your Deposit Request Has Been Submitted & Is Pending!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>Payment Gateway:</b> {method_name}\n"
            "💰 <b>Amount:</b> <code>{amount} {currency}</code>\n"
            "🔢 <b>TrxID:</b> <code>{trx_id}</code>\n"
            "🆔 <b>Request ID:</b> <code>#{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>For faster approval, notify admin directly:</b>\n"
            "👉 Admin Username: @{admin}\n"
            "<i>Admin will verify your proof and credit your wallet immediately.</i>"
        ),
        "hi": (
            "⏳ <b>आपका डिपॉजिट अनुरोध सबमिट हो गया है और लंबित है!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>गेटवे:</b> {method_name}\n"
            "💰 <b>राशि:</b> <code>{amount} {currency}</code>\n"
            "🔢 <b>TrxID:</b> <code>{trx_id}</code>\n"
            "🆔 <b>अनुरोध आईडी:</b> <code>#{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ त्वरित अप्रूवल के लिए एडमिन से संपर्क करें: @{admin}"
        )
    },

    # Orders and Checkout
    "order_success": {
        "bn": (
            "🎉 <b>অভিনন্দন! আপনার অর্ডার সফলভাবে সম্পন্ন হয়েছে!</b>\n\n"
            "🆔 <b>অর্ডার নং:</b> <code>#{order_id}</code>\n"
            "✨ <b>প্রোডাক্ট:</b> <b>{title}</b>\n"
            "💰 <b>পরিশোধিত:</b> <code>{amount} {currency}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>আপনার ডিজিটাল অ্যাক্সেস ডাটা / ক্রেডেনশিয়াল:</b>\n"
            "<pre>{delivery_data}</pre>\n"
            "<i>(বক্সের উপর ১-ট্যাপ করলেই স্বয়ংক্রিয়ভাবে কপি হয়ে যাবে)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>গুরুত্বপূর্ণ নোটিশ:</b> ওয়ান-টাইম ইনভাইট লিঙ্ক হলে অবিলম্বে জয়েন করুন অথবা অ্যাকাউন্ট হলে পাসওয়ার্ড সেভ করে নিন।"
        ),
        "en": (
            "🎉 <b>Congratulations! Your order has been completed!</b>\n\n"
            "🆔 <b>Order ID:</b> <code>#{order_id}</code>\n"
            "✨ <b>Product:</b> <b>{title}</b>\n"
            "💰 <b>Paid:</b> <code>{amount} {currency}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Your Access Link / Credentials:</b>\n"
            "<pre>{delivery_data}</pre>\n"
            "<i>(Tap the box above to copy instantly)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>Notice:</b> Please join the link or save credentials immediately."
        ),
        "hi": (
            "🎉 <b>बधाई हो! आपका ऑर्डर सफलतापूर्वक पूरा हो गया है!</b>\n\n"
            "🆔 <b>ऑर्डर नं:</b> <code>#{order_id}</code>\n"
            "✨ <b>प्रोडक्ट:</b> <b>{title}</b>\n"
            "💰 <b>भुगतान:</b> <code>{amount} {currency}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>आपका एक्सेस लिंक / विवरण:</b>\n"
            "<pre>{delivery_data}</pre>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>सूचना:</b> कृपया तुरंत जुड़ें या क्रेडेंशियल्स सुरक्षित करें।"
        )
    },
    "insufficient_balance": {
        "bn": (
            "❌ <b>আপনার ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 প্রয়োজনীয় ব্যালেন্স: <b>{unit}{price}</b>\n"
            "💳 আপনার বর্তমান ব্যালেন্স: <b>{unit}{user_bal:.2f}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ অনুগ্রহ করে নিচের বাটন থেকে ওয়ালেটে ব্যালেন্স রিচার্জ (ডিপোজিট) করুন।"
        ),
        "en": (
            "❌ <b>Insufficient Wallet Balance!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 Required Balance: <b>{unit}{price}</b>\n"
            "💳 Your Current Balance: <b>{unit}{user_bal:.2f}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ Please add balance to your wallet using the button below."
        ),
        "hi": (
            "❌ <b>वॉलेट में अपर्याप्त बैलेंस!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 आवश्यक बैलेंस: <b>{unit}{price}</b>\n"
            "💳 आपका वर्तमान बैलेंस: <b>{unit}{user_bal:.2f}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ कृपया नीचे दिए गए बटन से बैलेंस जोड़ें।"
        )
    },
    "insufficient_points": {
        "bn": (
            "❌ <b>আপনার অ্যাকাউন্টে পর্যাপ্ত রেফারেল পয়েন্ট নেই!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💎 প্রয়োজনীয় পয়েন্ট: <b>{price} Pts</b>\n"
            "🌟 আপনার বর্তমান পয়েন্ট: <b>{user_pts} Pts</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ বন্ধুদের রেফার করে পয়েন্ট অর্জন করুন অথবা ওয়ালেটে টাকা ডিপোজিট করে কোর্স কিনুন।"
        ),
        "en": (
            "❌ <b>Insufficient Referral Points!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💎 Required Points: <b>{price} Pts</b>\n"
            "🌟 Your Current Points: <b>{user_pts} Pts</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ Invite friends to earn free points or top-up your wallet balance."
        ),
        "hi": (
            "❌ <b>अपर्याप्त रेफरल पॉइंट्स!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💎 आवश्यक पॉइंट्स: <b>{price} Pts</b>\n"
            "🌟 आपके पॉइंट्स: <b>{user_pts} Pts</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    },
    # Global Cancellations
    "global_cancelled_msg": {
        "bn": (
            "❌ <b>বর্তমান প্রক্রিয়াটি সফলভাবে বাতিল করা হয়েছে।</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 আপনি মূল ড্যাশবোর্ডে ফিরে এসেছেন:"
        ),
        "en": (
            "❌ <b>Current operation has been cancelled.</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 You have returned to the main dashboard:"
        ),
        "hi": (
            "❌ <b>वर्तमान प्रक्रिया रद्द कर दी गई है।</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 आप मुख्य डैशबोर्ड पर वापस आ गए हैं:"
        )
    },
    "global_cancelled_alert": {
        "bn": "প্রক্রিয়াটি বাতিল করা হয়েছে।",
        "en": "Cancelled successfully.",
        "hi": "प्रक्रिया रद्द कर दी गई।"
    },

    # Orders Vault
    "orders_vault_empty": {
        "bn": (
            "{em_box} <b>আপনার অর্ডার ভল্ট বর্তমানে খালি!</b>\n\n"
            "আপনি এখনও কোনো কোর্স বা ডিজিটাল প্রোডাক্ট ক্রয় করেননি।\n"
            "কোর্স দেখতে নিচের <b>🛍️ Browse Courses</b> অপশনে যান!"
        ),
        "en": (
            "{em_box} <b>Your Order Vault is Currently Empty!</b>\n\n"
            "You haven't purchased any courses or digital products yet.\n"
            "Tap <b>🛍️ Browse Courses</b> below to explore our store!"
        ),
        "hi": (
            "{em_box} <b>आपका ऑर्डर वॉल्ट वर्तमान में खाली है!</b>\n\n"
            "आपने अभी तक कोई कोर्स या डिजिटल उत्पाद नहीं खरीदा है।"
        )
    },
    "orders_vault_header": {
        "bn": (
            "{em_box} <b>ডিজিটাল অর্ডার হিস্ট্রি ও এক্সেস ভল্ট</b> {em_box}\n"
            "<i>আপনার সাম্প্রতিক সব অর্ডার ও এক্সেস ডাটা নিচে দেওয়া হলো (১-ট্যাপে কপি করুন):</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ),
        "en": (
            "{em_box} <b>Digital Order History & Access Vault</b> {em_box}\n"
            "<i>Your recent orders and access credentials are listed below (Tap to copy):</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ),
        "hi": (
            "{em_box} <b>डिजिटल ऑर्डर इतिहास और एक्सेस वॉल्ट</b> {em_box}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
    },

    # Support Full Text
    "support_card_text": {
        "bn": (
            "{em_sup} <b>অফিসিয়াল কাস্টমার সাপোর্ট ও হেল্পডেস্ক</b> {em_sup}\n\n"
            "যেকোনো প্রশ্ন, কোর্স সম্পর্কিত তথ্য বা পেমেন্ট ভেরিফিকেশনের জন্য সরাসরি আমাদের সাথে যোগাযোগ করুন:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>সাপোর্ট অ্যাডমিন:</b> @{admin}\n"
            "{em_chn} <b>অফিসিয়াল আপডেট চ্যানেল:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <i>জরুরি প্রয়োজনে সরাসরি অ্যাডমিনকে ইনবক্স করতে নিচের বাটনে চাপুন:</i>"
        ),
        "en": (
            "{em_sup} <b>Official Customer Support & Helpdesk</b> {em_sup}\n\n"
            "For any inquiries, course access, or deposit queries, please contact our team directly:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>Support Admin:</b> @{admin}\n"
            "{em_chn} <b>Official Channel:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <i>Tap below to message the support admin directly:</i>"
        ),
        "hi": (
            "{em_sup} <b>आधिकारिक ग्राहक सहायता और हेल्पडेस्क</b> {em_sup}\n\n"
            "किसी भी प्रश्न या सहायता के लिए सीधे संपर्क करें:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>सपोर्ट एडमिन:</b> @{admin}\n"
            "{em_chn} <b>ऑफिशियल चैनल:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    },

    # Package Selection Card
    "checkout_tier_intro": {
        "bn": (
            "🛒 <b>প্যাকেজ নির্বাচন করুন: {title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "এই কোর্সের জন্য ২টি পৃথক অ্যাক্সেস প্যাকেজ উপলব্ধ রয়েছে:\n\n"
            "1️⃣ 📢 <b>VIP Telegram Channel Access:</b>\n"
            "• প্রাইভেট ভিআইপি চ্যানেলে লাইফটাইম অ্যাক্সেস (1-Time Invite Link)\n"
            "• মূল্য: <b>৳{ch_bdt} BDT</b> (${ch_usd} USD)\n\n"
            "2️⃣ 🔐 <b>Personal Account / Drive Access:</b>\n"
            "• পার্সোনাল লগইন অ্যাকাউন্ট বা ডিরেক্ট ড্রাইভ অ্যাক্সেস\n"
            "• মূল্য: <b>৳{acc_bdt} BDT</b> (${acc_usd} USD)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 আপনি কোন অ্যাক্সেসটি নিতে চান নিচের অপশন থেকে বেছে নিন:"
        ),
        "en": (
            "🛒 <b>Select Access Package: {title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Two distinct access tiers are available for this course:\n\n"
            "1️⃣ 📢 <b>VIP Telegram Channel Access:</b>\n"
            "• Private VIP channel lifetime access (1-Time Single-Use Link)\n"
            "• Price: <b>৳{ch_bdt} BDT</b> (${ch_usd} USD)\n\n"
            "2️⃣ 🔐 <b>Personal Account / Drive Access:</b>\n"
            "• Personal login account or dedicated cloud drive access\n"
            "• Price: <b>৳{acc_bdt} BDT</b> (${acc_usd} USD)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 Select your preferred access package below:"
        ),
        "hi": (
            "🛒 <b>पैकेज चुनें: {title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ 📢 <b>VIP Telegram Channel Access:</b> <b>৳{ch_bdt} BDT</b> (${ch_usd} USD)\n"
            "2️⃣ 🔐 <b>Personal Account / Drive Access:</b> <b>৳{acc_bdt} BDT</b> (${acc_usd} USD)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 अपना पसंदीदा विकल्प चुनें:"
        )
    },

    # Checkout Confirmation Card
    "checkout_confirm_card": {
        "bn": (
            "🛒 <b>অর্ডার চেকআউট কনফার্মেশন</b>\n"
            "<b>{title}</b>\n"
            "{tier_badge}"
            "{reseller_badge}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 কোর্স মূল্য: <b>৳{charge_bdt} BDT</b> অথবা <b>${charge_usd} USD</b>\n\n"
            "💳 <b>আপনার বর্তমান ওয়ালেট ব্যালেন্স:</b>\n"
            "• BDT: <b>৳{bal_bdt:.2f} BDT</b>\n"
            "• USD: <b>${bal_usd:.2f} USD</b>\n"
            "• রেফারেল পয়েন্ট: <b>{user_pts} Pts</b> (প্রয়োজন: {refs_needed} Pts)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 আপনি কোন ব্যালেন্স বা পয়েন্ট দিয়ে পে করতে চান নির্বাচন করুন:"
        ),
        "en": (
            "🛒 <b>Order Checkout Confirmation</b>\n"
            "<b>{title}</b>\n"
            "{tier_badge}"
            "{reseller_badge}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 Package Price: <b>৳{charge_bdt} BDT</b> or <b>${charge_usd} USD</b>\n\n"
            "💳 <b>Your Current Wallet Balance:</b>\n"
            "• BDT: <b>৳{bal_bdt:.2f} BDT</b>\n"
            "• USD: <b>${bal_usd:.2f} USD</b>\n"
            "• Referral Points: <b>{user_pts} Pts</b> (Needed: {refs_needed} Pts)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Choose your payment currency or points below:"
        ),
        "hi": (
            "🛒 <b>ऑर्डर चेकआउट पुष्टिकरण</b>\n"
            "<b>{title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 मूल्य: <b>৳{charge_bdt} BDT</b> / <b>${charge_usd} USD</b>\n\n"
            "💳 आपका बैलेंस: ৳{bal_bdt:.2f} BDT | ${bal_usd:.2f} USD\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    },

    # Coupon prompts
    "coupon_start_prompt": {
        "bn": (
            "🎟️ **কুপন বা ভাউচার কোড ব্যবহার করুন**\n\n"
            "👉 আপনার কুপন কোডটি লিখে সেন্ড করুন:\n"
            "_(যেমন: VIP50 বা SPECIAL100)_"
        ),
        "en": (
            "🎟️ **Apply Promo or Voucher Coupon**\n\n"
            "👉 Send your coupon code below:\n"
            "_(e.g., VIP50 or SPECIAL100)_"
        ),
        "hi": (
            "🎟️ **कूपन कोड दर्ज करें**\n\n"
            "👉 अपना कूपन कोड भेजें:"
        )
    },
    "coupon_invalid_alert": {
        "bn": "❌ **ভুল কুপন কোড অথবা মেয়াদ শেষ হয়ে গেছে!**\n\nসঠিক কোড দিন অথবা ফিরে যান:",
        "en": "❌ **Invalid or expired coupon code!**\n\nPlease enter a valid code or go back:",
        "hi": "❌ **अमान्य या समाप्त कूपन कोड!**"
    },
    "coupon_applied_card": {
        "bn": (
            "🛒 **অর্ডার কনফার্মেশন: {title}{tier_label}**\n\n"
            "🏷️ **প্রযোজ্য কুপন:** `{code}` (৳{discount_bdt} BDT ছাড় ✅)\n"
            "💰 **পরিশোধযোগ্য মূল্য:** `৳{final_bdt} BDT` অথবা `${final_usd} USD`\n\n"
            "💳 **আপনার বর্তমান ব্যালেন্স:**\n"
            "• BDT: `৳{bal_bdt:.2f}`\n"
            "• USD: `${bal_usd:.2f}`\n\n"
            "আপনি কোন ব্যালেন্স দিয়ে পে করতে চান নির্বাচন করুন:"
        ),
        "en": (
            "🛒 **Order Confirmation: {title}{tier_label}**\n\n"
            "🏷️ **Applied Coupon:** `{code}` (৳{discount_bdt} BDT Discount ✅)\n"
            "💰 **Final Payable Price:** `৳{final_bdt} BDT` or `${final_usd} USD`\n\n"
            "💳 **Your Current Balance:**\n"
            "• BDT: `৳{bal_bdt:.2f}`\n"
            "• USD: `${bal_usd:.2f}`\n\n"
            "Select your payment currency below:"
        ),
        "hi": (
            "🛒 **ऑर्डर पुष्टिकरण: {title}**\n\n"
            "🏷️ **कूपन:** `{code}` (৳{discount_bdt} छूट)\n"
            "💰 **देय राशि:** `৳{final_bdt} BDT` / `${final_usd} USD`"
        )
    },

    # Out of Stock Alert
    "out_of_stock_alert": {
        "bn": "❌ এই আইটেমটি বর্তমানে স্টকে নেই। শীঘ্রই রিস্টক করা হবে!",
        "en": "❌ This item is currently out of stock. It will be restocked soon!",
        "hi": "❌ यह आइटम वर्तमान में स्टॉक में नहीं है। जल्द ही उपलब्ध होगा!"
    },

    # Orders Vault
    "orders_vault_empty": {
        "bn": (
            "📦 <b>আপনার অর্ডার ভল্ট বর্তমানে খালি!</b>\n\n"
            "আপনি এখনও কোনো কোর্স বা ডিজিটাল প্রোডাক্ট ক্রয় করেননি।\n"
            "কোর্স দেখতে নিচের <b>🛍️ Browse Courses</b> অপশনে যান!"
        ),
        "en": (
            "📦 <b>Your Order Vault is currently empty!</b>\n\n"
            "You haven't purchased any courses or digital products yet.\n"
            "Tap <b>🛍️ Browse Courses</b> below to explore available courses!"
        ),
        "hi": (
            "📦 <b>आपका ऑर्डर वॉल्ट खाली है!</b>\n\n"
            "आपने अभी तक कोई कोर्स नहीं खरीदा है।"
        )
    },
    "orders_vault_header": {
        "bn": (
            "📦 <b>ডিজিটাল অর্ডার হিস্ট্রি ও এক্সেস ভল্ট</b> 📦\n"
            "<i>আপনার সাম্প্রতিক সব অর্ডার ও এক্সেস ডাটা নিচে দেওয়া হলো (১-ট্যাপে কপি করুন):</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ),
        "en": (
            "📦 <b>Digital Order History & Access Vault</b> 📦\n"
            "<i>Your recent orders and access credentials are shown below (1-tap to copy):</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ),
        "hi": (
            "📦 <b>डिजिटल ऑर्डर इतिहास और एक्सेस वॉल्ट</b> 📦\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
    },
    "orders_paid_label": {
        "bn": "পরিশোধিত মূল্য",
        "en": "Paid Amount",
        "hi": "भुगतान राशि"
    },
    "orders_date_label": {
        "bn": "তারিখ",
        "en": "Date",
        "hi": "तारीख"
    },
    "orders_access_label": {
        "bn": "এক্সেস ডাটা / ডেলিভারি ক্রেডেনশিয়াল",
        "en": "Access Data / Delivery Credentials",
        "hi": "एक्सेस डेटा / क्रेडेंशियल"
    },

    # Support & Helpdesk
    "support_card_text": {
        "bn": (
            "{em_sup} <b>অফিসিয়াল কাস্টমার সাপোর্ট ও হেল্পডেস্ক</b> {em_sup}\n\n"
            "যেকোনো প্রশ্ন, কোর্স সম্পর্কিত তথ্য বা পেমেন্ট ভেরিফিকেশনের জন্য সরাসরি আমাদের সাথে যোগাযোগ করুন:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>সাপোর্ট অ্যাডমিন:</b> @{admin}\n"
            "{em_chn} <b>অফিসিয়াল আপডেট চ্যানেল:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <i>জরুরি প্রয়োজনে সরাসরি অ্যাডমিনকে ইনবক্স করতে নিচের বাটনে চাপুন:</i>"
        ),
        "en": (
            "{em_sup} <b>Official Customer Support & Helpdesk</b> {em_sup}\n\n"
            "For any queries, course information, or payment verification, reach out to us directly:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>Support Admin:</b> @{admin}\n"
            "{em_chn} <b>Official Updates Channel:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <i>Tap the button below to message our official support team directly:</i>"
        ),
        "hi": (
            "{em_sup} <b>आधिकारिक ग्राहक सहायता और हेल्पडेस्क</b> {em_sup}\n\n"
            "किसी भी प्रश्न या सहायता के लिए सीधे संपर्क करें:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_adm} <b>सपोर्ट एडमिन:</b> @{admin}\n"
            "{em_chn} <b>चैनल:</b> {channel}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    },

    # Global Cancel
    "global_cancelled_msg": {
        "bn": (
            "❌ <b>বর্তমান প্রক্রিয়াটি সফলভাবে বাতিল করা হয়েছে।</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 আপনি মূল ড্যাশবোর্ডে ফিরে এসেছেন:"
        ),
        "en": (
            "❌ <b>The current process has been cancelled.</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 You have returned to the Main Dashboard:"
        ),
        "hi": (
            "❌ <b>वर्तमान प्रक्रिया सफलतापूर्वक रद्द कर दी गई है।</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 आप मुख्य डैशबोर्ड पर वापस आ गए हैं:"
        )
    },
    "global_cancelled_alert": {
        "bn": "প্রক্রিয়াটি বাতিল করা হয়েছে।",
        "en": "Process has been cancelled.",
        "hi": "प्रक्रिया रद्द कर दी गई है।"
    },

    # Search & Course Request Hub
    "course_req_prompt_text": {
        "bn": (
            "🎯 <b>প্রিমিয়াম কোর্স ও সফটওয়্যার রিকোয়েস্ট হাব</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার পছন্দের যে কোর্স, টুল বা প্রিমিয়াম অ্যাকাউন্টটি আমাদের ক্যাটালগে নেই, "
            "তার <b>নাম</b> অথবা <b>অফিশিয়াল ওয়েবসাইট লিংক</b> লিখে পাঠান:\n\n"
            "<i>(উদাহরণস্বরূপ: 10 Minute School Web Dev, অথবা Bohubrihi Python, অথবা https://udemy.com/...)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 আমাদের অ্যাডমিন টিম রিকোয়েস্ট পাওয়ার সাথে সাথেই তা ব্যবস্থা করার উদ্যোগ নেবে!"
        ),
        "en": (
            "🎯 <b>Premium Course & Software Request Hub</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "If the course, tool, or premium account you want is not in our catalog, "
            "send us its <b>Name</b> or <b>Official Website URL</b>:\n\n"
            "<i>(For example: 10 Minute School Web Dev, or Python Masterclass, or https://udemy.com/...)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Our admin team will arrange access as soon as we review your request!"
        ),
        "hi": (
            "🎯 <b>प्रीमियम कोर्स और सॉफ्टवेयर अनुरोध हब</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "जो कोर्स या टूल हमारी सूची में नहीं है, उसका <b>नाम</b> या <b>लिंक</b> भेजें:\n\n"
            "💡 हमारी टीम जल्द से जल्द इसकी व्यवस्था करेगी!"
        )
    },
    "course_req_cancelled_alert": {
        "bn": "❌ রিকোয়েস্ট বাতিল করা হয়েছে।",
        "en": "❌ Request cancelled.",
        "hi": "❌ अनुरोध रद्द कर दिया गया।"
    },
    "course_req_user_confirm": {
        "bn": (
            "✅ <b>আপনার কোর্স রিকোয়েস্ট সফলভাবে জমা হয়েছে!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📦 <b>রিকোয়েস্টকৃত আইটেম:</b>\n<code>{item}</code>\n\n"
            "🆔 <b>রিকোয়েস্ট ট্র্যাকিং আইডি:</b> <code>#REQ-{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 আমাদের অ্যাডমিন টিম এটি পর্যালোচনা করে দ্রুত ক্যাটালগে যুক্ত করবে অথবা আপনার সাথে ইনবক্সে যোগাযোগ করবে। ধন্যবাদ!"
        ),
        "en": (
            "✅ <b>Your course request has been submitted successfully!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📦 <b>Requested Item:</b>\n<code>{item}</code>\n\n"
            "🆔 <b>Tracking ID:</b> <code>#REQ-{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Our admin team will review this and add it to the catalog or contact you directly. Thank you!"
        ),
        "hi": (
            "✅ <b>आपका कोर्स अनुरोध सफलतापूर्वक सबमिट हो गया है!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📦 <b>अनुरोधित आइटम:</b>\n<code>{item}</code>\n\n"
            "🆔 <b>ट्रैकिंग आईडी:</b> <code>#REQ-{req_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 हमारी टीम जल्द ही इसे सूची में जोड़ेगी। धन्यवाद!"
        )
    },
    "search_found_single_text": {
        "bn": (
            "🎯 <b>আপনার কাঙ্ক্ষিত কোর্সটি খুঁজে পাওয়া গেছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_crs} <b>{title}</b>\n\n"
            "📝 <b>বিবরণ:</b>\n{desc}...\n\n"
            "💰 <b>মূল্য:</b> <b>৳{bdt} BDT</b> অথবা <b>${usd} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 <i>ইনস্ট্যান্ট এক্সেস নিতে বা রেফারেল দিয়ে ফ্রি পেতে নিচের বাটনে চাপুন:</i>"
        ),
        "en": (
            "🎯 <b>Found your desired course!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_crs} <b>{title}</b>\n\n"
            "📝 <b>Description:</b>\n{desc}...\n\n"
            "💰 <b>Price:</b> <b>৳{bdt} BDT</b> or <b>${usd} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 <i>Tap the buttons below for instant access or claim via referrals:</i>"
        ),
        "hi": (
            "🎯 <b>आपका कोर्स मिल गया है!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "{em_crs} <b>{title}</b>\n\n"
            "📝 <b>विवरण:</b>\n{desc}...\n\n"
            "💰 <b>मूल्य:</b> <b>৳{bdt} BDT</b> या <b>${usd} USD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    },
    "search_found_multiple_text": {
        "bn": (
            "🔍 <b>সার্চ রেজাল্ট: {count} টি কোর্স পাওয়া গেছে!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনি যা খুঁজছেন: <code>{query}</code>\n\n"
            "👇 যে কোর্সটির বিবরণ ও মূল্য দেখতে চান নিচের অপশন থেকে বেছে নিন:"
        ),
        "en": (
            "🔍 <b>Search Results: Found {count} matching items!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "You searched for: <code>{query}</code>\n\n"
            "👇 Select any course below to view details, pricing, and access:"
        ),
        "hi": (
            "🔍 <b>खोज परिणाम: {count} कोर्सेस मिले!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "आपने खोजा: <code>{query}</code>\n\n"
            "👇 विवरण और कीमत देखने के लिए नीचे दिए गए विकल्पों में से चुनें:"
        )
    },
    "search_not_found_text": {
        "bn": (
            "🔍 <b>সার্চ রেজাল্ট: ক্যাটালগে পাওয়া যায়নি</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনি যা খুঁজছেন:\n<code>{query}</code>\n\n"
            "⚠️ দুঃখিত, এই কোর্সটি বা লিংকটি বর্তমানে আমাদের ক্যাটালগে সরাসরি নেই।\n\n"
            "💡 <b>তবে কোনো চিন্তা নেই!</b> আমাদের কাছে আনলিমিটেড প্রিমিয়াম রিসোর্স ও প্রোভাইডার এক্সেস রয়েছে। "
            "আপনি চাইলে এখনই এটি রিকোয়েস্ট করতে পারেন—আমাদের অ্যাডমিন টিম দ্রুত আপনার জন্য এটি ম্যানেজ করে দেবে!"
        ),
        "en": (
            "🔍 <b>Search Result: Not Found in Catalog</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "You searched for:\n<code>{query}</code>\n\n"
            "⚠️ Sorry, this item or link is not currently listed in our catalog.\n\n"
            "💡 <b>Don't worry!</b> We have access to premium enterprise repositories and providers. "
            "You can request this item right now—our admin team will quickly source and prepare it for you!"
        ),
        "hi": (
            "🔍 <b>खोज परिणाम: कैटलॉग में नहीं मिला</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "आपने खोजा:\n<code>{query}</code>\n\n"
            "⚠️ यह कोर्स वर्तमान में हमारी सूची में नहीं है।\n\n"
            "💡 आप इसका अनुरोध कर सकते हैं—हमारी टीम जल्द से जल्द इसकी व्यवस्था करेगी!"
        )
    },
    "search_casual_guide_text": {
        "bn": (
            "👋 <b>আসসালামু আলাইকুম ভাই!</b>\n\n"
            "আপনার কি কোনো নির্দিষ্ট কোর্স, সফটওয়্যার বা প্রিমিয়াম অ্যাকাউন্ট লাগবে?\n\n"
            "• বট ব্যবহার করতে নিচের কিবোর্ড বাটনগুলো ব্যবহার করুন\n"
            "• অথবা আপনার যে কোর্স বা সফটওয়্যারটি প্রয়োজন তার <b>নাম বা ওয়েবসাইট লিংক</b> সরাসরি এখানে লিখে পাঠিয়ে দিন!"
        ),
        "en": (
            "👋 <b>Hello & Welcome!</b>\n\n"
            "Looking for a specific course, software tool, or premium account?\n\n"
            "• Use the interactive keyboard menu below to explore categories\n"
            "• Or simply send the <b>Name or Website URL</b> of what you need right here in the chat!"
        ),
        "hi": (
            "👋 <b>नमस्ते और स्वागत है!</b>\n\n"
            "क्या आपको किसी विशिष्ट कोर्स या टूल की आवश्यकता है?\n\n"
            "• नीचे दिए गए कीबोर्ड मेनू का उपयोग करें\n"
            "• या जो कोर्स चाहिए उसका <b>नाम या लिंक</b> सीधे यहाँ चैट में भेजें!"
        )
    },
    "deposit_invalid_method_alert": {
        "bn": "মেথড পাওয়া যায়নি!",
        "en": "Payment method not found!",
        "hi": "भुगतान विधि नहीं मिली!"
    },
    "deposit_method_maintenance_alert": {
        "bn": "⚠️ এই পেমেন্ট মেথডটি সাময়িক রক্ষণাবেক্ষণের জন্য বন্ধ আছে। অনুগ্রহ করে অন্য মেথড বেছে নিন।",
        "en": "⚠️ This payment gateway is temporarily undergoing maintenance. Please select an alternate method.",
        "hi": "⚠️ यह भुगतान गेटवे अस्थायी रूप से रखरखाव के अधीन है। कृपया अन्य विधि चुनें।"
    },
    "catalog_subcat_not_found_alert": {
        "bn": "সাব-ক্যাটাগরি পাওয়া যায়নি!",
        "en": "Sub-category not found!",
        "hi": "उप-श्रेणी नहीं मिली!"
    },
    "catalog_prod_not_found_alert": {
        "bn": "প্রোডাক্ট পাওয়া যায়নি!",
        "en": "Product not found!",
        "hi": "उत्पाद नहीं मिला!"
    },

    # Product Stock Status Badges
    "product_stock_out": {
        "bn": "🔴 আউট অব স্টক (Out of Stock)",
        "en": "🔴 Out of Stock",
        "hi": "🔴 आउट ऑफ स्टॉक (Out of Stock)"
    },
    "product_stock_in": {
        "bn": "🟢 ইন-স্টক ({count} টি অবশিষ্ট)",
        "en": "🟢 In Stock ({count} available)",
        "hi": "🟢 स्टॉक में उपलब्ध ({count})"
    },
    "product_stock_instant": {
        "bn": "🟢 ইন-স্টক (স্বয়ংক্রিয় ইনস্ট্যান্ট এক্সেস)",
        "en": "🟢 In Stock (Instant Delivery)",
        "hi": "🟢 स्टॉक में उपलब्ध (त्वरित डिलीवरी)"
    }
}

def t(key: str, lang: str = "bn", **kwargs) -> str:
    """Retrieve translated text by key and language code, with format interpolation."""
    lang_code = lang if lang in ["bn", "en", "hi"] else "bn"
    entry = TRANSLATIONS.get(key, {})
    template = entry.get(lang_code) or entry.get("en") or entry.get("bn") or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

def get_all_menu_button_texts(key: str) -> list:
    """Returns a list of all variations of a menu button across all supported languages."""
    entry = TRANSLATIONS.get(key, {})
    return list(entry.values())
