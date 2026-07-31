from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sauron_recon.domain.models import Listing, SearchCriteria


_FIELD_ALIASES = {
    "url": ("url", "link", "permalink", "enlace"),
    "title": ("title", "titulo", "name", "nombre"),
    "operation": ("operation", "operacion", "tipo_operacion"),
    "zone": ("zone", "zona", "locality", "localidad", "location", "ubicacion"),
    "price": ("price", "precio", "amount", "importe"),
    "currency": ("currency", "moneda", "divisa"),
    "area_m2": ("area_m2", "area", "superficie", "metros"),
    "address": ("address", "direccion", "domicilio"),
    "external_id": ("external_id", "id", "codigo", "code"),
    "expenses": ("expenses", "expensas", "gastos"),
    "availability": ("availability", "disponibilidad", "estado"),
}


def _value(row: dict[str, Any], field: str) -> str | None:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for alias in _FIELD_ALIASES[field]:
        value = normalized.get(alias)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _decimal(raw: str | None) -> Decimal | None:
    if not raw:
        return None
    cleaned = re.sub(r"(?i)m(?:2|²)", "", raw)
    cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _operation(raw: str | None) -> str | None:
    value = (raw or "").lower()
    if any(token in value for token in ("alquil", "rent")):
        return "rent"
    if any(token in value for token in ("venta", "vend", "sale")):
        return "sale"
    return raw or None


@dataclass
class FeedSource:
    path: str | Path
    name: str = "authorized-feed"

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        rows = self._read_rows()
        listings = [self._listing(row) for row in rows]
        return [listing for listing in listings if self._matches(listing, criteria)]

    def _read_rows(self) -> list[dict[str, Any]]:
        path = Path(self.path).expanduser()
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open(newline="", encoding="utf-8-sig") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload = payload.get("listings", payload.get("items", []))
            if not isinstance(payload, list):
                raise ValueError("feed JSON must contain a list or listings/items list")
            return [row for row in payload if isinstance(row, dict)]
        if suffix == ".xml":
            root = ET.parse(path).getroot()
            rows = []
            for item in root.iter():
                children = list(item)
                if children and any(child.tag.lower().split("}")[-1] in _FIELD_ALIASES["url"] for child in children):
                    rows.append({child.tag.lower().split("}")[-1]: child.text or "" for child in children})
            return rows
        raise ValueError("unsupported feed format; use CSV, JSON or XML")

    def _listing(self, row: dict[str, Any]) -> Listing:
        url = _value(row, "url")
        title = _value(row, "title")
        if not url or not title:
            raise ValueError("feed listing requires url and title")
        price_raw = _value(row, "price")
        currency = _value(row, "currency")
        if currency is None and price_raw:
            currency = "USD" if re.search(r"USD|US\$|U\$S", price_raw, re.IGNORECASE) else "ARS" if "$" in price_raw else None
        return Listing(
            source=self.name,
            url=url,
            title=title,
            operation=_operation(_value(row, "operation")),
            zone=_value(row, "zone"),
            price=_decimal(price_raw),
            currency=currency,
            area_m2=_decimal(_value(row, "area_m2")),
            address=_value(row, "address"),
            external_id=_value(row, "external_id"),
            expenses=_decimal(_value(row, "expenses")),
            availability=_value(row, "availability"),
            raw={"feed_path": str(self.path)},
        )

    @staticmethod
    def _matches(listing: Listing, criteria: SearchCriteria) -> bool:
        if criteria.operation != "rent_or_sale" and listing.operation and listing.operation != criteria.operation:
            return False
        if criteria.zones and listing.zone:
            haystack = listing.zone.lower()
            if not any(zone.lower() in haystack for zone in criteria.zones):
                return False
        if criteria.min_area_m2 is not None and (listing.area_m2 is None or listing.area_m2 < criteria.min_area_m2):
            return False
        if criteria.max_area_m2 is not None and (listing.area_m2 is None or listing.area_m2 > criteria.max_area_m2):
            return False
        return True
