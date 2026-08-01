from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from sauron_recon.adapters.crawl4ai_client import Crawl4AIClient
from sauron_recon.adapters.crawl4ai_source import Crawl4AIDynamicSource
from sauron_recon.adapters.firecrawl_client import FirecrawlClient
from sauron_recon.adapters.feed_source import FeedSource
from sauron_recon.adapters.in_memory import InMemorySource
from sauron_recon.adapters.portal_sources import build_portal_sources
from sauron_recon.adapters.sqlite import SQLiteListingRepository
from sauron_recon.application.reporting import render_report
from sauron_recon.application.pdf_reporting import render_pdf
from sauron_recon.application.xlsx_reporting import render_xlsx
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
        rooms=data.get("rooms"),
        bathrooms=data.get("bathrooms"),
        min_price_ars=Decimal(str(data["min_price_ars"])) if data.get("min_price_ars") is not None else None,
        max_price_ars=Decimal(str(data["max_price_ars"])) if data.get("max_price_ars") is not None else None,
        min_price_usd=Decimal(str(data["min_price_usd"])) if data.get("min_price_usd") is not None else None,
        max_price_usd=Decimal(str(data["max_price_usd"])) if data.get("max_price_usd") is not None else None,
        needs_three_phase=data.get("needs_three_phase"),
        locality=data.get("locality"),
        requirements=tuple(data.get("requirements", [])),
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
    search.add_argument("--pdf", help="write a PDF report to this path")
    search.add_argument("--xlsx", help="write an Excel (.xlsx) report to this path")
    search.add_argument("--sources", default="zonaprop,argenprop,mercadolibre", help="comma-separated portal adapters")
    search.add_argument("--feed", action="append", default=[], help="local CSV/JSON/XML authorized feed; repeatable")
    search.add_argument("--crawl4ai-url", action="append", default=[], help="authorized public search URL rendered by local Crawl4AI; repeatable")
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

    feed_sources = tuple(
        FeedSource(path, name=f"feed:{Path(path).stem}")
        for path in args.feed
    )
    crawl_sources = []
    for search_url in args.crawl4ai_url:
        parsed = urlsplit(search_url)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or not host:
            print(json.dumps({"ok": False, "error": f"invalid --crawl4ai-url: {search_url}"}), file=sys.stderr)
            return 2
        crawl_sources.append(Crawl4AIDynamicSource(
            client=Crawl4AIClient(),
            name=f"crawl4ai:{host}",
            allowed_domains=(host,),
            search_url_builder=lambda _criteria, url=search_url: url,
        ))
    if args.live:
        client = FirecrawlClient(
            base_url=os.getenv("FIRECRAWL_API_URL", "http://localhost:3002"),
            api_key=os.getenv("FIRECRAWL_API_KEY") or None,
        )
        portal_sources = build_portal_sources(
            client,
            tuple(name.strip() for name in args.sources.split(",") if name.strip()),
            max_results=max(1, min(args.limit, 50)),
            scrape_details=args.scrape_details,
            max_detail_pages=max(1, min(args.limit, 5)),
        )
        sources = (*feed_sources, *crawl_sources, *portal_sources)
    elif feed_sources or crawl_sources:
        sources = (*feed_sources, *crawl_sources)
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
    if args.pdf:
        print(str(render_pdf(result, changes, args.pdf)))
    if args.xlsx:
        print(str(render_xlsx(result, changes, args.xlsx)))
    if args.report or args.pdf or args.xlsx:
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
             "area_m2": str(item.area_m2) if item.area_m2 is not None else None,
             "external_id": item.external_id, "expenses": str(item.expenses) if item.expenses is not None else None,
             "availability": item.availability, "contact": item.contact}
            for item in result.listings
        ],
        "failures": [failure.__dict__ for failure in result.failures],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
