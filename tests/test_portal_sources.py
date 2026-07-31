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
        path = {
            "zonaprop.com.ar": "/propiedades/clasificado/alcllcin-local-59131762.html",
            "argenprop.com": "/local-en-alquiler-en-palermo--20056658",
            "inmuebles.mercadolibre.com.ar": "/inmueble.mercadolibre.com.ar/MLA-1846955251-local-en-alquiler-en-soler-y-coronel-diaz-_JM",
        }[domain]
        return Response({"success": True, "data": [{"url": (
            "https://inmueble.mercadolibre.com.ar/MLA-1846955251-local-en-alquiler-en-soler-y-coronel-diaz-_JM"
            if domain.startswith("inmuebles") else f"https://{domain}{path}"
        ), "title": "Local"}]})

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


def test_candidate_portals_build_as_domain_allowlisted_sources():
    client = FirecrawlClient("http://firecrawl")
    sources = build_portal_sources(client, ("inmuebles-clarin", "zetaprop", "servidos"))

    assert [source.name for source in sources] == ["inmuebles-clarin", "zetaprop", "servidos"]
    assert sources[0].allowed_domains == ("inmuebles.clarin.com",)
    assert sources[1].allowed_domains == ("zetaprop.com.ar",)


def test_blocked_or_unknown_sources_are_not_silently_added():
    client = FirecrawlClient("http://firecrawl")

    try:
        build_portal_sources(client, ("facebook-marketplace",))
    except ValueError as exc:
        assert "unknown portal source" in str(exc)
    else:
        raise AssertionError("blocked source must not be silently enabled")
