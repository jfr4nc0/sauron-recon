from decimal import Decimal

import pytest

from sauron_recon.application.pdf_reporting import render_pdf
from sauron_recon.application.ports import SearchResult
from sauron_recon.domain.changes import ListingChange
from sauron_recon.domain.models import Listing, utc_now


def test_render_pdf_is_deduplicated_and_readable(tmp_path):
    pytest.importorskip("reportlab")
    listing = Listing(source="fixture", url="https://example.com/1", title="Local Palermo", price=Decimal("1000"))
    result = SearchResult("run-1", utc_now(), (listing,), ())
    output = render_pdf(result, (ListingChange(listing, "new"), ListingChange(listing, "new")), tmp_path / "report.pdf")
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")
