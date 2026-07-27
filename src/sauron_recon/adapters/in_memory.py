from __future__ import annotations

from collections.abc import Iterable

from sauron_recon.domain.models import Listing, SearchCriteria


class InMemorySource:
    def __init__(self, name: str, listings: Iterable[Listing] = (), error: Exception | None = None):
        self.name = name
        self._listings = tuple(listings)
        self._error = error

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        if self._error:
            raise self._error
        return list(self._listings)
