from datetime import datetime, timezone
from decimal import Decimal

from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.application.use_cases import SearchListings
from sauron_recon.domain.models import Listing, SearchCriteria, canonical_url
from sauron_recon.domain.scoring import score_listing


def listing(**kwargs):
    return Listing(source="zonaprop", url="https://example.com/listing/1", title="Local comercial", **kwargs)


def test_canonical_url_removes_tracking_query_and_fragment():
    assert canonical_url("HTTPS://Example.COM/listing/1/?utm_source=x&foo=bar#contact") == "https://example.com/listing/1?foo=bar"


def test_search_isolates_source_failures_and_deduplicates():
    item = listing(operation="rent", zone="Palermo")
    result = SearchListings((
        InMemorySource("ok", [item, item]),
        InMemorySource("broken", error=TimeoutError("upstream timeout")),
    )).execute(SearchCriteria(operation="rent", zones=("Palermo",)))
    assert len(result.listings) == 1
    assert result.failures[0].source == "broken"
    assert result.failures[0].error_type == "TimeoutError"


def test_score_explains_matching_constraints():
    result = score_listing(
        listing(operation="rent", zone="Palermo", price=Decimal("1000"), area_m2=Decimal("80")),
        SearchCriteria(operation="rent", zones=("Palermo",), max_price=Decimal("1200"), min_area_m2=Decimal("60")),
    )
    assert result.hard_match is True
    assert result.value == 90
    assert "price within maximum" in result.reasons
    assert "area meets minimum" in result.reasons
