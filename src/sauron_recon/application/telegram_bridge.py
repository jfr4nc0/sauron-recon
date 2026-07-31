from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from sauron_recon.domain.models import SearchCriteria

from .connectors import ConnectorSetupWizard
from .source_registry import SourceCapabilityRegistry
from .wizard import RequirementsWizard, WizardStep


_CRITERIA_FIELDS = (
    "operation",
    "zones",
    "min_price",
    "max_price",
    "currency",
    "min_area_m2",
    "max_area_m2",
    "property_type",
    "rooms",
    "bathrooms",
    "min_price_ars",
    "max_price_ars",
    "min_price_usd",
    "max_price_usd",
    "needs_three_phase",
    "locality",
    "requirements",
)


@dataclass(frozen=True)
class WizardEvent:
    platform: str
    user_id: str | None
    chat_id: str | None
    chat_type: str | None
    thread_id: str | None
    text: str


class TelegramWizardBridge:
    """Bridge Telegram gateway messages to the deterministic requirements wizard.

    The bridge deliberately handles only Telegram messages from an explicitly
    allowlisted user or chat. It persists active sessions and confirmed
    criteria in runtime state, never in the knowledge vault.
    """

    def __init__(self, state_path: str | Path | None = None) -> None:
        self.state_path = Path(state_path or self._default_state_path()).expanduser()
        self._lock = threading.RLock()

    @staticmethod
    def _default_state_path() -> Path:
        data_dir = Path(os.getenv("SAURON_RECON_DATA_DIR", "./runtime")).expanduser()
        if not data_dir.is_absolute():
            data_dir = Path(os.getenv("HERMES_HOME", Path.cwd())) / data_dir
        return data_dir / "telegram-wizard.json"

    def handle(self, event: WizardEvent) -> dict[str, str] | None:
        if event.platform.lower() != "telegram" or not event.chat_id:
            return None
        if not self._authorized(event):
            return None

        command, args = self._parse_command(event.text)
        key = self._session_key(event)
        with self._lock:
            state = self._load()
            active = state.get("active", {})
            setups = state.setdefault("setup", {})

            if command == "start":
                wizard = RequirementsWizard()
                reply = wizard.start()
                active[key] = self._serialize_wizard(wizard)
                state["active"] = active
                self._save(state)
                return self._handled(reply.text)

            if command == "setup":
                setup = ConnectorSetupWizard()
                setups[key] = {"target": setup.target, "step": setup.step}
                state["setup"] = setups
                self._save(state)
                return self._handled(setup.start())

            if command == "sources":
                lines = ["Estado de fuentes configuradas:"]
                for source in SourceCapabilityRegistry.all():
                    lines.append(f"- {source.name}: {source.status.value} ({', '.join(mode.value for mode in source.modes)})")
                return self._handled("\n".join(lines))

            if command == "cancel" and (key in active or key in setups):
                active.pop(key, None)
                setups.pop(key, None)
                state["active"] = active
                state["setup"] = setups
                self._save(state)
                return self._handled("Cancelé la configuración de búsqueda.")

            if key in setups and not command:
                setup = self._restore_setup(setups[key])
                message, completed, connector = setup.receive(event.text)
                if completed:
                    setups.pop(key, None)
                    state["setup"] = setups
                    if connector is not None:
                        state.setdefault("connectors", {})[key] = connector
                else:
                    setups[key] = {"target": setup.target, "step": setup.step}
                    state["setup"] = setups
                self._save(state)
                return self._handled(message)

            if key not in active or command:
                return None

            wizard = self._restore_wizard(active[key])
            reply = wizard.receive(event.text)
            if reply.completed:
                active.pop(key, None)
                state["active"] = active
                if reply.criteria is not None:
                    state.setdefault("confirmed", {})[key] = self._serialize_criteria(reply.criteria)
            else:
                active[key] = self._serialize_wizard(wizard)
                state["active"] = active
            self._save(state)
            return self._handled(reply.text)

    @staticmethod
    def _handled(message: str) -> dict[str, str]:
        return {"action": "skip", "reason": "sauron-telegram-wizard", "reply": message}

    @staticmethod
    def _parse_command(text: str) -> tuple[str | None, str]:
        stripped = text.strip()
        if not stripped.startswith("/"):
            return None, ""
        command, _, args = stripped[1:].partition(" ")
        command = command.split("@", 1)[0].lower()
        return command, args.strip()

    @staticmethod
    def _session_key(event: WizardEvent) -> str:
        return ":".join(
            (
                event.platform.lower(),
                event.chat_type or "unknown",
                event.chat_id or "unknown",
                event.thread_id or "",
            )
        )

    @staticmethod
    def _authorized(event: WizardEvent) -> bool:
        allowed_users = {
            value.strip()
            for value in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
            if value.strip()
        }
        allowed_chats = {
            value.strip()
            for variable in ("TELEGRAM_ALLOWED_CHATS", "TELEGRAM_GROUP_ALLOWED_CHATS")
            for value in os.getenv(variable, "").split(",")
            if value.strip()
        }
        return bool(
            (event.user_id and str(event.user_id) in allowed_users)
            or (event.chat_id and str(event.chat_id) in allowed_chats)
        )

    @staticmethod
    def _serialize_decimal(value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    @classmethod
    def _serialize_criteria(cls, criteria: SearchCriteria) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in _CRITERIA_FIELDS:
            value = getattr(criteria, field)
            if isinstance(value, Decimal):
                value = cls._serialize_decimal(value)
            elif isinstance(value, tuple):
                value = list(value)
            result[field] = value
        return result

    @classmethod
    def _deserialize_criteria(cls, payload: dict[str, Any]) -> SearchCriteria:
        decimal_fields = {
            "min_price",
            "max_price",
            "min_area_m2",
            "max_area_m2",
            "min_price_ars",
            "max_price_ars",
            "min_price_usd",
            "max_price_usd",
        }
        values: dict[str, Any] = {}
        for field in _CRITERIA_FIELDS:
            value = payload.get(field)
            if field in decimal_fields and value is not None:
                value = Decimal(str(value))
            elif field in {"zones", "requirements"}:
                value = tuple(value or ())
            values[field] = value
        return SearchCriteria(**values)

    @classmethod
    def _serialize_wizard(cls, wizard: RequirementsWizard) -> dict[str, Any]:
        return {
            "step": wizard.step.value,
            "criteria": cls._serialize_criteria(wizard.criteria),
        }

    @classmethod
    def _restore_wizard(cls, payload: dict[str, Any]) -> RequirementsWizard:
        wizard = RequirementsWizard()
        wizard.criteria = cls._deserialize_criteria(payload.get("criteria", {}))
        wizard.step = WizardStep(payload.get("step", WizardStep.OPERATION.value))
        return wizard

    @staticmethod
    def _restore_setup(payload: dict[str, Any]) -> ConnectorSetupWizard:
        setup = ConnectorSetupWizard(target=str(payload.get("target", "mercadolibre")))
        setup.step = str(payload.get("step", "provider"))
        return setup

    def _load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {"active": {}, "confirmed": {}}
        except (FileNotFoundError, json.JSONDecodeError):
            return {"active": {}, "confirmed": {}}

    def _save(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)
