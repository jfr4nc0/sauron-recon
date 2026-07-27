from sauron_recon.application.ports import SearchResult
from sauron_recon.application.reporting import render_report
from sauron_recon.domain.changes import ListingChange
from sauron_recon.domain.models import Listing


def test_report_is_spanish_friendly_and_includes_coverage():
    listing = Listing(source="zonaprop", url="https://zonaprop.com.ar/l/1", title="Local Palermo")
    result = SearchResult("run-1", listing.observed_at, (listing,), ())
    report = render_report(result, (ListingChange(listing, "new"),))
    assert "Listings nuevos o modificados" in report
    assert "zonaprop.com.ar/l/1" in report
    assert "Cobertura" in report
    assert "no se infieren" in report
