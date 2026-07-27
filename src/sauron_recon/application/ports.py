from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sauron_recon.domain.dedup import DuplicateCandidate
from sauron_recon.domain.models import Listing, SearchCriteria


class SourcePort(Protocol):
    name: str

    def search(self, criteria: SearchCriteria) -> list[Listing]: ...


@dataclass(frozen=True)
class SourceFailure:
    source: str
    error_type: str
    message: str


@dataclass(frozen=True)
class SearchResult:
    run_id: str
    started_at: datetime
    listings: tuple[Listing, ...]
    failures: tuple[SourceFailure, ...]
    duplicate_candidates: tuple[DuplicateCandidate, ...] = ()


class ListingRepositoryPort(Protocol):
    def save_run(self, result: SearchResult) -> None: ...
