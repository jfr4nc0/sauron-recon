import sqlite3
from decimal import Decimal

from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.adapters.sqlite import SQLiteListingRepository
from sauron_recon.application.use_cases import SearchListings
from sauron_recon.domain.models import Listing, SearchCriteria


def test_sqlite_repository_is_idempotent(tmp_path):
    listing = Listing(
        source="fixture",
        url="https://example.com/l/1",
        title="Local",
        operation="rent",
        price=Decimal("1000"),
    )
    result = SearchListings((InMemorySource("fixture", [listing]),)).execute(SearchCriteria())
    repository = SQLiteListingRepository(tmp_path / "runtime" / "sauron.db")
    repository.save_run(result)
    repository.save_run(result)
    assert repository.count_runs() == 1
    assert repository.count_listings() == 1
    with sqlite3.connect(tmp_path / "runtime" / "sauron.db") as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
