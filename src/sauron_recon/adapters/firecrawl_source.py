from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from sauron_recon.domain.models import Listing, SearchCriteria

from .firecrawl_client import FirecrawlClient

_PRICE_RE = re.compile(r"(?:USD|US\$|U\$S|\$)\s*([\d.,]+)", re.IGNORECASE)
_AREA_RE = re.compile(r"([\d.,]+)\s*m(?:2|²)", re.IGNORECASE)


def _decimal(raw: str):
    cleaned = raw.replace(".", "").replace(",", ".")
    try:
        from decimal import Decimal
        return Decimal(cleaned)
    except Exception:
        return None


def criteria_query(criteria: SearchCriteria) -> str:
    operation = {"rent": "alquiler", "sale": "venta", "rent_or_sale": "alquiler venta"}[criteria.operation]
    zones = " ".join(criteria.zones) if criteria.zones else "Argentina"
    return f"local comercial {operation} {zones}"


@dataclass
class FirecrawlSource:
    client: FirecrawlClient
    name: str = "firecrawl"
    allowed_domains: tuple[str, ...] = (
        "mercadolibre.com.ar", "zonaprop.com.ar", "argenprop.com", "properati.com.ar"
    )
    max_results: int = 10
    scrape_details: bool = False

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        listings: list[Listing] = []
        for result in self.client.search(criteria_query(criteria), limit=self.max_results):
            url = result["url"]
            if not self._allowed(url):
                continue
            title = str(result.get("title") or "Listing sin título").strip()
            description = str(result.get("description") or "").strip()
            details = {}
            if self.scrape_details:
                details = self.client.scrape(url).get("data", {}) or {}
            markdown = str(details.get("markdown") or description)
            listings.append(Listing(
                source=self.name,
                url=url,
                title=title,
                operation=criteria.operation if criteria.operation != "rent_or_sale" else None,
                zone=criteria.zones[0] if criteria.zones else None,
                price=self._price(markdown),
                area_m2=self._area(markdown),
                raw={"description": description, "markdown": markdown[:4000]},
            ))
        return listings

    def _allowed(self, url: str) -> bool:
        hostname = (urlsplit(url).hostname or "").lower().removeprefix("www.")
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in self.allowed_domains)

    @staticmethod
    def _price(text: str):
        match = _PRICE_RE.search(text)
        return _decimal(match.group(1)) if match else None

    @staticmethod
    def _area(text: str):
        match = _AREA_RE.search(text)
        return _decimal(match.group(1)) if match else None
