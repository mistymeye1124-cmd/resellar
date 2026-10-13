"""
FINAL PRODUCTION SETUP SCRIPT
- Deletes ALL extra categories, products, free drops
- Keeps clean structure: 2 categories (1 course cat + 1 digital cat)
- Adds 1 proper demo course + 1 proper demo digital product with stock
- Cleans up orphaned data
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database.db import db

print("=" * 60)
print("FINAL PRODUCTION DB SETUP")
print("=" * 60)

conn = db._get_connection()
cursor = conn.cursor()

# ============================================================
# STEP 1: Wipe everything cleanly
# ============================================================
print("\n[1] Wiping all products, categories, stock, free drops...")

cursor.execute("DELETE FROM free_drop_claims")
cursor.execute("DELETE FROM free_drop_items")
cursor.execute("DELETE FROM free_drops")
cursor.execute("DELETE FROM stock_items")
cursor.execute("DELETE FROM orders")
cursor.execute("DELETE FROM products")
cursor.execute("DELETE FROM categories")
# Reset autoincrement counters
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('products','categories','free_drops','free_drop_items','free_drop_claims','stock_items','orders')")

conn.commit()
print("   Done. All products/categories/drops wiped.")

# ============================================================
# STEP 2: Create exactly 2 clean categories
# ============================================================
print("\n[2] Creating 2 clean categories...")

cursor.execute(
    "INSERT INTO categories (name, icon, type, order_num) VALUES (?, ?, ?, ?)",
    ("🎓 All Premium Courses (কোর্স ভল্ট)", "🎓", "course", 1)
)
course_cat_id = cursor.lastrowid

cursor.execute(
    "INSERT INTO categories (name, icon, type, order_num) VALUES (?, ?, ?, ?)",
    ("⚡ Digital Tools & Accounts (ডিজিটাল একাউন্ট)", "⚡", "digital", 2)
)
digital_cat_id = cursor.lastrowid

conn.commit()
print(f"   Course category ID: {course_cat_id}")
print(f"   Digital category ID: {digital_cat_id}")

# ============================================================
# STEP 3: Add 1 demo course (channel_link type)
# ============================================================
print("\n[3] Adding demo course product...")

cursor.execute("""
INSERT INTO products 
(category_id, title, description, price_bdt, price_usd, reseller_price_bdt, reseller_price_usd,
 product_type, channel_id, is_active, is_in_stock)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
""", (
    course_cat_id,
    "🎬 Premiere Pro & After Effects Masterclass 2026",
    "✅ Basic to Advanced Motion Graphics & Video Editing\n"
    "✅ 500+ GB Presets, SFX & Plugins Pack Included\n"
    "✅ Private VIP Telegram Channel — Lifetime Access\n"
    "✅ Weekly New Tutorials & Project Files Upload\n\n"
    "📌 এই কোর্সটি কিনলে আপনি আমাদের প্রাইভেট ভিআইপি চ্যানেলে লাইফটাইম অ্যাক্সেস পাবেন।\n"
    "চ্যানেলে ৫০০+ জিবি রিসোর্স, প্রিসেট, প্রজেক্ট ফাইল ও সাপোর্ট পাবেন।",
    350.0,   # retail BDT
    2.80,    # retail USD
    245.0,   # reseller BDT (30% off)
    1.95,    # reseller USD
    "channel_link",
    "@ProAccessBD",  # replace with real channel
))
course_prod_id = cursor.lastrowid
conn.commit()
print(f"   Course product ID: {course_prod_id}")

# ============================================================
# STEP 4: Add 1 demo digital product (stock_account type)
# ============================================================
print("\n[4] Adding demo digital product with stock...")

cursor.execute("""
INSERT INTO products 
(category_id, title, description, price_bdt, price_usd, reseller_price_bdt, reseller_price_usd,
 product_type, is_active, is_in_stock)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
