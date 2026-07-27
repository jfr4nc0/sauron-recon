from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sauron_recon.application.ports import SearchResult


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
"""


class SQLiteListingRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(_SCHEMA)

    def save_run(self, result: SearchResult) -> None:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?, ?, ?, ?)",
                (result.run_id, result.started_at.isoformat(), len(result.listings), len(result.failures),
                 json.dumps([failure.__dict__ for failure in result.failures])),
            )
            connection.executemany(
                """INSERT OR IGNORE INTO listings
                (identity, run_id, source, url, title, operation, zone, price, currency, area_m2, address, observed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(listing.identity, result.run_id, listing.source, listing.url, listing.title, listing.operation,
                  listing.zone, str(listing.price) if listing.price is not None else None, listing.currency,
                  str(listing.area_m2) if listing.area_m2 is not None else None, listing.address,
                  listing.observed_at.isoformat()) for listing in result.listings],
            )

    def count_runs(self) -> int:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]

    def count_listings(self) -> int:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
