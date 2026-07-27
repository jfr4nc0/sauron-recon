from decimal import Decimal

from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.adapters.sqlite import SQLiteListingRepository
from sauron_recon.application.use_cases import SearchListings
from sauron_recon.domain.models import Listing, SearchCriteria


def result_for(items):
    return SearchListings((InMemorySource("complete-source", items),)).execute(SearchCriteria())


def test_disappearance_requires_explicit_complete_source(tmp_path):
    repo = SQLiteListingRepository(tmp_path / "sauron.db")
    item = Listing(source="complete-source", url="https://example.com/l/1", title="Local", price=Decimal("1000"))
    repo.save_run(result_for([item]))
    empty = result_for([])
    repo.save_run(empty)
    assert repo.mark_disappeared(empty, set()) == ()
    disappeared = repo.mark_disappeared(empty, {"complete-source"})
    assert len(disappeared) == 1
    assert disappeared[0].kind == "disappeared"
    assert disappeared[0].is_actionable is True
    assert repo.mark_disappeared(empty, {"complete-source"}) == ()
