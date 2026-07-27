from __future__ import annotations

from dataclasses import dataclass

from .models import Listing, SearchCriteria


@dataclass(frozen=True)
class Score:
    value: int
    reasons: tuple[str, ...]
    hard_match: bool


def score_listing(listing: Listing, criteria: SearchCriteria) -> Score:
    reasons: list[str] = []
    hard_match = True
    value = 0

    if listing.operation and criteria.operation != "rent_or_sale" and listing.operation != criteria.operation:
        return Score(0, ("operation mismatch",), False)
    if listing.operation:
        value += 25
        reasons.append("operation matches")
    if criteria.zones:
        haystack = " ".join(filter(None, (listing.zone, listing.address, listing.title))).casefold()
        if any(zone.casefold() in haystack for zone in criteria.zones):
            value += 25
            reasons.append("zone matches")
        else:
            hard_match = False
            reasons.append("zone not confirmed")
    if criteria.max_price is not None:
        if listing.price is None:
            hard_match = False
            reasons.append("price unavailable")
        elif listing.price <= criteria.max_price:
            value += 20
            reasons.append("price within maximum")
        else:
            return Score(0, ("price exceeds maximum",), False)
    if criteria.min_price is not None and listing.price is not None and listing.price >= criteria.min_price:
        value += 5
        reasons.append("price above minimum")
    if criteria.min_area_m2 is not None:
        if listing.area_m2 is None:
            hard_match = False
            reasons.append("area unavailable")
        elif listing.area_m2 >= criteria.min_area_m2:
            value += 20
            reasons.append("area meets minimum")
        else:
            return Score(0, ("area below minimum",), False)
    if criteria.max_area_m2 is not None and listing.area_m2 is not None and listing.area_m2 <= criteria.max_area_m2:
        value += 5
        reasons.append("area within maximum")
    return Score(value, tuple(reasons), hard_match)
