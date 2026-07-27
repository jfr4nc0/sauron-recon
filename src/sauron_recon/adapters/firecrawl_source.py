from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from urllib.parse import urlsplit

from sauron_recon.domain.models import Listing, SearchCriteria

from .firecrawl_client import FirecrawlClient, FirecrawlError
from .resilience import CircuitBreaker, RateLimiter

_PRICE_RE = re.compile(r"(?:USD|US\$|U\$S|\$)\s*([\d.,]+)", re.IGNORECASE)
_AREA_RE = re.compile(r"([\d.,]+)\s*m(?:2|²)", re.IGNORECASE)


def _decimal(raw: str) -> Decimal | None:
    cleaned = raw.replace(".", "").replace(",", ".")
    try:
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
    rate_limiter: RateLimiter = field(default_factory=lambda: RateLimiter(min_interval_seconds=0.25))
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    query_builder: Callable[[SearchCriteria], str] | None = None
    fallback_builders: tuple[Callable[[SearchCriteria], str], ...] = ()
    snapshot_complete: bool = False
    last_warnings: list[str] = field(default_factory=list, init=False)

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        self.last_warnings.clear()
        self.circuit_breaker.before_call()
        try:
            builders = (self.query_builder or criteria_query, *self.fallback_builders)
            results = []
            for index, builder in enumerate(builders):
                self.rate_limiter.wait()
                results = self.client.search(builder(criteria), limit=self.max_results)
                if results or index == len(builders) - 1:
                    break
            self.circuit_breaker.record_success()
        except Exception:
            self.circuit_breaker.record_failure()
            raise

        listings: list[Listing] = []
        for result in results:
            url = result["url"]
            if not self._allowed(url):
                continue
            title = str(result.get("title") or "Listing sin título").strip()
            description = str(result.get("description") or "").strip()
            markdown = description
            if self.scrape_details:
                try:
                    self.circuit_breaker.before_call()
                    self.rate_limiter.wait()
                    details = self.client.scrape(url).get("data", {}) or {}
                    self.circuit_breaker.record_success()
                    markdown = str(details.get("markdown") or description)
                except Exception as exc:
                    self.circuit_breaker.record_failure()
                    self.last_warnings.append(f"{url}: {type(exc).__name__}: {exc}")
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
    def _price(text: str) -> Decimal | None:
        match = _PRICE_RE.search(text)
        return _decimal(match.group(1)) if match else None

    @staticmethod
    def _area(text: str) -> Decimal | None:
        match = _AREA_RE.search(text)
        return _decimal(match.group(1)) if match else None
