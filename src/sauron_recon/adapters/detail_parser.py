from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from urllib.parse import urlsplit

from sauron_recon.domain.models import Listing


class PageKind(StrEnum):
    DETAIL = "detail"
    CATEGORY = "category"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedDetail:
    title: str
    operation: str | None
    price: Decimal | None
    currency: str | None
    area_m2: Decimal | None
    address: str | None = None
    expenses: Decimal | None = None
    contact: str | None = None
    external_id: str | None = None


_PRICE_RE = re.compile(r"(?P<currency>US\$|U\$S|USD|\$)\s*:?\s*(?P<value>\d[\d.]*(?:,\d+)?)", re.IGNORECASE)
_AREA_RE = re.compile(r"(?P<value>\d[\d.]*(?:,\d+)?)\s*m(?:2|²)\s*(?P<label>tot(?:al)?|cub(?:iertos?)?)?", re.IGNORECASE)
_EXPENSES_RE = re.compile(r"expensas?\s*(?:de|:)?\s*(?:US\$|U\$S|USD|\$)?\s*(?P<value>\d[\d.]*(?:,\d+)?)", re.IGNORECASE)
_TITLE_LINK_RE = re.compile(r"\[[^\]]+\]\((?P<url>https?://[^)\s]+)", re.IGNORECASE)


def classify_url(url: str) -> PageKind:
    parts = urlsplit(url.lower())
    host = parts.hostname or ""
    path = parts.path
    if "zonaprop.com.ar" in host:
        if "/propiedades/clasificado/" in path:
            return PageKind.DETAIL
        if "/locales-comerciales-" in path or path.rstrip("/").endswith("/locales"):
            return PageKind.CATEGORY
    if "argenprop.com" in host:
        if re.search(r"(?:local|oficina|inmueble).*-\d+/?$", path):
            return PageKind.DETAIL
        if "/locales/" in path:
            return PageKind.CATEGORY
    if "inmueble.mercadolibre.com.ar" in host and re.search(r"/MLA-\d+", path, re.IGNORECASE):
        return PageKind.DETAIL
    if "inmuebles.mercadolibre.com.ar" in host:
        return PageKind.CATEGORY
    return PageKind.UNKNOWN


def _decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(".", "").replace(",", "."))
    except Exception:
        return None


def parse_detail(markdown: str, fallback_title: str = "Listing sin título", url: str | None = None) -> ParsedDetail:
    text = re.sub(r"\s+", " ", markdown).strip()
    title = fallback_title.strip() or "Listing sin título"
    headings = [re.sub(r"\s+", " ", heading).strip() for heading in re.findall(r"^#{1,6}\s+(.+)$", markdown, re.MULTILINE)]
    if headings:
        title = next((heading for heading in headings if re.search(r"local|oficina|alquiler|venta", heading, re.IGNORECASE)), headings[0])
    operation = None
    lower = text.lower()
    if re.search(r"\balquiler\b|\balquila\b", lower):
        operation = "rent"
    elif re.search(r"\bventa\b|\bvender\b", lower):
        operation = "sale"
    price_match = _PRICE_RE.search(text)
    currency = None
    price = None
    if price_match:
        price = _decimal(price_match.group("value"))
        currency = "USD" if price_match.group("currency").upper() in {"USD", "US$", "U$S"} else "ARS"
    areas = list(_AREA_RE.finditer(text))
    area_m2 = None
    if areas:
        preferred = next((m for m in areas if (m.group("label") or "").lower().startswith("tot")), areas[0])
        area_m2 = _decimal(preferred.group("value"))
    address = None
    location_match = re.search(r"(?:ubicación|direccion|dirección)\s*[:\-]?\s*([^|]+)", text, re.IGNORECASE)
    if location_match:
        address = location_match.group(1).strip()[:300]
    expenses_match = _EXPENSES_RE.search(text)
    expenses = _decimal(expenses_match.group("value")) if expenses_match else None
    contact = "public_contact_indicator" if re.search(r"whatsapp|contactar|tel[eé]fono|email", lower) else None
    external_id = None
    if url:
        id_match = re.search(r"(?:MLA[-_]?|--)(\d{6,})", url, re.IGNORECASE)
        external_id = id_match.group(1) if id_match else None
    return ParsedDetail(title, operation, price, currency, area_m2, address, expenses, contact, external_id)


def extract_detail_links(markdown: str, allowed_domains: tuple[str, ...], limit: int) -> tuple[str, ...]:
    links: list[str] = []
    for match in _TITLE_LINK_RE.finditer(markdown):
        url = match.group("url").split("#", 1)[0]
        host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
        if not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
            continue
        if classify_url(url) is not PageKind.DETAIL or url in links:
            continue
        links.append(url)
        if len(links) >= limit:
            break
    return tuple(links)


def listing_from_detail(source: str, url: str, parsed: ParsedDetail, raw_markdown: str) -> Listing:
    return Listing(
        source=source,
        url=url,
        title=parsed.title,
        operation=parsed.operation,
        price=parsed.price,
        currency=parsed.currency,
        area_m2=parsed.area_m2,
        address=parsed.address,
        external_id=parsed.external_id,
        expenses=parsed.expenses,
        contact=parsed.contact,
        raw={"page_kind": PageKind.DETAIL.value, "markdown": raw_markdown[:4000]},
    )
