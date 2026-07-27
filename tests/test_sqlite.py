import sqlite3
from decimal import Decimal

from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.adapters.sqlite import SQLiteListingRepository
from sauron_recon.application.use_cases import SearchListings
from sauron_recon.domain.models import Listing, SearchCriteria


def run_for(item):
    return SearchListings((InMemorySource("fixture", [item]),)).execute(SearchCriteria())


def test_sqlite_repository_is_idempotent(tmp_path):
    item = Listing(source="fixture", url="https://example.com/l/1", title="Local", operation="rent", price=Decimal("1000"))
    result = run_for(item)
    repository = SQLiteListingRepository(tmp_path / "runtime" / "sauron.db")
    repository.save_run(result)
    repository.save_run(result)
    assert repository.count_runs() == 1
    assert repository.count_listings() == 1
    assert repository.count_observations() == 1
    with sqlite3.connect(tmp_path / "runtime" / "sauron.db") as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_sqlite_repository_detects_new_and_changed_listings(tmp_path):
    path = tmp_path / "sauron.db"
    repository = SQLiteListingRepository(path)
    first = Listing(source="fixture", url="https://example.com/l/1", title="Local", price=Decimal("1000"))
    second = Listing(source="fixture", url="https://example.com/l/1", title="Local", price=Decimal("1200"))
    first_changes = repository.save_run(run_for(first))
    second_changes = repository.save_run(run_for(second))
    assert first_changes[0].kind == "new"
    assert second_changes[0].kind == "changed"
    assert second_changes[0].changed_fields == ("price",)
    assert repository.count_runs() == 2
    assert repository.count_observations() == 2
