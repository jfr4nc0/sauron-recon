from __future__ import annotations

from sauron_recon.domain.models import SearchCriteria

from .firecrawl_client import FirecrawlClient
from .firecrawl_source import FirecrawlSource


def _portal_query(criteria: SearchCriteria, domain: str, extra: str = "") -> str:
    operation = {"rent": "alquiler", "sale": "venta", "rent_or_sale": "alquiler venta"}[criteria.operation]
    zones = " ".join(criteria.zones) if criteria.zones else "Argentina"
    suffix = f" {extra}" if extra else ""
    return f"site:{domain} locales comerciales {operation} {zones}{suffix}"


def _fallback_query(criteria: SearchCriteria, keyword: str) -> str:
    operation = {"rent": "alquiler", "sale": "venta", "rent_or_sale": "alquiler venta"}[criteria.operation]
    zones = " ".join(criteria.zones) if criteria.zones else "Argentina"
    return f"local comercial {operation} {zones} {keyword}"


class ZonapropSource(FirecrawlSource):
    def __init__(self, client: FirecrawlClient, **kwargs):
        super().__init__(
            client=client,
            name="zonaprop",
            allowed_domains=("zonaprop.com.ar",),
            query_builder=lambda criteria: _portal_query(criteria, "zonaprop.com.ar"),
            fallback_builders=(lambda criteria: _fallback_query(criteria, "Zonaprop"),),
            **kwargs,
        )


class ArgenpropSource(FirecrawlSource):
    def __init__(self, client: FirecrawlClient, **kwargs):
        super().__init__(
            client=client,
            name="argenprop",
            allowed_domains=("argenprop.com",),
            query_builder=lambda criteria: _portal_query(criteria, "argenprop.com"),
            fallback_builders=(lambda criteria: _fallback_query(criteria, "Argenprop"),),
            **kwargs,
        )


class MercadoLibreSource(FirecrawlSource):
    def __init__(self, client: FirecrawlClient, **kwargs):
        super().__init__(
            client=client,
            name="mercadolibre",
            allowed_domains=("inmuebles.mercadolibre.com.ar", "mercadolibre.com.ar"),
            query_builder=lambda criteria: _portal_query(criteria, "inmuebles.mercadolibre.com.ar", "mercadolibre inmuebles"),
            fallback_builders=(lambda criteria: _fallback_query(criteria, "mercadolibre inmuebles"),),
            **kwargs,
        )


class InmobiliariaSource(FirecrawlSource):
    """Configurable adapter for a permitted individual real-estate domain."""

    def __init__(self, client: FirecrawlClient, domain: str, name: str | None = None, **kwargs):
        normalized = domain.lower().removeprefix("www.")
        super().__init__(
            client=client,
            name=name or normalized,
            allowed_domains=(normalized,),
            query_builder=lambda criteria: _portal_query(criteria, normalized),
            **kwargs,
        )


def build_portal_sources(client: FirecrawlClient, selected: tuple[str, ...], **kwargs) -> tuple[FirecrawlSource, ...]:
    factories = {
        "zonaprop": ZonapropSource,
        "argenprop": ArgenpropSource,
        "mercadolibre": MercadoLibreSource,
    }
    sources = []
    for name in selected:
        factory = factories.get(name)
        if factory is None:
            raise ValueError(f"unknown portal source: {name}")
        sources.append(factory(client, **kwargs))
    return tuple(sources)
