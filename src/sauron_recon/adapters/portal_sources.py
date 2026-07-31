from __future__ import annotations

import re
from urllib.parse import urlsplit

from sauron_recon.domain.models import SearchCriteria

from .detail_parser import PageKind
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


def _generic_portal_page_kind(url: str) -> PageKind:
    """Conservative classifier for candidate portals with differing URL shapes."""
    path = urlsplit(url).path.strip("/").lower()
    if not path or path in {"propiedades", "busqueda", "buscar", "inmuebles"}:
        return PageKind.CATEGORY
    if re.search(r"(?:/|[-_])(?:\d{5,}|[a-z0-9]{16,})(?:\.html?)?$", path):
        return PageKind.DETAIL
    if any(segment in path.split("/") for segment in ("alquiler", "venta", "locales", "departamentos", "casas", "propiedades")):
        return PageKind.CATEGORY
    return PageKind.DETAIL


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
            url_classifier=_generic_portal_page_kind,
            **kwargs,
        )


_CANDIDATE_PORTALS = {
    "inmuebles-clarin": "inmuebles.clarin.com",
    "zetaprop": "zetaprop.com.ar",
    "inmoup": "inmoup.com.ar",
    "publiqueinmuebles": "publiqueinmuebles.com.ar",
    "icasas": "icasas.com.ar",
    "bullano": "bullano.com.ar",
    "servidos": "servidos.ar",
    "inmopro": "inmopro.com.ar",
    "buscadorprop": "buscadorprop.com.ar",
    "inmueblesenbaires": "inmueblesenbaires.com.ar",
    "izr": "izr.com.ar",
}


def build_portal_sources(client: FirecrawlClient, selected: tuple[str, ...], **kwargs) -> tuple[FirecrawlSource, ...]:
    factories = {
        "zonaprop": ZonapropSource,
        "argenprop": ArgenpropSource,
        "mercadolibre": MercadoLibreSource,
    }
    sources = []
    for name in selected:
        factory = factories.get(name)
        if factory is not None:
            sources.append(factory(client, **kwargs))
            continue
        domain = _CANDIDATE_PORTALS.get(name)
        if domain is None:
            raise ValueError(f"unknown portal source: {name}")
        sources.append(InmobiliariaSource(client, domain=domain, name=name, **kwargs))
    return tuple(sources)
