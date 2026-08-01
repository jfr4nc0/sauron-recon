from __future__ import annotations

import os
import re
import sys
from pathlib import Path


# The distribution keeps the application package under <profile>/src while
# Hermes loads plugins from <profile>/plugins.
_profile_root = Path(os.getenv("HERMES_HOME", Path.cwd()))
_source_root = _profile_root / "src"
if _source_root.is_dir() and str(_source_root) not in sys.path:
    sys.path.insert(0, str(_source_root))

from sauron_recon.application.telegram_bridge import TelegramWizardBridge, WizardEvent


_bridge = TelegramWizardBridge()

# Commands that the wizard handles directly.
_WIZARD_COMMANDS = {"start", "setup", "sources", "cancel"}


def register(ctx) -> None:
    ctx.register_hook("pre_gateway_dispatch", _handle_message)


def _get_bot_username() -> str:
    """Read the bot username from env, without the @."""
    raw = os.getenv("TELEGRAM_BOT_USERNAME", "")
    return raw.lstrip("@").strip()


def _is_mentioned(text: str, bot_username: str) -> bool:
    """True if the text contains @bot_username or starts with a slash command."""
    if not text:
        return False
    stripped = text.strip()
    # Slash commands always count as a mention for wizard commands
    if stripped.startswith("/"):
        return True
    # @bot mention anywhere in text
    if bot_username:
        pattern = rf"@{re.escape(bot_username)}\b"
        if re.search(pattern, stripped, re.IGNORECASE):
            return True
    return False


def _handle_message(event, **_kwargs):
    source = getattr(event, "source", None)
    if source is None:
        return None

    text = str(getattr(event, "text", "") or "")
    chat_type = _string_or_none(getattr(source, "chat_type", None))

    # In groups: only respond when mentioned or when using a wizard command.
    # In private chats: always respond (the user explicitly messaged the bot).
    if chat_type and chat_type.lower() in ("group", "supergroup"):
        bot_username = _get_bot_username()
        if not _is_mentioned(text, bot_username):
            # Silently skip — do NOT let the agent process group chatter.
            return {"action": "skip", "reason": "sauron-telegram-not-mentioned", "reply": None}

    result = _bridge.handle(
        WizardEvent(
            platform=getattr(getattr(source, "platform", None), "value", "") or "",
            user_id=_string_or_none(getattr(source, "user_id", None)),
            chat_id=_string_or_none(getattr(source, "chat_id", None)),
            chat_type=_string_or_none(getattr(source, "chat_type", None)),
            thread_id=_string_or_none(getattr(source, "thread_id", None)),
            text=text,
        )
    )
    # If the bridge didn't handle it (non-wizard @mention), let the agent process it.
    return result


def _string_or_none(value) -> str | None:
    return None if value is None else str(value)
