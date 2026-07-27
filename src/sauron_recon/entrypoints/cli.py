from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from sauron_recon.adapters.in_memory import InMemorySource
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
    search = subparsers.add_parser("search", help="validate criteria and run the offline core")
    search.add_argument("--criteria", required=True, help="criteria JSON")
    search.add_argument("--dry-run", action="store_true", help="do not notify or persist")
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

    result = SearchListings((InMemorySource("offline-fixture"),)).execute(criteria)
    print(json.dumps({
        "ok": True,
        "run_id": result.run_id,
        "dry_run": args.dry_run,
        "listings": len(result.listings),
        "failures": [failure.__dict__ for failure in result.failures],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
