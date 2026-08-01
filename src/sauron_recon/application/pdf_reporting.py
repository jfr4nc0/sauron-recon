from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from sauron_recon.application.ports import SearchResult
from sauron_recon.domain.changes import ListingChange


def render_pdf(result: SearchResult, changes: Iterable[ListingChange], output: str | Path) -> Path:
    """Render a report PDF with all observed listings and a change summary."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF reports require the 'pdf' optional dependency (reportlab)") from exc

    change_list = list(changes)
    change_map: dict[str, ListingChange] = {}
    for change in change_list:
        change_map.setdefault(change.listing.identity, change)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    story: list = [Paragraph(f"Sauron Recon — corrida {result.run_id}", styles["Title"]), Spacer(1, 8)]

    total = len(result.listings)
    new_count = sum(1 for c in change_map.values() if c.kind == "new")
    changed_count = sum(1 for c in change_map.values() if c.kind == "changed")
    story.append(Paragraph(f"Listings observados: {total}", normal))
    story.append(Paragraph(f"Nuevos: {new_count} — Modificados: {changed_count}", normal))
    story.append(Paragraph(f"Candidatos de duplicado cross-source: {len(result.duplicate_candidates)}", normal))
    story.append(Spacer(1, 10))
    rows = [["Estado", "Fuente", "Aviso", "Descripción", "Precio", "Superficie", "Enlace"]]
    for listing in result.listings:
        change = change_map.get(listing.identity)
        kind = change.kind if change else "observado"
        description = " ".join(str(listing.raw.get("markdown", "")).split())
        description = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", description)
        description = re.sub(r"https?://\S+", "", description)
        description = re.sub(r"\s{3,}", "  ", description).strip()
        description = description[:240] + ("…" if len(description) > 240 else "")
        price = f"{listing.price} {listing.currency or ''}".strip() if listing.price is not None else "—"
        area = f"{listing.area_m2} m²" if listing.area_m2 is not None else "—"
        rows.append([kind, listing.source, listing.title[:90], description or "—", price, area, listing.url])
    table = Table(rows, colWidths=[18 * mm, 20 * mm, 42 * mm, 55 * mm, 25 * mm, 22 * mm, 28 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f7")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))
    for failure in result.failures:
        story.append(Paragraph(f"Advertencia {failure.source}: {failure.message}", normal))
    SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm).build(story)
    return output_path
