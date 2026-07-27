from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from sauron_recon.application.ports import SearchResult
from sauron_recon.domain.changes import ListingChange
from sauron_recon.domain.models import Listing


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  listing_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  failures_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
  identity TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  source TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  operation TEXT,
  zone TEXT,
  price TEXT,
  currency TEXT,
  area_m2 TEXT,
  address TEXT,
  observed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  identity TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  title TEXT NOT NULL,
  price TEXT,
  currency TEXT,
  area_m2 TEXT,
  address TEXT,
  PRIMARY KEY (run_id, identity)
);
CREATE INDEX IF NOT EXISTS observations_identity_time
  ON observations(identity, observed_at DESC);
"""


def _fingerprint(listing: Listing) -> str:
    payload = "|".join(str(value or "") for value in (
        listing.title, listing.price, listing.currency, listing.area_m2, listing.address,
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _changed_fields(previous: sqlite3.Row | None, listing: Listing) -> tuple[str, ...]:
    if previous is None:
        return ()
    current = {
        "title": listing.title,
        "price": str(listing.price) if listing.price is not None else None,
        "currency": listing.currency,
        "area_m2": str(listing.area_m2) if listing.area_m2 is not None else None,
        "address": listing.address,
    }
    return tuple(field for field, value in current.items() if previous[field] != value)


class SQLiteListingRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(_SCHEMA)

    def save_run(self, result: SearchResult) -> tuple[ListingChange, ...]:
        self.initialize()
        changes: list[ListingChange] = []
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            already_saved = connection.execute("SELECT 1 FROM runs WHERE run_id = ?", (result.run_id,)).fetchone()
            if already_saved:
                return ()
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?)",
                (result.run_id, result.started_at.isoformat(), len(result.listings), len(result.failures),
                 json.dumps([failure.__dict__ for failure in result.failures])),
            )
            for listing in result.listings:
                previous = connection.execute(
                    """SELECT title, price, currency, area_m2, address
                    FROM observations WHERE identity = ? ORDER BY observed_at DESC LIMIT 1""",
                    (listing.identity,),
                ).fetchone()
                kind = "new" if previous is None else ("changed" if _changed_fields(previous, listing) else "unchanged")
                changes.append(ListingChange(listing, kind, _changed_fields(previous, listing)))
                connection.execute(
                    """INSERT OR IGNORE INTO listings
                    (identity, run_id, source, url, title, operation, zone, price, currency, area_m2, address, observed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (listing.identity, result.run_id, listing.source, listing.url, listing.title, listing.operation,
                     listing.zone, str(listing.price) if listing.price is not None else None, listing.currency,
                     str(listing.area_m2) if listing.area_m2 is not None else None, listing.address,
                     listing.observed_at.isoformat()),
                )
                connection.execute(
                    """INSERT INTO observations
                    (run_id, identity, observed_at, fingerprint, title, price, currency, area_m2, address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (result.run_id, listing.identity, listing.observed_at.isoformat(), _fingerprint(listing),
                     listing.title, str(listing.price) if listing.price is not None else None, listing.currency,
                     str(listing.area_m2) if listing.area_m2 is not None else None, listing.address),
                )
        return tuple(changes)

    def count_runs(self) -> int:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]

    def count_listings(self) -> int:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM listings").fetchone()[0]

    def count_observations(self) -> int:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
