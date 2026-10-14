# Anti-Duplicate, Debounce & Concurrency Guard Middleware for Telegram Callbacks
import time
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

# Navigation callbacks that should automatically reset any active FSM input state
TOP_LEVEL_NAV_CALLBACKS = {
    "main_menu",
    "back_cats",
    "nav_profile",
    "profile_refresh",
    "nav_orders",
    "nav_referral",
    "nav_free_claim",
    "back_reseller_hub",
    "verify_reseller_prompt",
    "nav_lang",
    "add_balance_shortcut",
    "admin_main_dashboard",
    "admin_cats_menu",
    "admin_list_prods",
    "admin_stock_hub",
    "admin_coupons_menu",
    "admin_free_drops_menu",
    "admin_settings_menu",
    "admin_settings",
    "admin_pending_deps",
    "cancel_fsm",
    "toggle_bottom_menu"
}

TOP_LEVEL_NAV_PREFIXES = (
    "cat:",
    "claim_cat:",
    "set_lang:",
    "dep_method:",
    "locked_account_tier:",
    "locked_channel_tier:",
    "usr_ctl_tog_ch:",
    "usr_ctl_tog_acc:",
    "usr_ctl_tog_tier:"
)

class CallbackDeduplicationMiddleware(BaseMiddleware):
    def __init__(self, debounce_window: float = 0.8):
        self.debounce_window = debounce_window
        # user_id -> (last_callback_data, last_timestamp)
        self._last_callbacks: Dict[int, tuple[str, float]] = {}
        # user_id -> asyncio.Lock
        self._user_locks: Dict[int, asyncio.Lock] = {}

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        user_id = event.from_user.id
        callback_data = event.data or ""
        now = time.monotonic()

        # 1. Silently handle decorative/noop buttons without error or spinner
        if callback_data in ("noop", "noop_claimed", "noop_full"):
            try:
                await event.answer()
            except Exception:
                pass
            return

        # 2. Check Debounce for Rapid Double-Taps on the exact same button
        last_data, last_time = self._last_callbacks.get(user_id, ("", 0.0))
        if callback_data == last_data and (now - last_time) < self.debounce_window:
            logger.debug(f"Debounced rapid duplicate callback '{callback_data}' from user {user_id}")
            try:
                await event.answer()  # Stop mobile spinner
            except Exception:
                pass
            return

        self._last_callbacks[user_id] = (callback_data, now)

        # 3. Auto-clean any stale FSM input state when user triggers a navigation callback
        is_nav = (callback_data in TOP_LEVEL_NAV_CALLBACKS) or any(
            callback_data.startswith(p) for p in TOP_LEVEL_NAV_PREFIXES
        )
        if is_nav:
            state: FSMContext = data.get("state")
            if state:
                try:
                    current_st = await state.get_state()
                    if current_st:
                        logger.debug(f"Clearing state {current_st} for user {user_id} on nav callback {callback_data}")
                        await state.clear()
                except Exception as e:
                    logger.debug(f"Error checking/clearing state: {e}")

        # 4. Serialize callbacks from the same user using per-user async lock
        # This completely prevents race conditions and overlapping database/UI mutations
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
        lock = self._user_locks[user_id]

        async with lock:
            return await handler(event, data)