""", (
    digital_cat_id,
    "🤖 Gemini Advanced 12-Month Redeem Link",
    "⚡ Official Google Gemini Advanced 12-Month Direct Redeem Code\n"
    "⚡ No Credit Card Required — Just Redeem & Activate\n"
    "⚡ Full Gemini 1.5 Pro Access with 1M Context Window\n"
    "⚡ Google One 2TB Storage Included\n"
    "⚡ Instant Auto-Delivery to your chat upon purchase\n\n"
    "📌 রিডিম কোডটি পাওয়ার পর Google Gemini অ্যাপে গিয়ে Redeem করুন।\n"
    "সমস্যা হলে সাথে সাথে অ্যাডমিনকে জানান — ওয়ারেন্টি দেওয়া হবে।",
    79.0,    # retail BDT
    0.62,    # retail USD
    55.0,    # reseller BDT
    0.43,    # reseller USD
    "stock_account",
))
digital_prod_id = cursor.lastrowid
conn.commit()
print(f"   Digital product ID: {digital_prod_id}")

# ============================================================
# STEP 5: Add 10 demo stock items for the digital product
# ============================================================
print("\n[5] Adding 10 demo stock keys for digital product...")

demo_keys = [
    f"GEMINI-ADV-DEMO-KEY-{i:04d}-REPLACE-WITH-REAL" for i in range(1, 11)
]

stock_vals = [(digital_prod_id, key, 0, None, None) for key in demo_keys]
cursor.executemany(
    "INSERT INTO stock_items (product_id, content, is_used, used_by, used_at) VALUES (?, ?, ?, ?, ?)",
    stock_vals
)
conn.commit()
print(f"   Added {len(demo_keys)} stock keys.")
print("   *** IMPORTANT: Replace demo keys with real redeem codes before going live! ***")

# ============================================================
# STEP 6: Add 1 clean free drop (direct_link type for demo)
# ============================================================
print("\n[6] Adding 1 clean demo free drop...")

cursor.execute("""
INSERT INTO free_drops 
(title, description, giveaway_category, instructions, site_link, drop_type, direct_link, max_claims, claimed_count, is_active, required_referrals)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 0)
""", (
    "🎁 Free Canva Pro 30-Day Trial Link",
    "সম্পূর্ণ বিনামূল্যে Canva Pro ট্রায়াল — কোনো ক্রেডিট কার্ড লাগবে না!",
    "tools_drive",
    "1. নিচের লিংকে ক্লিক করুন\n2. Google বা Email দিয়ে সাইন আপ করুন\n3. Canva Pro ৩০ দিন সম্পূর্ণ ফ্রিতে উপভোগ করুন!",
    "https://www.canva.com",
    "direct_link",
    "https://partner.canva.com/replace-with-real-affiliate-link",  # replace with real
    100,
))
conn.commit()
print("   Demo free drop added.")
print("   *** Replace free drop link with real affiliate/promo link! ***")

# ============================================================
# STEP 7: Verify final state
# ============================================================
print("\n[7] Final DB Verification...")

cats = cursor.execute("SELECT id, name, type FROM categories").fetchall()
print(f"\n   Categories ({len(cats)}):")
for c in cats:
    print(f"   - ID:{c['id']} | {c['type']} | {c['name']}")

prods = cursor.execute("SELECT id, category_id, title, product_type, is_active FROM products").fetchall()
print(f"\n   Products ({len(prods)}):")
for p in prods:
    title = p['title'][:55]
    print(f"   - ID:{p['id']} | Cat:{p['category_id']} | {p['product_type']} | Active:{p['is_active']} | {title}")

stock = cursor.execute("SELECT product_id, COUNT(*) as cnt FROM stock_items WHERE is_used=0 GROUP BY product_id").fetchall()
print(f"\n   Available Stock:")
for s in stock:
    print(f"   - Product:{s['product_id']} | Available keys: {s['cnt']}")

drops = cursor.execute("SELECT id, title, is_active, max_claims FROM free_drops").fetchall()
print(f"\n   Free Drops ({len(drops)}):")
for d in drops:
    print(f"   - Drop:{d['id']} | Active:{d['is_active']} | Max:{d['max_claims']} | {d['title']}")

conn.close()

print("\n" + "=" * 60)
print("PRODUCTION SETUP COMPLETE!")
print("=" * 60)
print("\nREMINDER — Things to replace before going fully live:")
print("  1. Course channel_id: '@ProAccessBD' → your real private channel")
print("  2. Digital stock keys: demo keys → real Gemini redeem codes")
print("  3. Free drop link: partner.canva.com → your real promo link")
print("  4. Add your real products via Admin Panel (/admin → Products)")
print("=" * 60)
