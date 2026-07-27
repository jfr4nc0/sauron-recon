from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from sauron_recon.domain.models import SearchCriteria

from .ports import SearchResult, SourceFailure, SourcePort


@dataclass
class SearchListings:
    sources: tuple[SourcePort, ...]

    def execute(self, criteria: SearchCriteria) -> SearchResult:
        started_at = datetime.now(timezone.utc)
        run_id = sha256(f"{started_at.isoformat()}:{criteria!r}".encode()).hexdigest()[:16]
        by_identity = {}
        failures: list[SourceFailure] = []
        for source in self.sources:
            try:
                for listing in source.search(criteria):
                    by_identity.setdefault(listing.identity, listing)
            except Exception as exc:  # boundary isolation: one source cannot abort the run
                failures.append(SourceFailure(source.name, type(exc).__name__, str(exc)))
        result = SearchResult(run_id, started_at, tuple(by_identity.values()), tuple(failures))
        return result
