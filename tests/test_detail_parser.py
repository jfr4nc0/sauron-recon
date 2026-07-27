from decimal import Decimal

from sauron_recon.adapters.detail_parser import PageKind, classify_url, extract_detail_links, parse_detail


def test_classifies_category_and_detail_urls():
    assert classify_url("https://www.zonaprop.com.ar/locales-comerciales-alquiler-palermo.html") is PageKind.CATEGORY
    assert classify_url("https://www.zonaprop.com.ar/propiedades/clasificado/alcllcin-local-en-alquiler-59131762.html") is PageKind.DETAIL
    assert classify_url("https://www.argenprop.com/locales/alquiler/palermo") is PageKind.CATEGORY
    assert classify_url("https://www.argenprop.com/local-en-alquiler-en-palermo--20056658") is PageKind.DETAIL
    assert classify_url("https://inmuebles.mercadolibre.com.ar/locales/alquiler/capital-federal/palermo/") is PageKind.CATEGORY
    assert classify_url("https://inmueble.mercadolibre.com.ar/MLA-1846955251-local-en-alquiler") is PageKind.DETAIL


def test_parses_argentine_price_currency_and_area():
    parsed = parse_detail("# Local en Alquiler en Palermo\nalquiler $ 16.500.000\n* 660 m² tot.\n* 625 m² cub.")
    assert parsed.title == "Local en Alquiler en Palermo"
    assert parsed.operation == "rent"
    assert parsed.price == Decimal("16500000")
    assert parsed.currency == "ARS"
    assert parsed.area_m2 == Decimal("660")


def test_extracts_only_detail_links_from_category_markdown():
    markdown = """
    [Categoría](https://www.zonaprop.com.ar/locales-comerciales-alquiler-palermo.html)
    [Aviso](https://www.zonaprop.com.ar/propiedades/clasificado/alcllcin-local-59131762.html?x=1)
    [Otro](https://example.com/not-allowed)
    """
    assert extract_detail_links(markdown, ("zonaprop.com.ar",), 5) == (
        "https://www.zonaprop.com.ar/propiedades/clasificado/alcllcin-local-59131762.html?x=1",
    )
