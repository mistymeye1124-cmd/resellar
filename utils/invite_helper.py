# Invite Helper for Private Telegram Channels / VIP Groups
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

async def generate_single_use_invite_link(bot: Bot, channel_id: str, course_title: str) -> str:
    """
    Generates a 1-time single-use Telegram channel invite link (member_limit=1).
    This ensures that once the user joins, the link becomes invalid and cannot be shared.
    """
    try:
        # Convert channel_id to int if numeric
        target_chat = int(channel_id) if (channel_id.startswith("-100") or channel_id.isdigit() or (channel_id.startswith("-") and channel_id[1:].isdigit())) else channel_id
        
        invite_link = await bot.create_chat_invite_link(
            chat_id=target_chat,
            name=f"Access: {course_title[:25]}",
            member_limit=1
        )
        return invite_link.invite_link
    except Exception as e:
        logger.error(f"Failed to generate single-use invite link for {channel_id}: {e}")
        # If channel_id is already a valid full invite link
        if str(channel_id).startswith("http://") or str(channel_id).startswith("https://"):
            return str(channel_id)
        elif str(channel_id).startswith("@"):
            return f"https://t.me/{str(channel_id)[1:]}"
        # If numeric channel ID failed (e.g. -100...), bot lacks invite permission or invalid ID
        return ""
