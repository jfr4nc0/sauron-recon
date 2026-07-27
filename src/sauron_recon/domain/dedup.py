from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import Listing


@dataclass(frozen=True)
class DuplicateCandidate:
    first: Listing
    second: Listing
    reasons: tuple[str, ...]


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _tokens(value: str | None) -> set[str]:
    return {token for token in _normalize(value).split() if len(token) > 2}


def find_duplicate_candidates(listings: tuple[Listing, ...]) -> tuple[DuplicateCandidate, ...]:
    candidates: list[DuplicateCandidate] = []
    for index, first in enumerate(listings):
        for second in listings[index + 1:]:
            if first.source == second.source:
                continue
            reasons: list[str] = []
            if first.address and second.address and _normalize(first.address) == _normalize(second.address):
                reasons.append("same_address")
            if first.area_m2 is not None and second.area_m2 is not None and first.area_m2 == second.area_m2:
                reasons.append("same_area")
            overlap = _tokens(first.title) & _tokens(second.title)
            if len(overlap) >= 3:
                reasons.append("title_overlap")
            if ("same_address" in reasons and "same_area" in reasons) or len(reasons) >= 2:
                candidates.append(DuplicateCandidate(first, second, tuple(reasons)))
    return tuple(candidates)
