from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"invalid listing URL: {url!r}")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))


@dataclass(frozen=True)
class SearchCriteria:
    operation: str = "rent"
    zones: tuple[str, ...] = ()
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    currency: str | None = None
    min_area_m2: Decimal | None = None
    max_area_m2: Decimal | None = None
    property_type: str = "local"

    def __post_init__(self) -> None:
        if self.operation not in {"rent", "sale", "rent_or_sale"}:
            raise ValueError("operation must be rent, sale, or rent_or_sale")
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot exceed max_price")
        if self.min_area_m2 is not None and self.max_area_m2 is not None and self.min_area_m2 > self.max_area_m2:
            raise ValueError("min_area_m2 cannot exceed max_area_m2")


@dataclass(frozen=True)
class Listing:
    source: str
    url: str
    title: str
    operation: str | None = None
    zone: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    area_m2: Decimal | None = None
    address: str | None = None
    observed_at: datetime = field(default_factory=utc_now)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    external_id: str | None = None
    expenses: Decimal | None = None
    contact: str | None = None
    availability: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "url", canonical_url(self.url))
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.title.strip():
            raise ValueError("title is required")

    @property
    def identity(self) -> str:
        return f"{self.source}:{self.url}"
