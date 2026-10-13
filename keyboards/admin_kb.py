# Admin Keyboards for Reseller Bot - 100% Premium Animated Custom Emojis
from aiogram.types import InlineKeyboardMarkup
from typing import List, Dict, Any
from utils.emojis import make_custom_button

def get_admin_main_kb(stats: Dict[str, Any] = None, is_super: bool = True, permissions: Dict[str, Any] = None) -> InlineKeyboardMarkup:
    """Main dashboard for administrators with live telemetry counters, RBAC permission filtering, and premium emojis."""
    pending_count = stats.get('pending_deposits', 0) if stats else 0
    pending_resellers = stats.get('pending_reseller_apps', 0) if stats else 0
    
    dep_label = f"Deposits ({pending_count})" if pending_count > 0 else "Deposits (0)"
    res_label = f"Reseller Radar ({pending_resellers} apps)" if pending_resellers > 0 else "Reseller Radar"
    
    if is_super:
        buttons = [
            [
                make_custom_button(text="⚡ Stock Manager (স্টক অন/অফ)", callback_data="admin_stock_hub", emoji_key="zap"),
                make_custom_button(text="👑 Sub-Admins (টিম ও রোল)", callback_data="admin_subadmins_menu", emoji_key="crown")
            ],
            [
                make_custom_button(text="🤖 Auto Add Course (Groq AI ⚡)", callback_data="admin_groq_auto_add", emoji_key="zap"),
                make_custom_button(text="Add Course / Item", callback_data="admin_add_prod", emoji_key="courses")
            ],
            [
                make_custom_button(text="Upload Stock Keys", callback_data="admin_add_stock", emoji_key="box"),
                make_custom_button(text="Manage Courses", callback_data="admin_list_prods", emoji_key="catalog")
            ],
            [
                make_custom_button(text=res_label, callback_data="admin_resellers_menu", emoji_key="diamond"),
                make_custom_button(text="Smart User Search", callback_data="admin_search_user_prompt", emoji_key="search")
            ],
            [
                make_custom_button(text=dep_label, callback_data="admin_pending_deps", emoji_key="deposit"),
                make_custom_button(text="Live Order Ledger", callback_data="admin_recent_orders", emoji_key="orders")
            ],
            [
                make_custom_button(text="Broadcast Studio", callback_data="admin_broadcast_hub", emoji_key="broadcast"),
                make_custom_button(text="Showcase to Channel", callback_data="admin_channel_post", emoji_key="channel")
            ],
            [
                make_custom_button(text="User Balance Manager", callback_data="admin_manage_balance", emoji_key="wallet"),
                make_custom_button(text="Coupons & Vouchers", callback_data="admin_coupons_menu", emoji_key="coupon")
            ],
            [
                make_custom_button(text="Free Claim Drops (লুট/গিভঅ্যাওয়ে)", callback_data="admin_free_drops_menu", emoji_key="free_claim"),
                make_custom_button(text="Settings & Gateways", callback_data="admin_settings_menu", emoji_key="settings")
            ],
            [
                make_custom_button(text="💾 Instant DB Backup (ব্যাকআপ নিন)", callback_data="admin_instant_db_backup", emoji_key="box"),
                make_custom_button(text="Refresh Dashboard", callback_data="admin_main_dashboard", emoji_key="refresh")
            ],
            [
                make_custom_button(text="Close Admin Panel", callback_data="admin_close", emoji_key="cross")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    # For Sub-Admins: dynamically construct based on permissions
    perms = permissions or {}
    buttons = []

    # 1. Stock permission
    if perms.get("can_manage_stock"):
        buttons.append([
            make_custom_button(text="⚡ Stock Manager (স্টক অন/অফ)", callback_data="admin_stock_hub", emoji_key="zap"),
            make_custom_button(text="Upload Stock Keys", callback_data="admin_add_stock", emoji_key="box")
        ])

    # 2. Product permission
    if perms.get("can_manage_products"):
        buttons.append([
            make_custom_button(text="🤖 Auto Add Course (Groq AI ⚡)", callback_data="admin_groq_auto_add", emoji_key="zap"),
            make_custom_button(text="Add Course / Item", callback_data="admin_add_prod", emoji_key="courses")
        ])
        buttons.append([
            make_custom_button(text="Manage Courses", callback_data="admin_list_prods", emoji_key="catalog"),
            make_custom_button(text="Manage Categories", callback_data="admin_cats_menu", emoji_key="category")
        ])

    # 3. Deposits permission
    if perms.get("can_approve_deposits"):
        buttons.append([
            make_custom_button(text=dep_label, callback_data="admin_pending_deps", emoji_key="deposit"),
            make_custom_button(text="Live Order Ledger", callback_data="admin_recent_orders", emoji_key="orders")
        ])

    # 4. Resellers permission
    if perms.get("can_manage_resellers"):
        buttons.append([
            make_custom_button(text=res_label, callback_data="admin_resellers_menu", emoji_key="diamond")
        ])

    # 5. Users / Balance permission
    if perms.get("can_manage_users"):
        buttons.append([
            make_custom_button(text="Smart User Search", callback_data="admin_search_user_prompt", emoji_key="search"),
            make_custom_button(text="User Balance Manager", callback_data="admin_manage_balance", emoji_key="wallet")
        ])

    # 6. Broadcast permission
    if perms.get("can_broadcast"):
        buttons.append([
            make_custom_button(text="Broadcast Studio", callback_data="admin_broadcast_hub", emoji_key="broadcast"),
            make_custom_button(text="Showcase to Channel", callback_data="admin_channel_post", emoji_key="channel")
        ])

    # 7. Coupons permission
    if perms.get("can_manage_coupons"):
        buttons.append([
            make_custom_button(text="Coupons & Vouchers", callback_data="admin_coupons_menu", emoji_key="coupon")
        ])

    # 8. Free Claim Drops permission
    if perms.get("can_manage_free_drops"):
        buttons.append([
            make_custom_button(text="Free Claim Drops (লুট/গিভঅ্যাওয়ে)", callback_data="admin_free_drops_menu", emoji_key="free_claim")
        ])

    buttons.append([
        make_custom_button(text="Refresh Dashboard", callback_data="admin_main_dashboard", emoji_key="refresh"),
        make_custom_button(text="Close Admin Panel", callback_data="admin_close", emoji_key="cross")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_main_dashboard_kb(stats: Dict[str, Any] = None, is_super: bool = True, permissions: Dict[str, Any] = None) -> InlineKeyboardMarkup:
    """Wrapper alias to get_admin_main_kb ensuring cross-module compatibility."""
    return get_admin_main_kb(stats=stats, is_super=is_super, permissions=permissions)

def get_stock_hub_kb(products: List[Dict[str, Any]], page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Dedicated Stock Hub keyboard with 1-click In-Stock / Out-of-Stock toggles."""
    buttons = []
    for p in products:
        in_stock = bool(p.get("is_in_stock", 1) if p.get("is_in_stock") is not None else 1)
        btn_text = "🟢 ইন স্টক (ক্লিক: Out)" if in_stock else "🔴 আউট অব স্টক (ক্লিক: In)"
        emoji_k = "check" if in_stock else "cross"
        buttons.append([
            make_custom_button(text=f"📚 {p['title'][:22]} (৳{int(p.get('price_bdt', 0))})", callback_data=f"edit_p_select:{p['id']}", emoji_key="courses"),
            make_custom_button(text=btn_text, callback_data=f"stk_hub_tgl:{p['id']}:{page}", emoji_key=emoji_k)
        ])
    
    # Pagination
    nav = []
    if page > 0:
        nav.append(make_custom_button(text="⬅️ Previous", callback_data=f"admin_stock_page:{page - 1}", emoji_key="back"))
    nav.append(make_custom_button(text=f"📄 {page + 1}/{total_pages}", callback_data="noop", emoji_key="catalog"))
    if page < total_pages - 1:
        nav.append(make_custom_button(text="Next ➡️", callback_data=f"admin_stock_page:{page + 1}", emoji_key="zap"))
    if nav:
        buttons.append(nav)

    buttons.append([
        make_custom_button(text="🔙 Back to Admin Dashboard", callback_data="admin_main_dashboard", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subadmins_list_kb(subadmins: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """List of all appointed sub-admins with add and detail inspection buttons."""
    buttons = [
        [
            make_custom_button(text="➕ নতুন সাব-এডমিন যোগ করুন", callback_data="subadm_add_prompt", emoji_key="sparkle")
        ]
    ]
    for sub in subadmins:
        display_name = sub.get("name") or sub.get("username") or str(sub["user_id"])
        u_tag = f"@{sub['username']}" if sub.get("username") else f"ID: {sub['user_id']}"
        buttons.append([
            make_custom_button(text=f"👤 {display_name} ({u_tag})", callback_data=f"subadm_view:{sub['user_id']}", emoji_key="admin")
        ])
    
    buttons.append([
        make_custom_button(text="🔙 Back to Admin Dashboard", callback_data="admin_main_dashboard", emoji_key="home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subadmin_detail_kb(sub: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Interactive permission toggles for a specific sub-admin."""
    uid = sub["user_id"]
    
    def p_btn(label: str, perm_key: str, emoji_k: str):
        is_on = bool(sub.get(perm_key, 0))
        state_mark = "✅ চালু" if is_on else "❌ বন্ধ"
        return make_custom_button(
            text=f"{state_mark} | {label}",
            callback_data=f"subadm_perm_tgl:{uid}:{perm_key}",
            emoji_key="check" if is_on else "cross"
        )

    buttons = [
        [p_btn("ফ্রি ড্রপস/লুট (Free Drops)", "can_manage_free_drops", "free_claim")],
        [p_btn("স্টক অন/অফ (Stock Manager)", "can_manage_stock", "zap")],
        [p_btn("কোর্স ও ক্যাটাগরি (Products)", "can_manage_products", "courses")],
        [p_btn("ডিপোজিট অনুমোদন (Deposits)", "can_approve_deposits", "deposit")],
        [p_btn("রিসেলার রাডার (Reseller Apps)", "can_manage_resellers", "diamond")],
        [p_btn("ব্রডকাস্ট ও চ্যানেল পোস্ট", "can_broadcast", "broadcast")],
        [p_btn("ইউজার ব্যালেন্স কন্ট্রোল", "can_manage_users", "wallet")],
        [p_btn("ডিসকাউন্ট কুপন তৈরি", "can_manage_coupons", "coupon")],
        [
            make_custom_button(text="🗑️ সাব-এডমিনকে রিমুভ করুন", callback_data=f"subadm_remove_confirm:{uid}", emoji_key="cross")
        ],
        [
            make_custom_button(text="🔙 সাব-এডমিন তালিকা", callback_data="admin_subadmins_menu", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_control_kb(target_id: int, is_reseller: bool = False, is_banned: bool = False, is_perm_deact: bool = False) -> InlineKeyboardMarkup:
    """Action control buttons attached directly to a searched user's dossier."""
    res_btn_text = "Promote to Reseller"
    res_cb = f"usr_ctl_reseller:{target_id}"
    res_em = "diamond"
    if is_perm_deact:
        res_btn_text = "Reactivate Quota (Forgive)"
        res_cb = f"usr_ctl_reactivate:{target_id}"
        res_em = "check"
    elif is_reseller:
        res_btn_text = "Demote from Reseller"
        res_cb = f"usr_ctl_demote:{target_id}"
        res_em = "cross"

    ban_btn_text = "Unban User" if is_banned else "Ban User"
    ban_cb = f"usr_ctl_ban:{target_id}"
    ban_em = "check" if is_banned else "cross"

    buttons = [
        [
            make_custom_button(text="Add Balance", callback_data=f"usr_ctl_addbal:{target_id}", emoji_key="deposit"),
            make_custom_button(text="Cut Balance", callback_data=f"usr_ctl_cutbal:{target_id}", emoji_key="cash")
        ],
        [
            make_custom_button(text=res_btn_text, callback_data=res_cb, emoji_key=res_em),
            make_custom_button(text=ban_btn_text, callback_data=ban_cb, emoji_key=ban_em)
        ],
        [
            make_custom_button(text="User Orders", callback_data=f"usr_ctl_orders:{target_id}", emoji_key="orders"),
            make_custom_button(text="Send Direct DM", callback_data=f"usr_ctl_dm:{target_id}", emoji_key="support")
        ],
        [
            make_custom_button(text="Back to Admin", callback_data="admin_main_dashboard", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_edit_options_kb(product_id: int, is_active: bool = True, has_photo: bool = False, stock_count: int = 0, is_in_stock: bool = True) -> InlineKeyboardMarkup:
    """Interactive editor buttons for any product with full A-to-Z control."""
    status_text = "Deactivate Product" if is_active else "Activate Product"
    status_em = "cross" if is_active else "check"
    
    stock_status_btn = (
        make_custom_button(text="🟢 In Stock (ক্লিক: Out of Stock)", callback_data=f"toggle_p_stock:{product_id}", emoji_key="check")
        if is_in_stock else
        make_custom_button(text="🔴 Out of Stock (ক্লিক: In Stock)", callback_data=f"toggle_p_stock:{product_id}", emoji_key="cross")
    )
    
    photo_btn = (
        make_custom_button(text="Remove Photo", callback_data=f"edit_p_remphoto:{product_id}", emoji_key="cross")
        if has_photo else
        make_custom_button(text="Add Photo", callback_data=f"edit_p_photo:{product_id}", emoji_key="sparkle")
    )
    
    buttons = [
        [
            stock_status_btn
        ],
        [
            make_custom_button(text="Edit Title", callback_data=f"edit_p_title:{product_id}", emoji_key="edit"),
            make_custom_button(text="Edit Description", callback_data=f"edit_p_desc:{product_id}", emoji_key="edit")
        ],
        [
            make_custom_button(text="Edit Regular Price", callback_data=f"edit_p_price:{product_id}", emoji_key="cash"),
            make_custom_button(text="Edit Reseller Price", callback_data=f"edit_p_resprice:{product_id}", emoji_key="diamond")
        ],
        [
            make_custom_button(text="Change Category", callback_data=f"edit_p_category:{product_id}", emoji_key="category"),
            make_custom_button(text="Change Type", callback_data=f"edit_p_type:{product_id}", emoji_key="refresh")
        ],
        [
            make_custom_button(text="Edit Sales Page URL", callback_data=f"edit_p_salespage:{product_id}", emoji_key="channel"),
            make_custom_button(text="Edit Dual Pricing", callback_data=f"edit_p_tiers:{product_id}", emoji_key="box")
        ],
        [
            make_custom_button(text="Edit Target (Link/ID)", callback_data=f"edit_p_target:{product_id}", emoji_key="channel"),
            make_custom_button(text="Edit Banner Photo", callback_data=f"edit_p_photo:{product_id}", emoji_key="sparkle")
        ],
        [
            make_custom_button(text=f"Stock Manager ({stock_count})", callback_data=f"edit_p_stock:{product_id}", emoji_key="box"),
            photo_btn
        ],
        [
            make_custom_button(text=status_text, callback_data=f"edit_p_toggle:{product_id}", emoji_key=status_em),
            make_custom_button(text="Delete Product", callback_data=f"edit_p_delete:{product_id}", emoji_key="cross")
        ],
        [
            make_custom_button(text="Back to Products List", callback_data="admin_list_prods", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_hub_kb() -> InlineKeyboardMarkup:
    """Master settings hub with department categories and Custom Emojis Manager."""
    buttons = [
        [
            make_custom_button(text="১. পেমেন্ট গেটওয়ে ও নম্বর সেটিংস", callback_data="admin_set_cat:payment", emoji_key="deposit")
        ],
        [
            make_custom_button(text="২. রেফারেল ও গ্রোথ ইঞ্জিন সেটিংস", callback_data="admin_set_cat:referral", emoji_key="referral")
        ],
        [
            make_custom_button(text="৩. রিসেলার ও ফাইন্যান্সিয়াল সেটিংস", callback_data="admin_set_cat:reseller", emoji_key="diamond")
        ],
        [
            make_custom_button(text="৪. চ্যানেল ও সাপোর্ট সেটিংস", callback_data="admin_set_cat:channel", emoji_key="channel")
        ],
        [
            make_custom_button(text="৫. নোটিশ, নির্দেশিকা ও মিনিমাম ডিপোজিট", callback_data="admin_set_cat:texts", emoji_key="edit")
        ],
        [
            make_custom_button(text="৬. Telegram Premium Custom Emojis (ইমোজি হাব)", callback_data="admin_set_cat:emojis", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="৭. 🤖 Groq AI কী-ম্যানেজার (Multi-Key Engine)", callback_data="admin_groq_keys_menu", emoji_key="crown")
        ],
        [
            make_custom_button(text="৮. 💾 অটোমেটিক ডাটাবেজ ব্যাকআপ ও সেফটি", callback_data="admin_set_cat:backup", emoji_key="box")
        ],
        [
            make_custom_button(text="Back to Main Panel", callback_data="admin_main_dashboard", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_backup_kb() -> InlineKeyboardMarkup:
    """Database backup and export configuration keyboard."""
    buttons = [
        [
            make_custom_button(text="💾 এখনই ব্যাকআপ নিন (Download DB)", callback_data="admin_instant_db_backup", emoji_key="box")
        ],
        [
            make_custom_button(text="🔄 টেস্ট অটো-ব্যাকআপ রান (All Admins)", callback_data="admin_test_backup_run", emoji_key="broadcast")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_texts_kb() -> InlineKeyboardMarkup:
    """Custom notices, guidelines, and instructions configuration keyboard."""
    buttons = [
        [
            make_custom_button(text="Edit Welcome Announcement", callback_data="set_edit:welcome_announcement", emoji_key="broadcast")
        ],
        [
            make_custom_button(text="Edit Min Deposit (BDT)", callback_data="set_edit:min_deposit_bdt", emoji_key="cash"),
            make_custom_button(text="Edit Min Deposit (USD)", callback_data="set_edit:min_deposit_usd", emoji_key="cash")
        ],
        [
            make_custom_button(text="Edit Reseller Terms Note", callback_data="set_edit:reseller_policy_note", emoji_key="orders")
        ],
        [
            make_custom_button(text="Edit bKash Instruction", callback_data="set_edit:bkash_instruction", emoji_key="bkash"),
            make_custom_button(text="Edit Nagad Instruction", callback_data="set_edit:nagad_instruction", emoji_key="nagad")
        ],
        [
            make_custom_button(text="Edit Rocket Instruction", callback_data="set_edit:rocket_instruction", emoji_key="rocket"),
            make_custom_button(text="Edit Binance Instruction", callback_data="set_edit:binance_instruction", emoji_key="binance")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_payment_kb(gateways: Dict[str, bool] = None) -> InlineKeyboardMarkup:
    """Payment gateways control and number editor keyboard."""
    if not gateways:
        gateways = {"bkash": True, "nagad": True, "rocket": True, "binance": True}
    
    b_bkash = "bKash Active" if gateways.get("bkash", True) else "bKash Paused"
    b_nagad = "Nagad Active" if gateways.get("nagad", True) else "Nagad Paused"
    b_rocket = "Rocket Active" if gateways.get("rocket", True) else "Rocket Paused"
    b_binance = "Binance Active" if gateways.get("binance", True) else "Binance Paused"

    buttons = [
        [
            make_custom_button(text=b_bkash, callback_data="toggle_gw:bkash", emoji_key="bkash"),
            make_custom_button(text=b_nagad, callback_data="toggle_gw:nagad", emoji_key="nagad")
        ],
        [
            make_custom_button(text=b_rocket, callback_data="toggle_gw:rocket", emoji_key="rocket"),
            make_custom_button(text=b_binance, callback_data="toggle_gw:binance", emoji_key="binance")
        ],
        [
            make_custom_button(text="Edit bKash (Cash Out)", callback_data="set_edit:bkash_number", emoji_key="bkash"),
            make_custom_button(text="Edit Nagad (Cash Out)", callback_data="set_edit:nagad_number", emoji_key="nagad")
        ],
        [
            make_custom_button(text="Edit Rocket No", callback_data="set_edit:rocket_number", emoji_key="rocket"),
            make_custom_button(text="Edit Binance ID", callback_data="set_edit:binance_pay_id", emoji_key="binance")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_referral_kb() -> InlineKeyboardMarkup:
    """Referral and viral growth configuration keyboard."""
    buttons = [
        [
            make_custom_button(text="Edit Tier-1 Direct Bonus", callback_data="set_edit:referral_t1_bonus", emoji_key="free_claim"),
            make_custom_button(text="Edit Tier-2 Team %", callback_data="set_edit:referral_t2_percent", emoji_key="referral")
        ],
        [
            make_custom_button(text="Edit Newbie Welcome Gift", callback_data="set_edit:referral_welcome_bonus", emoji_key="gift"),
            make_custom_button(text="View Leaderboard", callback_data="ref_leaderboard", emoji_key="trophy")
        ],
        [
            make_custom_button(text="Edit Bronze Bonus", callback_data="set_edit:ref_milestone_bronze_bonus", emoji_key="star"),
            make_custom_button(text="Bronze Target", callback_data="set_edit:ref_milestone_bronze_target", emoji_key="target")
        ],
        [
            make_custom_button(text="Edit Silver Bonus", callback_data="set_edit:ref_milestone_silver_bonus", emoji_key="star"),
            make_custom_button(text="Silver Target", callback_data="set_edit:ref_milestone_silver_target", emoji_key="target")
        ],
        [
            make_custom_button(text="Edit Gold Bonus", callback_data="set_edit:ref_milestone_gold_bonus", emoji_key="trophy"),
            make_custom_button(text="Gold Target", callback_data="set_edit:ref_milestone_gold_target", emoji_key="target")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_reseller_kb() -> InlineKeyboardMarkup:
    """Reseller quota, min deposit, and USD exchange rate settings."""
    buttons = [
        [
            make_custom_button(text="Edit Reseller Min Load", callback_data="set_edit:reseller_min_deposit", emoji_key="diamond"),
            make_custom_button(text="Edit Activation Fee", callback_data="set_edit:reseller_activation_fee", emoji_key="shield")
        ],
        [
            make_custom_button(text="Edit USD Rate (BDT)", callback_data="set_edit:usd_rate", emoji_key="cash"),
            make_custom_button(text="Edit Sales Quota Target", callback_data="set_edit:reseller_monthly_quota", emoji_key="target")
        ],
        [
            make_custom_button(text="Edit Quota Cycle Days", callback_data="set_edit:reseller_quota_days", emoji_key="calendar"),
            make_custom_button(text="Force Quota Scan Now", callback_data="admin_enforce_quotas_now", emoji_key="refresh")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_channel_kb() -> InlineKeyboardMarkup:
    """Official channel and support username settings."""
    buttons = [
        [
            make_custom_button(text="Edit Official Channel", callback_data="set_edit:official_channel", emoji_key="channel"),
            make_custom_button(text="Edit Admin Username", callback_data="set_edit:admin_username", emoji_key="support")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_emojis_kb() -> InlineKeyboardMarkup:
    """Custom emoji inspection and management keyboard."""
    buttons = [
        [
            make_custom_button(text="Inspect Emojis Guide (/getemoji)", callback_data="admin_guide_getemoji", emoji_key="search"),
            make_custom_button(text="Set Emoji ID (/setemoji)", callback_data="admin_prompt_setemoji", emoji_key="edit")
        ],
        [
            make_custom_button(text="View Active Emoji Map", callback_data="admin_view_emojis_map", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_menu_kb(gateways: Dict[str, bool] = None) -> InlineKeyboardMarkup:
    """Alias for backwards compatibility."""
    return get_settings_hub_kb()

def get_admin_categories_kb(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """List of all categories with add and edit options."""
    buttons = []
    for c in categories:
        type_badge = "Course" if c["type"] == "course" else "Digital"
        btn_txt = f"{c['name']} [{type_badge}]"
        buttons.append([make_custom_button(text=btn_txt, callback_data=f"edit_cat_select:{c['id']}", emoji_key="category")])
    buttons.append([
        make_custom_button(text="Add New Category", callback_data="cat_add_new", emoji_key="courses"),
        make_custom_button(text="Back to Main Panel", callback_data="admin_main_dashboard", emoji_key="back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_category_edit_kb(cat_id: int, cat_type: str = "course") -> InlineKeyboardMarkup:
    """Category edit actions."""
    type_label = "Make Digital Tool" if cat_type == "course" else "Make Course Category"
    buttons = [
        [
            make_custom_button(text="➕ সাব-ক্যাটাগরি যোগ (Add Subcat)", callback_data=f"cat_add_sub:{cat_id}", emoji_key="courses"),
            make_custom_button(text="📋 সাব-ক্যাটাগরি সমূহ (Manage)", callback_data=f"cat_list_sub:{cat_id}", emoji_key="category")
        ],
        [
            make_custom_button(text="Rename Category", callback_data=f"cat_edit_name:{cat_id}", emoji_key="edit"),
            make_custom_button(text="Change Icon", callback_data=f"cat_edit_icon:{cat_id}", emoji_key="sparkle")
        ],
        [
            make_custom_button(text=type_label, callback_data=f"cat_toggle_type:{cat_id}", emoji_key="refresh"),
            make_custom_button(text="Delete Category", callback_data=f"cat_delete:{cat_id}", emoji_key="cross")
        ],
        [
            make_custom_button(text="Back to Categories", callback_data="admin_cats_menu", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_subcategories_kb(subcategories: List[Dict[str, Any]], parent_cat_id: int) -> InlineKeyboardMarkup:
    """List of all subcategories under a parent category."""
    buttons = []
    for sc in subcategories:
        icon = sc.get("icon") or "📁"
        btn_txt = f"{icon} {sc['name']}"
        buttons.append([make_custom_button(text=btn_txt, callback_data=f"edit_subcat_select:{sc['id']}", emoji_key="category")])
    buttons.append([
        make_custom_button(text="➕ নতুন সাব-ক্যাটাগরি যোগ", callback_data=f"cat_add_sub:{parent_cat_id}", emoji_key="courses"),
        make_custom_button(text="🔙 ক্যাটাগরিতে ব্যাক", callback_data=f"edit_cat_select:{parent_cat_id}", emoji_key="back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subcategory_edit_kb(subcat_id: int, parent_cat_id: int) -> InlineKeyboardMarkup:
    """Actions on an individual subcategory."""
    buttons = [
        [
            make_custom_button(text="Rename Subcategory", callback_data=f"subcat_edit_name:{subcat_id}", emoji_key="edit"),
            make_custom_button(text="Change Icon", callback_data=f"subcat_edit_icon:{subcat_id}", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="Delete Subcategory", callback_data=f"subcat_delete:{subcat_id}", emoji_key="cross"),
            make_custom_button(text="Back to Subcategories", callback_data=f"cat_list_sub:{parent_cat_id}", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_coupons_menu_kb() -> InlineKeyboardMarkup:
    """Coupon and promo code management buttons."""
    buttons = [
        [
            make_custom_button(text="Create New Coupon Code", callback_data="coupon_create", emoji_key="coupon"),
            make_custom_button(text="View All Coupons & Manage", callback_data="coupon_list", emoji_key="orders")
        ],
        [
            make_custom_button(text="Back to Main Panel", callback_data="admin_main_dashboard", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_coupon_actions_kb(coupon_id: int, is_active: bool = True) -> InlineKeyboardMarkup:
    """Action buttons for an individual coupon."""
    toggle_text = "Deactivate Coupon" if is_active else "Activate Coupon"
    toggle_em = "cross" if is_active else "check"
    buttons = [
        [
            make_custom_button(text=toggle_text, callback_data=f"coupon_toggle:{coupon_id}", emoji_key=toggle_em),
            make_custom_button(text="Delete Coupon", callback_data=f"coupon_del:{coupon_id}", emoji_key="cross")
        ],
        [
            make_custom_button(text="Back to Coupons", callback_data="coupon_list", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_stock_manage_kb(product_id: int, stock_count: int = 0) -> InlineKeyboardMarkup:
    """Stock management keyboard for an individual product."""
    buttons = [
        [
            make_custom_button(text="Add Stock Items", callback_data=f"admin_prod_add_stock:{product_id}", emoji_key="box"),
            make_custom_button(text=f"View Unused ({stock_count})", callback_data=f"admin_view_stock:{product_id}", emoji_key="orders")
        ],
        [
            make_custom_button(text="Clear All Unused Stock", callback_data=f"admin_clear_stock_ask:{product_id}", emoji_key="cross")
        ],
        [
            make_custom_button(text="Back to Product Editor", callback_data=f"edit_p_select:{product_id}", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reseller_pricing_shortcuts_kb(price_bdt: float) -> InlineKeyboardMarkup:
    """1-Click Discount Shortcuts."""
    p20 = int(price_bdt * 0.80)
    p30 = int(price_bdt * 0.70)
    p40 = int(price_bdt * 0.60)
    buttons = [
        [
            make_custom_button(text=f"20% Off (৳{p20})", callback_data=f"res_disc:20:{p20}", emoji_key="zap"),
            make_custom_button(text=f"30% Off (৳{p30})", callback_data=f"res_disc:30:{p30}", emoji_key="zap")
        ],
        [
            make_custom_button(text=f"40% Off (৳{p40})", callback_data=f"res_disc:40:{p40}", emoji_key="zap"),
            make_custom_button(text="Custom Reseller Price", callback_data="res_disc:custom:0", emoji_key="edit")
        ],
        [
            make_custom_button(text="Cancel", callback_data="cancel_fsm", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reseller_admin_menu_kb(at_risk_count: int = 0) -> InlineKeyboardMarkup:
    """Reseller management options in admin panel."""
    risk_text = f"Quota At-Risk ({at_risk_count})" if at_risk_count > 0 else "Quota Radar"
    buttons = [
        [
            make_custom_button(text="Reward Top Sellers (কুপন/পাস বিতরণ)", callback_data="admin_reward_top_hub", emoji_key="trophy"),
            make_custom_button(text="Active VIP Passes", callback_data="admin_active_vip_passes", emoji_key="diamond")
        ],
        [
            make_custom_button(text="Live Sales Race & Challenge", callback_data="admin_race_challenge_hub", emoji_key="flag")
        ],
        [
            make_custom_button(text="All Resellers List (/resellers)", callback_data="admin_list_resellers", emoji_key="users"),
            make_custom_button(text="Pending Applications", callback_data="admin_pending_reseller_apps", emoji_key="orders")
        ],
        [
            make_custom_button(text=risk_text, callback_data="admin_reseller_risk_radar", emoji_key="target"),
            make_custom_button(text="Send Quota Alert PMs", callback_data="admin_alert_risk_resellers", emoji_key="broadcast")
        ],
        [
            make_custom_button(text="Broadcast to Resellers Only", callback_data="admin_broadcast_resellers", emoji_key="broadcast"),
            make_custom_button(text="Quick Promote User", callback_data="admin_quick_promote_reseller", emoji_key="diamond")
        ],
        [
            make_custom_button(text="Back to Main Panel", callback_data="admin_main_dashboard", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_race_challenge_kb() -> InlineKeyboardMarkup:
    """Admin controls for Sales Race & Challenge."""
    buttons = [
        [
            make_custom_button(text="Edit Race Target & Rules (নিয়ম ও ছাড় এডিট)", callback_data="admin_edit_race_rules", emoji_key="edit")
        ],
        [
            make_custom_button(text="Reset Race (নতুন রাউন্ড শুরু)", callback_data="admin_reset_race_confirm", emoji_key="refresh")
        ],
        [
            make_custom_button(text="Back to Reseller Hub", callback_data="admin_resellers_menu", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reward_top_menu_kb() -> InlineKeyboardMarkup:
    """Menu for rewarding top sellers."""
    buttons = [
        [
            make_custom_button(text="Reward Top 3 Resellers (সেরা ৩ জন)", callback_data="reward_top_n:3", emoji_key="trophy"),
            make_custom_button(text="Reward Top 5 Resellers (সেরা ৫ জন)", callback_data="reward_top_n:5", emoji_key="gift")
        ],
        [
            make_custom_button(text="Reward Specific Reseller (কাস্টম)", callback_data="reward_custom_reseller", emoji_key="edit"),
            make_custom_button(text="View Active VIP Passes", callback_data="admin_active_vip_passes", emoji_key="diamond")
        ],
        [
            make_custom_button(text="Back to Reseller Hub", callback_data="admin_resellers_menu", emoji_key="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reward_discount_presets_kb(top_n: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            make_custom_button(text="৳30 Off / Item", callback_data=f"rwd_disc:{top_n}:30", emoji_key="zap"),
            make_custom_button(text="৳50 Off / Item", callback_data=f"rwd_disc:{top_n}:50", emoji_key="zap")
        ],
        [
            make_custom_button(text="৳100 Off / Item", callback_data=f"rwd_disc:{top_n}:100", emoji_key="zap"),
            make_custom_button(text="Custom Amount", callback_data=f"rwd_disc:{top_n}:custom", emoji_key="edit")
        ],
        [
            make_custom_button(text="Cancel", callback_data="admin_resellers_menu", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reward_duration_presets_kb(top_n: int, discount: float) -> InlineKeyboardMarkup:
    buttons = [
        [
            make_custom_button(text="7 Days (১ সপ্তাহ)", callback_data=f"rwd_dur:{top_n}:{discount}:7", emoji_key="orders"),
            make_custom_button(text="15 Days (১৫ দিন)", callback_data=f"rwd_dur:{top_n}:{discount}:15", emoji_key="orders")
        ],
        [
            make_custom_button(text="30 Days (১ মাস)", callback_data=f"rwd_dur:{top_n}:{discount}:30", emoji_key="orders")
        ],
        [
            make_custom_button(text="Cancel", callback_data="admin_resellers_menu", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reward_uses_presets_kb(top_n: int, discount: float, days: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            make_custom_button(text="5 Orders", callback_data=f"rwd_apply:{top_n}:{discount}:{days}:5", emoji_key="box"),
            make_custom_button(text="10 Orders", callback_data=f"rwd_apply:{top_n}:{discount}:{days}:10", emoji_key="box")
        ],
        [
            make_custom_button(text="20 Orders", callback_data=f"rwd_apply:{top_n}:{discount}:{days}:20", emoji_key="box"),
            make_custom_button(text="Unlimited (100)", callback_data=f"rwd_apply:{top_n}:{discount}:{days}:100", emoji_key="box")
        ],
        [
            make_custom_button(text="Cancel", callback_data="admin_resellers_menu", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_broadcast_target_kb() -> InlineKeyboardMarkup:
    """Target selection for broadcast studio."""
    buttons = [
        [
            make_custom_button(text="Broadcast to ALL Users", callback_data="bcast_target:all", emoji_key="broadcast"),
            make_custom_button(text="Broadcast to RESELLERS Only", callback_data="bcast_target:resellers", emoji_key="diamond")
        ],
        [
            make_custom_button(text="Cancel", callback_data="admin_main_dashboard", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_deposit_approval_kb(trx_id: int) -> InlineKeyboardMarkup:
    """Buttons attached to the payment screenshot sent to the Admin."""
    buttons = [
        [
            make_custom_button(text="Approve Deposit", callback_data=f"approve_dep:{trx_id}", emoji_key="check"),
            make_custom_button(text="Reject", callback_data=f"reject_dep:{trx_id}", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_type_kb() -> InlineKeyboardMarkup:
    """Select how the course/product will be delivered."""
    buttons = [
        [
            make_custom_button(text="🔥 Dual Package (Channel + Account Access একসাথে)", callback_data="prod_type:dual_access", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="📢 VIP Channel (1-Time Single-Use Link)", callback_data="prod_type:channel_link", emoji_key="channel")
        ],
        [
            make_custom_button(text="🔐 Ready Account (Mail:Pass + Portal + Tips)", callback_data="prod_type:stock_account", emoji_key="box")
        ],
        [
            make_custom_button(text="☁️ Google Drive / Mega Cloud Link", callback_data="prod_type:drive_link", emoji_key="download")
        ],
        [
            make_custom_button(text="Cancel", callback_data="cancel_fsm", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_giveaway_category_select_kb() -> InlineKeyboardMarkup:
    """Choose which giveaway section / category to drop."""
    buttons = [
        [
            make_custom_button(text="🔐 প্রিমিয়াম একাউন্টস (Accounts)", callback_data="drop_cat_sel:accounts", emoji_key="diamond"),
            make_custom_button(text="🍪 ব্রাউজার কুকিজ (Cookies)", callback_data="drop_cat_sel:cookies", emoji_key="sparkle")
        ],
        [
            make_custom_button(text="👑 সাবস্ক্রিপশন ও কি (Subscription/Keys)", callback_data="drop_cat_sel:subscription", emoji_key="crown"),
            make_custom_button(text="📢 ভিআইপি চ্যানেল এক্সেস (Channel)", callback_data="drop_cat_sel:channel", emoji_key="channel")
        ],
        [
            make_custom_button(text="💾 টুলস ও ক্লাউড ড্রাইভ (Tools/Drive)", callback_data="drop_cat_sel:tools_drive", emoji_key="box")
        ],
        [
            make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_free_drops_kb(drops: List[Dict[str, Any]] = None, current_cat: str = "all") -> InlineKeyboardMarkup:
    """List of all free claim drops with category filter tabs and creation button."""
    buttons = [
        [make_custom_button(text="➕ নতুন গিভঅ্যাওয়ে তৈরি করুন (New Drop)", callback_data="admin_drop_create", emoji_key="free_claim")],
        [
            make_custom_button(text=f"{'👉 ' if current_cat == 'accounts' else ''}🔐 Accounts", callback_data="admin_drop_filter:accounts", emoji_key="diamond"),
            make_custom_button(text=f"{'👉 ' if current_cat == 'cookies' else ''}🍪 Cookies", callback_data="admin_drop_filter:cookies", emoji_key="sparkle"),
            make_custom_button(text=f"{'👉 ' if current_cat == 'subscription' else ''}👑 Sub/Key", callback_data="admin_drop_filter:subscription", emoji_key="crown")
        ],
        [
            make_custom_button(text=f"{'👉 ' if current_cat == 'channel' else ''}📢 Channels", callback_data="admin_drop_filter:channel", emoji_key="channel"),
            make_custom_button(text=f"{'👉 ' if current_cat == 'tools_drive' else ''}💾 Tools", callback_data="admin_drop_filter:tools_drive", emoji_key="box"),
            make_custom_button(text=f"{'👉 ' if current_cat == 'all' else ''}🔥 All", callback_data="admin_drop_filter:all", emoji_key="fire")
        ]
    ]
    if drops:
        cat_icons = {"accounts": "🔐", "cookies": "🍪", "subscription": "👑", "channel": "📢", "tools_drive": "💾"}
        for d in drops[:15]:
            title = d.get('title', 'Drop')
            c_tag = cat_icons.get(d.get("giveaway_category", "accounts"), "🎁")
            claimed = d.get('claimed_count', 0)
            total = d.get('max_claims', 0)
            slots_str = f"{claimed}/{total}"
            btn_txt = f"{c_tag} {title[:18]} ({slots_str})"
            em_k = "check" if d.get('is_active') else "cross"
            buttons.append([make_custom_button(text=btn_txt, callback_data=f"admin_drop_detail:{d['id']}", emoji_key=em_k)])
    buttons.append([
        make_custom_button(text="Refresh", callback_data=f"admin_drop_filter:{current_cat}", emoji_key="refresh"),
        make_custom_button(text="Back to Dashboard", callback_data="admin_main_dashboard", emoji_key="back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_drop_type_kb(category: str = "accounts") -> InlineKeyboardMarkup:
    """Choose giveaway drop delivery type tailored to the selected category."""
    if category == "channel":
        buttons = [
            [make_custom_button(text="📢 চ্যানেল অটো-ইনভাইট (১ জন = ১ লিংক)", callback_data="drop_type:channel_link", emoji_key="channel")],
            [make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")]
        ]
    elif category == "cookies":
        buttons = [
            [make_custom_button(text="🍪 বাল্ক কুকিজ লিস্ট (প্রতি লাইনে ১টি কুকিজ)", callback_data="drop_type:bulk_combo", emoji_key="box")],
            [make_custom_button(text="📋 কমন কুকিজ কোড (সবার জন্য একই)", callback_data="drop_type:direct_link", emoji_key="download")],
            [make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")]
        ]
    elif category == "subscription":
        buttons = [
            [make_custom_button(text="🔑 বাল্ক ভাউচার / কি লিস্ট (১ জন = ১ কি)", callback_data="drop_type:bulk_combo", emoji_key="box")],
            [make_custom_button(text="🔗 কমন রিডিম লিঙ্ক (ড্রাইভ/ওয়েব)", callback_data="drop_type:direct_link", emoji_key="download")],
            [make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")]
        ]
    elif category == "tools_drive":
        buttons = [
            [make_custom_button(text="💾 গুগল ড্রাইভ / মেগা ক্লাউড লিংক", callback_data="drop_type:direct_link", emoji_key="download")],
            [make_custom_button(text="📦 বাল্ক এক্সেস কি / টোকেন লিস্ট", callback_data="drop_type:bulk_combo", emoji_key="box")],
            [make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")]
        ]
    else: # accounts default
        buttons = [
            [make_custom_button(text="📦 বাল্ক একাউন্ট কম্বো (মেইল:পাসওয়ার্ড)", callback_data="drop_type:bulk_combo", emoji_key="box")],
            [make_custom_button(text="🔗 কমন লগইন লিঙ্ক / পোর্টাল", callback_data="drop_type:direct_link", emoji_key="download")],
            [make_custom_button(text="❌ Cancel", callback_data="admin_free_drops_menu", emoji_key="cross")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_drop_detail_kb(drop_id: int, is_active: bool = True) -> InlineKeyboardMarkup:
    """Actions for a specific free claim drop."""
    buttons = []
    if is_active:
        buttons.append([
            make_custom_button(text="🔒 ভাইরাল শর্ত পরিবর্তন (Edit Gate)", callback_data=f"drop_edit_refs:{drop_id}", emoji_key="edit"),
            make_custom_button(text="📢 ব্রডকাস্ট পাঠান", callback_data=f"admin_drop_bcast:{drop_id}", emoji_key="broadcast")
        ])
        buttons.append([
            make_custom_button(text="🗑️ ড্রপ বন্ধ / রিমুভ করুন", callback_data=f"admin_drop_close:{drop_id}", emoji_key="cross")
        ])
    buttons.append([
        make_custom_button(text="View Claimed Users", callback_data=f"admin_drop_claims:{drop_id}", emoji_key="orders"),
        make_custom_button(text="Back to Drops", callback_data="admin_free_drops_menu", emoji_key="back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_groq_preview_kb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Shortcut edit and 1-tap publish keyboard for Groq Auto-Generated Course."""
    ch_p = int(data.get("price_channel_bdt", 150))
    acc_p = int(data.get("price_account_bdt", 350))
    has_ch = "✅" if data.get("channel_target") else "⚠️"
    has_acc = "✅" if data.get("account_data") else "⚠️"
    cat_name = data.get("category_name", "কোর্স")[:12]

    buttons = [
        [
            make_custom_button(text=f"💰 Channel: ৳{ch_p}", callback_data="groq_edit:ch_price", emoji_key="channel"),
            make_custom_button(text=f"💰 Account: ৳{acc_p}", callback_data="groq_edit:acc_price", emoji_key="box")
        ],
        [
            make_custom_button(text=f"{has_ch} Set Channel ID/Link", callback_data="groq_edit:channel_target", emoji_key="channel"),
            make_custom_button(text=f"{has_acc} Set Account/Drive", callback_data="groq_edit:account_data", emoji_key="box")
        ],
        [
            make_custom_button(text=f"📁 Cat: {cat_name}", callback_data="groq_edit:category", emoji_key="category"),
            make_custom_button(text="✏️ Edit Title / Desc", callback_data="groq_edit:content", emoji_key="edit")
        ],
        [
            make_custom_button(text="🚀 এক ক্লিকে পাবলিশ করুন (Publish)", callback_data="groq_publish_course", emoji_key="zap")
        ],
        [
            make_custom_button(text="❌ বাতিল (Cancel)", callback_data="cancel_fsm", emoji_key="cross")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_groq_keys_menu_kb(keys: List[str]) -> InlineKeyboardMarkup:
    """Multi-Key manager keyboard for Groq API keys."""
    buttons = [
        [
            make_custom_button(text="➕ Add New Groq Key", callback_data="groq_key_add", emoji_key="crown"),
            make_custom_button(text="⚡ Test Keys (Ping)", callback_data="groq_keys_test", emoji_key="zap")
        ],
        [
            make_custom_button(text="🗑️ Delete a Key", callback_data="groq_key_delete_menu", emoji_key="cross"),
            make_custom_button(text="🔄 Reset Key Failures", callback_data="groq_keys_reset_pool", emoji_key="refresh")
        ],
        [
            make_custom_button(text="সেটিংস মেনু", callback_data="admin_settings", emoji_key="back"),
            make_custom_button(text="মেইন প্যানেল", callback_data="admin_main_dashboard", emoji_key="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_groq_key_delete_kb(keys: List[str]) -> InlineKeyboardMarkup:
    """Keyboard to select and delete an individual Groq API key."""
    buttons = []
    for idx, k in enumerate(keys):
        masked = f"Key #{idx+1} (...{k[-6:]})" if len(k) > 6 else f"Key #{idx+1}"
        buttons.append([
            make_custom_button(text=f"🗑️ Delete {masked}", callback_data=f"groq_key_del_idx:{idx}", emoji_key="cross")
        ])
    buttons.append([
        make_custom_button(text="🔙 Back to Key Manager", callback_data="admin_groq_keys_menu", emoji_key="back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
