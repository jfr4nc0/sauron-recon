from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from urllib.parse import urlsplit

from sauron_recon.domain.models import Listing, SearchCriteria

from .detail_parser import PageKind, classify_url, extract_detail_links, listing_from_detail, parse_detail
from .firecrawl_client import FirecrawlClient
from .resilience import CircuitBreaker, RateLimiter


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
    max_detail_pages: int = 5
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
            kind = classify_url(url)
            if kind is PageKind.CATEGORY:
                if not self.scrape_details:
                    self.last_warnings.append(f"category_skipped:{url}")
                    continue
                listings.extend(self._expand_category(url, result, criteria))
                continue
            if kind is PageKind.UNKNOWN:
                self.last_warnings.append(f"unknown_page_kind:{url}")
                continue
            listings.append(self._parse_result(url, result, criteria))
        return listings

    def _parse_result(self, url: str, result: dict, criteria: SearchCriteria) -> Listing:
        title = str(result.get("title") or "Listing sin título").strip()
        markdown = str(result.get("description") or "").strip()
        if self.scrape_details:
            scraped = self._scrape_markdown(url)
            if scraped is not None:
                markdown = scraped
        parsed = parse_detail(markdown, fallback_title=title)
        if parsed.operation is None and criteria.operation != "rent_or_sale":
            parsed = parsed.__class__(parsed.title, criteria.operation, parsed.price, parsed.currency, parsed.area_m2, parsed.address)
        return listing_from_detail(self.name, url, parsed, markdown)

    def _expand_category(self, url: str, result: dict, criteria: SearchCriteria) -> list[Listing]:
        markdown = self._scrape_markdown(url)
        if markdown is None:
            return []
        links = extract_detail_links(markdown, self.allowed_domains, self.max_detail_pages)
        if not links:
            self.last_warnings.append(f"category_without_detail_links:{url}")
            return []
        listings: list[Listing] = []
        for detail_url in links:
            detail_markdown = self._scrape_markdown(detail_url)
            if detail_markdown is None:
                continue
            parsed = parse_detail(detail_markdown, fallback_title=str(result.get("title") or "Listing sin título"))
            if parsed.operation is None and criteria.operation != "rent_or_sale":
                parsed = parsed.__class__(parsed.title, criteria.operation, parsed.price, parsed.currency, parsed.area_m2, parsed.address)
            listings.append(listing_from_detail(self.name, detail_url, parsed, detail_markdown))
        return listings

    def _scrape_markdown(self, url: str) -> str | None:
        try:
            self.circuit_breaker.before_call()
            self.rate_limiter.wait()
            details = self.client.scrape(url).get("data", {}) or {}
            self.circuit_breaker.record_success()
            markdown = details.get("markdown")
            return str(markdown) if markdown else None
        except Exception as exc:
            self.circuit_breaker.record_failure()
            self.last_warnings.append(f"{url}: {type(exc).__name__}: {exc}")
            return None

    def _allowed(self, url: str) -> bool:
        hostname = (urlsplit(url).hostname or "").lower().removeprefix("www.")
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in self.allowed_domains)
