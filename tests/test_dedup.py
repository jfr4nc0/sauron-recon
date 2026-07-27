from decimal import Decimal

from sauron_recon.domain.dedup import find_duplicate_candidates
from sauron_recon.domain.models import Listing


def listing(source, title, address, area):
    return Listing(source=source, url=f"https://{source}.example/{title.replace(' ', '-')}", title=title,
                   address=address, area_m2=Decimal(str(area)))


def test_cross_source_duplicates_are_candidates_not_merged():
    first = listing("zonaprop", "Local Palermo Serrano", "Serrano 1300, Palermo", 100)
    second = listing("argenprop", "Local Comercial Serrano Palermo", "Serrano 1300, Palermo", 100)
    candidates = find_duplicate_candidates((first, second))
    assert len(candidates) == 1
    assert "same_address" in candidates[0].reasons
    assert first.identity != second.identity


def test_different_sources_without_strong_evidence_are_not_candidates():
    first = listing("zonaprop", "Local Palermo", "Serrano 1300", 100)
    second = listing("mercadolibre", "Local Palermo", "Honduras 500", 100)
    assert find_duplicate_candidates((first, second)) == ()
