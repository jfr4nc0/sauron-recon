import json
from urllib.error import HTTPError

import pytest

from sauron_recon.adapters.firecrawl_client import FirecrawlClient, FirecrawlError
from sauron_recon.adapters.firecrawl_source import FirecrawlSource
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


def test_firecrawl_source_filters_domains_and_maps_search_results():
    def opener(request, timeout):
        return Response({"success": True, "data": [
            {"url": "https://www.zonaprop.com.ar/propiedades/clasificado/alcllcin-local-en-alquiler-59131762.html", "title": "Local", "description": "USD 1.200, 80 m2"},
            {"url": "https://example.org/not-allowed", "title": "No", "description": "USD 1"},
        ]})

    client = FirecrawlClient("http://firecrawl", opener=opener, sleeper=lambda _: None)
    listings = FirecrawlSource(client).search(SearchCriteria(zones=("Palermo",)))
    assert len(listings) == 1
    assert listings[0].price == 1200
    assert listings[0].area_m2 == 80


def test_firecrawl_client_retries_transient_http_errors():
    attempts = 0

    def opener(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise HTTPError(request.full_url, 503, "busy", {}, None)
        return Response({"success": True, "data": []})

    client = FirecrawlClient("http://firecrawl", opener=opener, sleeper=lambda _: None)
    assert client.search("local") == []
    assert attempts == 3


def test_firecrawl_client_rejects_invalid_base_url():
    with pytest.raises(ValueError):
        FirecrawlClient("file:///tmp/firecrawl")
