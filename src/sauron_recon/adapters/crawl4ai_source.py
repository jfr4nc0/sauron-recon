from __future__ import annotations

import urllib.robotparser
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from sauron_recon.domain.models import Listing, SearchCriteria

from .detail_parser import PageKind, extract_detail_links, listing_from_detail, parse_detail
from .resilience import CircuitBreaker, RateLimiter


class CrawlClient(Protocol):
    def scrape(self, url: str) -> dict: ...


def _dynamic_page_kind(url: str) -> PageKind:
    path = urlsplit(url).path.strip("/").lower()
    if not path or path in {"buscar", "busqueda", "propiedades", "inmuebles"}:
        return PageKind.CATEGORY
    if re.search(r"(?:/|[-_])(?:\d{5,}|[a-z0-9]{16,})(?:\.html?)?$", path):
        return PageKind.DETAIL
    return PageKind.CATEGORY if any(item in path.split("/") for item in ("alquiler", "venta", "locales", "propiedades")) else PageKind.DETAIL


@dataclass
class Crawl4AIDynamicSource:
    """Crawl explicitly supplied public search URLs with robots enforcement."""

    client: CrawlClient
    name: str
    allowed_domains: tuple[str, ...]
    search_url_builder: Callable[[SearchCriteria], str]
    max_detail_pages: int = 5
    user_agent: str = "SauronRecon/0.1 (+public-source-audit)"
    rate_limiter: RateLimiter = field(default_factory=lambda: RateLimiter(min_interval_seconds=0.5))
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    robots_checker: Callable[[str], bool] | None = None
    last_warnings: list[str] = field(default_factory=list, init=False)

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        self.last_warnings.clear()
        search_url = self.search_url_builder(criteria)
        if not self._allowed(search_url) or not self._robots_allowed(search_url):
            self.last_warnings.append(f"source_url_not_allowed:{search_url}")
            return []
        markdown = self._scrape(search_url)
        if not markdown:
            return []
        links = extract_detail_links(markdown, self.allowed_domains, self.max_detail_pages, _dynamic_page_kind)
        if not links:
            self.last_warnings.append(f"category_without_detail_links:{search_url}")
            return []
        listings: list[Listing] = []
        for url in links:
            if not self._robots_allowed(url):
                self.last_warnings.append(f"detail_not_allowed:{url}")
                continue
            detail = self._scrape(url)
            if not detail:
                continue
            parsed = parse_detail(detail, fallback_title="Listing sin título", url=url)
            if parsed.operation is None and criteria.operation != "rent_or_sale":
                from dataclasses import replace
                parsed = replace(parsed, operation=criteria.operation)
            listings.append(listing_from_detail(self.name, url, parsed, detail))
        return listings

    def _scrape(self, url: str) -> str | None:
        try:
            self.circuit_breaker.before_call()
            self.rate_limiter.wait()
            payload = self.client.scrape(url)
            self.circuit_breaker.record_success()
            return str((payload.get("data") or {}).get("markdown") or "")
        except Exception as exc:
            self.circuit_breaker.record_failure()
            self.last_warnings.append(f"{url}: {type(exc).__name__}")
            return None

    def _allowed(self, url: str) -> bool:
        host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    def _robots_allowed(self, url: str) -> bool:
        if self.robots_checker is not None:
            return self.robots_checker(url)
        parsed = urlsplit(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            request = Request(robots_url, headers={"User-Agent": self.user_agent})
            with urlopen(request, timeout=15) as response:
                content = response.read().decode("utf-8", "ignore")
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(content.splitlines())
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return False
