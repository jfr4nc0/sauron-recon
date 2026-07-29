from __future__ import annotations

import os
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


def register(ctx) -> None:
    ctx.register_hook("pre_gateway_dispatch", _handle_message)


def _handle_message(event, **_kwargs):
    source = getattr(event, "source", None)
    if source is None:
        return None
    result = _bridge.handle(
        WizardEvent(
            platform=getattr(getattr(source, "platform", None), "value", "") or "",
            user_id=_string_or_none(getattr(source, "user_id", None)),
            chat_id=_string_or_none(getattr(source, "chat_id", None)),
            chat_type=_string_or_none(getattr(source, "chat_type", None)),
            thread_id=_string_or_none(getattr(source, "thread_id", None)),
            text=str(getattr(event, "text", "") or ""),
        )
    )
    return result


def _string_or_none(value) -> str | None:
    return None if value is None else str(value)
