import json

from sauron_recon.adapters.firecrawl_client import FirecrawlClient
from sauron_recon.adapters.firecrawl_source import FirecrawlSource
from sauron_recon.adapters.resilience import CircuitBreaker, RateLimiter
from sauron_recon.domain.models import SearchCriteria


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_detail_failure_does_not_drop_other_listings():
    def opener(request, timeout):
        if request.full_url.endswith("/v1/search"):
            return Response({"success": True, "data": [
                {"url": "https://zonaprop.com.ar/propiedades/clasificado/alcllcin-local-a-1.html", "title": "A", "description": "USD 1"},
                {"url": "https://zonaprop.com.ar/propiedades/clasificado/alcllcin-local-b-2.html", "title": "B", "description": "USD 2"},
            ]})
        raise RuntimeError("detail unavailable")

    source = FirecrawlSource(
        FirecrawlClient("http://firecrawl", opener=opener, sleeper=lambda _: None),
        scrape_details=True,
        rate_limiter=RateLimiter(sleeper=lambda _: None),
        circuit_breaker=CircuitBreaker(failure_threshold=5),
    )
    listings = source.search(SearchCriteria())
    assert [listing.title for listing in listings] == ["A", "B"]
    assert len(source.last_warnings) == 2
