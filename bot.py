# Main Bot Runner for Reseller Bot
import asyncio
import logging
import sys
import re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, MenuButtonCommands
from config import BOT_TOKEN, ADMIN_IDS
from handlers import core, start, deposit, admin_deposit, catalog, admin_panel, reseller, verify, referral, free_claim, search, groq_admin
from database.db import db
from utils.backup_manager import daily_database_backup_scheduler

# Configure Logging with rotation (max 5MB per file, keep 3 backups)
from logging.handlers import RotatingFileHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler("bot.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    ]
)
logger = logging.getLogger("ResellerBot")

async def reseller_quota_scheduler(bot: Bot):
    """Background worker running every 24 hours to enforce 30-day reseller quota."""
    while True:
        try:
            await asyncio.sleep(86400) # Check once every 24 hours
            deactivated = db.enforce_reseller_quotas()
            if deactivated:
                logger.info(f"Enforced quotas: {len(deactivated)} resellers deactivated.")
                for uid in deactivated:
                    try:
                        await bot.send_message(
                            chat_id=uid,
                            text="❌ **আপনার রিসেলার অ্যাকাউন্ট স্থায়ীভাবে বাতিল (Deactivated) করা হয়েছে!**\n\n"
                                 "কারণ: ৩০ দিনের মধ্যে ন্যূনতম মাসিক সেলস কোটা পূরণ করতে ব্যর্থ হয়েছেন। পলিসি অনুযায়ী এই সিদ্ধান্ত স্থায়ী।",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                for aid in ADMIN_IDS:
                    if aid > 0:
                        try:
                            await bot.send_message(
                                chat_id=aid,
                                text=f"⚠️ **দৈনিক কোটা স্ক্যান রিপোর্ট:** সেলস কোটা অপূর্ণ থাকায় `{len(deactivated)} জন` রিসেলারের অ্যাকাউন্ট স্থায়ীভাবে বাতিল করা হয়েছে।",
                                parse_mode="Markdown"
                            )
                        except Exception:
                            pass
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in reseller quota scheduler: {e}")

class SafeMarkdownMiddleware(BaseRequestMiddleware):
    """
    Globally intercepts Telegram entity parsing errors and custom emoji incompatibilities,
    automatically converting text emojis into Telegram Premium custom emojis (<tg-emoji>) for HTML
    and applying native animated custom emoji icons to all buttons.
    Ensures zero user-facing error crashes.
    """
    async def __call__(self, make_request, bot, method):
        # 1. Automatically enrich all keyboard buttons with Telegram Premium custom emojis
        if hasattr(method, "reply_markup") and method.reply_markup is not None:
            try:
                from utils.emojis import apply_premium_emojis_to_keyboard
                method.reply_markup = apply_premium_emojis_to_keyboard(method.reply_markup)
            except Exception:
                pass

        # 2. Automatically convert standard emojis into <tg-emoji> for HTML messages ONLY
        if getattr(method, "parse_mode", None) == "HTML":
            try:
                from utils.emojis import render_premium_html
                if hasattr(method, "text") and method.text:
                    method.text = render_premium_html(method.text)
                if hasattr(method, "caption") and method.caption:
                    method.caption = render_premium_html(method.caption)
            except Exception:
                pass

        try:
            return await make_request(bot, method)
        except TelegramBadRequest as e:
            err_msg = str(e).lower()

            # Idempotent ignore for message not modified (e.g. user refreshed unchanged menu)
            if "message is not modified" in err_msg:
                return True

            # Auto-recover from any entity, custom emoji or HTML parsing errors
            if any(term in err_msg for term in (
                "can't parse entities",
                "can't find end of the entity",
                "entity_text_invalid",
                "custom_emoji_id_invalid",
                "entity_bounds_invalid",
                "tag_empty",
                "failed to parse"
            )):
                # Step 1: Strip <tg-emoji> tags while preserving valid HTML and original emojis
                if hasattr(method, "text") and method.text and "<tg-emoji" in method.text:
                    method.text = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', method.text)
                    try:
                        return await make_request(bot, method)
                    except TelegramBadRequest as e2:
                        if "message is not modified" in str(e2).lower():
                            return True

                if hasattr(method, "caption") and method.caption and "<tg-emoji" in method.caption:
                    method.caption = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', method.caption)
                    try:
                        return await make_request(bot, method)
                    except TelegramBadRequest as e2:
                        if "message is not modified" in str(e2).lower():
                            return True

                # Step 1.5: Auto-sanitize HTML (strip <br>, auto-close dangling tags) and retry with HTML
                try:
                    from utils.ui_nav import render_safe_html_text
                    repaired_any = False
                    if hasattr(method, "text") and method.text:
                        clean_t = render_safe_html_text(method.text)
                        if clean_t != method.text:
                            method.text = clean_t
                            repaired_any = True
                    if hasattr(method, "caption") and method.caption:
                        clean_c = render_safe_html_text(method.caption)
                        if clean_c != method.caption:
                            method.caption = clean_c
                            repaired_any = True
                    if repaired_any:
                        try:
                            return await make_request(bot, method)
                        except TelegramBadRequest as e2:
                            if "message is not modified" in str(e2).lower():
                                return True
                except Exception:
                    pass

                # Step 2: Fall back to plain text (parse_mode=None)
                if hasattr(method, "parse_mode") and method.parse_mode is not None:
                    logger.warning(f"Auto-handled Markdown/HTML entity error in {type(method).__name__}. Retrying with parse_mode=None.")
                    method.parse_mode = None
                    try:
                        return await make_request(bot, method)
                    except TelegramBadRequest as e3:
                        if "message is not modified" in str(e3).lower():
                            return True

            # Step 3: Handle button custom emoji restrictions
            if any(term in err_msg for term in ("custom_emoji", "emoji_invalid", "button")):
                if hasattr(method, "reply_markup") and method.reply_markup is not None:
                    from utils.emojis import strip_button_custom_emojis
                    logger.warning(f"Auto-handled custom emoji restriction in {type(method).__name__}. Retrying without button custom emojis.")
                    method.reply_markup = strip_button_custom_emojis(method.reply_markup)
                    try:
                        return await make_request(bot, method)
                    except TelegramBadRequest as e4:
                        if "message is not modified" in str(e4).lower():
                            return True
                        raise e4

            raise e

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN is not configured in .env file! Please edit .env with your bot token.")
        print("\n=======================================================")
        print("⚠️  সতর্কবার্তা: আপনি এখনও .env ফাইলে BOT_TOKEN বসাননি!")
        print("Telegram @BotFather থেকে বটের টোকেন নিয়ে .env ফাইলে বসিয়ে দিন।")
        print("=======================================================\n")
        return

    session = AiohttpSession(timeout=30.0)
    bot = Bot(token=BOT_TOKEN, session=session)
    bot.session.middleware(SafeMarkdownMiddleware())
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Prefetch bot identity for instant zero-latency caching
    try:
        bot.cached_bot_info = await bot.get_me()
        logger.info(f"Bot identity cached: @{bot.cached_bot_info.username}")
    except Exception as e:
        logger.warning(f"Failed to prefetch bot info: {e}")
        bot.cached_bot_info = None

    # Register Anti-Duplicate, Debounce & Concurrency Guard Middleware
    from middlewares.anti_duplicate import CallbackDeduplicationMiddleware
    dp.callback_query.middleware(CallbackDeduplicationMiddleware(debounce_window=0.35))

    # Register Routers in proper order (Master Core / Cancel Router first)
    dp.include_router(core.router)
    dp.include_router(admin_panel.router)
    dp.include_router(groq_admin.router)
    dp.include_router(admin_deposit.router)
    dp.include_router(verify.router)
    dp.include_router(referral.router)
    dp.include_router(start.router)
    dp.include_router(reseller.router)
    dp.include_router(free_claim.router)
    dp.include_router(deposit.router)
    dp.include_router(catalog.router)
    dp.include_router(search.router)

    # Global Exception & Telegram API Error Handler
    @dp.error()
    async def global_error_handler(event):
        logger.exception(f"Unhandled error in update {event.update}: {event.exception}")
        try:
            if event.update and event.update.message:
                await event.update.message.answer("⚠️ একটি সমস্যা দেখা দিয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।")
            elif event.update and event.update.callback_query:
                await event.update.callback_query.answer("⚠️ একটি সমস্যা দেখা দিয়েছে। আবার চেষ্টা করুন।", show_alert=True)
        except Exception:
            pass

    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🏠 Main Menu / মূল মেনু"),
            BotCommand(command="courses", description="🎓 Browse Courses / কোর্স সমূহ"),
            BotCommand(command="deposit", description="💳 Add Balance / ডিপোজিট"),
            BotCommand(command="profile", description="👤 My Profile / প্রোফাইল"),
            BotCommand(command="orders", description="📦 My Orders / আমার অর্ডার"),
            BotCommand(command="free", description="🎁 Free Drops / গিভঅ্যাওয়ে"),
            BotCommand(command="reseller", description="🤝 Reseller Hub / রিসেলার হাব"),
            BotCommand(command="verify", description="🛡️ Verify Reseller / সততা যাচাই"),
            BotCommand(command="help", description="💬 Support / কাস্টমার সাপোর্ট"),
            BotCommand(command="cancel", description="❌ Cancel / যেকোনো কাজ বাতিল"),
            BotCommand(command="admin", description="👑 Admin Panel / অ্যাডমিন প্যানেল"),
            BotCommand(command="backup", description="💾 DB Backup / ডাটাবেজ ব্যাকআপ (Admin)")
        ])
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

    logger.info("🚀 Reseller Bot is starting...")
    
    # Notify admin on start
    for aid in ADMIN_IDS:
        if aid > 0:
            try:
                await bot.send_message(chat_id=aid, text="🚀 **রিসেলার বট সফলভাবে চালু হয়েছে এবং সক্রিয় আছে!**", parse_mode="Markdown")
            except Exception:
                pass

    quota_task = asyncio.create_task(reseller_quota_scheduler(bot))
    backup_task = asyncio.create_task(daily_database_backup_scheduler(bot))

    try:
        # Keep pending updates so any commands sent while restarting are processed immediately!
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=30,
            handle_as_tasks=True,
            tasks_concurrency_limit=64,
            handle_signals=False
        )
    finally:
        quota_task.cancel()
        backup_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
