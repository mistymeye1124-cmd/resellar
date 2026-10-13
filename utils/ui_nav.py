# UI Navigation Switcher for Seamless In-Place Transitions with Duplicate Guard
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

def render_safe_html_text(text: str) -> str:
    """
    Renders rich text for Telegram HTML parse_mode:
    1. Unescapes previously double-escaped standard tags (&lt;b&gt; -> <b>, etc.).
    2. Converts Markdown bold (**text**) to HTML <b>text</b>.
    3. Preserves valid Telegram HTML tags (<b>, <i>, <code>, <u>, <s>, <a>, <pre>, <tg-emoji>).
    4. Auto-closes any opened tags to prevent Telegram 'can't parse entities' errors.
    """
    if not text:
        return ""
    
    repaired = str(text)
    for tag in ["b", "i", "u", "s", "code", "pre", "tg-spoiler"]:
        repaired = re.sub(rf"&lt;({tag})&gt;", rf"<\1>", repaired, flags=re.I)
        repaired = re.sub(rf"&lt;/({tag})&gt;", rf"</\1>", repaired, flags=re.I)
    
    repaired = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", repaired)
    
    # Strip any dangling partial opening tag cut at the end (e.g. "<b" or "<a href...")
    repaired = re.sub(r"<[^>]*$", "", repaired)
    
    tag_pattern = re.compile(r"<(/?)([a-zA-Z0-9-]+)(?:\s+[^>]*)?>")
    stack = []
    for match in tag_pattern.finditer(repaired):
        is_closing = match.group(1) == "/"
        tag_name = match.group(2).lower()
        if tag_name in ["b", "i", "u", "s", "code", "pre", "tg-spoiler", "a"]:
            if not is_closing:
                stack.append(tag_name)
            else:
                if stack and stack[-1] == tag_name:
                    stack.pop()
                elif tag_name in stack:
                    stack.remove(tag_name)
    
    for unclosed in reversed(stack):
        repaired += f"</{unclosed}>"
        
    return repaired

async def safe_switch_screen(
    call: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    photo_url: Optional[str] = None,
    parse_mode: str = "HTML"
):
    """
    Seamlessly switches the current screen in-place.
    - If staying text -> text: edits message in-place.
    - If staying photo -> photo: edits caption in-place.
    - If transitioning text <-> photo: deletes old message and sends new one so chat remains 100% clean with zero clutter!
    - Completely prevents duplicate messages on re-clicks or identical content.
    """
    msg = call.message
    if not msg:
        return
    is_photo_current = bool(msg.photo)

    # Check if a valid photo identifier (URL or Telegram file_id) is provided
    has_photo = bool(photo_url and isinstance(photo_url, str) and photo_url.strip())

    if has_photo:
        caption = text
        if len(caption) > 1024:
            caption = caption[:1015] + "..."
            caption = render_safe_html_text(caption)
            
        if is_photo_current:
            try:
                await msg.edit_caption(caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
                return
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Content is already identical on screen; do NOT delete or resend!
                    return
                logger.debug(f"edit_caption TelegramBadRequest: {e}")
            except Exception as e:
                logger.debug(f"edit_caption failed: {e}")

        # Transitioning text -> photo or photo update failed
        try:
            await msg.delete()
        except Exception:
            pass
        try:
            await msg.answer_photo(photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except Exception as e:
            logger.warning(f"answer_photo failed ({e}), falling back to text")
            try:
                await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception:
                pass
    else:
        # Target screen is text
        if not is_photo_current:
            try:
                await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                return
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Content is already identical on screen; do NOT delete or resend!
                    return
                logger.debug(f"edit_text TelegramBadRequest: {e}")
            except Exception as e:
                logger.debug(f"edit_text failed: {e}")

        # Transitioning photo -> text or edit failed
        try:
            await msg.delete()
        except Exception:
            pass
        try:
            await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            logger.warning(f"answer text failed: {e}")

async def render_screen(
    call: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML"
):
    """
    Safely renders a text screen from a callback:
    - If current message is a photo, deletes it and sends the text message.
    - If current message is text, edits it in-place.
    - Idempotently ignores 'message is not modified' errors so zero duplicate messages are created.
    """
    msg = call.message
    if not msg:
        return
        
    if msg.photo:
        try:
            await msg.delete()
        except Exception:
            pass
        try:
            await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            logger.warning(f"render_screen answer failed: {e}")
    else:
        try:
            await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            if "message is not modified" in err_msg:
                # Screen is ALREADY up to date with exact content & keyboard! Never delete/resend!
                return
            # If message was somehow not editable as text, fall back to clean delete + answer
            try:
                await msg.delete()
            except Exception:
                pass
            try:
                await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception:
                pass
        except Exception:
            try:
                await msg.delete()
            except Exception:
                pass
            try:
                await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception:
                pass
