from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SourceMode(StrEnum):
    API = "api"
    AUTHORIZED_FEED = "feed_authorized"
    PUBLIC_FIRECRAWL = "public_firecrawl"
    MANUAL_IMPORT = "manual_import"
    DISABLED = "disabled"


class SourceStatus(StrEnum):
    ENABLED = "enabled"
    CANDIDATE = "candidate"
    PARTIAL = "partial"
    PENDING_AUTHORIZATION = "pending_authorization"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SourceCapability:
    name: str
    domains: tuple[str, ...]
    modes: tuple[SourceMode, ...]
    status: SourceStatus
    geography: str
    categories: tuple[str, ...]
    operations: tuple[str, ...]
    details: bool
    pagination: bool
    reason: str


_CAPABILITIES: tuple[SourceCapability, ...] = (
    SourceCapability(
        "zonaprop", ("zonaprop.com.ar",), (SourceMode.PUBLIC_FIRECRAWL,), SourceStatus.ENABLED,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno"), ("rent", "sale"),
        True, True, "Adapter Firecrawl existente; cobertura debe validarse por corrida.",
    ),
    SourceCapability(
        "argenprop", ("argenprop.com",), (SourceMode.PUBLIC_FIRECRAWL,), SourceStatus.PARTIAL,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno"), ("rent", "sale"),
        True, True, "Adapter existente con fallas parciales de detalle observadas.",
    ),
    SourceCapability(
        "mercadolibre", ("mercadolibre.com.ar",), (SourceMode.API,), SourceStatus.PENDING_AUTHORIZATION,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno"), ("rent", "sale"),
        True, True, "Requiere API oficial OAuth; no usar scraping como sustituto.",
    ),
    SourceCapability(
        "inmuebles-clarin", ("inmuebles.clarin.com",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno"), ("rent", "sale"),
        True, True, "Spike Firecrawl exitoso con búsqueda y fichas públicas; falta validar términos y normalización.",
    ),
    SourceCapability(
        "zetaprop", ("zetaprop.com.ar",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "terreno"), ("rent", "sale"),
        True, True, "Búsqueda y fichas públicas observadas; falta spike completo.",
    ),
    SourceCapability(
        "inmoup", ("inmoup.com.ar",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "terreno"), ("rent", "sale"),
        True, True, "URLs públicas multi-provincia observadas; falta validar filtros y detalle.",
    ),
    SourceCapability(
        "publiqueinmuebles", ("publiqueinmuebles.com.ar",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno", "galpon"), ("rent", "sale"),
        True, True, "Categorías nacionales públicas observadas; respetar rutas permitidas por robots.",
    ),
    SourceCapability(
        "icasas", ("icasas.com.ar",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "terreno"), ("rent", "sale"),
        True, True, "Agregador con rutas públicas; requiere control fuerte de duplicados.",
    ),
    SourceCapability(
        "bullano", ("bullano.com.ar",), (SourceMode.PUBLIC_FIRECRAWL, SourceMode.AUTHORIZED_FEED), SourceStatus.CANDIDATE,
        "Argentina", ("local", "departamento", "casa", "terreno"), ("rent", "sale"),
        True, True, "Acceso público observado; falta confirmar locales y cobertura provincial.",
    ),
    SourceCapability(
        "servidos", ("servidos.ar",), (SourceMode.DISABLED,), SourceStatus.BLOCKED,
        "Argentina", ("local", "departamento", "casa", "oficina", "terreno", "galpon"), ("rent", "sale"),
        False, False, "Sitio nuevo sin inventario real: 0 anuncios en todas las categorías verificadas.",
    ),
    SourceCapability(
        "facebook-marketplace", ("facebook.com",), (SourceMode.DISABLED,), SourceStatus.BLOCKED,
        "Argentina", (), (), False, False, "Login requerido y recolección automatizada prohibida sin autorización expresa.",
    ),
)


class SourceCapabilityRegistry:
    @classmethod
    def all(cls) -> tuple[SourceCapability, ...]:
        return _CAPABILITIES

    @classmethod
    def get(cls, name: str) -> SourceCapability | None:
        normalized = name.strip().lower().replace("_", "-")
        return next((item for item in _CAPABILITIES if item.name == normalized), None)

    @classmethod
    def selectable(cls) -> tuple[SourceCapability, ...]:
        return tuple(item for item in _CAPABILITIES if item.status is not SourceStatus.BLOCKED)

    @classmethod
    def enabled(cls) -> tuple[SourceCapability, ...]:
        return tuple(item for item in _CAPABILITIES if item.status is SourceStatus.ENABLED)
