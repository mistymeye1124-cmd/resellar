# Multi-Language Localization Engine (Bangla, English, Hindi)
from typing import Dict

LANGUAGES = {
    "bn": "🇧🇩 বাংলা",
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिंदी"
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Main Navigation Buttons
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
        "bn": "🌐 Language / ভাষা / भाषा",
        "en": "🌐 Language / ভাষা / भाषा",
        "hi": "🌐 Language / ভাষা / भाषा"
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
        "en": "🎁 Free Claim (Giveaways)",
        "hi": "🎁 फ्री क्लेम (Giveaway)"
    },

    # Common Action Buttons
    "btn_back": {
        "bn": "🔙 Back",
        "en": "🔙 Back",
        "hi": "🔙 वापस जाएं"
    },
    "btn_cancel": {
        "bn": "❌ Cancel",
        "en": "❌ Cancel",
        "hi": "❌ रद्द करें"
    },
    "btn_buy_now": {
        "bn": "🚀 Buy Now",
        "en": "🚀 Buy Now",
        "hi": "🚀 अभी खरीदें"
    },
    "btn_out_of_stock": {
        "bn": "❌ Out of Stock",
        "en": "❌ Out of Stock",
        "hi": "❌ आउट ऑफ स्टॉक"
    },
    "btn_apply_coupon": {
        "bn": "🎟️ Apply Coupon / কুপন কোড দিন",
        "en": "🎟️ Apply Promo Coupon",
        "hi": "🎟️ कूपन कोड दर्ज करें"
    },
    "btn_add_balance": {
        "bn": "💳 Add Balance",
        "en": "💳 Add Balance",
        "hi": "💳 बैलेंस जोड़ें"
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
        "bn": "সাধারণ ক্রেতা (Regular Customer)",
        "en": "Regular Customer",
        "hi": "सामान्य ग्राहक (Regular Customer)"
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
            '<i>Select your preferred payment method to add instant balance to your wallet:</i>\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            '• <tg-emoji emoji-id="6237941149873478197">💳</tg-emoji> <b>bKash (Agent):</b> bKash Cash Out (BDT)\n'
            '• <tg-emoji emoji-id="6235269688805301565">💳</tg-emoji> <b>Nagad (Agent):</b> Nagad Cash Out (BDT)\n'
            '• <tg-emoji emoji-id="6235282831405227077">💳</tg-emoji> <b>Rocket (Personal):</b> Rocket Send Money (BDT)\n'
            '• <tg-emoji emoji-id="6235545537374855311">💳</tg-emoji> <b>Binance Pay:</b> USDT Deposit (0% Fee, USD)\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
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
        "bn": "⚡ দ্রুত অ্যাপ্রুভ পেতে অ্যাডমিনকে নক দিন 💬",
        "en": "⚡ Knock Admin for Fast Approval 💬",
        "hi": "⚡ तुरंत अप्रूवल के लिए संपर्क करें 💬"
    },

    # Catalog & Purchase
    "catalog_courses_title": {
        "bn": "🎓 **কোর্স ক্যাটাগরি সমূহ (Courses Catalog)**\n\n👇 আপনার পছন্দের ক্যাটাগরি নির্বাচন করুন:",
        "en": "🎓 **Course Categories**\n\n👇 Select your preferred category:",
        "hi": "🎓 **कोर्स श्रेणियां (Categories)**\n\n👇 अपनी पसंदीदा श्रेणी चुनें:"
    },
    "catalog_digital_title": {
        "bn": "⚡ **ডিজিটাল টুলস ও অ্যাকাউন্টস (Digital Tools & Accounts)**\n\n👇 আপনার পছন্দের ক্যাটাগরি নির্বাচন করুন:",
        "en": "⚡ **Digital Tools & Accounts**\n\n👇 Select your preferred category:",
        "hi": "⚡ **डिजिटल टूल्स और अकाउंट्स**\n\n👇 अपनी पसंदीदा श्रेणी चुनें:"
    },
    "reseller_savings_teaser": {
        "bn": "💡 _(রিসেলারদের জন্য পাইকারি রেট মাত্র ৳{res_bdt}! রিসেলার হতে মেনুর 🤝 Reseller Hub দেখুন)_",
        "en": "💡 _(Wholesale rate for resellers is only ৳{res_bdt}! Check 🤝 Reseller Hub to join)_",
        "hi": "💡 _(रीसेलर्स के लिए थोक दर सिर्फ ৳{res_bdt}! शामिल होने के लिए 🤝 Reseller Hub देखें)_"
    },
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
