from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConnectorProvider(StrEnum):
    LOCAL = "local"
    NGROK = "ngrok"
    CLOUDFLARE = "cloudflare"
    CUSTOM_DOMAIN = "custom_domain"
    MANUAL = "manual"


@dataclass(frozen=True)
class ConnectorOption:
    provider: ConnectorProvider
    label: str
    description: str
    self_hosted: bool
    external_service: bool


_OPTIONS: tuple[ConnectorOption, ...] = (
    ConnectorOption(
        ConnectorProvider.LOCAL,
        "Sólo local",
        "No habilita OAuth HTTPS externo; sirve para fuentes que no requieren callback.",
        True,
        False,
    ),
    ConnectorOption(
        ConnectorProvider.NGROK,
        "ngrok local",
        "El agente corre en tu máquina y ngrok publica sólo el callback HTTPS.",
        False,
        True,
    ),
    ConnectorOption(
        ConnectorProvider.CLOUDFLARE,
        "Cloudflare Tunnel local",
        "El agente corre en tu máquina y Cloudflare publica sólo el callback HTTPS.",
        False,
        True,
    ),
    ConnectorOption(
        ConnectorProvider.CUSTOM_DOMAIN,
        "Dominio HTTPS propio",
        "Usa un dominio y reverse proxy administrados por el usuario.",
        True,
        False,
    ),
    ConnectorOption(
        ConnectorProvider.MANUAL,
        "Configuración manual",
        "Para un callback HTTPS existente o una instalación avanzada.",
        True,
        False,
    ),
)


class ConnectorRegistry:
    """Registry safe to expose in setup flows; it never contains credentials."""

    @classmethod
    def options(cls) -> tuple[ConnectorOption, ...]:
        return _OPTIONS

    @classmethod
    def get(cls, provider: str) -> ConnectorOption | None:
        normalized = provider.strip().lower().replace("-", "_")
        aliases = {
            "1": ConnectorProvider.LOCAL,
            "2": ConnectorProvider.NGROK,
            "3": ConnectorProvider.CLOUDFLARE,
            "4": ConnectorProvider.CUSTOM_DOMAIN,
            "5": ConnectorProvider.MANUAL,
            "cloudflare_tunnel": ConnectorProvider.CLOUDFLARE,
            "custom": ConnectorProvider.CUSTOM_DOMAIN,
        }
        provider = aliases.get(normalized, normalized)
        return next((option for option in _OPTIONS if option.provider.value == provider), None)

    @classmethod
    def menu(cls) -> str:
        lines = ["Conectores disponibles para MercadoLibre OAuth:"]
        for index, option in enumerate(_OPTIONS, start=1):
            mode = "self-hosted" if option.self_hosted else "usa servicio externo"
            lines.append(f"{index}. {option.label} ({mode}) — {option.description}")
        return "\n".join(lines)


class ConnectorSetupWizard:
    """Small deterministic setup flow; secret acquisition stays outside Telegram."""

    def __init__(self, target: str = "mercadolibre") -> None:
        self.target = target
        self.step = "provider"

    def start(self) -> str:
        self.step = "provider"
        return f"Configuración de {self.target}.\n\n{ConnectorRegistry.menu()}\n\nRespondé con el número o nombre del conector."

    def receive(self, answer: str) -> tuple[str, bool, dict[str, str] | None]:
        if self.step != "provider":
            return "Este setup ya está completo. Usá /setup para comenzar otra configuración.", True, None
        option = ConnectorRegistry.get(answer)
        if option is None:
            return f"No reconocí ese conector.\n\n{ConnectorRegistry.menu()}", False, None
        self.step = "complete"
        payload = {
            "target": self.target,
            "provider": option.provider.value,
            "self_hosted": str(option.self_hosted).lower(),
            "external_service": str(option.external_service).lower(),
            "status": "selected",
        }
        next_step = (
            "La opción local no puede recibir el callback HTTPS de MercadoLibre por sí sola."
            if option.provider is ConnectorProvider.LOCAL
            else "El próximo paso es validar el endpoint HTTPS y completar OAuth; todavía no se guardaron secretos."
        )
        return f"Conector seleccionado: {option.label}.\n{next_step}", True, payload
