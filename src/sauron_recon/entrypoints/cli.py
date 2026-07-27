from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

from sauron_recon.adapters.firecrawl_client import FirecrawlClient
from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.adapters.portal_sources import build_portal_sources
from sauron_recon.adapters.sqlite import SQLiteListingRepository
from sauron_recon.application.reporting import render_report
from sauron_recon.application.use_cases import SearchListings
from sauron_recon.domain.models import SearchCriteria


def parse_criteria(raw: str) -> SearchCriteria:
    data = json.loads(raw)
    return SearchCriteria(
        operation=data.get("operation", "rent"),
        zones=tuple(data.get("zones", [])),
        min_price=Decimal(str(data["min_price"])) if data.get("min_price") is not None else None,
        max_price=Decimal(str(data["max_price"])) if data.get("max_price") is not None else None,
        currency=data.get("currency"),
        min_area_m2=Decimal(str(data["min_area_m2"])) if data.get("min_area_m2") is not None else None,
        max_area_m2=Decimal(str(data["max_area_m2"])) if data.get("max_area_m2") is not None else None,
        property_type=data.get("property_type", "local"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sauron-recon")
    subparsers = parser.add_subparsers(dest="command", required=True)
    search = subparsers.add_parser("search", help="run a saved criteria search")
    search.add_argument("--criteria", required=True, help="criteria JSON")
    search.add_argument("--dry-run", action="store_true", help="do not persist or notify")
    search.add_argument("--live", action="store_true", help="query the existing Firecrawl daemon")
    search.add_argument("--limit", type=int, default=10, help="maximum Firecrawl results")
    search.add_argument("--scrape-details", action="store_true", help="scrape each allowed result URL")
    search.add_argument("--report", action="store_true", help="render a Markdown report")
    search.add_argument("--sources", default="zonaprop,argenprop,mercadolibre", help="comma-separated portal adapters")
    subparsers.add_parser("health", help="check that the deterministic core imports")
    args = parser.parse_args(argv)

    if args.command == "health":
        print(json.dumps({"ok": True, "component": "sauron-recon-core"}))
        return 0

    try:
        criteria = parse_criteria(args.criteria)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2

    if args.live:
        client = FirecrawlClient(
            base_url=os.getenv("FIRECRAWL_API_URL", "http://localhost:3002"),
            api_key=os.getenv("FIRECRAWL_API_KEY") or None,
        )
        sources = build_portal_sources(
            client,
            tuple(name.strip() for name in args.sources.split(",") if name.strip()),
            max_results=max(1, min(args.limit, 50)),
            scrape_details=args.scrape_details,
            max_detail_pages=max(1, min(args.limit, 5)),
        )
    else:
        sources = (InMemorySource("offline-fixture"),)

    try:
        result = SearchListings(sources).execute(criteria)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"search failed: {type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1

    if not args.dry_run:
        data_dir = Path(os.getenv("SAURON_RECON_DATA_DIR", "./runtime"))
        changes = SQLiteListingRepository(data_dir / "sauron-recon.sqlite3").save_run(result)
    else:
        changes = ()

    if args.report:
        print(render_report(result, changes))
        return 0

    print(json.dumps({
        "ok": True,
        "run_id": result.run_id,
        "mode": "live" if args.live else "offline",
        "dry_run": args.dry_run,
        "changes": [{"identity": change.listing.identity, "kind": change.kind,
                     "changed_fields": change.changed_fields} for change in changes],
        "listings": [
            {"source": item.source, "url": item.url, "title": item.title,
             "price": str(item.price) if item.price is not None else None,
             "area_m2": str(item.area_m2) if item.area_m2 is not None else None}
            for item in result.listings
        ],
        "failures": [failure.__dict__ for failure in result.failures],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
