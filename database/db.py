# SQLite Database Handler for Reseller Bot
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

DB_PATH = os.getenv("DATABASE_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 15000")
        conn.execute("PRAGMA cache_size = -10000")   # ~10MB page cache
        conn.execute("PRAGMA mmap_size = 134217728") # 128MB memory-mapped I/O
        conn.execute("PRAGMA temp_store = MEMORY")   # temp tables in RAM
        return conn

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=15.0) as init_conn:
            init_conn.execute("PRAGMA journal_mode = WAL")
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance_bdt REAL DEFAULT 0.0,
                balance_usd REAL DEFAULT 0.0,
                total_spent_bdt REAL DEFAULT 0.0,
                total_spent_usd REAL DEFAULT 0.0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            )
            """)

            # 2. Categories table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '📁',
                type TEXT DEFAULT 'course', -- 'course' or 'digital'
                parent_id INTEGER DEFAULT NULL,
                order_num INTEGER DEFAULT 0
            )
            """)

            # 3. Products table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                subcategory_id INTEGER DEFAULT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                price_bdt REAL NOT NULL,
                price_usd REAL NOT NULL,
                product_type TEXT NOT NULL, -- 'channel_link', 'stock_account', 'drive_link', 'manual'
                channel_id TEXT DEFAULT NULL,
                drive_link TEXT DEFAULT NULL,
                photo_file_id TEXT DEFAULT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (subcategory_id) REFERENCES categories (id)
            )
            """)

            # Auto-migration for subcategory columns
            cursor.execute("PRAGMA table_info(categories)")
            cat_cols = [r[1] for r in cursor.fetchall()]
            if "parent_id" not in cat_cols:
                cursor.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER DEFAULT NULL REFERENCES categories(id) ON DELETE CASCADE")

            cursor.execute("PRAGMA table_info(products)")
            prod_cols = [r[1] for r in cursor.fetchall()]
            if "subcategory_id" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN subcategory_id INTEGER DEFAULT NULL REFERENCES categories(id) ON DELETE SET NULL")

            # 4. Stock items (accounts, serial keys, one-time drive links)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER DEFAULT NULL,
                used_at TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """)

            # 5. Transactions (Deposits with mandatory Screenshot)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL, -- 'BDT' or 'USD'
                trx_id TEXT NOT NULL,
                screenshot_file_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP DEFAULT NULL,
                reviewed_by INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 6. Orders
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_title TEXT NOT NULL,
                product_type TEXT NOT NULL,
                amount_paid REAL NOT NULL,
                currency TEXT NOT NULL,
                delivery_content TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 7. Reseller Applications table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reseller_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                info TEXT DEFAULT '',
                balance_at_apply REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 8. Dynamic Bot Settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)

            # 9. Promo Coupons / Vouchers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_bdt REAL DEFAULT 0.0,
                discount_percent REAL DEFAULT 0.0,
                max_uses INTEGER DEFAULT 100,
                used_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 10. Reseller VIP Reward Passes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reseller_vip_passes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                coupon_code TEXT NOT NULL,
                discount_bdt REAL DEFAULT 0.0,
                discount_percent REAL DEFAULT 0.0,
                expires_at TIMESTAMP NOT NULL,
                max_uses INTEGER DEFAULT 5,
                used_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 11. Reseller Competition / Race Challenges table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reseller_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT 'Monthly Super Seller Race',
                target_sales INTEGER DEFAULT 15,
                max_slots INTEGER DEFAULT 3,
                discount_bdt REAL DEFAULT 50.0,
                days_valid INTEGER DEFAULT 15,
                max_uses INTEGER DEFAULT 10,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 12. Challenge Claimed Winners table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenge_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                vip_pass_id INTEGER NOT NULL,
                sales_at_win INTEGER NOT NULL,
                won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (challenge_id) REFERENCES reseller_challenges (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(challenge_id, user_id)
            )
            """)

            # 13. Referral Logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                tier INTEGER NOT NULL, -- 1 for direct, 2 for indirect/sub-referral
                bonus_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
            """)

            # 14. Free Drops (Giveaways / Free Claim Hub)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS free_drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                giveaway_category TEXT DEFAULT 'accounts', -- 'accounts', 'cookies', 'subscription', 'channel', 'tools_drive'
                instructions TEXT DEFAULT '',
                site_link TEXT DEFAULT '', -- Target website / portal URL (e.g., https://instructory.net)
                drop_type TEXT NOT NULL, -- 'channel_link', 'bulk_combo', 'direct_link'
                channel_id TEXT DEFAULT NULL,
                direct_link TEXT DEFAULT NULL,
                max_claims INTEGER NOT NULL,
                claimed_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                required_referrals INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 15. Free Drop Bulk Items (for bulk account/key combos)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS free_drop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drop_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_claimed INTEGER DEFAULT 0,
                claimed_by INTEGER DEFAULT NULL,
                claimed_at TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (drop_id) REFERENCES free_drops (id)
            )
            """)

            # 16. Free Drop Claims (User Claim Logs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS free_drop_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drop_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                delivery_content TEXT NOT NULL,
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drop_id) REFERENCES free_drops (id),
                UNIQUE(drop_id, user_id)
            )
            """)

            # Seed initial challenge if none exists
            cursor.execute("SELECT COUNT(*) as cnt FROM reseller_challenges")
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute("""
                INSERT INTO reseller_challenges (title, target_sales, max_slots, discount_bdt, days_valid, max_uses, is_active)
                VALUES ('Monthly Super Seller Race', 15, 3, 50.0, 15, 10, 1)
                """)

            # Run safe migrations for existing tables if columns don't exist
            cursor.execute("PRAGMA table_info(users)")
            user_cols = [row["name"] for row in cursor.fetchall()]
            if "is_reseller" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN is_reseller INTEGER DEFAULT 0")
            if "reseller_code" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN reseller_code TEXT DEFAULT NULL")
            if "referred_by" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
            if "referral_earnings_bdt" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_earnings_bdt REAL DEFAULT 0.0")
            if "referral_count_t1" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_count_t1 INTEGER DEFAULT 0")
            if "referral_count_t2" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_count_t2 INTEGER DEFAULT 0")
            if "referral_milestone_tier" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_milestone_tier INTEGER DEFAULT 0")
            if "reseller_quota_start" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN reseller_quota_start TIMESTAMP DEFAULT NULL")
            if "reseller_monthly_sales" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN reseller_monthly_sales INTEGER DEFAULT 0")
            if "reseller_deactivated_permanent" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN reseller_deactivated_permanent INTEGER DEFAULT 0")
            if "language" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'bn'")
            if "referral_points" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_points INTEGER DEFAULT 0")
                cursor.execute("UPDATE users SET referral_points = referral_count_t1 WHERE referral_points = 0 AND referral_count_t1 > 0")
            if "show_bottom_menu" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN show_bottom_menu INTEGER DEFAULT 1")
            if "reseller_tier" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN reseller_tier INTEGER DEFAULT 1")
            if "can_sell_channel" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN can_sell_channel INTEGER DEFAULT 1")
            if "can_sell_account" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN can_sell_account INTEGER DEFAULT 0")

            cursor.execute("PRAGMA table_info(products)")
            prod_cols = [row["name"] for row in cursor.fetchall()]
            if "reseller_price_bdt" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN reseller_price_bdt REAL DEFAULT 0.0")
            if "reseller_price_usd" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN reseller_price_usd REAL DEFAULT 0.0")
            if "is_combo" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN is_combo INTEGER DEFAULT 0")
            if "is_flash_sale" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN is_flash_sale INTEGER DEFAULT 0")
            if "sales_page_url" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN sales_page_url TEXT DEFAULT NULL")
            if "price_channel_bdt" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN price_channel_bdt REAL DEFAULT 0.0")
            if "price_channel_usd" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN price_channel_usd REAL DEFAULT 0.0")
            if "price_account_bdt" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN price_account_bdt REAL DEFAULT 0.0")
            if "price_account_usd" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN price_account_usd REAL DEFAULT 0.0")
            if "reseller_price_channel_bdt" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN reseller_price_channel_bdt REAL DEFAULT 0.0")
            if "reseller_price_account_bdt" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN reseller_price_account_bdt REAL DEFAULT 0.0")
            if "is_in_stock" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN is_in_stock INTEGER DEFAULT 1")
            if "channel_title" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN channel_title TEXT DEFAULT NULL")
            if "channel_verified" not in prod_cols:
                cursor.execute("ALTER TABLE products ADD COLUMN channel_verified INTEGER DEFAULT 0")

            cursor.execute("PRAGMA table_info(orders)")
            order_cols = [row["name"] for row in cursor.fetchall()]
            if "is_reseller_order" not in order_cols:
                cursor.execute("ALTER TABLE orders ADD COLUMN is_reseller_order INTEGER DEFAULT 0")
            if "savings_bdt" not in order_cols:
                cursor.execute("ALTER TABLE orders ADD COLUMN savings_bdt REAL DEFAULT 0.0")
            if "savings_usd" not in order_cols:
                cursor.execute("ALTER TABLE orders ADD COLUMN savings_usd REAL DEFAULT 0.0")
            if "access_tier" not in order_cols:
                cursor.execute("ALTER TABLE orders ADD COLUMN access_tier TEXT DEFAULT 'default'")

            cursor.execute("PRAGMA table_info(reseller_applications)")
            app_cols = [row["name"] for row in cursor.fetchall()]
            if "balance_at_apply" not in app_cols:
                cursor.execute("ALTER TABLE reseller_applications ADD COLUMN balance_at_apply REAL DEFAULT 0.0")
            if "requested_tier" not in app_cols:
                cursor.execute("ALTER TABLE reseller_applications ADD COLUMN requested_tier INTEGER DEFAULT 1")

            # 17. Sub-Admin Staff Roles & RBAC table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                user_id INTEGER PRIMARY KEY,
                name TEXT DEFAULT '',
                username TEXT DEFAULT '',
                added_by INTEGER DEFAULT 0,
                can_manage_free_drops INTEGER DEFAULT 1,
                can_manage_stock INTEGER DEFAULT 0,
                can_manage_products INTEGER DEFAULT 0,
                can_approve_deposits INTEGER DEFAULT 0,
                can_manage_resellers INTEGER DEFAULT 0,
                can_broadcast INTEGER DEFAULT 0,
                can_manage_users INTEGER DEFAULT 0,
                can_manage_coupons INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("PRAGMA table_info(admin_roles)")
            admin_cols = [row["name"] for row in cursor.fetchall()]
            for perm in ["can_manage_free_drops", "can_manage_stock", "can_manage_products",
                         "can_approve_deposits", "can_manage_resellers", "can_broadcast",
                         "can_manage_users", "can_manage_coupons"]:
                if perm not in admin_cols:
                    try:
                        cursor.execute(f"ALTER TABLE admin_roles ADD COLUMN {perm} INTEGER DEFAULT 0")
                    except Exception:
                        pass

            cursor.execute("PRAGMA table_info(free_drops)")
            drop_cols = [row["name"] for row in cursor.fetchall()]
            if "giveaway_category" not in drop_cols:
                try:
                    cursor.execute("ALTER TABLE free_drops ADD COLUMN giveaway_category TEXT DEFAULT 'accounts'")
                except Exception:
                    pass
            if "instructions" not in drop_cols:
                try:
                    cursor.execute("ALTER TABLE free_drops ADD COLUMN instructions TEXT DEFAULT ''")
                except Exception:
                    pass
            if "site_link" not in drop_cols:
                try:
                    cursor.execute("ALTER TABLE free_drops ADD COLUMN site_link TEXT DEFAULT ''")
                except Exception:
                    pass
            if "required_referrals" not in drop_cols:
                try:
                    cursor.execute("ALTER TABLE free_drops ADD COLUMN required_referrals INTEGER DEFAULT 0")
                except Exception:
                    pass

            # 18. Referral Course Tracking table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_course_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                referred_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (course_id) REFERENCES products (id),
                FOREIGN KEY (referred_user_id) REFERENCES users (user_id)
            )
            """)

            # 19. Referral & Wallet Conversion History table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_type TEXT NOT NULL, -- 'points' or 'bdt'
                to_type TEXT NOT NULL,   -- 'bdt' or 'usd'
                amount_in REAL NOT NULL,
                amount_out REAL NOT NULL,
                rate_used REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 20. Customer Course & Digital Product Requests table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT DEFAULT '',
                course_query TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- 'pending', 'available', 'rejected'
                admin_notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Seed default settings if missing
            default_settings = [
                ("bkash_number", "01718539406"),
                ("nagad_number", "01718539406"),
                ("rocket_number", "01718539406"),
                ("binance_pay_id", "892612368"),
                ("bkash_active", "1"),
                ("nagad_active", "1"),
                ("rocket_active", "1"),
                ("binance_active", "1"),
                ("referral_t1_bonus", "10"),
                ("referral_t2_percent", "50"),
                ("referral_welcome_bonus", "5"),
                ("ref_milestone_bronze_target", "10"),
                ("ref_milestone_bronze_bonus", "25"),
                ("ref_milestone_silver_target", "25"),
                ("ref_milestone_silver_bonus", "75"),
                ("ref_milestone_gold_target", "50"),
                ("ref_milestone_gold_bonus", "200"),
                ("usd_rate", "127.0"),
                ("usd_to_bdt_rate", "127.0"),
                ("reseller_min_deposit", "1000"),
                ("reseller_activation_fee", "500"),
                ("reseller_monthly_quota", "5"),
                ("official_channel", "@ProAccessBD"),
                ("admin_username", "proaccessteam")
            ]
            for skey, sval in default_settings:
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (skey, sval))

            # Seed default categories if empty
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            count = cursor.fetchone()["count"]
            if count == 0:
                default_categories = [
                    ("📱 Video Editing & Premiere VIP", "🎬", "course", 1),
                    ("🎨 Graphic Design & Freelancing", "🎨", "course", 2),
                    ("💻 Web Dev & Programming Bundles", "💻", "course", 3),
                    ("📈 Digital Marketing & Dropshipping", "📈", "course", 4),
                    ("🤖 AI Mastery & Automation", "🤖", "course", 5),
                    ("👑 VIP Mega Course Vault (All Access)", "👑", "course", 6),
                    ("🎁 Super Combos & Bundles", "🔥", "course", 7),
                    ("🤖 AI Tools & Accounts (Gemini, ChatGPT, etc.)", "⚡", "digital", 8),
                    ("🎨 Creative Tools (Canva Pro, CapCut, etc.)", "💎", "digital", 9)
                ]
                cursor.executemany(
                    "INSERT INTO categories (name, icon, type, order_num) VALUES (?, ?, ?, ?)",
                    default_categories
                )

            conn.commit()

    # --- USER METHODS ---
    def register_or_update_user(self, user_id: int, username: Optional[str], first_name: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                cursor.execute(
                    "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name)
                )
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
            else:
                # Update info
                cursor.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id)
                )
                conn.commit()
            return dict(user)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_language(self, user_id: int) -> str:
        user = self.get_user(user_id)
        if user and user.get("language"):
            return user["language"]
        return "bn"

    def set_user_language(self, user_id: int, language: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_user_bottom_menu_status(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if user and "show_bottom_menu" in user and user["show_bottom_menu"] is not None:
            return bool(user["show_bottom_menu"])
        return True

    def set_user_bottom_menu_status(self, user_id: int, status: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET show_bottom_menu = ? WHERE user_id = ?", (1 if status else 0, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def add_user_balance(self, user_id: int, amount: float, currency: str = "BDT") -> bool:
        curr_str = str(currency).upper() if currency else "BDT"
        field = "balance_bdt" if curr_str == "BDT" else "balance_usd"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {field} = {field} + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def deduct_user_balance(self, user_id: int, amount: float, currency: str = "BDT") -> bool:
        curr_str = str(currency).upper() if currency else "BDT"
        field = "balance_bdt" if curr_str == "BDT" else "balance_usd"
        spent_field = "total_spent_bdt" if curr_str == "BDT" else "total_spent_usd"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE users SET {field} = {field} - ?, {spent_field} = {spent_field} + ? WHERE user_id = ? AND {field} >= ?",
                (amount, amount, user_id, amount)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_user_balance(self, user_id: int, amount: float, currency: str = "BDT") -> bool:
        if amount >= 0:
            return self.add_user_balance(user_id, amount, currency)
        else:
            return self.deduct_user_balance(user_id, abs(amount), currency)

    # --- CATEGORY & PRODUCT METHODS ---
    def get_categories(self, cat_type: Optional[str] = None, parent_id: Any = None) -> List[Dict[str, Any]]:
        """
        Fetches categories.
        - parent_id=None: only root categories (parent_id IS NULL).
        - parent_id='all': all categories (roots + subcategories).
        - parent_id=int: subcategories under specific parent_id.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if cat_type:
                conditions.append("type = ?")
                params.append(cat_type)
            if parent_id != "all":
                if parent_id is None:
                    conditions.append("parent_id IS NULL")
                else:
                    conditions.append("parent_id = ?")
                    params.append(int(parent_id))
            where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cursor.execute(f"SELECT * FROM categories {where_sql} ORDER BY order_num ASC, id ASC", params)
            return [dict(row) for row in cursor.fetchall()]

    def get_subcategories(self, parent_id: int) -> List[Dict[str, Any]]:
        """Returns all subcategories under a specific parent category."""
        return self.get_categories(parent_id=parent_id)

    def has_subcategories(self, parent_id: int) -> bool:
        """Returns True if the category has one or more subcategories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id = ?", (parent_id,))
            return cursor.fetchone()[0] > 0

    def get_categories_by_type(self, cat_type: str) -> List[Dict[str, Any]]:
        return self.get_categories(cat_type=cat_type, parent_id=None)

    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_category(self, name: str, icon: str, cat_type: str = "course", parent_id: Optional[int] = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name, icon, type, parent_id) VALUES (?, ?, ?, ?)", (name, icon, cat_type, parent_id))
            conn.commit()
            return cursor.lastrowid

    def get_all_categories(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY type ASC, order_num ASC, id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def update_category(self, category_id: int, name: str, icon: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE categories SET name = ?, icon = ? WHERE id = ?", (name, icon, category_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_category_type(self, category_id: int, cat_type: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE categories SET type = ? WHERE id = ?", (cat_type, category_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_category(self, category_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET subcategory_id = NULL 
                WHERE subcategory_id = ? OR subcategory_id IN (SELECT id FROM categories WHERE parent_id = ?)
            """, (category_id, category_id))
            cursor.execute("UPDATE products SET category_id = NULL, is_active = 0 WHERE category_id = ?", (category_id,))
            cursor.execute("DELETE FROM categories WHERE parent_id = ?", (category_id,))
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id is not None:
            return self.get_products_by_category(category_id)
        return self.get_all_products()

    def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE (category_id = ? OR subcategory_id = ?) AND is_active = 1", (category_id, category_id))
            return [dict(row) for row in cursor.fetchall()]

    def get_products_by_subcategory(self, subcategory_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE subcategory_id = ? AND is_active = 1 ORDER BY id DESC", (subcategory_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Returns all active products across categories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_courses(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Intelligent fuzzy and keyword/URL course search.
        Matches against:
        1. Sales page URL (exact match or domain/slug match)
        2. Direct product title (exact, prefix, or partial)
        3. Product description keywords
        4. Category names
        """
        if not query or not query.strip():
            return []
        
        clean_q = query.strip()
        is_url = ("http://" in clean_q or "https://" in clean_q or "www." in clean_q or ('.' in clean_q and ' ' not in clean_q and '/' in clean_q))
        
        url_keywords = []
        if is_url:
            import urllib.parse
            try:
                parsed = urllib.parse.urlparse(clean_q if "://" in clean_q else f"https://{clean_q}")
                path = parsed.path.strip("/").replace("-", " ").replace("_", " ").replace("/", " ")
                url_keywords = [w.lower() for w in path.split() if len(w) > 2 and not w.isdigit()]
            except Exception:
                pass

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. URL match
            if is_url:
                core_url = clean_q.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
                cursor.execute("""
                SELECT p.*, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND p.sales_page_url IS NOT NULL 
                  AND (p.sales_page_url LIKE ? OR ? LIKE '%' || p.sales_page_url || '%')
                LIMIT ?
                """, (f"%{core_url}%", clean_q, limit))
                url_matches = [dict(r) for r in cursor.fetchall()]
                if url_matches:
                    return url_matches

            # 2. Direct Substring Match on full query
            cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
              AND (
                  LOWER(p.title) LIKE ? 
                  OR LOWER(COALESCE(p.description, '')) LIKE ?
                  OR LOWER(COALESCE(p.sales_page_url, '')) LIKE ?
                  OR LOWER(COALESCE(c.name, '')) LIKE ?
              )
            ORDER BY 
              CASE WHEN LOWER(p.title) LIKE ? THEN 1
                   WHEN LOWER(p.title) LIKE ? THEN 2
                   ELSE 3 END,
              p.id DESC
            LIMIT ?
            """, (
                f"%{clean_q.lower()}%",
                f"%{clean_q.lower()}%",
                f"%{clean_q.lower()}%",
                f"%{clean_q.lower()}%",
                f"{clean_q.lower()}%",
                f"%{clean_q.lower()}%",
                limit
            ))
            exact_matches = [dict(r) for r in cursor.fetchall()]
            if exact_matches:
                return exact_matches

            # 3. Keyword / Slug Multi-Term Search
            search_terms = [w.lower() for w in clean_q.split() if len(w) > 1]
            combined_terms = list(set(search_terms + url_keywords))
            fillers = {"course", "কোর্স", "kono", "lagbe", "লাগবে", "chai", "চাই", "kinte", "need", "buy", "dam", "price", "the", "and", "for", "in", "of", "to", "a"}
            meaningful_terms = [t for t in combined_terms if t not in fillers and len(t) > 2]
            
            if meaningful_terms:
                conditions = []
                params = []
                for term in meaningful_terms[:5]:
                    conditions.append("(LOWER(p.title) LIKE ? OR LOWER(COALESCE(p.description, '')) LIKE ?)")
                    params.extend([f"%{term}%", f"%{term}%"])
                
                sql = f"""
                SELECT p.*, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND ({' OR '.join(conditions)})
                ORDER BY p.id DESC
                LIMIT ?
                """
                params.append(limit)
                cursor.execute(sql, params)
                return [dict(r) for r in cursor.fetchall()]

            return []

    def record_course_request(self, user_id: int, user_name: str, course_query: str) -> int:
        """Stores a customer request for a course or tool not in the catalog."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO course_requests (user_id, user_name, course_query)
            VALUES (?, ?, ?)
            """, (user_id, user_name, course_query))
            conn.commit()
            return cursor.lastrowid

    def get_pending_course_requests(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns pending customer course requests for admin view."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT cr.*, u.username, u.first_name
            FROM course_requests cr
            LEFT JOIN users u ON cr.user_id = u.user_id
            WHERE cr.status = 'pending'
            ORDER BY cr.id DESC
            LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def update_course_request_status(self, request_id: int, status: str, admin_notes: str = "") -> bool:
        """Updates request status (e.g. 'available', 'rejected')."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE course_requests 
            SET status = ?, admin_notes = ? 
            WHERE id = ?
            """, (status, admin_notes, request_id))
            conn.commit()
            return cursor.rowcount > 0

    def add_product(self, category_id: int, title: str, description: str, price_bdt: float, price_usd: float,
                    product_type: str, channel_id: Optional[str] = None, drive_link: Optional[str] = None,
                    photo_file_id: Optional[str] = None,
                    reseller_price_bdt: float = 0.0, reseller_price_usd: float = 0.0,
                    price_channel_bdt: float = 0.0, price_channel_usd: float = 0.0,
                    price_account_bdt: float = 0.0, price_account_usd: float = 0.0,
                    reseller_price_channel_bdt: float = 0.0, reseller_price_account_bdt: float = 0.0,
                    is_in_stock: int = 1,
                    sales_page_url: Optional[str] = None,
                    subcategory_id: Optional[int] = None,
                    channel_title: Optional[str] = None,
                    channel_verified: int = 0) -> int:
        if reseller_price_bdt <= 0 and price_bdt > 0:
            reseller_price_bdt = round(price_bdt * 0.70, 2) # default 30% discount for resellers
        if reseller_price_usd <= 0 and price_usd > 0:
            reseller_price_usd = round(price_usd * 0.70, 2)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO products (
                category_id, subcategory_id, title, description, price_bdt, price_usd, product_type,
                channel_id, drive_link, photo_file_id, reseller_price_bdt, reseller_price_usd,
                price_channel_bdt, price_channel_usd, price_account_bdt, price_account_usd,
                reseller_price_channel_bdt, reseller_price_account_bdt, is_in_stock,
                sales_page_url, channel_title, channel_verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id, subcategory_id, title, description, price_bdt, price_usd, product_type,
                channel_id, drive_link, photo_file_id, reseller_price_bdt, reseller_price_usd,
                price_channel_bdt, price_channel_usd, price_account_bdt, price_account_usd,
                reseller_price_channel_bdt, reseller_price_account_bdt, is_in_stock,
                sales_page_url, channel_title, channel_verified
            ))
            conn.commit()
            return cursor.lastrowid

    def update_product_subcategory(self, product_id: int, subcategory_id: Optional[int]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET subcategory_id = ? WHERE id = ?", (subcategory_id, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_product(self, product_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_product_stock(self, product_id: int) -> bool:
        """Toggles product stock status (In Stock <-> Out of Stock) in 1-click."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE products 
            SET is_in_stock = CASE WHEN COALESCE(is_in_stock, 1) = 1 THEN 0 ELSE 1 END 
            WHERE id = ?
            """, (product_id,))
            conn.commit()
            cursor.execute("SELECT is_in_stock FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return bool(row["is_in_stock"]) if row else False

    # --- STOCK METHODS ---
    def add_stock_items(self, product_id: int, items: List[str]) -> int:
        cleaned = [it.strip() for it in items if it.strip()]
        if not cleaned:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            data = [(product_id, item) for item in cleaned]
            cursor.executemany("INSERT INTO stock_items (product_id, content) VALUES (?, ?)", data)
            conn.commit()
            return len(cleaned)

    def get_stock_count(self, product_id: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM stock_items WHERE product_id = ? AND is_used = 0", (product_id,))
            return cursor.fetchone()["cnt"]

    def pop_stock_item(self, product_id: int, user_id: int) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM stock_items WHERE product_id = ? AND is_used = 0 ORDER BY id ASC LIMIT 1", (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item_id = row["id"]
            content = row["content"]
            cursor.execute("UPDATE stock_items SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP WHERE id = ? AND is_used = 0", (user_id, item_id))
            if cursor.rowcount == 0:
                conn.commit()
                return self.pop_stock_item(product_id, user_id)
            conn.commit()
            return content

    def get_product_stock_items(self, product_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stock_items WHERE product_id = ? AND is_used = 0 ORDER BY id ASC LIMIT ?", (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def clear_product_stock(self, product_id: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_items WHERE product_id = ? AND is_used = 0", (product_id,))
            conn.commit()
            return cursor.rowcount

    def delete_stock_item(self, stock_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_items WHERE id = ?", (stock_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- TRANSACTION / DEPOSIT METHODS ---
    def create_deposit_request(self, user_id: int, method: str, amount: float, currency: str, trx_id: str, screenshot_file_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO transactions (user_id, method, amount, currency, trx_id, screenshot_file_id, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (user_id, method, amount, currency, trx_id, screenshot_file_id))
            conn.commit()
            return cursor.lastrowid

    def get_transaction(self, trx_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def approve_deposit(self, transaction_id: int, reviewer_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ? AND status = 'pending'", (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            trx = dict(row)
            cursor.execute(
                "UPDATE transactions SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ? WHERE id = ?",
                (reviewer_id, transaction_id)
            )
            # Add balance
            field = "balance_bdt" if trx["currency"].upper() == "BDT" else "balance_usd"
            cursor.execute(f"UPDATE users SET {field} = {field} + ? WHERE user_id = ?", (trx["amount"], trx["user_id"]))
            conn.commit()
            trx["status"] = "approved"
            trx["reviewed_by"] = reviewer_id
            return trx

    def reject_deposit(self, transaction_id: int, reviewer_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ? AND status = 'pending'", (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            trx = dict(row)
            cursor.execute(
                "UPDATE transactions SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ? WHERE id = ?",
                (reviewer_id, transaction_id)
            )
            conn.commit()
            trx["status"] = "rejected"
            trx["reviewed_by"] = reviewer_id
            return trx

    approve_transaction = approve_deposit
    reject_transaction = reject_deposit

    def get_pending_transactions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE status = 'pending' ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- ORDER METHODS ---
    def record_order(self, user_id: int, product_id: int, product_title: str, product_type: str,
                     amount_paid: float, currency: str, delivery_content: str,
                     is_reseller_order: int = 0, savings_bdt: float = 0.0, savings_usd: float = 0.0,
                     access_tier: str = "default") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO orders (user_id, product_id, product_title, product_type, amount_paid, currency, delivery_content, is_reseller_order, savings_bdt, savings_usd, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, product_id, product_title, product_type, amount_paid, currency, delivery_content, is_reseller_order, savings_bdt, savings_usd, access_tier))
            conn.commit()
            return cursor.lastrowid

    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # --- RESELLER SYSTEM METHODS ---
    def set_reseller_status(self, user_id: int, is_reseller: int = 1, code: Optional[str] = None, tier: int = 1) -> bool:
        if not code and is_reseller:
            code = f"RS-{user_id % 10000:04d}"
        can_acc = 1 if (is_reseller >= 1 and tier >= 2) else 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_reseller = ?, reseller_code = ?, reseller_tier = ?, can_sell_channel = 1, can_sell_account = ? WHERE user_id = ?",
                (is_reseller, code, tier, can_acc, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_user_permissions(self, user_id: int) -> Dict[str, Any]:
        user = self.get_user(user_id) or {}
        return {
            "is_reseller": int(user.get("is_reseller", 0) or 0),
            "reseller_tier": int(user.get("reseller_tier", 1) or 1),
            "can_sell_channel": bool(user.get("can_sell_channel", 1) if user.get("can_sell_channel") is not None else 1),
            "can_sell_account": bool(user.get("can_sell_account", 0) if user.get("can_sell_account") is not None else 0),
        }

    def set_user_permission(self, user_id: int, perm_key: str, value: int) -> bool:
        if perm_key not in ["can_sell_channel", "can_sell_account", "reseller_tier", "is_reseller"]:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {perm_key} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_user_permission(self, user_id: int, perm_key: str) -> bool:
        if perm_key not in ["can_sell_channel", "can_sell_account"]:
            return False
        user = self.get_user(user_id) or {}
        current = int(user.get(perm_key, 1 if perm_key == "can_sell_channel" else 0) or 0)
        new_val = 0 if current else 1
        return self.set_user_permission(user_id, perm_key, new_val)

    def set_reseller_tier(self, user_id: int, tier: int) -> bool:
        can_acc = 1 if tier >= 2 else 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET reseller_tier = ?, can_sell_account = ? WHERE user_id = ?", (tier, can_acc, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def is_elite_reseller(self, user_id: int) -> bool:
        user = self.get_user(user_id) or {}
        is_res = user.get("is_reseller", 0) >= 1
        tier = user.get("reseller_tier", 1) or 1
        can_acc = user.get("can_sell_account", 0) or 0
        return bool(is_res and tier >= 2 and can_acc == 1)

    def get_all_resellers(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT u.*, 
                   COUNT(o.id) as reseller_orders_count,
                   COALESCE(SUM(o.amount_paid), 0) as reseller_total_spent
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id AND o.is_reseller_order = 1
            WHERE u.is_reseller >= 1
            GROUP BY u.user_id
            ORDER BY u.joined_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_reseller_stats(self, user_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT COUNT(*) as orders_count,
                   COALESCE(SUM(amount_paid), 0) as total_spent,
                   COALESCE(SUM(savings_bdt), 0) as total_savings_bdt,
                   COALESCE(SUM(savings_usd), 0) as total_savings_usd
            FROM orders
            WHERE user_id = ? AND is_reseller_order = 1
            """, (user_id,))
            row = cursor.fetchone()
            d = dict(row) if row else {
                "orders_count": 0, "total_spent": 0, "total_savings_bdt": 0, "total_savings_usd": 0
            }
            d["total_orders"] = d["orders_count"]
            return d

    def get_pending_reseller_applications(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT ra.*, u.username, u.first_name, u.balance_bdt 
            FROM reseller_applications ra
            JOIN users u ON ra.user_id = u.user_id
            WHERE ra.status = 'pending'
            ORDER BY ra.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]


    def update_product_reseller_pricing(self, product_id: int, reseller_bdt: float, reseller_usd: float) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET reseller_price_bdt = ?, reseller_price_usd = ? WHERE id = ?", (reseller_bdt, reseller_usd, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_active_products(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT p.*, c.name as category_name, c.icon as category_icon
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            ORDER BY p.category_id ASC, p.id ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_all_products(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT p.*, c.name as category_name, c.icon as category_icon
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # --- STATS METHODS ---
    def get_bot_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) as total_resellers FROM users WHERE is_reseller >= 1")
            total_resellers = cursor.fetchone()["total_resellers"]

            cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
            total_orders = cursor.fetchone()["total_orders"]

            cursor.execute("SELECT SUM(amount) as total_deposit_bdt FROM transactions WHERE status = 'approved' AND currency = 'BDT'")
            row = cursor.fetchone()
            total_deposit_bdt = row["total_deposit_bdt"] or 0.0

            cursor.execute("SELECT SUM(amount) as total_deposit_usd FROM transactions WHERE status = 'approved' AND currency = 'USD'")
            row = cursor.fetchone()
            total_deposit_usd = row["total_deposit_usd"] or 0.0

            cursor.execute("SELECT COUNT(*) as pending_deposits FROM transactions WHERE status = 'pending'")
            pending_deposits = cursor.fetchone()["pending_deposits"]

            cursor.execute("SELECT COUNT(*) as pending_reseller_apps FROM reseller_applications WHERE status = 'pending'")
            pending_reseller_apps = cursor.fetchone()["pending_reseller_apps"]

            return {
                "total_users": total_users,
                "total_resellers": total_resellers,
                "total_orders": total_orders,
                "total_deposit_bdt": total_deposit_bdt,
                "total_deposit_usd": total_deposit_usd,
                "pending_deposits": pending_deposits,
                "pending_reseller_apps": pending_reseller_apps
            }

    # --- DYNAMIC SETTINGS METHODS ---
    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
            return True

    # --- COUPONS / VOUCHERS METHODS ---
    def create_coupon(self, code: str, discount_bdt: float = 0.0, discount_percent: float = 0.0, max_uses: int = 100) -> int:
        clean_code = code.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO coupons (code, discount_bdt, discount_percent, max_uses, used_count, is_active)
            VALUES (?, ?, ?, ?, 0, 1)
            """, (clean_code, discount_bdt, discount_percent, max_uses))
            conn.commit()
            return cursor.lastrowid

    def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        clean_code = code.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (clean_code,))
            row = cursor.fetchone()
            if not row:
                return None
            c = dict(row)
            if c["used_count"] >= c["max_uses"]:
                return None
            return c

    def use_coupon(self, code: str) -> bool:
        clean_code = code.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = ? AND is_active = 1 AND used_count < max_uses", (clean_code,))
            conn.commit()
            return cursor.rowcount > 0

    def list_coupons(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_coupon(self, coupon_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE coupons SET is_active = 0 WHERE id = ?", (coupon_id,))
            conn.commit()
            return cursor.rowcount > 0

    def hard_delete_coupon(self, coupon_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_coupon(self, coupon_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE coupons SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (coupon_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- PRODUCT EDITING METHODS ---
    def update_product(self, product_id: int, title: str, description: str,
                       price_bdt: float, price_usd: float,
                       reseller_price_bdt: float, reseller_price_usd: float,
                       is_active: int = 1) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE products
            SET title = ?, description = ?, price_bdt = ?, price_usd = ?,
                reseller_price_bdt = ?, reseller_price_usd = ?, is_active = ?
            WHERE id = ?
            """, (title, description, price_bdt, price_usd, reseller_price_bdt, reseller_price_usd, is_active, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_category(self, product_id: int, category_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET category_id = ? WHERE id = ?", (category_id, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_type(self, product_id: int, product_type: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET product_type = ? WHERE id = ?", (product_type, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_target(self, product_id: int, channel_id: Optional[str] = None, drive_link: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET channel_id = ?, drive_link = ? WHERE id = ?", (channel_id, drive_link, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_channel(self, product_id: int, channel_id: Optional[str], channel_title: Optional[str] = None, channel_verified: int = 1) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET channel_id = ?, channel_title = ?, channel_verified = ? WHERE id = ?",
                (channel_id, channel_title, channel_verified, product_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_product_drive_link(self, product_id: int, drive_link: Optional[str]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET drive_link = ? WHERE id = ?", (drive_link, product_id))
            conn.commit()
            return cursor.rowcount > 0


    def update_product_photo(self, product_id: int, photo_file_id: Optional[str]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET photo_file_id = ? WHERE id = ?", (photo_file_id, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def remove_product_photo(self, product_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET photo_file_id = NULL WHERE id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_sales_page(self, product_id: int, sales_page_url: Optional[str]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET sales_page_url = ? WHERE id = ?", (sales_page_url, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_product_tier_pricing(self, product_id: int, price_channel_bdt: float, price_channel_usd: float,
                                    price_account_bdt: float, price_account_usd: float,
                                    reseller_price_channel_bdt: float = 0.0, reseller_price_account_bdt: float = 0.0) -> bool:
        if reseller_price_channel_bdt <= 0 and price_channel_bdt > 0:
            reseller_price_channel_bdt = round(price_channel_bdt * 0.70, 2)
        if reseller_price_account_bdt <= 0 and price_account_bdt > 0:
            reseller_price_account_bdt = round(price_account_bdt * 0.70, 2)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE products 
            SET price_channel_bdt = ?, price_channel_usd = ?,
                price_account_bdt = ?, price_account_usd = ?,
                reseller_price_channel_bdt = ?, reseller_price_account_bdt = ?
            WHERE id = ?
            """, (price_channel_bdt, price_channel_usd, price_account_bdt, price_account_usd,
                  reseller_price_channel_bdt, reseller_price_account_bdt, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_product_permanent(self, product_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_items WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- ADVANCED RESELLER QUOTA & LEADERBOARD METHODS ---
    def submit_reseller_application(self, user_id: int, info: str, balance: float = 0.0, requested_tier: int = 1) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO reseller_applications (user_id, info, balance_at_apply, requested_tier, status)
            VALUES (?, ?, ?, ?, 'pending')
            """, (user_id, info, balance, requested_tier))
            conn.commit()
            return cursor.lastrowid

    def approve_reseller_application(self, app_id: int, tier: int = 1) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM reseller_applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            if not row:
                return None
            user_id = row["user_id"]
            
            cursor.execute("SELECT balance_bdt, username, first_name FROM users WHERE user_id = ?", (user_id,))
            u = cursor.fetchone()
            if not u:
                return None
                
            fee = float(self.get_setting("reseller_activation_fee", "500.0"))
            curr_bal = u["balance_bdt"] or 0.0
            new_bal = max(0.0, curr_bal - fee)
            code = f"RS-{user_id % 10000:04d}"
            can_acc = 1 if tier >= 2 else 0
            
            cursor.execute("UPDATE reseller_applications SET status = 'approved' WHERE id = ?", (app_id,))
            cursor.execute("""
            UPDATE users 
            SET is_reseller = 1, reseller_code = ?, reseller_tier = ?, can_sell_channel = 1, can_sell_account = ?,
                reseller_quota_start = CURRENT_TIMESTAMP, 
                reseller_monthly_sales = 0, reseller_deactivated_permanent = 0, balance_bdt = ?
            WHERE user_id = ?
            """, (code, tier, can_acc, new_bal, user_id))
            
            # Record fee deduction in orders ledger
            cursor.execute("""
            INSERT INTO orders (user_id, product_id, product_title, product_type, amount_paid, currency, delivery_content, status)
            VALUES (?, 0, '👑 VIP Reseller Verified Activation Fee (নন-রিফান্ডেবল পার্টনারশিপ ফি)', 'reseller_fee', ?, 'BDT', 'Verified VIP Partner Fee successfully credited to platform.', 'completed')
            """, (user_id, fee))
            
            conn.commit()
            return {
                "user_id": user_id,
                "reseller_code": code,
                "fee_deducted": fee,
                "remaining_balance": new_bal,
                "reseller_tier": tier,
                "can_sell_account": bool(can_acc)
            }

    def reject_reseller_application(self, app_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM reseller_applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            if not row:
                return None
            user_id = row["user_id"]
            cursor.execute("UPDATE reseller_applications SET status = 'rejected' WHERE id = ?", (app_id,))
            conn.commit()
            return user_id

    def increment_reseller_sale(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users 
            SET reseller_monthly_sales = reseller_monthly_sales + 1
            WHERE user_id = ?
            """, (user_id,))
            conn.commit()

    def get_reseller_quota_info(self, user_id: int) -> Dict[str, Any]:
        quota_target = int(self.get_setting("reseller_monthly_quota", "5"))
        quota_days = int(self.get_setting("reseller_quota_days", "30"))
        user = self.get_user(user_id)
        if not user:
            return {"active": False, "sales": 0, "target": quota_target, "days_left": 0, "is_permanent_banned": False}

        is_perm = user.get("reseller_deactivated_permanent", 0) == 1 or user.get("is_reseller", 0) == -1
        sales = user.get("reseller_monthly_sales", 0)

        # Calculate days left
        days_left = quota_days
        quota_start = user.get("reseller_quota_start")
        if quota_start:
            try:
                start_dt = datetime.strptime(quota_start[:19], "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start_dt).days
                days_left = max(0, quota_days - elapsed)
            except Exception:
                pass

        return {
            "active": user.get("is_reseller", 0) == 1,
            "sales": sales,
            "target": quota_target,
            "days_left": days_left,
            "is_permanent_banned": is_perm
        }

    def enforce_reseller_quotas(self) -> List[int]:
        """
        Scans all resellers. If quota_days elapsed and sales < quota,
        permanently deactivates their reseller status (is_reseller = -1).
        If quota met, resets cycle for next round of quota_days.
        Returns list of deactivated user_ids.
        """
        quota_target = int(self.get_setting("reseller_monthly_quota", "5"))
        quota_days = int(self.get_setting("reseller_quota_days", "30"))
        deactivated = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, reseller_quota_start, reseller_monthly_sales FROM users WHERE is_reseller = 1")
            resellers = cursor.fetchall()
            now = datetime.now()

            for r in resellers:
                uid = r["user_id"]
                q_start = r["reseller_quota_start"]
                sales = r["reseller_monthly_sales"] or 0
                if not q_start:
                    continue
                try:
                    start_dt = datetime.strptime(q_start[:19], "%Y-%m-%d %H:%M:%S")
                    if (now - start_dt).days >= quota_days:
                        if sales < quota_target:
                            # PERMANENT DEACTIVATION!
                            cursor.execute("""
                            UPDATE users 
                            SET is_reseller = -1, reseller_deactivated_permanent = 1
                            WHERE user_id = ?
                            """, (uid,))
                            deactivated.append(uid)
                        else:
                            # Renew cycle
                            cursor.execute("""
                            UPDATE users 
                            SET reseller_quota_start = CURRENT_TIMESTAMP, reseller_monthly_sales = 0
                            WHERE user_id = ?
                            """, (uid,))
                except Exception:
                    pass
            conn.commit()
        return deactivated

    def get_reseller_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT user_id, username, first_name, reseller_code, reseller_monthly_sales
            FROM users
            WHERE is_reseller = 1
            ORDER BY reseller_monthly_sales DESC, total_spent_bdt DESC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_reseller_ids(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_reseller = 1 AND is_banned = 0")
            return [row["user_id"] for row in cursor.fetchall()]

    def get_all_user_ids(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            return [row["user_id"] for row in cursor.fetchall()]

    def get_active_users_for_broadcast(self) -> List[Dict[str, Any]]:
        """Returns list of active non-banned users with their preferred language for smart multilingual broadcast."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, COALESCE(language, 'bn') as language FROM users WHERE is_banned = 0")
            return [dict(row) for row in cursor.fetchall()]

    def find_user(self, query: Optional[str]) -> Optional[Dict[str, Any]]:
        """Smart finder by User ID, @username, or Reseller Code."""
        if not query:
            return None
        q = str(query).strip()
        if not q:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. By Telegram ID
            if q.isdigit():
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (int(q),))
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # 2. By Username
            clean_username = q.lstrip("@").lower()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean_username,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            # 3. By Reseller Code variations (RS-1001, RS1001)
            code_candidates = [q.upper()]
            if q.upper().startswith("RS") and "-" not in q:
                code_candidates.append(f"RS-{q[2:]}")
            for c in code_candidates:
                cursor.execute("SELECT * FROM users WHERE UPPER(reseller_code) = ?", (c,))
                row = cursor.fetchone()
                if row:
                    return dict(row)

            return None

    def verify_reseller(self, query: Optional[str]) -> Optional[Dict[str, Any]]:
        """Dedicated reseller verification finder."""
        return self.find_user(query)

    def set_user_referrer(self, user_id: int, referrer_id: int) -> bool:
        """Sets the referrer for a user if not already referred and not self."""
        res = self.process_referral_join(user_id, referrer_id)
        return res is not None

    def process_referral_join(self, new_user_id: int, referrer_id: int, course_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Processes a new user joining through a referral link.
        - Validates fraud/self-referral/duplicate checks.
        - Credits Tier-1 direct referral point (1 pt) and referral count.
        - Records course-specific referral if course_id is provided.
        - Credits Tier-2 sub-referral commission (50%) to referrer's upline if present.
        - Credits welcome starter bonus to new user.
        - Checks & unlocks viral milestones (10, 25, 50).
        """
        if new_user_id == referrer_id:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if new user is already referred
            cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (new_user_id,))
            u_row = cursor.fetchone()
            if not u_row or u_row["referred_by"] is not None:
                return None

            cursor.execute("SELECT id FROM referral_logs WHERE referred_id = ?", (new_user_id,))
            if cursor.fetchone():
                return None

            # Verify referrer exists and is not banned
            cursor.execute("SELECT user_id, referred_by, referral_count_t1, referral_milestone_tier, balance_bdt, referral_points FROM users WHERE user_id = ? AND is_banned = 0", (referrer_id,))
            ref_row = cursor.fetchone()
            if not ref_row:
                return None

            # Settings
            t1_bonus = float(self.get_setting("referral_t1_bonus", "10.0"))
            t2_pct = float(self.get_setting("referral_t2_percent", "50.0"))
            welcome_bonus = float(self.get_setting("referral_welcome_bonus", "5.0"))

            # 1. Update new user with referrer & welcome starter bonus
            cursor.execute("""
            UPDATE users 
            SET referred_by = ?, balance_bdt = balance_bdt + ?
            WHERE user_id = ?
            """, (referrer_id, welcome_bonus, new_user_id))

            # 2. Credit Tier-1 Referrer: 1 spendable referral point + 1 total count
            cursor.execute("""
            UPDATE users 
            SET referral_count_t1 = referral_count_t1 + 1,
                referral_points = referral_points + 1
            WHERE user_id = ?
            """, (referrer_id,))

            cursor.execute("""
            INSERT INTO referral_logs (referrer_id, referred_id, tier, bonus_amount)
            VALUES (?, ?, 1, ?)
            """, (referrer_id, new_user_id, t1_bonus))

            # Track course if joined through specific course link
            if course_id:
                try:
                    cursor.execute("""
                    INSERT INTO referral_course_tracking (referrer_id, course_id, referred_user_id)
                    VALUES (?, ?, ?)
                    """, (referrer_id, course_id, new_user_id))
                except Exception:
                    pass

            cursor.execute("SELECT balance_bdt, referral_count_t1, referral_points FROM users WHERE user_id = ?", (referrer_id,))
            updated_ref = cursor.fetchone()
            t1_new_bal = updated_ref["balance_bdt"]
            new_t1_count = updated_ref["referral_count_t1"]
            new_t1_points = updated_ref["referral_points"]

            # 3. Check Dynamic Milestones for T1 Referrer
            milestone_info = None
            curr_tier = ref_row["referral_milestone_tier"] or 0
            bronze_tgt = int(self.get_setting("ref_milestone_bronze_target", "10"))
            bronze_bns = float(self.get_setting("ref_milestone_bronze_bonus", "25.0"))
            silver_tgt = int(self.get_setting("ref_milestone_silver_target", "25"))
            silver_bns = float(self.get_setting("ref_milestone_silver_bonus", "75.0"))
            gold_tgt = int(self.get_setting("ref_milestone_gold_target", "50"))
            gold_bns = float(self.get_setting("ref_milestone_gold_bonus", "200.0"))

            if new_t1_count >= gold_tgt and curr_tier < 3:
                # Gold Ambassador: Dynamic Bonus + Reseller status
                cursor.execute("""
                UPDATE users 
                SET balance_bdt = balance_bdt + ?, 
                    referral_earnings_bdt = referral_earnings_bdt + ?,
                    referral_milestone_tier = 3,
                    is_reseller = CASE WHEN is_reseller < 1 THEN 1 ELSE is_reseller END
                WHERE user_id = ?
                """, (gold_bns, gold_bns, referrer_id))
                milestone_info = {"tier": 3, "title": "🥇 Gold Ambassador", "bonus": gold_bns, "extra": "ফ্রি রিসেলার স্ট্যাটাস"}
            elif new_t1_count >= silver_tgt and curr_tier < 2:
                # Silver VIP: Dynamic Bonus
                cursor.execute("""
                UPDATE users 
                SET balance_bdt = balance_bdt + ?, 
                    referral_earnings_bdt = referral_earnings_bdt + ?,
                    referral_milestone_tier = 2
                WHERE user_id = ?
                """, (silver_bns, silver_bns, referrer_id))
                milestone_info = {"tier": 2, "title": "🥈 Silver VIP", "bonus": silver_bns, "extra": "৫% লাইফটাইম কোর্স ডিসকাউন্ট"}
            elif new_t1_count >= bronze_tgt and curr_tier < 1:
                # Bronze Star: Dynamic Bonus
                cursor.execute("""
                UPDATE users 
                SET balance_bdt = balance_bdt + ?, 
                    referral_earnings_bdt = referral_earnings_bdt + ?,
                    referral_milestone_tier = 1
                WHERE user_id = ?
                """, (bronze_bns, bronze_bns, referrer_id))
                milestone_info = {"tier": 1, "title": "🥉 Bronze Star", "bonus": bronze_bns, "extra": "মাইলস্টোন বাউন্টি"}

            # 4. Check Tier-2 Sub-referral
            t2_referrer_id = ref_row["referred_by"]
            t2_bonus = 0.0
            t2_new_bal = 0.0
            if t2_referrer_id and t2_referrer_id != new_user_id and t2_referrer_id != referrer_id:
                t2_bonus = round(t1_bonus * (t2_pct / 100.0), 2)
                if t2_bonus > 0:
                    cursor.execute("""
                    UPDATE users 
                    SET balance_bdt = balance_bdt + ?, 
                        referral_earnings_bdt = referral_earnings_bdt + ?,
                        referral_count_t2 = referral_count_t2 + 1
                    WHERE user_id = ?
                    """, (t2_bonus, t2_bonus, t2_referrer_id))

                    cursor.execute("""
                    INSERT INTO referral_logs (referrer_id, referred_id, tier, bonus_amount)
                    VALUES (?, ?, 2, ?)
                    """, (t2_referrer_id, new_user_id, t2_bonus))

                    cursor.execute("SELECT balance_bdt FROM users WHERE user_id = ?", (t2_referrer_id,))
                    t2_res = cursor.fetchone()
                    if t2_res:
                        t2_new_bal = t2_res["balance_bdt"]

            conn.commit()

            return {
                "t1_referrer_id": referrer_id,
                "t1_bonus": t1_bonus,
                "t1_new_balance": t1_new_bal,
                "t1_count": new_t1_count,
                "t1_points": new_t1_points,
                "course_id": course_id,
                "t2_referrer_id": t2_referrer_id if t2_bonus > 0 else None,
                "t2_bonus": t2_bonus,
                "t2_new_balance": t2_new_bal,
                "welcome_bonus": welcome_bonus,
                "milestone": milestone_info
            }

    def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Telemetry details for user's referral hub."""
        user = self.get_user(user_id)
        if not user:
            return {}
            
        t1_count = user.get("referral_count_t1") or 0
        t2_count = user.get("referral_count_t2") or 0
        total_earned = user.get("referral_earnings_bdt") or 0.0
        balance_bdt = user.get("balance_bdt") or 0.0
        milestone_tier = user.get("referral_milestone_tier") or 0
        
        bronze_tgt = int(self.get_setting("ref_milestone_bronze_target", "10"))
        bronze_bns = float(self.get_setting("ref_milestone_bronze_bonus", "25.0"))
        silver_tgt = int(self.get_setting("ref_milestone_silver_target", "25"))
        silver_bns = float(self.get_setting("ref_milestone_silver_bonus", "75.0"))
        gold_tgt = int(self.get_setting("ref_milestone_gold_target", "50"))
        gold_bns = float(self.get_setting("ref_milestone_gold_bonus", "200.0"))

        milestones = [
            {"tier": 1, "target": bronze_tgt, "title": "🥉 Bronze Star", "bonus": bronze_bns},
            {"tier": 2, "target": silver_tgt, "title": "🥈 Silver VIP", "bonus": silver_bns},
            {"tier": 3, "target": gold_tgt, "title": "🥇 Gold Ambassador", "bonus": gold_bns}
        ]
        
        next_m = None
        for m in milestones:
            if t1_count < m["target"]:
                next_m = m
                break
                
        if not next_m:
            next_m = {"target": gold_tgt * 2, "title": "💎 Diamond Elite", "bonus": gold_bns * 2}
            
        progress_pct = min(100, int((t1_count / next_m["target"]) * 100)) if next_m["target"] > 0 else 100
        bars = int(progress_pct / 10)
        filled_bars = "▰" * bars
        empty_bars = "▱" * (10 - bars)
        progress_bar = f"{filled_bars}{empty_bars} {progress_pct}%"
        
        t1_bonus = float(self.get_setting("referral_t1_bonus", "10.0"))
        t2_pct = float(self.get_setting("referral_t2_percent", "50.0"))
        welcome_bonus = float(self.get_setting("referral_welcome_bonus", "5.0"))
        
        return {
            "user_id": user_id,
            "t1_count": t1_count,
            "t2_count": t2_count,
            "total_count": t1_count + t2_count,
            "total_earned": total_earned,
            "balance_bdt": balance_bdt,
            "milestone_tier": milestone_tier,
            "next_target": next_m["target"],
            "next_title": next_m["title"],
            "next_bonus": next_m["bonus"],
            "needed": max(0, next_m["target"] - t1_count),
            "progress_bar": progress_bar,
            "t1_bonus": t1_bonus,
            "t2_pct": t2_pct,
            "welcome_bonus": welcome_bonus,
            "bronze_target": bronze_tgt,
            "bronze_bonus": bronze_bns,
            "silver_target": silver_tgt,
            "silver_bonus": silver_bns,
            "gold_target": gold_tgt,
            "gold_bonus": gold_bns
        }

    def get_referral_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Top referrers leaderboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT user_id, first_name, username, referral_count_t1, referral_count_t2, referral_earnings_bdt
            FROM users 
            WHERE referral_count_t1 > 0
            ORDER BY referral_count_t1 DESC, referral_earnings_bdt DESC
            LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_user_referral_summary(self, user_id: int) -> Dict[str, Any]:
        """Comprehensive referral overview for My Profile and Hub."""
        user = self.get_user(user_id)
        if not user:
            return {
                "total_referrals": 0, "t1_count": 0, "t2_count": 0, "referral_points": 0, "course_refs_count": 0,
                "t1_bonus": 10.0, "points_value_bdt": 0.0, "total_converted_bdt": 0.0,
                "balance_bdt": 0.0, "balance_usd": 0.0
            }
        t1_count = user.get("referral_count_t1", 0) or 0
        t2_count = user.get("referral_count_t2", 0) or 0
        points = user.get("referral_points", 0) or 0
        t1_bonus = float(self.get_setting("referral_t1_bonus", "10.0"))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Course-specific referrals count
            cursor.execute("SELECT COUNT(*) as c FROM referral_course_tracking WHERE referrer_id = ?", (user_id,))
            c_row = cursor.fetchone()
            course_refs_count = c_row["c"] if c_row else 0

            # Total converted BDT from points
            cursor.execute("""
            SELECT SUM(amount_out) as total_conv 
            FROM referral_conversions 
            WHERE user_id = ? AND from_type = 'points' AND to_type = 'bdt'
            """, (user_id,))
            conv_row = cursor.fetchone()
            total_converted_bdt = float(conv_row["total_conv"] or 0.0) if conv_row else 0.0

        return {
            "total_referrals": t1_count + t2_count,
            "t1_count": t1_count,
            "t2_count": t2_count,
            "referral_points": points,
            "available_points": points,
            "points_value_bdt": points * t1_bonus,
            "bdt_value": points * t1_bonus,
            "course_refs_count": course_refs_count,
            "course_referrals": course_refs_count,
            "t1_bonus": t1_bonus,
            "total_converted_bdt": total_converted_bdt,
            "converted_bdt_total": total_converted_bdt,
            "balance_bdt": user.get("balance_bdt", 0.0) or 0.0,
            "balance_usd": user.get("balance_usd", 0.0) or 0.0
        }

    def get_course_referral_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns course breakdown of referrals brought by user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT rct.course_id, p.title as course_title, COUNT(rct.id) as ref_count
            FROM referral_course_tracking rct
            LEFT JOIN products p ON rct.course_id = p.id
            WHERE rct.referrer_id = ?
            GROUP BY rct.course_id
            ORDER BY ref_count DESC
            """, (user_id,))
            rows = cursor.fetchall()
            res = []
            for r in rows:
                d = dict(r)
                d["referral_count"] = d.get("ref_count", 0)
                res.append(d)
            return res

    def convert_referral_points_to_bdt(self, user_id: int, points: int) -> Dict[str, Any]:
        """Converts available referral points into BDT wallet balance."""
        if points <= 0:
            return {"success": False, "message": "পয়েন্টের সংখ্যা অন্তত ১ হতে হবে।"}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT referral_points, balance_bdt FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "ইউজার পাওয়া যায়নি।"}
            
            avail_pts = user["referral_points"] or 0
            if avail_pts < points:
                return {"success": False, "message": f"পর্যাপ্ত পয়েন্ট নেই! আপনার আছে {avail_pts} টি পয়েন্ট।"}

            t1_bonus = float(self.get_setting("referral_t1_bonus", "10.0"))
            bdt_gained = points * t1_bonus

            cursor.execute("""
            UPDATE users 
            SET referral_points = referral_points - ?,
                balance_bdt = balance_bdt + ?,
                referral_earnings_bdt = referral_earnings_bdt + ?
            WHERE user_id = ?
            """, (points, bdt_gained, bdt_gained, user_id))

            cursor.execute("""
            INSERT INTO referral_conversions (user_id, from_type, to_type, amount_in, amount_out, rate_used)
            VALUES (?, 'points', 'bdt', ?, ?, ?)
            """, (user_id, points, bdt_gained, t1_bonus))

            conn.commit()

            cursor.execute("SELECT referral_points, balance_bdt FROM users WHERE user_id = ?", (user_id,))
            updated = cursor.fetchone()
            return {
                "success": True,
                "points_converted": points,
                "bdt_gained": bdt_gained,
                "bdt_credited": bdt_gained,
                "rate": t1_bonus,
                "rate_used": t1_bonus,
                "remaining_points": updated["referral_points"],
                "new_balance_bdt": updated["balance_bdt"]
            }

    def convert_bdt_to_usd(self, user_id: int, bdt_amount: float) -> Dict[str, Any]:
        """Converts BDT balance into USD balance at dynamic live rate."""
        if bdt_amount <= 0:
            return {"success": False, "message": "টাকার পরিমাণ ০ এর বেশি হতে হবে।"}

        from config import get_live_usd_rate
        live_rate = get_live_usd_rate()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance_bdt, balance_usd FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "ইউজার পাওয়া যায়নি।"}

            avail_bdt = user["balance_bdt"] or 0.0
            if avail_bdt < bdt_amount:
                return {"success": False, "message": f"পর্যাপ্ত BDT ব্যালেন্স নেই! আপনার ব্যালেন্স: ৳{avail_bdt:.2f} BDT"}

            usd_gained = round(bdt_amount / live_rate, 2)
            if usd_gained <= 0:
                return {"success": False, "message": f"কনভার্সনের পর অন্তত $0.01 USD হতে হবে।"}

            cursor.execute("""
            UPDATE users 
            SET balance_bdt = balance_bdt - ?,
                balance_usd = balance_usd + ?
            WHERE user_id = ?
            """, (bdt_amount, usd_gained, user_id))

            cursor.execute("""
            INSERT INTO referral_conversions (user_id, from_type, to_type, amount_in, amount_out, rate_used)
            VALUES (?, 'bdt', 'usd', ?, ?, ?)
            """, (user_id, bdt_amount, usd_gained, live_rate))

            conn.commit()

            cursor.execute("SELECT balance_bdt, balance_usd FROM users WHERE user_id = ?", (user_id,))
            updated = cursor.fetchone()
            return {
                "success": True,
                "bdt_spent": bdt_amount,
                "bdt_deducted": bdt_amount,
                "usd_gained": usd_gained,
                "usd_credited": usd_gained,
                "rate": live_rate,
                "rate_used": live_rate,
                "new_balance_bdt": updated["balance_bdt"],
                "new_balance_usd": updated["balance_usd"]
            }

    def get_user_conversion_history(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns log of all conversions made by user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM referral_conversions 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT ?
            """, (user_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def deduct_referral_points(self, user_id: int, points: int) -> bool:
        """Deducts referral points when paying for courses directly with referrals."""
        if points <= 0:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users 
            SET referral_points = referral_points - ?
            WHERE user_id = ? AND referral_points >= ?
            """, (points, user_id, points))
            conn.commit()
            return cursor.rowcount > 0

    def get_referral_bot_telemetry(self) -> Dict[str, Any]:
        """Platform-wide referral telemetry for admin center."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_joins, COALESCE(SUM(bonus_amount), 0) as total_payout FROM referral_logs")
            log_stats = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as total_referrers FROM users WHERE referral_count_t1 > 0")
            ref_count = cursor.fetchone()
            
            cursor.execute("SELECT user_id, first_name, username, referral_count_t1 FROM users ORDER BY referral_count_t1 DESC LIMIT 1")
            top_ref = cursor.fetchone()
            
            return {
                "total_joins": log_stats["total_joins"] if log_stats else 0,
                "total_payout": log_stats["total_payout"] if log_stats else 0.0,
                "total_referrers": ref_count["total_referrers"] if ref_count else 0,
                "top_referrer": dict(top_ref) if top_ref and top_ref["referral_count_t1"] > 0 else None,
                "t1_bonus": float(self.get_setting("referral_t1_bonus", "10.0")),
                "t2_pct": float(self.get_setting("referral_t2_percent", "50.0")),
                "welcome_bonus": float(self.get_setting("referral_welcome_bonus", "5.0"))
            }

    def credit_referral_reward(self, user_id: int, order_amount_bdt: float) -> Optional[Dict[str, Any]]:
        """Credits referral commission to referrer if applicable."""
        user = self.get_user(user_id)
        if not user or not user.get("referred_by"):
            return None
        referrer_id = user["referred_by"]
        bonus_pct = float(self.get_setting("referral_bonus_percent", "5"))
        bonus_amount = round(order_amount_bdt * (bonus_pct / 100.0), 2)
        if bonus_amount <= 0:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users 
            SET balance_bdt = balance_bdt + ?, referral_earnings_bdt = referral_earnings_bdt + ?
            WHERE user_id = ?
            """, (bonus_amount, bonus_amount, referrer_id))
            conn.commit()

        return {
            "referrer_id": referrer_id,
            "buyer_id": user_id,
            "bonus_amount": bonus_amount,
            "buyer_name": user.get("first_name", "User")
        }

    def get_extended_bot_stats(self) -> Dict[str, Any]:
        """Deep analytics telemetry for smart admin center."""
        base = self.get_bot_stats()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Deactivated resellers
            cursor.execute("SELECT COUNT(*) as deact FROM users WHERE is_reseller = -1 OR reseller_deactivated_permanent = 1")
            deactivated_resellers = cursor.fetchone()["deact"]

            # Today's orders
            cursor.execute("SELECT COUNT(*) as today_cnt, COALESCE(SUM(amount_paid), 0) as today_rev FROM orders WHERE date(created_at) = date('now')")
            today_row = cursor.fetchone()
            today_orders = today_row["today_cnt"]
            today_revenue = today_row["today_rev"]

            # Active catalog products
            cursor.execute("SELECT COUNT(*) as active_p FROM products WHERE is_active = 1")
            active_products = cursor.fetchone()["active_p"]

            base["deactivated_resellers"] = deactivated_resellers
            base["today_orders"] = today_orders
            base["today_sales_bdt"] = today_revenue
            base["active_products"] = active_products
            return base

    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT o.*, u.username, u.first_name 
            FROM orders o 
            LEFT JOIN users u ON o.user_id = u.user_id 
            ORDER BY o.id DESC 
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_analytics_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Deep analytics dossier for a specific user: earnings breakdown, deposit history, and order/queue stats."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return None
            res = dict(user)
            
            # 1. Deposit Statistics ("deposit koto")
            cursor.execute("""
            SELECT 
                COUNT(*) as count_approved,
                COALESCE(SUM(CASE WHEN currency = 'BDT' THEN amount ELSE 0 END), 0) as approved_bdt,
                COALESCE(SUM(CASE WHEN currency = 'USD' THEN amount ELSE 0 END), 0) as approved_usd
            FROM transactions 
            WHERE user_id = ? AND status = 'approved'
            """, (user_id,))
            dep_row = cursor.fetchone()
            res["deposits_approved_count"] = dep_row["count_approved"] if dep_row else 0
            res["deposits_approved_bdt"] = dep_row["approved_bdt"] if dep_row else 0.0
            res["deposits_approved_usd"] = dep_row["approved_usd"] if dep_row else 0.0
            
            cursor.execute("SELECT COUNT(*) as pending_dep FROM transactions WHERE user_id = ? AND status = 'pending'", (user_id,))
            pending_row = cursor.fetchone()
            res["deposits_pending_count"] = pending_row["pending_dep"] if pending_row else 0
            
            # Last approved deposit
            cursor.execute("SELECT method, amount, currency, trx_id, created_at FROM transactions WHERE user_id = ? AND status = 'approved' ORDER BY id DESC LIMIT 1", (user_id,))
            last_dep = cursor.fetchone()
            res["last_deposit"] = dict(last_dep) if last_dep else None
            
            # 2. Earnings Analysis ("kivabe earn korce")
            referrer_info = None
            if res.get("referred_by"):
                cursor.execute("SELECT user_id, first_name, username FROM users WHERE user_id = ?", (res["referred_by"],))
                ref_row = cursor.fetchone()
                if ref_row:
                    referrer_info = dict(ref_row)
            res["referrer_info"] = referrer_info
            
            cursor.execute("""
            SELECT 
                COUNT(CASE WHEN tier = 1 THEN 1 END) as t1_joins,
                COUNT(CASE WHEN tier = 2 THEN 1 END) as t2_joins,
                COALESCE(SUM(bonus_amount), 0) as total_referral_bonus_earned
            FROM referral_logs
            WHERE referrer_id = ?
            """, (user_id,))
            ref_log_row = cursor.fetchone()
            res["referral_log_t1"] = ref_log_row["t1_joins"] if ref_log_row else 0
            res["referral_log_t2"] = ref_log_row["t2_joins"] if ref_log_row else 0
            res["referral_log_earnings"] = ref_log_row["total_referral_bonus_earned"] if ref_log_row else 0.0
            
            cursor.execute("SELECT COUNT(*) as drops_claimed FROM free_drop_claims WHERE user_id = ?", (user_id,))
            claim_row = cursor.fetchone()
            res["free_drops_claimed"] = claim_row["drops_claimed"] if claim_row else 0
            
            # 3. Orders and Queue Analysis ("total order and quie order")
            cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
            all_orders = [dict(r) for r in cursor.fetchall()]
            
            completed_orders = [o for o in all_orders if o.get("status") == "completed"]
            queue_orders = [o for o in all_orders if o.get("status") in ("pending", "in_queue", "processing")]
            
            cursor.execute("SELECT * FROM course_requests WHERE user_id = ? AND status = 'pending' ORDER BY id DESC", (user_id,))
            pending_requests = [dict(r) for r in cursor.fetchall()]
            
            res["orders_all"] = all_orders
            res["orders_completed_count"] = len(completed_orders)
            res["orders_queue"] = queue_orders
            res["orders_queue_count"] = len(queue_orders)
            res["pending_requests"] = pending_requests
            res["pending_requests_count"] = len(pending_requests)
            res["total_queue_count"] = len(queue_orders) + len(pending_requests)
            
            return res

    def get_paginated_users_directory(self, page: int = 1, per_page: int = 8, filter_type: str = "all", search: Optional[str] = None) -> Dict[str, Any]:
        """Paginated directory of all users with live earnings, deposit totals, order counts, and queue items."""
        page = max(1, page)
        offset = (page - 1) * per_page
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Global summary counters
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users_global = cursor.fetchone()["total_users"]
            
            cursor.execute("SELECT COUNT(*) as total_resellers FROM users WHERE is_reseller >= 1")
            total_resellers_global = cursor.fetchone()["total_resellers"]
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_dep FROM transactions WHERE status = 'approved' AND currency = 'BDT'")
            total_dep_global = cursor.fetchone()["total_dep"]
            
            cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
            total_orders_global = cursor.fetchone()["total_orders"]
            
            cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM transactions WHERE status = 'pending') +
                (SELECT COUNT(*) FROM orders WHERE status IN ('pending', 'in_queue', 'processing')) +
                (SELECT COUNT(*) FROM course_requests WHERE status = 'pending') as queue_items
            """)
            total_queue_global = cursor.fetchone()["queue_items"]
            
            base_query = """
            SELECT 
                u.user_id,
                u.username,
                u.first_name,
                u.balance_bdt,
                u.balance_usd,
                u.total_spent_bdt,
                u.joined_at,
                u.is_banned,
                u.is_reseller,
                u.reseller_code,
                u.referral_count_t1,
                u.referral_points,
                u.referral_earnings_bdt,
                u.referred_by,
                COALESCE(dep.total_dep_bdt, 0) as total_deposited_bdt,
                COALESCE(dep.pending_dep_cnt, 0) as pending_deposits_count,
                COALESCE(ord.total_orders_cnt, 0) as orders_count,
                COALESCE(ord.queue_orders_cnt, 0) as queue_orders_count,
                COALESCE(req.pending_req_cnt, 0) as pending_requests_count
            FROM users u
            LEFT JOIN (
                SELECT 
                    user_id, 
                    SUM(CASE WHEN status = 'approved' AND currency = 'BDT' THEN amount ELSE 0 END) as total_dep_bdt,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_dep_cnt
                FROM transactions
                GROUP BY user_id
            ) dep ON u.user_id = dep.user_id
            LEFT JOIN (
                SELECT 
                    user_id,
                    COUNT(*) as total_orders_cnt,
                    SUM(CASE WHEN status IN ('pending', 'in_queue', 'processing') THEN 1 ELSE 0 END) as queue_orders_cnt
                FROM orders
                GROUP BY user_id
            ) ord ON u.user_id = ord.user_id
            LEFT JOIN (
                SELECT 
                    user_id,
                    COUNT(*) as pending_req_cnt
                FROM course_requests
                WHERE status = 'pending'
                GROUP BY user_id
            ) req ON u.user_id = req.user_id
            """
            
            where_clauses = []
            params = []
            
            if search:
                clean_s = search.strip().lstrip("@")
                if clean_s.isdigit():
                    where_clauses.append("(u.user_id = ? OR u.reseller_code LIKE ?)")
                    params.extend([int(clean_s), f"%{clean_s}%"])
                else:
                    where_clauses.append("(LOWER(u.username) LIKE ? OR LOWER(u.first_name) LIKE ? OR UPPER(u.reseller_code) LIKE ?)")
                    params.extend([f"%{clean_s.lower()}%", f"%{clean_s.lower()}%", f"%{clean_s.upper()}%"])
            
            if filter_type == "resellers":
                where_clauses.append("u.is_reseller >= 1")
            elif filter_type == "top_deposit":
                where_clauses.append("(COALESCE(dep.total_dep_bdt, 0) > 0 OR u.balance_bdt > 0)")
            elif filter_type == "top_earners":
                where_clauses.append("(u.referral_count_t1 > 0 OR u.referral_earnings_bdt > 0 OR u.referral_points > 0)")
            elif filter_type == "top_buyers":
                where_clauses.append("(COALESCE(ord.total_orders_cnt, 0) > 0 OR u.total_spent_bdt > 0)")
            elif filter_type == "in_queue":
                where_clauses.append("(COALESCE(dep.pending_dep_cnt, 0) > 0 OR COALESCE(ord.queue_orders_cnt, 0) > 0 OR COALESCE(req.pending_req_cnt, 0) > 0)")
                
            where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            if filter_type == "top_deposit":
                order_sql = " ORDER BY dep.total_dep_bdt DESC, u.balance_bdt DESC"
            elif filter_type == "top_earners":
                order_sql = " ORDER BY u.referral_count_t1 DESC, u.referral_earnings_bdt DESC, u.referral_points DESC"
            elif filter_type == "top_buyers":
                order_sql = " ORDER BY ord.total_orders_cnt DESC, u.total_spent_bdt DESC"
            elif filter_type == "in_queue":
                order_sql = " ORDER BY (COALESCE(dep.pending_dep_cnt, 0) + COALESCE(ord.queue_orders_cnt, 0) + COALESCE(req.pending_req_cnt, 0)) DESC, u.joined_at DESC"
            else:
                order_sql = " ORDER BY u.joined_at DESC"
                
            count_sql = f"SELECT COUNT(*) as cnt FROM ({base_query}{where_sql})"
            cursor.execute(count_sql, params)
            total_matching = cursor.fetchone()["cnt"]
            
            paginated_sql = f"{base_query}{where_sql}{order_sql} LIMIT ? OFFSET ?"
            cursor.execute(paginated_sql, params + [per_page, offset])
            rows = [dict(r) for r in cursor.fetchall()]
            
            total_pages = max(1, (total_matching + per_page - 1) // per_page)
            
            return {
                "users": rows,
                "current_page": page,
                "total_pages": total_pages,
                "total_matching": total_matching,
                "per_page": per_page,
                "filter_type": filter_type,
                "global_stats": {
                    "total_users": total_users_global,
                    "total_resellers": total_resellers_global,
                    "total_deposited_bdt": total_dep_global,
                    "total_orders": total_orders_global,
                    "total_queue": total_queue_global
                }
            }

    def toggle_user_ban(self, user_id: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return 0
            new_status = 1 if row["is_banned"] == 0 else 0
            cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_status, user_id))
            conn.commit()
            return new_status

    def reactivate_reseller(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users 
            SET is_reseller = 1, reseller_deactivated_permanent = 0, 
                reseller_quota_start = CURRENT_TIMESTAMP, reseller_monthly_sales = 0
            WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_at_risk_resellers(self) -> List[Dict[str, Any]]:
        """Identify resellers who have < 7 days remaining and haven't fulfilled quota."""
        quota_target = int(self.get_setting("reseller_monthly_quota", "5"))
        at_risk = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT user_id, username, first_name, reseller_code, reseller_quota_start, reseller_monthly_sales
            FROM users 
            WHERE is_reseller = 1
            """)
            rows = cursor.fetchall()
            now = datetime.now()
            for r in rows:
                sales = r["reseller_monthly_sales"] or 0
                if sales >= quota_target:
                    continue
                q_start = r["reseller_quota_start"]
                if not q_start:
                    continue
                try:
                    start_dt = datetime.strptime(q_start[:19], "%Y-%m-%d %H:%M:%S")
                    days_elapsed = (now - start_dt).days
                    days_left = max(0, 30 - days_elapsed)
                    if days_left <= 7:
                        at_risk.append({
                            "user_id": r["user_id"],
                            "username": r["username"],
                            "first_name": r["first_name"],
                            "reseller_code": r["reseller_code"],
                            "sales": sales,
                            "target": quota_target,
                            "days_left": days_left
                        })
                except Exception:
                    pass
        return at_risk

    def is_gateway_active(self, method: str) -> bool:
        return self.get_setting(f"gateway_{method.lower()}_active", "1") == "1"

    def set_gateway_active(self, method: str, is_active: bool) -> bool:
        val = "1" if is_active else "0"
        return self.set_setting(f"gateway_{method.lower()}_active", val)

    def create_reseller_vip_pass(self, user_id: int, discount_bdt: float, days_valid: int, max_uses: int = 5, code: Optional[str] = None) -> Dict[str, Any]:
        """Creates a time-bound VIP pass granting extra discount on top of reseller wholesale price."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if not code:
                code = f"VIP-{user_id % 10000:04d}-{int(discount_bdt)}TK"
            clean_code = code.strip().upper()
            expires_at = datetime.now() + timedelta(days=days_valid)
            exp_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO reseller_vip_passes (user_id, coupon_code, discount_bdt, expires_at, max_uses, used_count, is_active)
            VALUES (?, ?, ?, ?, ?, 0, 1)
            """, (user_id, clean_code, discount_bdt, exp_str, max_uses))
            pass_id = cursor.lastrowid

            # Also record in coupons table so it can be verified as a voucher code
            cursor.execute("""
            INSERT OR REPLACE INTO coupons (code, discount_bdt, max_uses, used_count, is_active)
            VALUES (?, ?, ?, 0, 1)
            """, (clean_code, discount_bdt, max_uses))
            conn.commit()

            return {
                "id": pass_id,
                "user_id": user_id,
                "coupon_code": clean_code,
                "discount_bdt": discount_bdt,
                "expires_at": exp_str,
                "days_valid": days_valid,
                "max_uses": max_uses,
                "used_count": 0
            }

    def get_active_reseller_vip_pass(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Returns active VIP Pass with remaining days and orders, or None if expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM reseller_vip_passes
            WHERE user_id = ? AND is_active = 1 AND used_count < max_uses
            ORDER BY discount_bdt DESC, id DESC
            """, (user_id,))
            rows = cursor.fetchall()
            now = datetime.now()
            for r in rows:
                exp_str = r["expires_at"]
                try:
                    exp_dt = datetime.strptime(exp_str[:19], "%Y-%m-%d %H:%M:%S")
                    if now < exp_dt:
                        diff = exp_dt - now
                        days_left = max(1, diff.days + (1 if diff.seconds > 0 else 0))
                        res_dict = dict(r)
                        res_dict["days_left"] = days_left
                        res_dict["remaining_uses"] = r["max_uses"] - r["used_count"]
                        return res_dict
                    else:
                        cursor.execute("UPDATE reseller_vip_passes SET is_active = 0 WHERE id = ?", (r["id"],))
                        conn.commit()
                except Exception:
                    pass
            return None

    def record_vip_pass_usage(self, pass_id: int) -> bool:
        """Increments usage count and automatically deactivates pass when limit reached."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reseller_vip_passes SET used_count = used_count + 1 WHERE id = ?", (pass_id,))
            cursor.execute("UPDATE reseller_vip_passes SET is_active = 0 WHERE id = ? AND used_count >= max_uses", (pass_id,))
            conn.commit()
            return True

    def reward_top_resellers(self, top_n: int = 3, discount_bdt: float = 50.0, days_valid: int = 7, max_uses: int = 10) -> List[Dict[str, Any]]:
        """Distributes exclusive reward VIP passes to Top N resellers on monthly leaderboard."""
        top_list = self.get_reseller_leaderboard(limit=top_n)
        results = []
        for rank, r in enumerate(top_list, start=1):
            uid = r["user_id"]
            code = f"TOP{rank}-{r.get('reseller_code', 'RS')}-{uid % 1000}"
            p = self.create_reseller_vip_pass(
                user_id=uid,
                discount_bdt=discount_bdt,
                days_valid=days_valid,
                max_uses=max_uses,
                code=code
            )
            p["rank"] = rank
            p["first_name"] = r.get("first_name", "Reseller")
            p["username"] = r.get("username")
            p["sales"] = r.get("reseller_monthly_sales", 0)
            results.append(p)
        return results

    def list_active_vip_passes(self) -> List[Dict[str, Any]]:
        """Lists all active passes across all resellers."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT p.*, u.first_name, u.username, u.reseller_code
            FROM reseller_vip_passes p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE p.is_active = 1 AND p.used_count < p.max_uses
            ORDER BY p.id DESC
            """)
            rows = cursor.fetchall()
            now = datetime.now()
            active_list = []
            for r in rows:
                try:
                    exp_dt = datetime.strptime(r["expires_at"][:19], "%Y-%m-%d %H:%M:%S")
                    if now < exp_dt:
                        diff = exp_dt - now
                        d = dict(r)
                        d["days_left"] = max(1, diff.days + (1 if diff.seconds > 0 else 0))
                        d["remaining_uses"] = r["max_uses"] - r["used_count"]
                        active_list.append(d)
                except Exception:
                    pass
            return active_list

    def revoke_vip_pass(self, pass_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reseller_vip_passes SET is_active = 0 WHERE id = ?", (pass_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- RESELLER CHALLENGE & COMPETITION METHODS ---
    def get_active_challenge(self) -> Optional[Dict[str, Any]]:
        """Returns currently active sales race challenge with current winners and remaining slots."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reseller_challenges WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None
            ch = dict(row)
            cursor.execute("""
            SELECT cw.*, u.first_name, u.username, u.reseller_code, p.coupon_code
            FROM challenge_winners cw
            JOIN users u ON cw.user_id = u.user_id
            LEFT JOIN reseller_vip_passes p ON cw.vip_pass_id = p.id
            WHERE cw.challenge_id = ?
            ORDER BY cw.rank ASC
            """, (ch["id"],))
            winners = [dict(w) for w in cursor.fetchall()]
            ch["winners"] = winners
            ch["claimed_slots"] = len(winners)
            ch["remaining_slots"] = max(0, ch["max_slots"] - len(winners))
            ch["is_full"] = ch["claimed_slots"] >= ch["max_slots"]
            return ch

    def set_or_create_challenge(
        self,
        target_sales: int = 15,
        max_slots: int = 3,
        discount_bdt: float = 50.0,
        days_valid: int = 15,
        max_uses: int = 10,
        title: str = "Monthly Super Seller Race"
    ) -> Dict[str, Any]:
        """Creates or updates the active race challenge."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reseller_challenges SET is_active = 0 WHERE is_active = 1")
            cursor.execute("""
            INSERT INTO reseller_challenges (title, target_sales, max_slots, discount_bdt, days_valid, max_uses, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (title, target_sales, max_slots, discount_bdt, days_valid, max_uses))
            conn.commit()
            return self.get_active_challenge()

    def reset_challenge(self) -> Dict[str, Any]:
        """Resets the challenge race for a new month/round."""
        curr = self.get_active_challenge()
        if curr:
            return self.set_or_create_challenge(
                target_sales=curr["target_sales"],
                max_slots=curr["max_slots"],
                discount_bdt=curr["discount_bdt"],
                days_valid=curr["days_valid"],
                max_uses=curr["max_uses"],
                title=curr.get("title", "Monthly Super Seller Race")
            )
        else:
            return self.set_or_create_challenge()

    def check_and_claim_challenge_reward(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Called when a reseller makes a sale.
        If user hits target_sales and slots remain, automatically unlocks and grants the VIP Pass!
        """
        ch = self.get_active_challenge()
        if not ch or not ch["is_active"]:
            return None
        if ch["remaining_slots"] <= 0:
            return None

        # Check if user already won in this challenge
        already_won = any(w["user_id"] == user_id for w in ch["winners"])
        if already_won:
            return None

        user = self.get_user(user_id)
        if not user or user.get("is_reseller", 0) < 1:
            return None

        sales = user.get("reseller_monthly_sales", 0)
        if sales < ch["target_sales"]:
            return None

        # User qualifies! Claim slot
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM challenge_winners WHERE challenge_id = ?", (ch["id"],))
            current_claimed = cursor.fetchone()["cnt"]
            if current_claimed >= ch["max_slots"]:
                return None
            
            rank = current_claimed + 1
            r_code = user.get("reseller_code", "RS")
            pass_code = f"WIN{rank}-{r_code}-{user_id % 1000}"

            # Create VIP Pass
            p = self.create_reseller_vip_pass(
                user_id=user_id,
                discount_bdt=ch["discount_bdt"],
                days_valid=ch["days_valid"],
                max_uses=ch["max_uses"],
                code=pass_code
            )

            cursor.execute("""
            INSERT INTO challenge_winners (challenge_id, user_id, rank, vip_pass_id, sales_at_win)
            VALUES (?, ?, ?, ?, ?)
            """, (ch["id"], user_id, rank, p["id"], sales))
            conn.commit()

            return {
                "challenge_id": ch["id"],
                "user_id": user_id,
                "first_name": user.get("first_name", "Reseller"),
                "username": user.get("username"),
                "reseller_code": r_code,
                "rank": rank,
                "target_sales": ch["target_sales"],
                "sales_at_win": sales,
                "discount_bdt": ch["discount_bdt"],
                "days_valid": ch["days_valid"],
                "max_uses": ch["max_uses"],
                "coupon_code": pass_code,
                "remaining_slots": ch["max_slots"] - rank,
                "max_slots": ch["max_slots"]
            }

    def get_challenge_leaderboard(self) -> Dict[str, Any]:
        """Provides complete race telemetry for the competition screen."""
        ch = self.get_active_challenge()
        if not ch:
            ch = self.set_or_create_challenge()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.reseller_code, u.reseller_monthly_sales,
                   cw.rank as won_rank, cw.won_at
            FROM users u
            LEFT JOIN challenge_winners cw ON u.user_id = cw.user_id AND cw.challenge_id = ?
            WHERE u.is_reseller = 1
            ORDER BY 
                CASE WHEN cw.rank IS NOT NULL THEN 0 ELSE 1 END,
                cw.rank ASC,
                u.reseller_monthly_sales DESC,
                u.total_spent_bdt DESC
            LIMIT 20
            """, (ch["id"],))
            racers = [dict(row) for row in cursor.fetchall()]
            
            return {
                "challenge": ch,
                "racers": racers
            }

    # --- FREE CLAIM & GIVEAWAY DROPS METHODS ---
    def create_free_drop(
        self,
        title: str,
        drop_type: str,
        max_claims: int,
        description: str = "",
        giveaway_category: str = "accounts",
        instructions: str = "",
        site_link: str = "",
        channel_id: Optional[str] = None,
        direct_link: Optional[str] = None,
        bulk_items: Optional[List[str]] = None,
        required_referrals: int = 0
    ) -> int:
        """Creates a new categorized giveaway drop with usage guide, website link and optional referral unlock requirement."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO free_drops (
                title, description, giveaway_category, instructions, site_link, drop_type, channel_id, direct_link, max_claims, claimed_count, is_active, required_referrals
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            """, (title, description, giveaway_category, instructions, site_link.strip() if site_link else "", drop_type, channel_id, direct_link, max_claims, max(0, required_referrals)))
            drop_id = cursor.lastrowid

            if bulk_items:
                for item in bulk_items:
                    clean = item.strip()
                    if clean:
                        cursor.execute("""
                        INSERT INTO free_drop_items (drop_id, content, is_claimed)
                        VALUES (?, ?, 0)
                        """, (drop_id, clean))

            return drop_id

    def get_active_free_drops(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all currently active free giveaway drops, optionally filtered by category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category and category != "all":
                cursor.execute("""
                SELECT * FROM free_drops
                WHERE is_active = 1 AND giveaway_category = ?
                ORDER BY id DESC
                """, (category,))
            else:
                cursor.execute("""
                SELECT * FROM free_drops
                WHERE is_active = 1
                ORDER BY id DESC
                """)
            drops = [dict(row) for row in cursor.fetchall()]
            for d in drops:
                d["remaining"] = max(0, d["max_claims"] - d["claimed_count"])
            return drops

    def get_free_drop_counts_by_category(self) -> Dict[str, int]:
        return self.get_active_drop_counts_by_category()

    def get_active_drop_counts_by_category(self) -> Dict[str, int]:
        """Returns live counts of active giveaway drops per category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT giveaway_category, COUNT(*) as cnt
            FROM free_drops
            WHERE is_active = 1
            GROUP BY giveaway_category
            """)
            counts = {row["giveaway_category"]: row["cnt"] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) as total FROM free_drops WHERE is_active = 1")
            row = cursor.fetchone()
            counts["total"] = row["total"] if row else 0
            return counts

    def get_all_free_drops(self, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Returns recent free drops for admin management, optionally filtered by category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category and category != "all":
                cursor.execute("""
                SELECT * FROM free_drops
                WHERE giveaway_category = ?
                ORDER BY id DESC
                LIMIT ?
                """, (category, limit))
            else:
                cursor.execute("""
                SELECT * FROM free_drops
                ORDER BY id DESC
                LIMIT ?
                """, (limit,))
            drops = [dict(row) for row in cursor.fetchall()]
            for d in drops:
                d["remaining"] = max(0, d["max_claims"] - d["claimed_count"])
            return drops

    def get_free_drop(self, drop_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM free_drops WHERE id = ?", (drop_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["remaining"] = max(0, d["max_claims"] - d["claimed_count"])
            return d

    def get_user_drop_claim(self, drop_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM free_drop_claims WHERE drop_id = ? AND user_id = ?", (drop_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def claim_free_drop_item(self, drop_id: int, user_id: int, delivery_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely and atomically processes a free claim for user.
        Ensures 1 claim per user, respects max_claims limit, and handles bulk combos.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Check if user already claimed
            cursor.execute("SELECT * FROM free_drop_claims WHERE drop_id = ? AND user_id = ?", (drop_id, user_id))
            prev = cursor.fetchone()
            if prev:
                return {"success": False, "reason": "already_claimed", "content": prev["delivery_content"]}

            # 2. Check drop status and slot availability
            cursor.execute("SELECT * FROM free_drops WHERE id = ? AND is_active = 1", (drop_id,))
            drop = cursor.fetchone()
            if not drop:
                return {"success": False, "reason": "inactive", "message": "এই গিভঅ্যাওয়ে বর্তমানে সক্রিয় নেই বা শেষ হয়ে গেছে।"}

            if drop["claimed_count"] >= drop["max_claims"]:
                return {"success": False, "reason": "full", "message": "দুঃখিত! এই গিভঅ্যাওয়ের সকল ফ্রি স্লট ইতিমধ্যে শেষ হয়ে গেছে।"}

            final_content = delivery_content

            # 3. Handle bulk_combo item dispatch
            if drop["drop_type"] == "bulk_combo":
                cursor.execute("""
                SELECT id, content FROM free_drop_items
                WHERE drop_id = ? AND is_claimed = 0
                ORDER BY id ASC LIMIT 1
                """, (drop_id,))
                item = cursor.fetchone()
                if not item:
                    return {"success": False, "reason": "empty_stock", "message": "স্টক শেষ হয়ে গেছে!"}
                final_content = item["content"]
                cursor.execute("""
                UPDATE free_drop_items
                SET is_claimed = 1, claimed_by = ?, claimed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (user_id, item["id"]))

            elif drop["drop_type"] == "direct_link":
                final_content = drop["direct_link"]

            if not final_content:
                final_content = "অ্যাক্সেস অনুমোদিত হয়েছে।"

            # 4. Insert into claims
            cursor.execute("""
            INSERT INTO free_drop_claims (drop_id, user_id, delivery_content)
            VALUES (?, ?, ?)
            """, (drop_id, user_id, final_content))

            # 5. Increment claimed_count
            cursor.execute("UPDATE free_drops SET claimed_count = claimed_count + 1 WHERE id = ?", (drop_id,))

            new_claimed = drop["claimed_count"] + 1
            if new_claimed >= drop["max_claims"]:
                cursor.execute("UPDATE free_drops SET is_active = 0 WHERE id = ?", (drop_id,))

            return {"success": True, "content": final_content, "claimed_count": new_claimed, "max_claims": drop["max_claims"]}

    def close_free_drop(self, drop_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE free_drops SET is_active = 0 WHERE id = ?", (drop_id,))
            return cursor.rowcount > 0

    def update_free_drop_referrals(self, drop_id: int, required_referrals: int) -> bool:
        """Updates the required referral count for a specific giveaway drop."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE free_drops SET required_referrals = ? WHERE id = ?", (max(0, required_referrals), drop_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_drop_claims(self, drop_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.id, c.user_id, c.delivery_content, c.claimed_at,
                   u.username, u.first_name
            FROM free_drop_claims c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE c.drop_id = ?
            ORDER BY c.id DESC
            LIMIT ?
            """, (drop_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # --- SUB-ADMIN RBAC METHODS ---
    def add_sub_admin(self, user_id: int, name: str = "", username: str = "", added_by: int = 0,
                      can_manage_free_drops: int = 1, can_manage_stock: int = 0,
                      can_manage_products: int = 0, can_approve_deposits: int = 0,
                      can_manage_resellers: int = 0, can_broadcast: int = 0,
                      can_manage_users: int = 0, can_manage_coupons: int = 0) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO admin_roles (
                user_id, name, username, added_by,
                can_manage_free_drops, can_manage_stock, can_manage_products,
                can_approve_deposits, can_manage_resellers, can_broadcast,
                can_manage_users, can_manage_coupons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                username = excluded.username,
                added_by = excluded.added_by
            """, (
                user_id, name, username, added_by,
                can_manage_free_drops, can_manage_stock, can_manage_products,
                can_approve_deposits, can_manage_resellers, can_broadcast,
                can_manage_users, can_manage_coupons
            ))
            conn.commit()
            return True

    def remove_sub_admin(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin_roles WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_sub_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_roles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_sub_admins(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_roles ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def is_sub_admin(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admin_roles WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def toggle_admin_permission(self, user_id: int, perm_key: str) -> bool:
        allowed = {
            "can_manage_free_drops", "can_manage_stock", "can_manage_products",
            "can_approve_deposits", "can_manage_resellers", "can_broadcast",
            "can_manage_users", "can_manage_coupons"
        }
        if perm_key not in allowed:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
            UPDATE admin_roles
            SET {perm_key} = CASE WHEN COALESCE({perm_key}, 0) = 1 THEN 0 ELSE 1 END
            WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            cursor.execute(f"SELECT {perm_key} FROM admin_roles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return bool(row[perm_key]) if row else False

db = Database()


