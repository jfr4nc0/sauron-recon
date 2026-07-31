import json
from decimal import Decimal

from sauron_recon.adapters.feed_source import FeedSource
from sauron_recon.domain.models import SearchCriteria


def test_json_feed_normalizes_and_filters_listings(tmp_path):
    path = tmp_path / "feed.json"
    path.write_text(json.dumps({"listings": [
        {"id": "a1", "url": "https://example.org/a1", "titulo": "Local Palermo", "operacion": "alquiler", "zona": "Palermo", "precio": "USD 1200", "superficie": "80 m2"},
        {"id": "a2", "url": "https://example.org/a2", "titulo": "Local Córdoba", "operacion": "venta", "zona": "Córdoba", "precio": "100000", "superficie": "60"},
    ]}), encoding="utf-8")

    listings = FeedSource(path, name="partner-feed").search(
        SearchCriteria(operation="rent", zones=("Palermo",), min_area_m2=Decimal("70"))
    )

    assert len(listings) == 1
    assert listings[0].source == "partner-feed"
    assert listings[0].price == 1200
    assert listings[0].currency == "USD"
    assert listings[0].area_m2 == 80


def test_csv_feed_requires_url_and_title(tmp_path):
    path = tmp_path / "feed.csv"
    path.write_text("url,title\nhttps://example.org/1,Local\n", encoding="utf-8")

    listings = FeedSource(path).search(SearchCriteria())

    assert listings[0].title == "Local"
