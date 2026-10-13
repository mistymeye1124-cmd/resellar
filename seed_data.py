# Seed Demo Products into the Database
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from database.db import db

def seed():
    # 1. Fetch categories
    cats = db.get_categories_by_type("course") + db.get_categories_by_type("digital")
    cat_map = {c["name"]: c["id"] for c in cats}
    
    # 2. Sample Courses (90%)
    sample_courses = [
        {
            "cat_name": "📱 Video Editing & Premiere VIP",
            "title": "🎬 Premiere Pro & After Effects Masterclass 2026",
            "desc": "✅ Basic to Advanced Motion Graphics & Editing\n✅ 500+ GB Presets, SFX & Plugins Pack\n✅ Private VIP Telegram Channel Access with Lifetime Updates",
            "price_bdt": 350.0,
            "price_usd": 2.8,
            "type": "channel_link",
            "channel_id": "@ProAccessBD" # Placeholder, AN0N replaces with their channel
        },
        {
            "cat_name": "🎨 Graphic Design & Freelancing",
            "title": "🎨 Complete Graphic Design & Fiverr Freelancing Course",
            "desc": "✅ Photoshop, Illustrator & T-Shirt Design\n✅ Client Hunting & Marketplace Secrets\n✅ Full Cloud Drive VIP Folder Access",
            "price_bdt": 299.0,
            "price_usd": 2.4,
            "type": "drive_link",
            "drive_link": "https://drive.google.com/drive/folders/sample_graphic_vault"
        },
        {
            "cat_name": "💻 Web Dev & Programming Bundles",
            "title": "💻 Full-Stack Web Development Bootcamp (MERN)",
            "desc": "✅ HTML, CSS, JavaScript, React, Node.js & MongoDB\n✅ 10+ Real-World Projects\n✅ Private VIP Channel Access",
            "price_bdt": 499.0,
            "price_usd": 4.0,
            "type": "channel_link",
            "channel_id": "@ProAccessBD"
        },
        {
            "cat_name": "🤖 AI Mastery & Automation",
            "title": "🤖 AI Prompt Engineering & Automation Mastery",
            "desc": "✅ ChatGPT, Claude & Midjourney Complete Workflow\n✅ n8n & Make Automation for Business\n✅ VIP Channel Access",
            "price_bdt": 399.0,
            "price_usd": 3.2,
            "type": "channel_link",
            "channel_id": "@ProAccessBD"
        },
        {
            "cat_name": "👑 VIP Mega Course Vault (All Access)",
            "title": "👑 All-in-One Mega Vault (100+ Premium Courses Lifetime)",
            "desc": "💎 All Video Editing, Marketing, Coding & Design Courses in 1 Place!\n💎 Daily/Weekly New Course Uploads\n💎 Lifetime Single-Use VIP Access",
            "price_bdt": 999.0,
            "price_usd": 8.0,
            "type": "channel_link",
            "channel_id": "@ProAccessBD"
        }
    ]
    
    # 3. Sample Digital Tools (10%)
    sample_tools = [
        {
            "cat_name": "🤖 AI Tools & Accounts (Gemini, ChatGPT, etc.)",
            "title": "🤖 Gemini Advanced 18 Months Redeem Link",
            "desc": "⚡ Official Google Gemini 18-Month Direct Redeem Link\n⚡ No Card Needed to Activate\n⚡ Instant Auto-Delivery to your chat",
            "price_bdt": 75.0,
            "price_usd": 0.60,
            "type": "stock_account"
        },
        {
            "cat_name": "🎨 Creative Tools (Canva Pro, CapCut, etc.)",
            "title": "🎨 Canva Pro 1-Year Private / Invite Access",
            "desc": "💎 1-Year Full Warranty\n💎 Brand Kit, Magic Studio & All Pro Elements\n💎 Instant Delivery",
            "price_bdt": 120.0,
            "price_usd": 0.99,
            "type": "stock_account"
        }
    ]
    
    print("Seeding sample courses & tools...")
    for item in sample_courses + sample_tools:
        cat_id = None
        for cname, cid in cat_map.items():
            if item["cat_name"].split()[0] in cname:
                cat_id = cid
                break
        if not cat_id:
            cat_id = list(cat_map.values())[0]
            
        pid = db.add_product(
            category_id=cat_id,
            title=item["title"],
            description=item["desc"],
            price_bdt=item["price_bdt"],
            price_usd=item["price_usd"],
            product_type=item["type"],
            channel_id=item.get("channel_id"),
            drive_link=item.get("drive_link")
        )
        print(f"Added: #{pid} {item['title']}")
        
        # Add sample stock for stock_account
        if item["type"] == "stock_account":
            demo_items = [
                f"REDEEM-KEY-DEMO-A1-{pid}",
                f"REDEEM-KEY-DEMO-B2-{pid}",
                f"REDEEM-KEY-DEMO-C3-{pid}"
            ]
            added = db.add_stock_items(pid, demo_items)
            print(f"  -> Added {added} stock accounts/keys")

    print("\n✅ Seeding complete! Database is populated with ready demo courses and digital tools.")

if __name__ == "__main__":
    seed()
