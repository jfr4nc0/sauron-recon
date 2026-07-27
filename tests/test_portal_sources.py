import json

from sauron_recon.adapters.firecrawl_client import FirecrawlClient
from sauron_recon.adapters.portal_sources import ArgenpropSource, MercadoLibreSource, ZonapropSource, build_portal_sources
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


def test_portal_adapters_have_isolated_domains_and_queries():
    requests = []

    def opener(request, timeout):
        payload = json.loads(request.data)
        requests.append(payload)
        query = payload["query"]
        domain = "zonaprop.com.ar" if "zonaprop" in query else "argenprop.com" if "argenprop" in query else "inmuebles.mercadolibre.com.ar"
        return Response({"success": True, "data": [{"url": f"https://{domain}/l/1", "title": "Local"}]})

    client = FirecrawlClient("http://firecrawl", opener=opener, sleeper=lambda _: None)
    criteria = SearchCriteria(zones=("Palermo",))
    sources = [ZonapropSource(client), ArgenpropSource(client), MercadoLibreSource(client)]
    for source in sources:
        assert len(source.search(criteria)) == 1

    assert requests[0]["query"].startswith("site:zonaprop.com.ar")
    assert requests[1]["query"].startswith("site:argenprop.com")
    assert requests[2]["query"].startswith("site:inmuebles.mercadolibre.com.ar")
    assert sources[0].allowed_domains == ("zonaprop.com.ar",)
    assert sources[1].allowed_domains == ("argenprop.com",)
    assert "inmuebles.mercadolibre.com.ar" in sources[2].allowed_domains


def test_factory_rejects_unknown_portal():
    client = FirecrawlClient("http://firecrawl", opener=lambda *args, **kwargs: Response({"success": True, "data": []}))
    try:
        build_portal_sources(client, ("unknown",))
    except ValueError as exc:
        assert "unknown portal source" in str(exc)
    else:
        raise AssertionError("unknown source was accepted")
