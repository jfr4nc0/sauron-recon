from sauron_recon.adapters.crawl4ai_source import Crawl4AIDynamicSource
from sauron_recon.domain.models import SearchCriteria


class FakeCrawl4AI:
    def __init__(self):
        self.urls = []

    def scrape(self, url):
        self.urls.append(url)
        if url.endswith("/buscar"):
            return {"data": {"markdown": "[Local](https://example.com/local-en-alquiler-123456)"}}
        return {"data": {"markdown": "# Local en alquiler\nUSD 1200\n80 m2\nDisponible"}}


def test_crawl4ai_source_requires_robots_permission_and_extracts_detail():
    client = FakeCrawl4AI()
    source = Crawl4AIDynamicSource(
        client=client,
        name="crawl4ai:example.com",
        allowed_domains=("example.com",),
        search_url_builder=lambda _: "https://example.com/buscar",
        robots_checker=lambda url: True,
    )

    listings = source.search(SearchCriteria(operation="rent"))

    assert len(listings) == 1
    assert listings[0].price == 1200
    assert listings[0].area_m2 == 80
    assert client.urls == [
        "https://example.com/buscar",
        "https://example.com/local-en-alquiler-123456",
    ]


def test_crawl4ai_source_fails_closed_when_robots_denies():
    client = FakeCrawl4AI()
    source = Crawl4AIDynamicSource(
        client=client,
        name="crawl4ai:example.com",
        allowed_domains=("example.com",),
        search_url_builder=lambda _: "https://example.com/buscar",
        robots_checker=lambda url: False,
    )

    assert source.search(SearchCriteria(operation="rent")) == []
    assert client.urls == []
