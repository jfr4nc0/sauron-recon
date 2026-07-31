from decimal import Decimal

from sauron_recon.application.telegram_bridge import TelegramWizardBridge, WizardEvent
from sauron_recon.application.wizard import WizardStep


def _event(text: str, *, thread_id: str | None = None) -> WizardEvent:
    return WizardEvent(
        platform="telegram",
        user_id="42",
        chat_id="-100123",
        chat_type="group",
        thread_id=thread_id,
        text=text,
    )


def test_bridge_handles_start_and_persists_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "42")
    bridge = TelegramWizardBridge(tmp_path / "wizard.json")

    reply = bridge.handle(_event("/start@SauronBot", thread_id="7"))

    assert reply is not None
    assert reply["action"] == "skip"
    assert "comprar" in reply["reply"]
    assert (tmp_path / "wizard.json").exists()

    restored = TelegramWizardBridge(tmp_path / "wizard.json")
    next_reply = restored.handle(_event("alquilar", thread_id="7"))
    assert next_reply is not None
    assert "Qué querés buscar" in next_reply["reply"]


def test_bridge_keeps_topic_sessions_separate(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "42")
    bridge = TelegramWizardBridge(tmp_path / "wizard.json")

    bridge.handle(_event("/start", thread_id="1"))
    bridge.handle(_event("/start", thread_id="2"))
    bridge.handle(_event("comprar", thread_id="1"))

    state = (tmp_path / "wizard.json").read_text(encoding="utf-8")
    assert '"telegram:group:-100123:1"' in state
    assert '"telegram:group:-100123:2"' in state


def test_bridge_confirms_criteria_and_removes_active_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "42")
    bridge = TelegramWizardBridge(tmp_path / "wizard.json")
    bridge.handle(_event("/start"))
    for answer in (
        "alquilar",
        "local",
        "cualquiera",
        "cualquiera",
        "80 a 150 m2",
        "no",
        "Palermo",
        "ARS 500000 a 900000",
        "sí",
    ):
        reply = bridge.handle(_event(answer))

    assert reply is not None
    assert reply["action"] == "skip"
    assert "confirmada" in reply["reply"]
    payload = (tmp_path / "wizard.json").read_text(encoding="utf-8")
    assert '"active": {}' in payload
    assert '"min_price_ars": "500000"' in payload


def test_bridge_does_not_bypass_authorization(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "99")
    bridge = TelegramWizardBridge(tmp_path / "wizard.json")

    assert bridge.handle(_event("/start")) is None
    assert not (tmp_path / "wizard.json").exists()


def test_bridge_setup_persists_connector_choice_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "42")
    bridge = TelegramWizardBridge(tmp_path / "wizard.json")

    reply = bridge.handle(_event("/setup"))
    assert reply is not None
    assert "Conectores disponibles" in reply["reply"]

    reply = bridge.handle(_event("2"))
    assert reply is not None
    assert "ngrok local" in reply["reply"]

    payload = (tmp_path / "wizard.json").read_text(encoding="utf-8")
    assert '"provider": "ngrok"' in payload
    assert "secret" not in payload.lower()
