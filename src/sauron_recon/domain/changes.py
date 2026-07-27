from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import Listing


ChangeKind = Literal["new", "changed", "unchanged", "disappeared"]


@dataclass(frozen=True)
class ListingChange:
    listing: Listing
    kind: ChangeKind
    changed_fields: tuple[str, ...] = ()

    @property
    def is_actionable(self) -> bool:
        return self.kind in {"new", "changed", "disappeared"}
